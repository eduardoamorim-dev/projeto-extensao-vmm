from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone

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

    # Dados básicos do voluntário
    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo")
    email_corporativo = models.EmailField(unique=True, verbose_name="Email Corporativo")
    agencia = models.CharField(
        max_length=3, 
        choices=AGENCIAS_CHOICES,
        verbose_name="Agência"
    )
    setor = models.CharField(max_length=100, verbose_name="Setor")
    
    # Validador para telefone 
    telefone_validator = RegexValidator(
        regex=r'^\(\d{2}\)\s\d{4,5}-\d{4}$',
        message="Telefone deve estar no formato: (11) 99999-9999"
    )
    telefone = models.CharField(
        max_length=15, 
        validators=[telefone_validator],
        verbose_name="Telefone"
    )
    tamanho_camiseta = models.CharField(
        max_length=5,  
        choices=TAMANHOS_CAMISETA,
        verbose_name="Tamanho da Camiseta"
    )

    # Dados complementares
    cpf = models.CharField(
        max_length=14, 
        unique=True,
        help_text="Formato: 000.000.000-00",
        verbose_name="CPF"
    )
    
    # Dados profissionais
    cargo = models.CharField(max_length=100, verbose_name="Cargo a desempenhar no evento")
    experiencia_anterior = models.TextField(
        blank=True, 
        null=True,
        help_text="Experiências anteriores em voluntariado",
        verbose_name="Experiência Anterior"
    )
    
    # Campos de controle
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ativo',
        verbose_name="Status"
    )
    data_cadastro = models.DateTimeField(
        default=timezone.now,
        verbose_name="Data de Cadastro"
    )

    # Campos de auditoria
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    @staticmethod
    def formatar_cpf(cpf):
        """Remove formatação e aplica máscara do CPF"""
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        if len(cpf_limpo) == 11:
            return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
        return cpf

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
    
    def save(self, *args, **kwargs):
        # Formatar campos antes de salvar
        if self.cpf:
            self.cpf = self.formatar_cpf(self.cpf)
        super().save(*args, **kwargs)