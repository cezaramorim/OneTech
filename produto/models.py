import uuid
from django.db import models
from django.db.models import Sum
from decimal import Decimal
from django.utils.timezone import now
from empresas.models import EmpresaAvancada
from .models_fiscais import DetalhesFiscaisProduto

# 📦 Categoria de Produtos
class CategoriaProduto(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome


# 📐 Unidade de Medida (UN, KG, CX, etc.)
class UnidadeMedida(models.Model):
    sigla = models.CharField(max_length=10, unique=True)
    descricao = models.CharField(max_length=100)

    def __str__(self):
        return self.sigla


# 📚 Tabela de NCMs
class NCM(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    descricao = models.TextField()

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


# 🛒 Produto principal — agora usado também como item da nota
class Produto(models.Model):
    # 🔑 Identificação
    codigo_interno = models.CharField(max_length=50, unique=True, editable=False, help_text="Código único interno do produto (gerado automaticamente).")
    codigo_fornecedor = models.CharField(max_length=50, blank=True, null=True, help_text="Código do produto conforme fornecedor.")
    nome = models.CharField(max_length=255)

    # 📂 Classificações
    categoria = models.ForeignKey(CategoriaProduto, on_delete=models.SET_NULL, null=True, related_name='produtos')
    unidade_medida_interna = models.ForeignKey(UnidadeMedida, on_delete=models.SET_NULL, null=True, blank=True, related_name='produtos', help_text="Unidade de medida para controle interno de estoque.")
    
    TIPOS_PRODUTO = [
        ('Produto', 'Produto'),
        ('Insumo', 'Insumo'),
        ('Matéria-prima', 'Matéria-prima'),
    ]

    tipo = models.CharField(
        max_length=30,
        choices=TIPOS_PRODUTO,
        default='Produto',
        help_text="Classificação do produto para fins operacionais."
    )


    # 💰 Preços
    preco_custo = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    preco_venda = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    preco_medio = models.DecimalField(max_digits=18, decimal_places=10, default=0)

    # 📦 Estoque
    estoque_total = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    quantidade_saidas = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    estoque_atual = models.DecimalField(max_digits=18, decimal_places=10, default=0)

    controla_estoque = models.BooleanField(default=True)
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateField(default=now)

    # 🧾 Dados fiscais complementares
    codigo_barras = models.CharField(max_length=50, blank=True, null=True, help_text="Código de barras (EAN)")
    
    # 📝 Observações
    observacoes = models.TextField(blank=True, null=True)

    # 🔗 Fornecedor
    fornecedor = models.ForeignKey(
        EmpresaAvancada,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="produtos_fornecidos",
        help_text="Empresa fornecedora vinculada via XML da nota fiscal."
    )

    # 🧾 Nota fiscal de origem (para importação XML)
    nota_fiscal = models.ForeignKey(
        'nota_fiscal.NotaFiscal',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='produtos',
        help_text="Nota fiscal à qual este produto está vinculado (caso importado do XML)"
    )

    # 🔄 Conversão de Unidade
    fator_conversao = models.DecimalField(
        max_digits=18,
        decimal_places=10,
        default=1,
        help_text="Fator para converter a unidade de compra para a unidade interna. Ex: Se compra em CX com 12 UN, o fator é 12."
    )
    unidade_fornecedor_padrao = models.ForeignKey(UnidadeMedida, on_delete=models.SET_NULL, null=True, blank=True, related_name='produtos_unidade_fornecedor', help_text="Unidade de medida padrão usada pelo fornecedor para este produto.")

    def calcular_estoque_atual(self):
        return self.estoque_total - self.quantidade_saidas

    def recalculate_stock_and_prices(self):
        print(f"DEBUG: Iniciando recalculate_stock_and_prices para o produto: {self.nome} (ID: {self.pk})")
        from produto.models_entradas import EntradaProduto # Importação local para evitar circular dependency

        total_quantidade_entradas = Decimal('0')
        total_valor_entradas = Decimal('0')
        
        # Recalcula estoque_total e preco_medio com base nas entradas existentes
        entradas = EntradaProduto.objects.filter(item_nota_fiscal__produto=self)
        print(f"DEBUG: Encontradas {entradas.count()} entradas para o produto {self.nome}.")

        for entrada in entradas:
            # Aplica o fator de conversão atual do produto
            quantidade_convertida = entrada.quantidade * self.fator_conversao
            preco_unitario_convertido = entrada.preco_unitario / self.fator_conversao if self.fator_conversao > 0 else entrada.preco_unitario

            total_quantidade_entradas += quantidade_convertida
            total_valor_entradas += preco_unitario_convertido * quantidade_convertida
            print(f"DEBUG: Entrada {entrada.pk}: Quantidade XML: {entrada.quantidade}, Preço Unitário XML: {entrada.preco_unitario}, Quantidade Convertida: {quantidade_convertida}, Preço Convertido: {preco_unitario_convertido}")


        self.estoque_total = total_quantidade_entradas
        if total_quantidade_entradas > 0:
            self.preco_medio = total_valor_entradas / total_quantidade_entradas
            # O preco_custo pode ser o preco_medio ou o preco_unitario da última entrada,
            # dependendo da regra de negócio. Por simplicidade, usaremos o preco_medio.
            self.preco_custo = self.preco_medio
        else:
            self.preco_medio = Decimal('0')
            self.preco_custo = Decimal('0')

        self.estoque_atual = self.calcular_estoque_atual()
        print(f"DEBUG: Valores recalculados para {self.nome}: Estoque Total: {self.estoque_total}, Preço Médio: {self.preco_medio}, Preço Custo: {self.preco_custo}")
        self.save(update_fields=['estoque_total', 'preco_medio', 'preco_custo', 'estoque_atual'])
        print(f"DEBUG: Finalizado recalculate_stock_and_prices para o produto: {self.nome}")


    def save(self, *args, **kwargs):
        # Gerar codigo_interno se não existir e o produto for novo
        if not self.pk and not self.codigo_interno:
            self.codigo_interno = str(uuid.uuid4()).replace('-', '')[:20].upper()

        print(f"DEBUG: Método save do Produto chamado para {self.nome} (ID: {self.pk})")
        # Verifica se o fator_conversao foi alterado
        if self.pk: # Se o objeto já existe no banco de dados
            try:
                original = Produto.objects.get(pk=self.pk)
                if original.fator_conversao != self.fator_conversao:
                    print(f"DEBUG: Fator de conversão alterado de {original.fator_conversao} para {self.fator_conversao}. Recalculando estoque e preços.")
                    # Salva primeiro para garantir que o fator_conversao esteja atualizado
                    super().save(*args, **kwargs) 
                    self.recalculate_stock_and_prices()
                    return # Já salvou e recalculou, então retorna
            except Produto.DoesNotExist:
                print(f"DEBUG: Produto com ID {self.pk} não encontrado no banco de dados. Prosseguindo com save normal.")
                pass # Objeto não existe, é uma criação, prossegue com o save normal
        
        self.estoque_atual = self.calcular_estoque_atual()
        print(f"DEBUG: Salvando produto {self.nome} com estoque_atual: {self.estoque_atual}")
        super().save(*args, **kwargs)
        print(f"DEBUG: Produto {self.nome} salvo com sucesso.")


    def __str__(self):
        return f"{self.codigo_interno or self.codigo_fornecedor} - {self.nome}"
