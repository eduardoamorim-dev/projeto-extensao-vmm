from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.db.models import Count
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
            agencia_raw = request.POST.get('agencia', '').strip()
            setor = request.POST.get('setor', '').strip()
            tamanho_camiseta = request.POST.get('tamanho_camiseta', '')
            experiencia_anterior = request.POST.get('experiencia_anterior', '').strip()

            # Processar agência (extrair código se veio no formato "001 - Nome da Agência")
            agencia = agencia_raw
            if ' - ' in agencia_raw:
                agencia = agencia_raw.split(' - ')[0].strip()

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
            else:
                # Verificar se a agência existe na lista
                agencias_validas = [codigo for codigo, nome in Voluntario.AGENCIAS_CHOICES]
                if agencia not in agencias_validas:
                    errors.append("Agência selecionada não é válida.")
                
            if not setor:
                errors.append("Setor é obrigatório.")
                
            if not tamanho_camiseta:
                errors.append("Tamanho da camiseta é obrigatório.")
            else:
                # Verificar se o tamanho da camiseta é válido
                tamanhos_validos = [codigo for codigo, nome in Voluntario.TAMANHOS_CAMISETA]
                if tamanho_camiseta not in tamanhos_validos:
                    errors.append("Tamanho da camiseta selecionado não é válido.")

            # Se há erros, retornar para o formulário
            if errors:
                for error in errors:
                    messages.error(request, error)
                return render(request, 'cadastro_voluntario.html', {
                    'form_data': request.POST,
                    'agencias': Voluntario.AGENCIAS_CHOICES,
                    'tamanhos_camiseta': Voluntario.TAMANHOS_CAMISETA,
                })

            # Limpar CPF para armazenamento (apenas números)
            cpf_limpo = re.sub(r'[^\d]', '', cpf)

            # Criar o voluntário
            voluntario = Voluntario.objects.create(
                nome_completo=nome_completo,
                email_corporativo=email_corporativo,
                cpf=cpf_limpo,  # Salvar CPF limpo
                telefone=telefone,
                agencia=agencia,  # Salvar apenas o código
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
            
            return redirect('vmm:cadastro_voluntario') 

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
                'form_data': request.POST,
                'agencias': Voluntario.AGENCIAS_CHOICES,
                'tamanhos_camiseta': Voluntario.TAMANHOS_CAMISETA,
            })
            
        except Exception as e:
            print(f"Erro inesperado no cadastro: {e}")
            
            messages.error(
                request, 
                "Ocorreu um erro inesperado. Por favor, tente novamente ou "
                "entre em contato com o suporte."
            )
            
            return render(request, 'cadastro_voluntario.html', {
                'form_data': request.POST,
                'agencias': Voluntario.AGENCIAS_CHOICES,
                'tamanhos_camiseta': Voluntario.TAMANHOS_CAMISETA,
            })

    # GET request - mostrar formulário limpo
    return render(request, 'cadastro_voluntario.html', {
        'agencias': Voluntario.AGENCIAS_CHOICES,
        'tamanhos_camiseta': Voluntario.TAMANHOS_CAMISETA,
    })


def lista_voluntarios(request):
    """
    View para listar todos os voluntários (apenas para staff)
    """
    # Buscar todos os voluntários para estatísticas gerais
    todos_voluntarios = Voluntario.objects.all()
    voluntarios = todos_voluntarios.order_by('-data_cadastro')
    
    # Filtros opcionais - aplicar apenas na listagem, não no resumo
    agencia_filtro = request.GET.get('agencia')
    status_filtro = request.GET.get('status')
    
    if agencia_filtro:
        voluntarios = voluntarios.filter(agencia=agencia_filtro)
    
    if status_filtro:
        voluntarios = voluntarios.filter(status=status_filtro)
    
    # Estatísticas agregadas para evitar duplicação
    voluntarios_por_agencia = (
        todos_voluntarios.values('agencia')
        .annotate(total=Count('id'))
        .order_by('agencia')
    )
    
    camisetas_por_tamanho = (
        todos_voluntarios.values('tamanho_camiseta')
        .annotate(total=Count('id'))
        .order_by('tamanho_camiseta')
    )
    
    # Converter códigos para nomes
    def get_nome_agencia(codigo):
        for cod, nome in Voluntario.AGENCIAS_CHOICES:
            if cod == codigo:
                return nome
        return codigo
    
    def get_nome_tamanho(codigo):
        for cod, nome in Voluntario.TAMANHOS_CAMISETA:
            if cod == codigo:
                return nome
        return codigo
    
    # Preparar dados para o template
    agencias_stats = []
    for item in voluntarios_por_agencia:
        agencias_stats.append({
            'nome': get_nome_agencia(item['agencia']),
            'total': item['total']
        })
    
    camisetas_stats = []
    for item in camisetas_por_tamanho:
        camisetas_stats.append({
            'nome': get_nome_tamanho(item['tamanho_camiseta']),
            'total': item['total']
        })
    
    context = {
        'voluntarios': voluntarios,
        'agencias': Voluntario.AGENCIAS_CHOICES,
        'status_choices': Voluntario.STATUS_CHOICES,
        'tamanhos_camiseta': Voluntario.TAMANHOS_CAMISETA,
        'agencia_filtro': agencia_filtro,
        'status_filtro': status_filtro,
        'agencias_stats': agencias_stats,
        'camisetas_stats': camisetas_stats,
    }

    return render(request, 'admin_voluntarios_lista.html', context)


@csrf_protect
def editar_voluntario(request, voluntario_id):
    """
    View para editar voluntário
    """
    voluntario = get_object_or_404(Voluntario, id=voluntario_id)
    
    if request.method == "POST":
        try:
            voluntario.nome_completo = request.POST.get('nome_completo', '').strip()
            voluntario.email_corporativo = request.POST.get('email_corporativo', '').strip().lower()
            voluntario.cpf = request.POST.get('cpf', '').strip()
            voluntario.telefone = request.POST.get('telefone', '').strip()
            voluntario.agencia = request.POST.get('agencia', '')
            voluntario.setor = request.POST.get('setor', '').strip()
            voluntario.tamanho_camiseta = request.POST.get('tamanho_camiseta', '')
            voluntario.cargo = request.POST.get('cargo', '').strip()
            voluntario.status = request.POST.get('status', '')
            voluntario.experiencia_anterior = request.POST.get('experiencia_anterior', '').strip()
            
            # Validações básicas
            errors = []
            
            if not voluntario.nome_completo or len(voluntario.nome_completo) < 3:
                errors.append("Nome deve ter pelo menos 3 caracteres.")
                
            if not voluntario.email_corporativo.endswith('@sicoob.com.br'):
                errors.append("Email deve ser do domínio @sicoob.com.br")
                
            # Validar CPF
            if voluntario.cpf:
                cpf_limpo = re.sub(r'[^\d]', '', voluntario.cpf)
                if len(cpf_limpo) != 11:
                    errors.append("CPF deve conter 11 dígitos.")
                elif not validar_cpf(cpf_limpo):
                    errors.append("CPF inválido.")
                    
            # Validar telefone
            if voluntario.telefone:
                telefone_pattern = r'^\(\d{2}\)\s\d{4,5}-\d{4}$'
                if not re.match(telefone_pattern, voluntario.telefone):
                    errors.append("Telefone deve estar no formato: (11) 99999-9999")
                    
            # Validar agência
            agencias_validas = [codigo for codigo, nome in Voluntario.AGENCIAS_CHOICES]
            if voluntario.agencia not in agencias_validas:
                errors.append("Agência selecionada não é válida.")
                
            # Validar tamanho
            tamanhos_validos = [codigo for codigo, nome in Voluntario.TAMANHOS_CAMISETA]
            if voluntario.tamanho_camiseta not in tamanhos_validos:
                errors.append("Tamanho da camiseta selecionado não é válido.")
                
            # Validar status
            status_validos = [codigo for codigo, nome in Voluntario.STATUS_CHOICES]
            if voluntario.status not in status_validos:
                errors.append("Status selecionado não é válido.")
            
            if errors:
                for error in errors:
                    messages.error(request, error)

                cpf_formatado = voluntario.formatar_cpf(voluntario.cpf) if voluntario.cpf else ''
                return render(request, 'editar_voluntario.html', {
                    'voluntario': voluntario,
                    'cpf_formatado': cpf_formatado,
                    'agencias': Voluntario.AGENCIAS_CHOICES,
                    'tamanhos_camiseta': Voluntario.TAMANHOS_CAMISETA,
                    'status_choices': Voluntario.STATUS_CHOICES,
                })
            
            voluntario.cpf = re.sub(r'[^\d]', '', voluntario.cpf)
            
            voluntario.save()
            messages.success(request, f'Voluntário {voluntario.nome_completo} atualizado com sucesso!')
            return redirect('vmm:lista_voluntarios')
            
        except IntegrityError as e:
            error_message = str(e).lower()
            if 'email_corporativo' in error_message:
                messages.error(request, "Este email já está cadastrado por outro voluntário.")
            elif 'cpf' in error_message:
                messages.error(request, "Este CPF já está cadastrado por outro voluntário.")
            else:
                messages.error(request, "Já existe um cadastro com essas informações.")
                
        except Exception as e:
            messages.error(request, "Erro inesperado ao atualizar voluntário.")
    
    # Formatar CPF para exibição (GET request ou erros)
    cpf_formatado = voluntario.formatar_cpf(voluntario.cpf) if voluntario.cpf else ''
    
    return render(request, 'editar_voluntario.html', {
        'voluntario': voluntario,
        'cpf_formatado': cpf_formatado,
        'agencias': Voluntario.AGENCIAS_CHOICES,
        'tamanhos_camiseta': Voluntario.TAMANHOS_CAMISETA,
        'status_choices': Voluntario.STATUS_CHOICES,
    })


@csrf_protect
@require_http_methods(["POST"])
def excluir_voluntario(request, voluntario_id):
    """
    View para excluir voluntário
    """
    voluntario = get_object_or_404(Voluntario, id=voluntario_id)
    nome = voluntario.nome_completo
    
    try:
        voluntario.delete()
        messages.success(request, f'Voluntário {nome} excluído com sucesso!')
    except Exception as e:
        messages.error(request, 'Erro ao excluir voluntário.')
    
    return redirect('vmm:lista_voluntarios')


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


# Funções auxiliares para APIs 
def get_agencias_json(request):
    """
    Retorna as agências em formato JSON para AJAX
    """
    from django.http import JsonResponse
    return JsonResponse({'agencias': Voluntario.AGENCIAS_CHOICES})


def get_tamanhos_json(request):
    """
    Retorna os tamanhos em formato JSON para AJAX
    """
    from django.http import JsonResponse
    return JsonResponse({'tamanhos': Voluntario.TAMANHOS_CAMISETA})