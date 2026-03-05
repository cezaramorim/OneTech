from django.db import models
from django.conf import settings
from django.utils import timezone
from produto.models import Produto
from django.core.validators import MinValueValidator
from datetime import date
from decimal import Decimal
import math

# Importa as funções de cálculo para uso nas propriedades
from django.db.models import Q
from .utils_uom import calc_biomassa_kg, g_to_kg

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

class TipoEvento(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Tipo de Evento"
        verbose_name_plural = "Tipos de Evento"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class CurvaCrescimento(models.Model):
    nome = models.CharField(max_length=255, unique=True, help_text="Nome único para a curva, ex: Curva Tilápia Verão 2025")
    especie = models.CharField(max_length=100, default='', help_text="Espécie do animal, ex: Tilápia")
    rendimento_perc = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Percentual de rendimento da carcaça")
    trato_perc_curva = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Percentual de trato da curva")
    peso_pretendido = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.000'), help_text="Peso pretendido (em g)")
    trato_sabados_perc = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Percentual de trato aos sábados")
    trato_domingos_perc = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Percentual de trato aos domingos")
    trato_feriados_perc = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Percentual de trato aos feriados")

    class Meta:
        verbose_name = "Curva de Crescimento"
        verbose_name_plural = "Curvas de Crescimento"
        ordering = ['nome']

    def __str__(self):
        return self.nome

class CurvaCrescimentoDetalhe(models.Model):
    curva = models.ForeignKey(CurvaCrescimento, on_delete=models.CASCADE, related_name='detalhes')
    periodo_semana = models.IntegerField(help_text="Número do período ou semana do ciclo", default=0)
    periodo_dias = models.IntegerField(help_text="Número de dias no período (ex: 7)", default=0)
    peso_inicial = models.DecimalField(max_digits=10, decimal_places=3, help_text="Peso inicial do animal no período (em g)", default=0)
    peso_final = models.DecimalField(max_digits=10, decimal_places=3, help_text="Peso final do animal no período (em g)", default=0)
    ganho_de_peso = models.DecimalField(max_digits=10, decimal_places=3, help_text="Ganho de peso total no período (em g)", default=0)
    numero_tratos = models.IntegerField(help_text="Número de tratos de ração por dia", default=0)
    hora_inicio = models.TimeField(help_text="Hora de início do primeiro trato do dia", default='00:00')
    arracoamento_biomassa_perc = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentual de arraçoamento sobre a biomassa (%BW/dia)", default=0)
    mortalidade_presumida_perc = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentual de mortalidade presumida para o período", default=0)
    racao = models.ForeignKey(
        Produto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='curvas_crescimento',
        help_text="Ração utilizada no período (vinculada ao cadastro de produtos)"
    )
    gpd = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Ganho de Peso Diário (g)", default=0)
    tca = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Taxa de Conversão Alimentar", default=0)

    class Meta:
        verbose_name = "Detalhe da Curva de Crescimento"
        verbose_name_plural = "Detalhes da Curva de Crescimento"
        ordering = ['curva', 'periodo_semana']
        unique_together = ('curva', 'periodo_semana')

    def __str__(self):
        return f"{self.curva.nome} - Semana {self.periodo_semana}"

class Tanque(models.Model):
    nome = models.CharField(max_length=120)
    largura = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Largura em metros (m)")
    comprimento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Comprimento em metros (m)")
    profundidade = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Profundidade em metros (m)")

    metro_quadrado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Área em metros quadrados (m²)")
    metro_cubico   = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True, help_text="Volume em metros cúbicos (m³)")
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

    @property
    def volume_calculado_m3(self):
        """Retorna o volume em m³, usando o campo 'metro_cubico' ou calculando-o."""
        if self.metro_cubico and self.metro_cubico > 0:
            return self.metro_cubico
        if self.largura and self.comprimento and self.profundidade:
            return self.largura * self.comprimento * self.profundidade
        # Adicionar lógica para tanques circulares se houver campo de diâmetro
        return Decimal('0.000')

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.id} - {self.nome}'

    def verificar_e_liberar_status(self, lote_sendo_deletado=None):
        lotes_ativos_no_tanque = self.lotes_no_tanque.filter(ativo=True)
        if lote_sendo_deletado:
            lotes_ativos_no_tanque = lotes_ativos_no_tanque.exclude(pk=lote_sendo_deletado.pk)
        if not lotes_ativos_no_tanque.exists():
            try:
                status_livre = StatusTanque.objects.get(nome__iexact='Livre')
                if self.status_tanque != status_livre:
                    self.status_tanque = status_livre
                    self.save(update_fields=['status_tanque'])
            except StatusTanque.DoesNotExist:
                pass

class Lote(models.Model):
    nome = models.CharField(max_length=255)
    curva_crescimento = models.ForeignKey(CurvaCrescimento, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes')
    fase_producao = models.ForeignKey(FaseProducao, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes')
    tanque_atual = models.ForeignKey(Tanque, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes_no_tanque')
    quantidade_inicial = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    peso_medio_inicial = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0)], help_text="Peso médio inicial em gramas (g)")
    data_povoamento = models.DateField()
    ativo = models.BooleanField(default=True)

    @property
    def biomassa_inicial_g(self):
        """Retorna a biomassa inicial calculada em gramas."""
        return self.quantidade_inicial * self.peso_medio_inicial

    @property
    def biomassa_inicial_kg(self):
        """Retorna a biomassa inicial convertida para kg."""
        return calc_biomassa_kg(self.quantidade_inicial, self.peso_medio_inicial)

    @property
    def quantidade_atual(self):
        """
        Calcula a quantidade atual de peixes no lote em tempo real,
        somando e subtraindo a partir dos eventos de manejo.
        """
        from django.db.models import Sum, Case, When, DecimalField

        # Agrega todas as quantidades de eventos, separando por tipo
        agregado = self.eventos_manejo.aggregate(
            entradas=Sum(
                Case(
                    When(Q(tipo_evento__nome='Povoamento') | Q(tipo_movimento='Entrada'), then='quantidade'),
                    output_field=DecimalField()
                )
            ),
            saidas=Sum(
                Case(
                    When(Q(tipo_evento__nome__in=['Mortalidade', 'Despesca']) | Q(tipo_movimento='Saída'), then='quantidade'),
                    output_field=DecimalField()
                )
            )
        )
        
        total_entradas = agregado.get('entradas') or Decimal('0')
        total_saidas = agregado.get('saidas') or Decimal('0')
        
        return total_entradas - total_saidas

    @property
    def peso_medio_atual(self):
        """
        Busca o peso médio mais recente do histórico diário do lote (LoteDiario).
        """
        from django.utils import timezone
        today = timezone.now().date()

        latest_lote_diario = self.historico_diario.filter(data_evento__lte=today).order_by('-data_evento').first()

        if latest_lote_diario:
            # Prioriza o peso real; se não houver, usa o projetado.
            peso = latest_lote_diario.peso_medio_real if latest_lote_diario.peso_medio_real is not None else latest_lote_diario.peso_medio_projetado
            return peso if peso is not None else self.peso_medio_inicial
        
        # Se não houver nenhum registro diário, reverte para o peso inicial
        return self.peso_medio_inicial

    @property
    def biomassa_atual_g(self):
        """Retorna a biomassa atual calculada em gramas."""
        return self.quantidade_atual * self.peso_medio_atual

    @property
    def biomassa_atual_kg(self):
        """Retorna a biomassa atual convertida para kg."""
        return calc_biomassa_kg(self.quantidade_atual, self.peso_medio_atual)

    @property
    def gpd(self):
        if self.data_povoamento and self.peso_medio_inicial and self.peso_medio_atual:
            dias_cultivo = (date.today() - self.data_povoamento).days
            if dias_cultivo > 0:
                return (self.peso_medio_atual - self.peso_medio_inicial) / dias_cultivo
        return Decimal('0.0')

    def verificar_e_liberar_status(self, lote_sendo_deletado=None):
        lotes_ativos_no_tanque = self.lotes_no_tanque.filter(ativo=True)
        if lote_sendo_deletado:
            lotes_ativos_no_tanque = lotes_ativos_no_tanque.exclude(pk=lote_sendo_deletado.pk)
        if not lotes_ativos_no_tanque.exists():
            try:
                status_livre = StatusTanque.objects.get(nome__iexact='Livre')
                if self.status_tanque != status_livre:
                    self.status_tanque = status_livre
                    self.save(update_fields=['status_tanque'])
            except StatusTanque.DoesNotExist:
                pass

    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"

    def __str__(self):
        return self.nome

class EventoManejo(models.Model):
    tipo_evento = models.ForeignKey(
        'producao.TipoEvento',
        on_delete=models.PROTECT,
        related_name='eventos_manejo',
        help_text="Tipo do evento de manejo."
    )

    tipo_movimento = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Indica se o evento representa uma entrada ou saída de peixes."
    )
    transferencia_total = models.BooleanField(
        default=False,
        help_text="Marque se esta é uma transferência total, que desativará o lote de origem."
    )
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='eventos_manejo')
    tanque_origem = models.ForeignKey(Tanque, on_delete=models.SET_NULL, null=True, blank=True, related_name='eventos_origem')
    tanque_destino = models.ForeignKey(Tanque, on_delete=models.SET_NULL, null=True, blank=True, related_name='eventos_destino')
    data_evento = models.DateField()
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    peso_medio = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0)], help_text="Peso médio em gramas (g)")
    observacoes = models.TextField(blank=True, null=True)

    @property
    def biomassa_g(self):
        """Retorna a biomassa do evento em gramas."""
        return self.quantidade * self.peso_medio
    
    @property
    def biomassa_kg(self):
        """Retorna a biomassa do evento em quilogramas."""
        return calc_biomassa_kg(self.quantidade, self.peso_medio)

    class Meta:
        verbose_name = "Evento de Manejo"
        verbose_name_plural = "Eventos de Manejo"

    def __str__(self):
        return f"{self.tipo_evento} - {self.lote.nome} em {self.data_evento}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class LoteDiario(models.Model):
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='historico_diario')
    tanque = models.ForeignKey(
        Tanque,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Tanque em que o lote se encontrava nesta data. Garante a precisão histórica."
    )
    data_evento = models.DateField(help_text="A data de referência para este registro diário.")

    quantidade_inicial = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Qtd. de peixes no início do dia")
    peso_medio_inicial = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, help_text="Peso médio no início do dia (g)")
    biomassa_inicial = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True, help_text="Biomassa no início do dia (kg)")

    racao_sugerida = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes_diarios_sugeridos')
    racao_sugerida_kg = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)

    # --- PASSO 5: Snapshot do Ajuste Ambiental (auditoria) ---
    racao_sugerida_ajustada_kg = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
        help_text="Ração sugerida ajustada por ambiente/manejo (kg)"
    )
    fator_ambiente = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True,
        help_text="Fator total de ajuste ambiental aplicado na sugestão (ex: 0.85)"
    )
    fator_manejo = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True,
        help_text="Fator de manejo (acima/abaixo/100%) aplicado na sugestão (ex: 1.00)"
    )

    # Snapshot dos parâmetros ambientais do dia (médias e variação)
    od_medio = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    temp_media = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    temp_min = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    temp_max = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    variacao_termica = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    # --- FIM PASSO 5 ---
    quantidade_projetada = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Qtd. de peixes projetada para o FIM do dia")
    peso_medio_projetado = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, help_text="Peso médio projetado para o FIM do dia (g)")
    biomassa_projetada = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True, help_text="Biomassa projetada para o FIM do dia (kg)")
    gpd_projetado = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="GPD Projetado (g)")
    gpt_projetado = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="GPT Projetado (g)")
    conversao_alimentar_projetada = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="Conversão Alimentar Projetada")

    racao_realizada = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes_diarios_realizados')
    racao_realizada_kg = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    quantidade_real = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Qtd. de peixes real no FIM do dia")
    peso_medio_real = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, help_text="Peso médio real no FIM do dia (g)")
    biomassa_real = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True, help_text="Biomassa real no FIM do dia (kg)")
    gpd_real = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="GPD Real (g)")
    gpt_real = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="GPT Real (g)")
    conversao_alimentar_real = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="Conversão Alimentar Real")

    observacoes = models.TextField(blank=True, null=True)
    data_lancamento = models.DateTimeField(auto_now_add=True)
    data_edicao = models.DateTimeField(null=True, blank=True)
    usuario_lancamento = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes_diarios_criados')
    usuario_edicao = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes_diarios_editados')

    @property
    def biomassa_calc_kg(self):
        """Propriedade de apoio para recomputar a biomassa do dia em kg, se necessário."""
        if self.quantidade_inicial and self.peso_medio_inicial:
            return calc_biomassa_kg(self.quantidade_inicial, self.peso_medio_inicial)
        return Decimal('0.000')

    class Meta:
        verbose_name = "Histórico Diário do Lote"
        verbose_name_plural = "Históricos Diários dos Lotes"
        unique_together = ('lote', 'data_evento')
        ordering = ['lote', '-data_evento']

    def __str__(self):
        return f"Histórico de {self.lote.nome} em {self.data_evento.strftime('%d/%m/%Y')}"

class ArracoamentoSugerido(models.Model):
    lote_diario = models.OneToOneField(LoteDiario, on_delete=models.CASCADE, related_name='sugestao')
    produto_racao = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True)
    quantidade_kg = models.DecimalField(max_digits=10, decimal_places=3)
    status = models.CharField(max_length=20, choices=[('Pendente', 'Pendente'), ('Aprovado', 'Aprovado'), ('Rejeitado', 'Rejeitado')], default='Pendente')
    data_sugestao = models.DateTimeField(auto_now_add=True)
    usuario_sugestao = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sugestoes_criadas')

    class Meta:
        verbose_name = "Sugestão de Arraçoamento"
        verbose_name_plural = "Sugestões de Arraçoamento"
        ordering = ['-data_sugestao']

    def __str__(self):
        return f"Sugestão para {self.lote_diario} - {self.quantidade_kg} kg"

class ArracoamentoRealizado(models.Model):
    lote_diario = models.ForeignKey(LoteDiario, on_delete=models.CASCADE, related_name='realizacoes')
    produto_racao = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True, help_text="Ração efetivamente utilizada.")
    quantidade_kg = models.DecimalField(max_digits=10, decimal_places=3)
    data_realizacao = models.DateTimeField(null=True, blank=True)
    data_evento = models.DateField(null=True, blank=True, db_index=True)
    observacoes = models.TextField(blank=True, null=True)
    
    data_lancamento = models.DateTimeField(auto_now_add=True)
    data_edicao = models.DateTimeField(null=True, blank=True)
    usuario_lancamento = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='arracoamentos_lancados')
    usuario_edicao = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='arracoamentos_editados')

    class Meta:
        verbose_name = "Arraçoamento Realizado"
        verbose_name_plural = "Arraçoamentos Realizados"
        ordering = ['-data_realizacao']

    def __str__(self):
        return f"Realizado para {self.lote_diario} - {self.quantidade_kg} kg"

class ParametroAmbientalDiario(models.Model):
    """
    Registro ambiental diário por FASE de produção.
    Permite até 5 leituras por dia (um por trato).
    Calcula automaticamente médias e variações térmicas.
    """

    fase = models.ForeignKey(
        FaseProducao,
        on_delete=models.CASCADE,
        related_name='parametros_ambientais'
    )

    data = models.DateField()

    # Leituras de Oxigênio (até 5 tratos)
    od_1 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    od_2 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    od_3 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    od_4 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    od_5 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    # Leituras de Temperatura (até 5 tratos)
    temp_1 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    temp_2 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    temp_3 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    temp_4 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    temp_5 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    # Parâmetros químicos adicionais
    ph = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    amonia = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    nitrito = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    nitrato = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    alcalinidade = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    # Campos calculados automaticamente
    od_medio = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    temp_media = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    temp_min = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    temp_max = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    variacao_termica = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('fase', 'data')
        verbose_name = "Parâmetro Ambiental Diário"
        verbose_name_plural = "Parâmetros Ambientais Diários"
        ordering = ['-data']

    def __str__(self):
        return f"{self.fase} - {self.data}"

    def calcular_estatisticas(self):
        """
        Calcula médias, mínimo, máximo e variação térmica automaticamente.
        """
        ods = [v for v in [self.od_1, self.od_2, self.od_3, self.od_4, self.od_5] if v is not None]
        temps = [v for v in [self.temp_1, self.temp_2, self.temp_3, self.temp_4, self.temp_5] if v is not None]

        if ods:
            self.od_medio = sum(ods) / len(ods)

        if temps:
            self.temp_media = sum(temps) / len(temps)
            self.temp_min = min(temps)
            self.temp_max = max(temps)
            self.variacao_termica = self.temp_max - self.temp_min

    def save(self, *args, **kwargs):
        self.calcular_estatisticas()
        super().save(*args, **kwargs)
