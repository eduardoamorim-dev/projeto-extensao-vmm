from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from .models import Voluntario
import re

@csrf_protect
@require_http_methods(["GET", "POST"])
def cadastro_voluntario(request):
    """
    View para inscrição de voluntários
    """
    if request.method == "POST":
        try:
            # Capturar dados do formulário
            nome_completo = request.POST.get('nome_completo', '').strip()
            email_corporativo = request.POST.get('email_corporativo', '').strip().lower()
            cpf = request.POST.get('cpf', '').strip()
            telefone = request.POST.get('telefone', '').strip()
            agencia = request.POST.get('agencia', '')
            setor = request.POST.get('setor', '').strip()
            tamanho_camiseta = request.POST.get('tamanho_camiseta', '')
            experiencia_anterior = request.POST.get('experiencia_anterior', '').strip()

            # Validações básicas
            errors = []
            
            if not nome_completo:
                errors.append("Nome completo é obrigatório.")
            elif len(nome_completo) < 3:
                errors.append("Nome deve ter pelo menos 3 caracteres.")
                
            if not email_corporativo:
                errors.append("Email corporativo é obrigatório.")
            elif not email_corporativo.endswith('@sicoob.com.br'):
                errors.append("Email deve ser do domínio @sicoob.com.br")
                
            if not cpf:
                errors.append("CPF é obrigatório.")
            else:
                # Validar formato do CPF
                cpf_limpo = re.sub(r'[^\d]', '', cpf)
                if len(cpf_limpo) != 11:
                    errors.append("CPF deve conter 11 dígitos.")
                elif not validar_cpf(cpf_limpo):
                    errors.append("CPF inválido.")
                    
            if not telefone:
                errors.append("Telefone é obrigatório.")
            else:
                # Validar formato do telefone
                telefone_pattern = r'^\(\d{2}\)\s\d{4,5}-\d{4}$'
                if not re.match(telefone_pattern, telefone):
                    errors.append("Telefone deve estar no formato: (11) 99999-9999")
                    
            if not agencia:
                errors.append("Agência é obrigatória.")
                
            if not setor:
                errors.append("Setor é obrigatório.")
                
            if not tamanho_camiseta:
                errors.append("Tamanho da camiseta é obrigatório.")

            # Se há erros, retornar para o formulário
            if errors:
                for error in errors:
                    messages.error(request, error)
                return render(request, 'cadastro_voluntario.html', {
                    'form_data': request.POST
                })

            # Limpar CPF para armazenamento (apenas números)
            cpf_limpo = re.sub(r'[^\d]', '', cpf)

            # Criar o voluntário
            voluntario = Voluntario.objects.create(
                nome_completo=nome_completo,
                email_corporativo=email_corporativo,
                cpf=cpf_limpo,  # Salvar CPF limpo
                telefone=telefone,
                agencia=agencia,
                setor=setor,
                tamanho_camiseta=tamanho_camiseta,
                experiencia_anterior=experiencia_anterior if experiencia_anterior else None,
                cargo=""  # Campo vazio para ser preenchido pelo admin
            )

            # Mensagem de sucesso
            messages.success(
                request, 
                f"Inscrição realizada com sucesso! Obrigado {nome_completo}, "
                "sua candidatura foi registrada e será analisada pela equipe organizadora."
            )
            
            # Redirecionar para evitar reenvio do formulário e limpar campos
            return redirect('vmm:cadastro_voluntario')  # Use o namespace correto

        except IntegrityError as e:
            error_message = str(e).lower()
            if 'email_corporativo' in error_message or 'unique' in error_message:
                if 'email' in error_message:
                    messages.error(request, "Este email já está cadastrado.")
                elif 'cpf' in error_message:
                    messages.error(request, "Este CPF já está cadastrado.")
                else:
                    messages.error(request, "Já existe um cadastro com essas informações.")
            else:
                messages.error(request, "Erro ao processar inscrição. Tente novamente.")
            
            return render(request, 'cadastro_voluntario.html', {
                'form_data': request.POST
            })
            
        except Exception as e:
            # Log do erro para debug (opcional)
            print(f"Erro inesperado no cadastro: {e}")
            
            messages.error(
                request, 
                "Ocorreu um erro inesperado. Por favor, tente novamente ou "
                "entre em contato com o suporte."
            )
            
            return render(request, 'cadastro_voluntario.html', {
                'form_data': request.POST
            })

    # GET request - mostrar formulário limpo (sem form_data)
    return render(request, 'cadastro_voluntario.html')

def validar_cpf(cpf):
    """
    Valida se o CPF é válido usando o algoritmo oficial
    """
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^\d]', '', cpf)
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Calcula o primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    # Verifica o primeiro dígito
    if int(cpf[9]) != digito1:
        return False
    
    # Calcula o segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    # Verifica o segundo dígito
    return int(cpf[10]) == digito2

# View adicional para listar voluntários (para admin)
def lista_voluntarios(request):
    """
    View para listar todos os voluntários (apenas para staff)
    """
    if not request.user.is_staff:
        messages.error(request, "Acesso negado.")
        return redirect('vmm:cadastro_voluntario')  # Use o namespace correto
    
    voluntarios = Voluntario.objects.all().order_by('-data_cadastro')
    
    # Filtros opcionais
    agencia_filtro = request.GET.get('agencia')
    status_filtro = request.GET.get('status')
    
    if agencia_filtro:
        voluntarios = voluntarios.filter(agencia=agencia_filtro)
    
    if status_filtro:
        voluntarios = voluntarios.filter(status=status_filtro)
    
    context = {
        'voluntarios': voluntarios,
        'agencias': Voluntario.AGENCIAS_CHOICES,
        'status_choices': Voluntario.STATUS_CHOICES,
        'agencia_filtro': agencia_filtro,
        'status_filtro': status_filtro,
    }
    
    return render(request, 'voluntarios/lista.html', context)