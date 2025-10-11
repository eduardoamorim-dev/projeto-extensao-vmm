from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, time

class Voluntario(models.Model):
    TAMANHOS_CAMISETA = [
        ('P', 'P'),
        ('M', 'M'),
        ('G', 'G'),
        ('GG', 'GG'),
        ('XG', 'XG'),
        ('BL_P', 'Baby Look P'),
        ('BL_M', 'Baby Look M'),
        ('BL_G', 'Baby Look G'),
        ('BL_GG', 'Baby Look GG'),
    ]
    
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
    ]

    AGENCIAS_CHOICES = [
        ('001', '001 - Matriz Patrocinio'),
        ('002', '002 - Agência Uberlândia'),
        ('003', '003 - Agência Guimarânia'),
        ('004', '004 - Agência Coromandael'),
    ]

    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo")
    email_corporativo = models.EmailField(unique=True, verbose_name="Email Corporativo")
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF")
    
    telefone_validator = RegexValidator(
        regex=r'^\(\d{2}\)\s\d{4,5}-\d{4}$',
        message="Telefone deve estar no formato: (11) 99999-9999"
    )
    telefone = models.CharField(
        max_length=15, 
        validators=[telefone_validator],
        verbose_name="Telefone"
    )
    
    agencia = models.CharField(
        max_length=3, 
        choices=AGENCIAS_CHOICES,
        verbose_name="Agência"
    )
    setor = models.CharField(max_length=100, verbose_name="Setor")
    tamanho_camiseta = models.CharField(
        max_length=5,  
        choices=TAMANHOS_CAMISETA,
        verbose_name="Tamanho da Camiseta"
    )
    
    cargo = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name="Cargo Principal"
    )
    experiencia_anterior = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Experiência Anterior"
    )
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ativo',
        verbose_name="Status"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo no Sistema")
    data_cadastro = models.DateTimeField(default=timezone.now, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    @staticmethod
    def formatar_cpf(cpf):
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        if len(cpf_limpo) == 11:
            return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
        return cpf

    def verificar_disponibilidade(self, data_evento, hora_inicio, hora_fim):
        return not VoluntarioEvento.objects.filter(
            voluntario=self,
            evento__data_evento=data_evento,
            evento__hora_inicio__lt=hora_fim,
            evento__hora_fim__gt=hora_inicio
        ).exists()

    class Meta:
        verbose_name = "Voluntário"
        verbose_name_plural = "Voluntários"
        ordering = ['-data_cadastro']
        indexes = [
            models.Index(fields=['email_corporativo']),
            models.Index(fields=['cpf']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.nome_completo} - {self.get_agencia_display()}"


class Veiculo(models.Model):
    TIPO_VEICULO = [
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('van', 'Van'),
        ('pickup', 'Pickup'),
    ]
    
    STATUS_VEICULO = [
        ('disponivel', 'Disponível'),
        ('manutencao', 'Em Manutenção'),
        ('indisponivel', 'Indisponível'),
    ]
    
    nome = models.CharField(max_length=100, verbose_name="Identificação do Veículo")
    placa = models.CharField(max_length=8, unique=True, verbose_name="Placa")
    tipo = models.CharField(max_length=20, choices=TIPO_VEICULO, verbose_name="Tipo")
    capacidade = models.IntegerField(default=5, verbose_name="Capacidade de Passageiros")
    status = models.CharField(
        max_length=20,
        choices=STATUS_VEICULO,
        default='disponivel',
        verbose_name="Status"
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def verificar_disponibilidade(self, data_evento, hora_inicio, hora_fim):
        if self.status != 'disponivel':
            return False
            
        return not EventoVeiculo.objects.filter(
            veiculo=self,
            evento__data_evento=data_evento,
            evento__hora_inicio__lt=hora_fim,
            evento__hora_fim__gt=hora_inicio
        ).exists()

    class Meta:
        verbose_name = "Veículo"
        verbose_name_plural = "Veículos"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - {self.placa}"


class Evento(models.Model):
    STATUS_EVENTO = [
        ('planejamento', 'Em Planejamento'),
        ('confirmado', 'Confirmado'),
        ('em_andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]
    
    nome_escola = models.CharField(max_length=255, verbose_name="Nome da Escola")
    responsavel_escola = models.CharField(max_length=255, verbose_name="Responsável da Escola")
    telefone_responsavel = models.CharField(max_length=15, verbose_name="Telefone do Responsável")
    cidade = models.CharField(max_length=100, verbose_name="Cidade")
    endereco = models.TextField(verbose_name="Endereço Completo")
    
    data_evento = models.DateField(verbose_name="Data do Evento")
    hora_inicio = models.TimeField(verbose_name="Hora de Início")
    hora_fim = models.TimeField(verbose_name="Hora de Término")
    
    qtd_tv = models.IntegerField(default=0, verbose_name="Quantidade de TVs")
    qtd_computador = models.IntegerField(default=0, verbose_name="Quantidade de Computadores")
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_EVENTO,
        default='planejamento',
        verbose_name="Status do Evento"
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    criado_por = models.CharField(max_length=255, blank=True, verbose_name="Criado Por")
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        
        if self.hora_inicio and self.hora_fim:
            if self.hora_inicio >= self.hora_fim:
                raise ValidationError({
                    'hora_fim': 'A hora de término deve ser posterior à hora de início.'
                })

    def get_voluntarios_count(self):
        return self.voluntarioevento_set.count()

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ['data_evento', 'hora_inicio']
        indexes = [
            models.Index(fields=['data_evento', 'hora_inicio']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.nome_escola} - {self.data_evento.strftime('%d/%m/%Y')}"


class EventoVeiculo(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE)
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE)
    motorista = models.ForeignKey(
        Voluntario, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='veiculos_dirigidos'
    )
    observacoes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['evento', 'veiculo']
        verbose_name = "Veículo no Evento"
        verbose_name_plural = "Veículos nos Eventos"

    @property
    def voluntarios_count(self):
        return VoluntarioEvento.objects.filter(
            evento=self.evento,
            evento_veiculo=self
        ).count()
    
    @property
    def ocupacao_percentual(self):
        if self.veiculo.capacidade == 0:
            return 0
        return (self.voluntarios_count / self.veiculo.capacidade) * 100

    def __str__(self):
        return f"{self.veiculo.nome} - {self.evento.nome_escola}"


class VoluntarioEvento(models.Model):
    FUNCOES = [
        ('coordenador', 'Coordenador do Evento'),
        ('motorista', 'Motorista'),
        ('apoio_logistico', 'Apoio Logístico'),
        ('triagem', 'Triagem'),
        ('monitor', 'Monitor de Atividades'),
        ('fotografo', 'Fotógrafo/Registro'),
        ('outro', 'Outro'),
    ]
    
    STATUS_PRESENCA = [
        ('pendente', 'Pendente'),
        ('confirmado', 'Confirmado'),
        ('presente', 'Presente'),
        ('ausente', 'Ausente'),
        ('cancelado', 'Cancelado'),
    ]
    
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE)
    voluntario = models.ForeignKey(Voluntario, on_delete=models.CASCADE)
    funcao = models.CharField(
        max_length=30,
        choices=FUNCOES,
        verbose_name="Função no Evento"
    )
    funcao_customizada = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Descrição Customizada da Função"
    )
    
    presenca = models.CharField(
        max_length=20,
        choices=STATUS_PRESENCA,
        default='pendente',
        verbose_name="Status de Presença"
    )
    
    vai_no_veiculo = models.BooleanField(default=False)
    evento_veiculo = models.ForeignKey(
        EventoVeiculo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    data_vinculo = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        
        conflitos = VoluntarioEvento.objects.filter(
            voluntario=self.voluntario,
            evento__data_evento=self.evento.data_evento,
            evento__hora_inicio__lt=self.evento.hora_fim,
            evento__hora_fim__gt=self.evento.hora_inicio
        ).exclude(pk=self.pk)
        
        if conflitos.exists():
            evento_conflito = conflitos.first().evento
            raise ValidationError(
                f'O voluntário {self.voluntario.nome_completo} já está alocado '
                f'no evento "{evento_conflito.nome_escola}" no mesmo horário.'
            )
        
        if self.vai_no_veiculo and self.evento_veiculo:
            ocupantes = VoluntarioEvento.objects.filter(
                evento=self.evento,
                evento_veiculo=self.evento_veiculo
            ).exclude(pk=self.pk).count()
            
            if ocupantes >= self.evento_veiculo.veiculo.capacidade:
                raise ValidationError({
                    'vai_no_veiculo': f'O veículo já atingiu sua capacidade máxima '
                                        f'({self.evento_veiculo.veiculo.capacidade} pessoas).'
                })

    class Meta:
        verbose_name = "Voluntário no Evento"
        verbose_name_plural = "Voluntários nos Eventos"
        unique_together = ['evento', 'voluntario']
        ordering = ['evento__data_evento', 'funcao']
        indexes = [
            models.Index(fields=['evento', 'voluntario']),
            models.Index(fields=['presenca']),
        ]

    def __str__(self):
        funcao_display = self.funcao_customizada if self.funcao == 'outro' else self.get_funcao_display()
        return f"{self.voluntario.nome_completo} - {funcao_display} ({self.evento})"