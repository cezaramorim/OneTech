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
    # Campos Mantidos
    nome = models.CharField(max_length=255, unique=True)
    linha_producao = models.ForeignKey(LinhaProducao, on_delete=models.SET_NULL, null=True, blank=True, related_name='tanques_linha_producao')
    tipo_tanque = models.ForeignKey(TipoTanque, on_delete=models.SET_NULL, null=True, blank=True, related_name='tanques')
    status_tanque = models.ForeignKey(StatusTanque, on_delete=models.SET_NULL, null=True, blank=True, related_name='tanques_status')
    largura = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    comprimento = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    profundidade = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    ativo = models.BooleanField(default=True)

    data_criacao = models.DateTimeField(default=timezone.now)
    metro_cubico = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)
    metro_quadrado = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)
    ha = models.DecimalField(max_digits=10, decimal_places=4, editable=False, default=0, verbose_name="Hectares (ha)")
    unidade = models.ForeignKey(Unidade, on_delete=models.SET_NULL, null=True, blank=True)
    fase = models.ForeignKey(FaseProducao, on_delete=models.SET_NULL, null=True, blank=True)
    sequencia = models.IntegerField(default=0)
    malha = models.ForeignKey(Malha, on_delete=models.SET_NULL, null=True, blank=True)
    tag_tanque = models.CharField(max_length=100, blank=True)
    tipo_tela = models.ForeignKey(TipoTela, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Lógica de Cálculo
        if self.largura and self.comprimento:
            self.metro_quadrado = self.largura * self.comprimento
            self.ha = self.metro_quadrado / 10000
        else:
            self.metro_quadrado = Decimal('0')
            self.ha = Decimal('0')

        # metro_cubico agora depende apenas de profundidade, largura e comprimento
        if self.largura and self.comprimento and self.profundidade:
            self.metro_cubico = self.largura * self.comprimento * self.profundidade
        else:
            self.metro_cubico = Decimal('0')
            
        super().save(*args, **kwargs)

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
