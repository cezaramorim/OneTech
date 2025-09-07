from django.db import models
from django.utils import timezone
from produto.models import Produto # Importa o modelo Produto do app produto
from django.core.validators import MinValueValidator
from datetime import date # Importa date para calculo de GPD
from decimal import Decimal # Importa Decimal para cálculos precisos

# NOVOS MODELOS DE SUPORTE
class Unidade(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    class Meta:
        verbose_name = "Unidade"
        verbose_name_plural = "Unidades"
    def __str__(self):
        return self.nome

class Malha(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    class Meta:
        verbose_name = "Malha"
        verbose_name_plural = "Malhas"
    def __str__(self):
        return self.nome

class TipoTela(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    class Meta:
        verbose_name = "Tipo de Tela"
        verbose_name_plural = "Tipos de Tela"
    def __str__(self):
        return self.nome

# MODELOS EXISTENTES
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

# Modelo para o cabeçalho da Curva de Crescimento
class CurvaCrescimento(models.Model):
    nome = models.CharField(max_length=255, unique=True, help_text="Nome único para a curva, ex: Curva Tilápia Verão 2025")
    especie = models.CharField(max_length=100, default='', help_text="Espécie do animal, ex: Tilápia")
    rendimento_perc = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Percentual de rendimento da carcaça")
    trato_perc_curva = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Percentual de trato da curva")
    peso_pretendido = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Peso pretendido (em gramas)")
    trato_sabados_perc = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Percentual de trato aos sábados")
    trato_domingos_perc = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Percentual de trato aos domingos")
    trato_feriados_perc = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Percentual de trato aos feriados")

    class Meta:
        verbose_name = "Curva de Crescimento"
        verbose_name_plural = "Curvas de Crescimento"
        ordering = ['nome']

    def __str__(self):
        return self.nome

# Modelo para os detalhes (linhas) da Curva de Crescimento
class CurvaCrescimentoDetalhe(models.Model):
    curva = models.ForeignKey(CurvaCrescimento, on_delete=models.CASCADE, related_name='detalhes')
    periodo_semana = models.IntegerField(help_text="Número do período ou semana do ciclo", default=0)
    periodo_dias = models.IntegerField(help_text="Número de dias no período (ex: 7)", default=0)
    peso_inicial = models.DecimalField(max_digits=10, decimal_places=2, help_text="Peso inicial do animal no período (em gramas)", default=0)
    peso_final = models.DecimalField(max_digits=10, decimal_places=2, help_text="Peso final do animal no período (em gramas)", default=0)
    ganho_de_peso = models.DecimalField(max_digits=10, decimal_places=2, help_text="Ganho de peso total no período (em gramas)", default=0)
    numero_tratos = models.IntegerField(help_text="Número de tratos de ração por dia", default=0)
    hora_inicio = models.TimeField(help_text="Hora de início do primeiro trato do dia", default='00:00')
    arracoamento_biomassa_perc = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentual de arraçoamento sobre a biomassa", default=0)
    mortalidade_presumida_perc = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentual de mortalidade presumida para o período", default=0)
    racao = models.ForeignKey(
        Produto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='curvas_crescimento',
        help_text="Ração utilizada no período (vinculada ao cadastro de produtos)"
    )
    gpd = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ganho de Peso Diário (g)", default=0)
    tca = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Taxa de Conversão Alimentar", default=0)

    class Meta:
        verbose_name = "Detalhe da Curva de Crescimento"
        verbose_name_plural = "Detalhes da Curva de Crescimento"
        ordering = ['curva', 'periodo_semana']
        unique_together = ('curva', 'periodo_semana') # Garante que cada período é único para uma curva

    def __str__(self):
        return f"{self.curva.nome} - Semana {self.periodo_semana}"

class Tanque(models.Model):
    nome = models.CharField(max_length=120)
    largura = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    comprimento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    profundidade = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    metro_quadrado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    metro_cubico   = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    ha             = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)

    unidade = models.ForeignKey('producao.Unidade', on_delete=models.SET_NULL, null=True, blank=True)
    fase = models.ForeignKey('producao.FaseProducao', on_delete=models.SET_NULL, null=True, blank=True)
    tipo_tanque = models.ForeignKey('producao.TipoTanque', on_delete=models.SET_NULL, null=True, blank=True)
    linha_producao = models.ForeignKey('producao.LinhaProducao', on_delete=models.SET_NULL, null=True, blank=True)
    malha = models.ForeignKey('producao.Malha', on_delete=models.SET_NULL, null=True, blank=True)
    status_tanque = models.ForeignKey('producao.StatusTanque', on_delete=models.SET_NULL, null=True, blank=True)
    tipo_tela = models.ForeignKey('producao.TipoTela', on_delete=models.SET_NULL, null=True, blank=True)

    sequencia = models.PositiveIntegerField(null=True, blank=True)
    tag_tanque = models.CharField(max_length=100, blank=True)
    ativo = models.BooleanField(default=True)

    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.id} - {self.nome}'

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

    tipo_movimento = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Indica se o evento representa uma entrada ou saída de peixes."
    )
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

    def _liberar_tanque_se_vazio(self, lote):
        """Verifica se um lote ficou vazio e, em caso afirmativo, libera o tanque."""
        if lote.quantidade_atual <= 0:
            lote.ativo = False
            tanque_a_liberar = lote.tanque_atual
            if tanque_a_liberar:
                try:
                    status_livre = StatusTanque.objects.get(nome__iexact='Livre')
                    tanque_a_liberar.status_tanque = status_livre
                    tanque_a_liberar.save(update_fields=['status_tanque'])
                except StatusTanque.DoesNotExist:
                    # Idealmente, logar um erro aqui. Por enquanto, a falha é silenciosa
                    # para não interromper o fluxo principal por um status faltante.
                    pass
            lote.tanque_atual = None
            lote.save(update_fields=['ativo', 'tanque_atual'])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

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
