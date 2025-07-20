from django.db import models
from produto.models import Produto # Importa o modelo Produto do app produto
from django.core.validators import MinValueValidator
from datetime import date # Importa date para calculo de GPD
from decimal import Decimal # Importa Decimal para cálculos precisos

class LinhaProducao(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Linha de Produção"
        verbose_name_plural = "Linhas de Produção"

    def __str__(self):
        return self.nome

class StatusTanque(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Status do Tanque"
        verbose_name_plural = "Status dos Tanques"

    def __str__(self):
        return self.nome

class FaseProducao(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Fase de Produção"
        verbose_name_plural = "Fases de Produção"

    def __str__(self):
        return self.nome

class TipoTanque(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Tipo de Tanque"
        verbose_name_plural = "Tipos de Tanque"

    def __str__(self):
        return self.nome

class Atividade(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Atividade"
        verbose_name_plural = "Atividades"

    def __str__(self):
        return self.nome

class CurvaCrescimento(models.Model):
    nome = models.CharField(max_length=255, unique=True)
    produto_racao = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True, related_name='curvas_crescimento')
    # Adicionar campos para a curva de crescimento (ex: dia, peso_medio, consumo_racao)
    # Isso pode ser uma relação OneToMany para um modelo CurvaCrescimentoDetalhe, ou um JSONField
    # Por simplicidade inicial, vamos considerar que os dados da curva serão inseridos via importação ou um campo mais complexo.

    class Meta:
        verbose_name = "Curva de Crescimento"
        verbose_name_plural = "Curvas de Crescimento"

    def __str__(self):
        return self.nome

class Tanque(models.Model):
    nome = models.CharField(max_length=255, unique=True)
    linha_producao = models.ForeignKey(LinhaProducao, on_delete=models.SET_NULL, null=True, blank=True, related_name='tanques')
    tipo_tanque = models.ForeignKey(TipoTanque, on_delete=models.SET_NULL, null=True, blank=True, related_name='tanques')
    atividade = models.ForeignKey(Atividade, on_delete=models.SET_NULL, null=True, blank=True, related_name='tanques')
    status_tanque = models.ForeignKey(StatusTanque, on_delete=models.SET_NULL, null=True, blank=True, related_name='tanques')
    largura = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    comprimento = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    profundidade = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    ativo = models.BooleanField(default=True)

    @property
    def area_m2(self):
        return self.largura * self.comprimento

    @property
    def volume_m3(self):
        return self.largura * self.comprimento * self.profundidade

    class Meta:
        verbose_name = "Tanque"
        verbose_name_plural = "Tanques"

    def __str__(self):
        return self.nome

class Lote(models.Model):
    nome = models.CharField(max_length=255)
    curva_crescimento = models.ForeignKey(CurvaCrescimento, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes')
    fase_producao = models.ForeignKey(FaseProducao, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes')
    tanque_atual = models.ForeignKey(Tanque, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes_no_tanque')
    quantidade_inicial = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    peso_medio_inicial = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    data_povoamento = models.DateField()
    ativo = models.BooleanField(default=True)

    # Campos calculados (serão atualizados por eventos de manejo)
    quantidade_atual = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    peso_medio_atual = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    @property
    def biomassa_inicial(self):
        return self.quantidade_inicial * self.peso_medio_inicial

    @property
    def biomassa_atual(self):
        return self.quantidade_atual * self.peso_medio_atual

    @property
    def gpd(self):
        if self.data_povoamento and self.peso_medio_inicial and self.peso_medio_atual:
            dias_cultivo = (date.today() - self.data_povoamento).days
            if dias_cultivo > 0:
                return (self.peso_medio_atual - self.peso_medio_inicial) / dias_cultivo
        return Decimal('0.0') # Retorna Decimal para consistência

    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"

    def __str__(self):
        return self.nome

class EventoManejo(models.Model):
    TIPO_EVENTO_CHOICES = [
        ('Povoamento', 'Povoamento'),
        ('Transferencia', 'Transferência'),
        ('Classificacao', 'Classificação'),
        ('Despesca', 'Despesca'),
        ('Mortalidade', 'Mortalidade'),
        ('Outro', 'Outro'),
    ]
    tipo_evento = models.CharField(max_length=50, choices=TIPO_EVENTO_CHOICES)
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='eventos_manejo')
    tanque_origem = models.ForeignKey(Tanque, on_delete=models.SET_NULL, null=True, blank=True, related_name='eventos_origem')
    tanque_destino = models.ForeignKey(Tanque, on_delete=models.SET_NULL, null=True, blank=True, related_name='eventos_destino')
    data_evento = models.DateField()
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    peso_medio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    observacoes = models.TextField(blank=True, null=True)

    @property
    def biomassa(self):
        return self.quantidade * self.peso_medio

    class Meta:
        verbose_name = "Evento de Manejo"
        verbose_name_plural = "Eventos de Manejo"

    def __str__(self):
        return f"{self.tipo_evento} - {self.lote.nome} em {self.data_evento}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.tipo_evento == 'Povoamento':
            self.lote.quantidade_atual = self.quantidade
            self.lote.peso_medio_atual = self.peso_medio
            self.lote.tanque_atual = self.tanque_destino
            self.lote.save()
        elif self.tipo_evento == 'Transferencia':
            # Lógica para Transferência
            # Se o lote está sendo transferido para um novo tanque
            if self.tanque_destino and self.lote.tanque_atual != self.tanque_destino:
                self.lote.tanque_atual = self.tanque_destino
            # A quantidade e peso médio do lote são atualizados com base no evento
            self.lote.quantidade_atual = self.quantidade
            self.lote.peso_medio_atual = self.peso_medio
            self.lote.save()
        elif self.tipo_evento == 'Classificacao':
            # Lógica para Classificação
            # A classificação pode resultar na divisão do lote ou na remoção de parte dele.
            # Por simplicidade, vamos considerar que a quantidade e peso médio do evento
            # representam o que *resta* no lote principal após a classificação.
            self.lote.quantidade_atual = self.quantidade
            self.lote.peso_medio_atual = self.peso_medio
            self.lote.save()
        elif self.tipo_evento == 'Despesca':
            # Lógica para Despesca
            # A despesca remove peixes do lote.
            self.lote.quantidade_atual -= self.quantidade
            # O peso médio pode ser recalculado se houver uma amostra do peso dos peixes restantes.
            # Por enquanto, manteremos o peso médio do evento como o peso dos peixes despescados.
            # Se o peso médio do lote precisar ser atualizado, seria necessário um cálculo mais complexo
            # baseado na biomassa restante e quantidade.
            self.lote.save()
        elif self.tipo_evento == 'Mortalidade':
            # Lógica para Mortalidade
            # Diminui a quantidade de peixes no lote.
            self.lote.quantidade_atual -= self.quantidade
            self.lote.save()
        # O tipo 'Outro' não exige atualização automática do lote, mas pode ser usado para registros diversos.

class AlimentacaoDiaria(models.Model):
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='alimentacoes_diarias')
    produto_racao = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True, related_name='alimentacoes_consumidas')
    data_alimentacao = models.DateField()
    quantidade_racao = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    observacoes = models.TextField(blank=True, null=True)

    @property
    def custo_racao(self):
        if self.produto_racao and self.produto_racao.preco_custo:
            return self.quantidade_racao * self.produto_racao.preco_custo
        return Decimal('0.0') # Retorna Decimal para consistência

    @property
    def tca(self):
        # TCA (Taxa de Conversão Alimentar) = Ração Consumida / Ganho de Peso
        # Esta é uma implementação simplificada para um único evento de alimentação.
        # Uma TCA mais precisa exigiria a soma da ração consumida e o ganho de peso
        # de um lote ao longo de um período, o que envolveria consultas mais complexas.
        if self.lote and self.lote.biomassa_inicial and self.lote.biomassa_atual and self.quantidade_racao:
            ganho_peso = self.lote.biomassa_atual - self.lote.biomassa_inicial
            if ganho_peso > 0:
                return self.quantidade_racao / ganho_peso
        return Decimal('0.0') # Retorna Decimal para consistência

    class Meta:
        verbose_name = "Alimentação Diária"
        verbose_name_plural = "Alimentações Diárias"

    def __str__(self):
        return f"Alimentação do Lote {self.lote.nome} em {self.data_alimentacao}"
