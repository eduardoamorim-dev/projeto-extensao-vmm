# models.py
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, time

class Voluntario(models.Model):
    """Modelo existente - mantido com pequenos ajustes"""
    
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

    # Dados básicos
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
    
    # Campos profissionais
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
    
    # Controle
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
        """Verifica se o voluntário está disponível para o horário especificado"""
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
    """Gestão de veículos disponíveis"""
    
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
        """Verifica se o veículo está disponível para o horário especificado"""
        if self.status != 'disponivel':
            return False
            
        return not Evento.objects.filter(
            veiculo=self,
            data_evento=data_evento,
            hora_inicio__lt=hora_fim,
            hora_fim__gt=hora_inicio
        ).exists()

    class Meta:
        verbose_name = "Veículo"
        verbose_name_plural = "Veículos"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - {self.placa}"


class Evento(models.Model):
    """Gestão de eventos em escolas"""
    
    STATUS_EVENTO = [
        ('planejamento', 'Em Planejamento'),
        ('confirmado', 'Confirmado'),
        ('em_andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]
    
    # Dados da escola
    nome_escola = models.CharField(max_length=255, verbose_name="Nome da Escola")
    responsavel_escola = models.CharField(max_length=255, verbose_name="Responsável da Escola")
    telefone_responsavel = models.CharField(max_length=15, verbose_name="Telefone do Responsável")
    cidade = models.CharField(max_length=100, verbose_name="Cidade")
    endereco = models.TextField(verbose_name="Endereço Completo")
    
    # Data e horário
    data_evento = models.DateField(verbose_name="Data do Evento")
    hora_inicio = models.TimeField(verbose_name="Hora de Início")
    hora_fim = models.TimeField(verbose_name="Hora de Término")
    
    # Recursos necessários
    qtd_tv = models.IntegerField(default=0, verbose_name="Quantidade de TVs")
    qtd_computador = models.IntegerField(default=0, verbose_name="Quantidade de Computadores")
    
    # Veículo (opcional)
    veiculo = models.ForeignKey(
        Veiculo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Veículo Designado"
    )
    
    # Status e controle
    status = models.CharField(
        max_length=20,
        choices=STATUS_EVENTO,
        default='planejamento',
        verbose_name="Status do Evento"
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    # Auditoria
    criado_por = models.CharField(max_length=255, blank=True, verbose_name="Criado Por")
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validações de conflito de horário e veículo"""
        super().clean()
        
        # Validar horários
        if self.hora_inicio and self.hora_fim:
            if self.hora_inicio >= self.hora_fim:
                raise ValidationError({
                    'hora_fim': 'A hora de término deve ser posterior à hora de início.'
                })
        
        # Validar conflito de veículo
        if self.veiculo:
            conflito_veiculo = Evento.objects.filter(
                veiculo=self.veiculo,
                data_evento=self.data_evento,
                hora_inicio__lt=self.hora_fim,
                hora_fim__gt=self.hora_inicio
            ).exclude(pk=self.pk)
            
            if conflito_veiculo.exists():
                raise ValidationError({
                    'veiculo': f'O veículo {self.veiculo.nome} já está alocado neste horário.'
                })

    def get_voluntarios_count(self):
        """Retorna quantidade de voluntários no evento"""
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


class VoluntarioEvento(models.Model):
    """Relacionamento entre voluntários e eventos com função específica"""
    
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
        verbose_name="Descrição Customizada da Função",
        help_text="Use quando a função for 'Outro'"
    )
    
    # Controle de presença
    presenca = models.CharField(
        max_length=20,
        choices=STATUS_PRESENCA,
        default='confirmado',
        verbose_name="Status de Presença"
    )
    
    # Informações adicionais
    vai_no_veiculo = models.BooleanField(
        default=False,
        verbose_name="Irá no Veículo Designado"
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    # Auditoria
    data_vinculo = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    vai_no_veiculo = models.BooleanField(default=False)
    evento_veiculo = models.ForeignKey(
        EventoVeiculo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Qual veículo o voluntário vai utilizar"
    )

    def clean(self):
        """Validações de conflito de horário"""
        super().clean()
        
        # Verificar conflito de horário para o voluntário
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
        
        # Validar se vai no veículo mas o evento não tem veículo
        if self.vai_no_veiculo and not self.evento.veiculo:
            raise ValidationError({
                'vai_no_veiculo': 'O evento não possui veículo designado.'
            })
        
        # Validar capacidade do veículo
        if self.vai_no_veiculo and self.evento.veiculo:
            ocupantes = VoluntarioEvento.objects.filter(
                evento=self.evento,
                vai_no_veiculo=True
            ).exclude(pk=self.pk).count()
            
            if ocupantes >= self.evento.veiculo.capacidade:
                raise ValidationError({
                    'vai_no_veiculo': f'O veículo já atingiu sua capacidade máxima '
                                        f'({self.evento.veiculo.capacidade} pessoas).'
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