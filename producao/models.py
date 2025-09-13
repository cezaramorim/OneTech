from django.db import models
from django.conf import settings
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

    def recalcular_estado_atual(self):
        # Inicializa com os valores do povoamento inicial
        povoamento_inicial_evento = self.eventos_manejo.filter(tipo_evento='Povoamento').order_by('data_evento', 'id').first()
        
        if not povoamento_inicial_evento:
            self.quantidade_atual = Decimal('0')
            self.peso_medio_atual = Decimal('0')
            self.ativo = False
            self.tanque_atual = None
            self.save(update_fields=['quantidade_atual', 'peso_medio_atual', 'ativo', 'tanque_atual'])
            return

        current_quantidade = povoamento_inicial_evento.quantidade
        current_peso_medio = povoamento_inicial_evento.peso_medio
        current_tanque = povoamento_inicial_evento.tanque_destino

        # Itera sobre os eventos subsequentes para agregar
        eventos_subsequentes = self.eventos_manejo.filter(
            data_evento__gte=povoamento_inicial_evento.data_evento
        ).exclude(id=povoamento_inicial_evento.id).order_by('data_evento', 'id')

        for evento in eventos_subsequentes:
            if evento.tipo_evento == 'Povoamento': # Reforço de lote
                quantidade_evento = evento.quantidade or Decimal('0')
                peso_medio_evento = evento.peso_medio or Decimal('0')

                if quantidade_evento > 0:
                    biomassa_existente = current_quantidade * current_peso_medio
                    biomassa_adicionada = quantidade_evento * peso_medio_evento
                    
                    nova_quantidade = current_quantidade + quantidade_evento
                    nova_biomassa = biomassa_existente + biomassa_adicionada
                    
                    if nova_quantidade > 0:
                        current_peso_medio = nova_biomassa / nova_quantidade
                    else:
                        current_peso_medio = peso_medio_evento

                    current_quantidade = nova_quantidade
            elif evento.tipo_evento == 'Mortalidade' or evento.tipo_evento == 'Despesca':
                current_quantidade -= (evento.quantidade or Decimal('0'))
                if current_quantidade < 0:
                    current_quantidade = Decimal('0')
            elif evento.tipo_evento == 'Transferencia':
                current_quantidade = evento.quantidade
                current_peso_medio = evento.peso_medio
                current_tanque = evento.tanque_destino

        self.quantidade_atual = current_quantidade
        self.peso_medio_atual = current_peso_medio
        self.tanque_atual = current_tanque

        if self.quantidade_atual <= 0:
            self.ativo = False
            try:
                status_livre = StatusTanque.objects.get(nome__iexact='Livre')
                if self.tanque_atual and self.tanque_atual.status_tanque != status_livre:
                    self.tanque_atual.status_tanque = status_livre
                    self.tanque_atual.save(update_fields=['status_tanque'])
            except StatusTanque.DoesNotExist:
                pass
            self.tanque_atual = None
        else:
            self.ativo = True
            try:
                status_em_uso = StatusTanque.objects.get(nome__iexact='Em uso')
                if self.tanque_atual and self.tanque_atual.status_tanque != status_em_uso:
                    self.tanque_atual.status_tanque = status_em_uso
                    self.tanque_atual.save(update_fields=['status_tanque'])
            except StatusTanque.DoesNotExist:
                pass

        self.save(update_fields=['quantidade_atual', 'peso_medio_atual', 'ativo', 'tanque_atual'])

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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)




# =========================================================================
# NOVOS MODELOS PARA O SISTEMA DE ARRAÇOAMENTO (v2 - PROATIVO)
# =========================================================================




class LoteDiario(models.Model):
    """
    Armazena um snapshot diário consolidado do estado e performance de um lote.
    É pré-populado com projeções e depois atualizado com dados reais.
    """
    # --- Chaves e Data de Referência ---
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='historico_diario')
    data_evento = models.DateField(help_text="A data de referência para este registro diário.")

    # --- Dados Projetados/Sugeridos ---
    racao_sugerida = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes_diarios_sugeridos')
    racao_sugerida_kg = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    quantidade_projetada = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    peso_medio_projetado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Peso em gramas")
    biomassa_projetada = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="em kg")
    gpd_projetado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="GPD Projetado (g)")
    gpt_projetado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="GPT Projetado (g)")
    conversao_alimentar_projetada = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="Conversão Alimentar Projetada")

    # --- Dados Reais (Pós-Evento) ---
    racao_realizada = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes_diarios_realizados')
    racao_realizada_kg = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    quantidade_real = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    peso_medio_real = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Peso em gramas")
    biomassa_real = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="em kg")
    gpd_real = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="GPD Real (g)")
    gpt_real = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="GPT Real (g)")
    conversao_alimentar_real = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="Conversão Alimentar Real")

    # --- Auditoria e Observações ---
    observacoes = models.TextField(blank=True, null=True)
    data_lancamento = models.DateTimeField(auto_now_add=True)
    data_edicao = models.DateTimeField(auto_now=True)
    usuario_lancamento = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes_diarios_criados')
    usuario_edicao = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes_diarios_editados')

    class Meta:
        verbose_name = "Histórico Diário do Lote"
        verbose_name_plural = "Históricos Diários dos Lotes"
        unique_together = ('lote', 'data_evento')
        ordering = ['lote', '-data_evento']

    def __str__(self):
        return f"Histórico de {self.lote.nome} em {self.data_evento.strftime('%d/%m/%Y')}"


class ArracoamentoSugerido(models.Model):
    """
    Armazena a transação de uma sugestão de arraçoamento gerada pelo sistema.
    O status é controlado pelo usuário para indicar pendências.
    """
    STATUS_CHOICES = [
        ('Pendente', 'Pendente'),
        ('Aprovado', 'Aprovado'),
        ('Rejeitado', 'Rejeitado'),
    ]
    lote_diario = models.OneToOneField(LoteDiario, on_delete=models.CASCADE, related_name='sugestao')
    produto_racao = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True)
    quantidade_kg = models.DecimalField(max_digits=10, decimal_places=3)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pendente')
    data_sugestao = models.DateTimeField(auto_now_add=True)
    usuario_sugestao = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sugestoes_criadas')

    class Meta:
        verbose_name = "Sugestão de Arraçoamento"
        verbose_name_plural = "Sugestões de Arraçoamento"
        ordering = ['-data_sugestao']

    def __str__(self):
        return f"Sugestão para {self.lote_diario} - {self.quantidade_kg} kg"


class ArracoamentoRealizado(models.Model):
    """
    Registra a transação de um arraçoamento que foi efetivamente realizado,
    seja a partir de uma sugestão aprovada ou de um lançamento manual.
    """
    lote_diario = models.ForeignKey(LoteDiario, on_delete=models.CASCADE, related_name='realizacoes')
    produto_racao = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True, help_text="Ração efetivamente utilizada.")
    quantidade_kg = models.DecimalField(max_digits=10, decimal_places=3)
    data_realizacao = models.DateTimeField()
    observacoes = models.TextField(blank=True, null=True)
    
    # Auditoria
    data_lancamento = models.DateTimeField(auto_now_add=True)
    data_edicao = models.DateTimeField(auto_now=True)
    usuario_lancamento = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='arracoamentos_lancados')
    usuario_edicao = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='arracoamentos_editados')

    class Meta:
        verbose_name = "Arraçoamento Realizado"
        verbose_name_plural = "Arraçoamentos Realizados"
        ordering = ['-data_realizacao']

    def __str__(self):
        return f"Realizado para {self.lote_diario} - {self.quantidade_kg} kg"

