# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.db.models import Count, Q, Prefetch
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
import re

from .models import Voluntario, Evento, Veiculo, VoluntarioEvento, EventoVeiculo


# ==================== VIEWS DE VOLUNTÁRIOS  ====================

@csrf_protect
@require_http_methods(["GET", "POST"])
def cadastro_voluntario(request):
    """View para inscrição de voluntários"""
    if request.method == "POST":
        try:
            # Capturar dados
            nome_completo = request.POST.get('nome_completo', '').strip()
            email_corporativo = request.POST.get('email_corporativo', '').strip().lower()
            cpf = request.POST.get('cpf', '').strip()
            telefone = request.POST.get('telefone', '').strip()
            agencia_raw = request.POST.get('agencia', '').strip()
            setor = request.POST.get('setor', '').strip()
            tamanho_camiseta = request.POST.get('tamanho_camiseta', '')
            experiencia_anterior = request.POST.get('experiencia_anterior', '').strip()

            # Processar agência
            agencia = agencia_raw
            if ' - ' in agencia_raw:
                agencia = agencia_raw.split(' - ')[0].strip()

            # Validações
            errors = []
            
            if not nome_completo or len(nome_completo) < 3:
                errors.append("Nome deve ter pelo menos 3 caracteres.")
                
            if not email_corporativo:
                errors.append("Email corporativo é obrigatório.")
            elif not email_corporativo.endswith('@sicoob.com.br'):
                errors.append("Email deve ser do domínio @sicoob.com.br")
                
            if not cpf:
                errors.append("CPF é obrigatório.")
            else:
                cpf_limpo = re.sub(r'[^\d]', '', cpf)
                if len(cpf_limpo) != 11:
                    errors.append("CPF deve conter 11 dígitos.")
                elif not validar_cpf(cpf_limpo):
                    errors.append("CPF inválido.")
                    
            if not telefone:
                errors.append("Telefone é obrigatório.")
            else:
                telefone_pattern = r'^\(\d{2}\)\s\d{4,5}-\d{4}$'
                if not re.match(telefone_pattern, telefone):
                    errors.append("Telefone deve estar no formato: (11) 99999-9999")
                    
            if not agencia:
                errors.append("Agência é obrigatória.")
            else:
                agencias_validas = [codigo for codigo, nome in Voluntario.AGENCIAS_CHOICES]
                if agencia not in agencias_validas:
                    errors.append("Agência selecionada não é válida.")
                
            if not setor:
                errors.append("Setor é obrigatório.")
                
            if not tamanho_camiseta:
                errors.append("Tamanho da camiseta é obrigatório.")
            else:
                tamanhos_validos = [codigo for codigo, nome in Voluntario.TAMANHOS_CAMISETA]
                if tamanho_camiseta not in tamanhos_validos:
                    errors.append("Tamanho da camiseta selecionado não é válido.")

            if errors:
                for error in errors:
                    messages.error(request, error)
                return render(request, 'cadastro_voluntario.html', {
                    'form_data': request.POST,
                    'agencias': Voluntario.AGENCIAS_CHOICES,
                    'tamanhos_camiseta': Voluntario.TAMANHOS_CAMISETA,
                    'scroll_to_messages': True,
                })

            # Criar voluntário
            cpf_limpo = re.sub(r'[^\d]', '', cpf)
            voluntario = Voluntario.objects.create(
                nome_completo=nome_completo,
                email_corporativo=email_corporativo,
                cpf=cpf_limpo,
                telefone=telefone,
                agencia=agencia,
                setor=setor,
                tamanho_camiseta=tamanho_camiseta,
                cargo="",
                experiencia_anterior=experiencia_anterior if experiencia_anterior else None
            )

            # Limpar todas as mensagens anteriores antes de adicionar sucesso
            storage = messages.get_messages(request)
            storage.used = True
            
            messages.success(
                request, 
                f"Inscrição realizada com sucesso! Obrigado {nome_completo}, "
                "sua candidatura foi registrada e será analisada pela equipe organizadora."
            )
            
            # Renderizar com contexto limpo ao invés de redirecionar
            return render(request, 'cadastro_voluntario.html', {
                'agencias': Voluntario.AGENCIAS_CHOICES,
                'tamanhos_camiseta': Voluntario.TAMANHOS_CAMISETA,
                'scroll_to_messages': True,
            })

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
                'scroll_to_messages': True,
            })
            
        except Exception as e:
            messages.error(
                request, 
                "Ocorreu um erro inesperado. Por favor, tente novamente."
            )
            return render(request, 'cadastro_voluntario.html', {
                'form_data': request.POST,
                'agencias': Voluntario.AGENCIAS_CHOICES,
                'tamanhos_camiseta': Voluntario.TAMANHOS_CAMISETA,
                'scroll_to_messages': True,
            })

    return render(request, 'cadastro_voluntario.html', {
        'agencias': Voluntario.AGENCIAS_CHOICES,
        'tamanhos_camiseta': Voluntario.TAMANHOS_CAMISETA,
    })



@csrf_protect
def editar_voluntario(request, voluntario_id):
    """View para editar voluntário"""
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
            
            experiencia_raw = request.POST.get('experiencia_anterior', '').strip()
            voluntario.experiencia_anterior = experiencia_raw if experiencia_raw and experiencia_raw != 'None' else None
            
            # Validações
            errors = []
            
            if not voluntario.nome_completo or len(voluntario.nome_completo) < 3:
                errors.append("Nome deve ter pelo menos 3 caracteres.")
                
            if not voluntario.email_corporativo.endswith('@sicoob.com.br'):
                errors.append("Email deve ser do domínio @sicoob.com.br")
                
            if voluntario.cpf:
                cpf_limpo = re.sub(r'[^\d]', '', voluntario.cpf)
                if len(cpf_limpo) != 11:
                    errors.append("CPF deve conter 11 dígitos.")
                elif not validar_cpf(cpf_limpo):
                    errors.append("CPF inválido.")
                    
            if voluntario.telefone:
                telefone_pattern = r'^\(\d{2}\)\s\d{4,5}-\d{4}$'
                if not re.match(telefone_pattern, voluntario.telefone):
                    errors.append("Telefone deve estar no formato: (11) 99999-9999")
                    
            agencias_validas = [codigo for codigo, nome in Voluntario.AGENCIAS_CHOICES]
            if voluntario.agencia not in agencias_validas:
                errors.append("Agência selecionada não é válida.")
                
            tamanhos_validos = [codigo for codigo, nome in Voluntario.TAMANHOS_CAMISETA]
            if voluntario.tamanho_camiseta not in tamanhos_validos:
                errors.append("Tamanho da camiseta selecionado não é válido.")
                
            status_validos = [codigo for codigo, nome in Voluntario.STATUS_CHOICES]
            if voluntario.status not in status_validos:
                errors.append("Status selecionado não é válido.")
            
            if errors:
                for error in errors:
                    messages.error(request, error)
                cpf_formatado = voluntario.formatar_cpf(voluntario.cpf) if voluntario.cpf else ''
                experiencia_display = voluntario.experiencia_anterior if voluntario.experiencia_anterior and voluntario.experiencia_anterior != 'None' else ''
                return render(request, 'editar_voluntario.html', {
                    'voluntario': voluntario,
                    'cpf_formatado': cpf_formatado,
                    'experiencia_display': experiencia_display,
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
    
    cpf_formatado = voluntario.formatar_cpf(voluntario.cpf) if voluntario.cpf else ''
    experiencia_display = voluntario.experiencia_anterior if voluntario.experiencia_anterior and voluntario.experiencia_anterior != 'None' else ''
    
    return render(request, 'editar_voluntario.html', {
        'voluntario': voluntario,
        'cpf_formatado': cpf_formatado,
        'experiencia_display': experiencia_display,
        'agencias': Voluntario.AGENCIAS_CHOICES,
        'tamanhos_camiseta': Voluntario.TAMANHOS_CAMISETA,
        'status_choices': Voluntario.STATUS_CHOICES,
    })

def lista_voluntarios(request):
    """View para listar voluntários (incluindo inativos se solicitado)"""
    # Verificar se deve mostrar inativos
    mostrar_inativos = request.GET.get('mostrar_inativos', 'false') == 'true'
    
    if mostrar_inativos:
        todos_voluntarios = Voluntario.objects.all()
    else:
        todos_voluntarios = Voluntario.objects.filter(ativo=True)
    
    voluntarios = todos_voluntarios.order_by('-data_cadastro')
    
    # Filtros
    agencias_filtro = request.GET.getlist('agencia')
    status_filtro = request.GET.get('status')
    busca = request.GET.get('busca', '').strip()
    
    if busca:
        voluntarios = voluntarios.filter(
            Q(nome_completo__icontains=busca) |
            Q(email_corporativo__icontains=busca) |
            Q(cpf__icontains=busca)
        )
    
    if agencias_filtro:
        voluntarios = voluntarios.filter(agencia__in=agencias_filtro)
    
    if status_filtro:
        voluntarios = voluntarios.filter(status=status_filtro)
    
    # Paginação
    paginator = Paginator(voluntarios, 10)
    page_number = request.GET.get('page')
    voluntarios_page = paginator.get_page(page_number)
    
    # Estatísticas (apenas ativos)
    voluntarios_ativos = Voluntario.objects.filter(ativo=True)
    
    voluntarios_por_agencia = (
        voluntarios_ativos.values('agencia')
        .annotate(total=Count('id'))
        .order_by('agencia')
    )
    
    camisetas_por_tamanho = (
        voluntarios_ativos.values('tamanho_camiseta')
        .annotate(total=Count('id'))
        .order_by('tamanho_camiseta')
    )
    
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
    
    agencias_stats = [
        {'nome': get_nome_agencia(item['agencia']), 'total': item['total']}
        for item in voluntarios_por_agencia
    ]
    
    camisetas_stats = [
        {'nome': get_nome_tamanho(item['tamanho_camiseta']), 'total': item['total']}
        for item in camisetas_por_tamanho
    ]
    
    context = {
        'voluntarios': voluntarios_page,
        'agencias': Voluntario.AGENCIAS_CHOICES,
        'status_choices': Voluntario.STATUS_CHOICES,
        'tamanhos_camiseta': Voluntario.TAMANHOS_CAMISETA,
        'agencias_filtro': agencias_filtro,
        'status_filtro': status_filtro,
        'busca': busca,
        'mostrar_inativos': mostrar_inativos,
        'agencias_stats': agencias_stats,
        'camisetas_stats': camisetas_stats,
        'total_voluntarios': voluntarios_ativos.count(),
        'total_inativos': Voluntario.objects.filter(ativo=False).count(),
        'cadastros_recentes': voluntarios_ativos.filter(
            data_cadastro__gte=timezone.now() - timedelta(days=7)
        ).count(),
        'total_ativos': voluntarios_ativos.filter(status='ativo').count(),
        'total_agencias': len(Voluntario.AGENCIAS_CHOICES),
        'has_filters': bool(agencias_filtro or status_filtro or busca),
    }

    return render(request, 'admin_voluntarios_lista.html', context)


@csrf_protect
@require_http_methods(["POST"])
def excluir_voluntario(request, voluntario_id):
    """Soft delete de voluntário"""
    voluntario = get_object_or_404(Voluntario, id=voluntario_id)
    nome = voluntario.nome_completo
    
    # Verificar se voluntário está em eventos futuros ativos
    eventos_futuros = VoluntarioEvento.objects.filter(
        voluntario=voluntario,
        evento__data_evento__gte=timezone.now().date(),
        evento__ativo=True,
        ativo=True
    )
    
    if eventos_futuros.exists():
        messages.warning(
            request, 
            f"Não é possível inativar {nome} pois está vinculado a eventos futuros. "
            "Remova primeiro das escalas de eventos."
        )
        return redirect('vmm:lista_voluntarios')
    
    # Soft delete usando o método customizado do model
    voluntario.delete()
    
    messages.success(request, f'Voluntário {nome} foi inativado com sucesso!')
    return redirect('vmm:lista_voluntarios')


@csrf_protect
@require_http_methods(["POST"])
def reativar_voluntario(request, voluntario_id):
    """Reativar voluntário"""
    voluntario = get_object_or_404(Voluntario, id=voluntario_id)
    
    voluntario.ativo = True
    voluntario.data_inativacao = None
    voluntario.status = 'ativo'
    voluntario.save()
    
    messages.success(request, f"Voluntário {voluntario.nome_completo} foi reativado com sucesso.")
    return redirect('vmm:lista_voluntarios')




@csrf_protect
@require_http_methods(["POST"])
def editar_voluntario_evento(request, voluntario_evento_id):
    """Editar função e veículo do voluntário no evento"""
    vol_evento = get_object_or_404(VoluntarioEvento, id=voluntario_evento_id)
    
    try:
        funcao = request.POST.get('funcao')
        funcao_customizada = request.POST.get('funcao_customizada', '').strip()
        evento_veiculo_id = request.POST.get('evento_veiculo')
        
        if not funcao:
            messages.error(request, 'Função é obrigatória.')
            return redirect('vmm:detalhe_evento', evento_id=vol_evento.evento.id)
        
        vol_evento.funcao = funcao
        vol_evento.funcao_customizada = funcao_customizada if funcao == 'outro' else ''
        
        # Atualizar veículo
        if evento_veiculo_id:
            evento_veiculo = get_object_or_404(EventoVeiculo, id=evento_veiculo_id, evento=vol_evento.evento)
            
            # Verificar capacidade
            ocupacao_atual = VoluntarioEvento.objects.filter(
                evento=vol_evento.evento,
                evento_veiculo=evento_veiculo
            ).exclude(pk=vol_evento.pk).count()
            
            if ocupacao_atual >= evento_veiculo.veiculo.capacidade:
                messages.error(
                    request, 
                    f'O veículo {evento_veiculo.veiculo.nome} já está na capacidade máxima.'
                )
                return redirect('vmm:detalhe_evento', evento_id=vol_evento.evento.id)
            
            vol_evento.vai_no_veiculo = True
            vol_evento.evento_veiculo = evento_veiculo
        else:
            vol_evento.vai_no_veiculo = False
            vol_evento.evento_veiculo = None
        
        vol_evento.save()
        messages.success(request, f'Dados de {vol_evento.voluntario.nome_completo} atualizados!')
        
    except Exception as e:
        messages.error(request, f'Erro ao atualizar: {str(e)}')
    
    return redirect('vmm:detalhe_evento', evento_id=vol_evento.evento.id)


# ==================== VIEWS DE VEÍCULOS ====================

def lista_veiculos(request):
    """Lista todos os veículos com filtros"""
    mostrar_inativos = request.GET.get('mostrar_inativos', 'false') == 'true'
    
    if mostrar_inativos:
        veiculos = Veiculo.objects.all()
    else:
        veiculos = Veiculo.objects.filter(ativo=True)
    
    veiculos = veiculos.order_by('nome')
    
    # Filtros
    status_filtro = request.GET.get('status')
    tipo_filtro = request.GET.get('tipo')
    busca = request.GET.get('busca', '').strip()
    
    if busca:
        veiculos = veiculos.filter(
            Q(nome__icontains=busca) |
            Q(placa__icontains=busca)
        )
    
    if status_filtro:
        veiculos = veiculos.filter(status=status_filtro)
    
    if tipo_filtro:
        veiculos = veiculos.filter(tipo=tipo_filtro)
    
    # Paginação
    paginator = Paginator(veiculos, 10)
    page_number = request.GET.get('page')
    veiculos_page = paginator.get_page(page_number)
    
    # Estatísticas (apenas ativos)
    veiculos_ativos = Veiculo.objects.filter(ativo=True)
    
    context = {
        'veiculos': veiculos_page,
        'status_choices': Veiculo.STATUS_VEICULO,
        'tipo_choices': Veiculo.TIPO_VEICULO,
        'status_filtro': status_filtro,
        'tipo_filtro': tipo_filtro,
        'busca': busca,
        'mostrar_inativos': mostrar_inativos,
        'total_veiculos': veiculos_ativos.count(),
        'total_inativos': Veiculo.objects.filter(ativo=False).count(),
        'disponiveis': veiculos_ativos.filter(status='disponivel').count(),
        'em_manutencao': veiculos_ativos.filter(status='manutencao').count(),
        'has_filters': bool(status_filtro or tipo_filtro or busca),
    }
    
    return render(request, 'veiculos_lista.html', context)


@csrf_protect
@require_http_methods(["POST"])
def excluir_veiculo(request, veiculo_id):
    """Soft delete de veículo"""
    veiculo = get_object_or_404(Veiculo, id=veiculo_id)
    nome = veiculo.nome
    
    # Verificar se há eventos futuros com este veículo
    hoje = timezone.now().date()
    eventos_futuros = EventoVeiculo.objects.filter(
        veiculo=veiculo,
        evento__data_evento__gte=hoje,
        evento__ativo=True,
        ativo=True
    ).exists()
    
    if eventos_futuros:
        messages.error(
            request, 
            f'O veículo {nome} possui eventos futuros agendados. '
            'Remova-o dos eventos antes de inativar.'
        )
        return redirect('vmm:lista_veiculos')
    
    # Soft delete usando o método customizado do model
    veiculo.delete()
    
    messages.success(request, f'Veículo {nome} foi inativado com sucesso!')
    return redirect('vmm:lista_veiculos')


@csrf_protect
@require_http_methods(["POST"])
def reativar_veiculo(request, veiculo_id):
    """Reativar veículo"""
    veiculo = get_object_or_404(Veiculo, id=veiculo_id)
    
    veiculo.ativo = True
    veiculo.data_inativacao = None
    veiculo.status = 'disponivel'
    veiculo.save()
    
    messages.success(request, f"Veículo {veiculo.nome} foi reativado com sucesso.")
    return redirect('vmm:lista_veiculos')

@csrf_protect
@require_http_methods(["GET", "POST"])
def cadastro_veiculo(request):
    """Cadastrar novo veículo"""
    if request.method == "POST":
        try:
            nome = request.POST.get('nome', '').strip()
            placa = request.POST.get('placa', '').strip().upper()
            tipo = request.POST.get('tipo', '')
            capacidade = request.POST.get('capacidade', 5)
            status = request.POST.get('status', 'disponivel')
            observacoes = request.POST.get('observacoes', '').strip()
            
            # Validações
            errors = []
            
            if not nome:
                errors.append("Nome do veículo é obrigatório.")
            
            if not placa:
                errors.append("Placa é obrigatória.")
            elif len(placa) < 7:
                errors.append("Placa inválida.")
            
            if tipo not in [t[0] for t in Veiculo.TIPO_VEICULO]:
                errors.append("Tipo de veículo inválido.")
            
            try:
                capacidade = int(capacidade)
                if capacidade < 1 or capacidade > 50:
                    errors.append("Capacidade deve estar entre 1 e 50.")
            except ValueError:
                errors.append("Capacidade inválida.")
            
            if errors:
                for error in errors:
                    messages.error(request, error)
                return render(request, 'veiculo_cadastro.html', {
                    'form_data': request.POST,
                    'tipo_choices': Veiculo.TIPO_VEICULO,
                    'status_choices': Veiculo.STATUS_VEICULO,
                })
            
            # Criar veículo
            veiculo = Veiculo.objects.create(
                nome=nome,
                placa=placa,
                tipo=tipo,
                capacidade=capacidade,
                status=status,
                observacoes=observacoes
            )
            
            messages.success(request, f'Veículo {veiculo.nome} cadastrado com sucesso!')
            return redirect('vmm:lista_veiculos')
            
        except IntegrityError:
            messages.error(request, 'Já existe um veículo com esta placa.')
            return render(request, 'veiculo_cadastro.html', {
                'form_data': request.POST,
                'tipo_choices': Veiculo.TIPO_VEICULO,
                'status_choices': Veiculo.STATUS_VEICULO,
            })
        except Exception as e:
            messages.error(request, 'Erro ao cadastrar veículo.')
            return render(request, 'veiculo_cadastro.html', {
                'form_data': request.POST,
                'tipo_choices': Veiculo.TIPO_VEICULO,
                'status_choices': Veiculo.STATUS_VEICULO,
            })
    
    return render(request, 'veiculo_cadastro.html', {
        'tipo_choices': Veiculo.TIPO_VEICULO,
        'status_choices': Veiculo.STATUS_VEICULO,
    })


@csrf_protect
def editar_veiculo(request, veiculo_id):
    """Editar veículo existente"""
    veiculo = get_object_or_404(Veiculo, id=veiculo_id)
    
    if request.method == "POST":
        try:
            veiculo.nome = request.POST.get('nome', '').strip()
            veiculo.placa = request.POST.get('placa', '').strip().upper()
            veiculo.tipo = request.POST.get('tipo', '')
            veiculo.capacidade = int(request.POST.get('capacidade', 5))
            veiculo.status = request.POST.get('status', '')
            veiculo.observacoes = request.POST.get('observacoes', '').strip()
            
            # Validações
            errors = []
            
            if not veiculo.nome:
                errors.append("Nome do veículo é obrigatório.")
            
            if not veiculo.placa or len(veiculo.placa) < 7:
                errors.append("Placa inválida.")
            
            if veiculo.tipo not in [t[0] for t in Veiculo.TIPO_VEICULO]:
                errors.append("Tipo de veículo inválido.")
            
            if veiculo.capacidade < 1 or veiculo.capacidade > 50:
                errors.append("Capacidade deve estar entre 1 e 50.")
            
            if errors:
                for error in errors:
                    messages.error(request, error)
                return render(request, 'veiculo_editar.html', {
                    'veiculo': veiculo,
                    'tipo_choices': Veiculo.TIPO_VEICULO,
                    'status_choices': Veiculo.STATUS_VEICULO,
                })
            
            veiculo.save()
            messages.success(request, f'Veículo {veiculo.nome} atualizado com sucesso!')
            return redirect('vmm:lista_veiculos')
            
        except IntegrityError:
            messages.error(request, 'Já existe um veículo com esta placa.')
        except Exception as e:
            messages.error(request, 'Erro ao atualizar veículo.')
    
    return render(request, 'veiculo_editar.html', {
        'veiculo': veiculo,
        'tipo_choices': Veiculo.TIPO_VEICULO,
        'status_choices': Veiculo.STATUS_VEICULO,
    })


@csrf_protect
@require_http_methods(["POST"])
def adicionar_veiculo_evento(request, evento_id):
    """Adicionar veículo a um evento"""
    evento = get_object_or_404(Evento, id=evento_id)
    
    try:
        with transaction.atomic():
            veiculo_id = request.POST.get('veiculo_id')
            motorista_id = request.POST.get('motorista_id')
            observacoes = request.POST.get('observacoes', '').strip()
            
            if not veiculo_id:
                messages.error(request, 'Veículo é obrigatório.')
                return redirect('vmm:detalhe_evento', evento_id=evento.id)
            
            veiculo = get_object_or_404(Veiculo, id=veiculo_id, ativo=True)
            
            if EventoVeiculo.objects.filter(evento=evento, veiculo=veiculo).exists():
                messages.warning(request, f'{veiculo.nome} já está neste evento.')
                return redirect('vmm:detalhe_evento', evento_id=evento.id)
            
            conflito = EventoVeiculo.objects.filter(
                veiculo=veiculo,
                evento__data_evento=evento.data_evento,
                evento__hora_inicio__lt=evento.hora_fim,
                evento__hora_fim__gt=evento.hora_inicio
            ).exclude(evento=evento)
            
            if conflito.exists():
                messages.error(request, f'O veículo {veiculo.nome} já está alocado em outro evento neste horário.')
                return redirect('vmm:detalhe_evento', evento_id=evento.id)
            
            motorista = None
            if motorista_id:
                motorista = get_object_or_404(Voluntario, id=motorista_id)
                vol_evento = VoluntarioEvento.objects.filter(
                    evento=evento, 
                    voluntario=motorista
                ).first()
                
                if not vol_evento:
                    messages.error(request, 'O motorista deve ser um voluntário alocado neste evento.')
                    return redirect('vmm:detalhe_evento', evento_id=evento.id)
            
            evento_veiculo = EventoVeiculo.objects.create(
                evento=evento,
                veiculo=veiculo,
                motorista=motorista,
                observacoes=observacoes
            )
            
            if motorista:
                vol_evento = VoluntarioEvento.objects.get(evento=evento, voluntario=motorista)
                vol_evento.vai_no_veiculo = True
                vol_evento.evento_veiculo = evento_veiculo
                vol_evento.save()
            
            messages.success(request, f'Veículo {veiculo.nome} adicionado ao evento!')
        
    except Exception as e:
        messages.error(request, f'Erro ao adicionar veículo: {str(e)}')
    
    return redirect('vmm:detalhe_evento', evento_id=evento.id)

@csrf_protect
@require_http_methods(["POST"])
def remover_veiculo_evento(request, evento_veiculo_id):
    """Soft delete - remover veículo de um evento"""
    evento_veiculo = get_object_or_404(EventoVeiculo, id=evento_veiculo_id)
    evento_id = evento_veiculo.evento.id
    nome_veiculo = evento_veiculo.veiculo.nome
    
    # Verificar se há voluntários alocados neste veículo
    voluntarios_no_veiculo = VoluntarioEvento.objects.filter(
        evento=evento_veiculo.evento,
        evento_veiculo=evento_veiculo,
        ativo=True
    ).count()
    
    if voluntarios_no_veiculo > 0:
        messages.warning(
            request,
            f'O veículo {nome_veiculo} possui {voluntarios_no_veiculo} voluntário(s) alocado(s). '
            'Eles foram desvinculados do veículo.'
        )
        # Desvincular voluntários
        VoluntarioEvento.objects.filter(
            evento=evento_veiculo.evento,
            evento_veiculo=evento_veiculo,
            ativo=True
        ).update(evento_veiculo=None, vai_no_veiculo=False)
    
    # Soft delete usando o método customizado do model
    evento_veiculo.delete()
    
    messages.success(request, f'Veículo {nome_veiculo} removido do evento.')
    return redirect('vmm:detalhe_evento', evento_id=evento_id)



# ==================== VIEWS DE EVENTOS ====================

def lista_eventos(request):
    """Lista todos os eventos com filtros"""
    mostrar_inativos = request.GET.get('mostrar_inativos', 'false') == 'true'
    
    if mostrar_inativos:
        eventos = Evento.objects.all()
    else:
        eventos = Evento.objects.filter(ativo=True)
    
    eventos = eventos.prefetch_related(
        Prefetch(
            'voluntarioevento_set',
            queryset=VoluntarioEvento.objects.filter(ativo=True).select_related('voluntario')
        ),
        Prefetch(
            'eventoveiculo_set',
            queryset=EventoVeiculo.objects.filter(ativo=True).select_related('veiculo')
        )
    ).order_by('-data_evento', '-hora_inicio')
    
    # Filtros
    status_filtro = request.GET.get('status')
    cidade_filtro = request.GET.get('cidade')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    busca = request.GET.get('busca', '').strip()
    
    if busca:
        eventos = eventos.filter(
            Q(nome_escola__icontains=busca) |
            Q(responsavel_escola__icontains=busca) |
            Q(cidade__icontains=busca)
        )
    
    if status_filtro:
        eventos = eventos.filter(status=status_filtro)
    
    if cidade_filtro:
        eventos = eventos.filter(cidade__icontains=cidade_filtro)
    
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            eventos = eventos.filter(data_evento__gte=data_inicio_obj)
        except ValueError:
            pass
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            eventos = eventos.filter(data_evento__lte=data_fim_obj)
        except ValueError:
            pass
    
    # Paginação
    paginator = Paginator(eventos, 10)
    page_number = request.GET.get('page')
    eventos_page = paginator.get_page(page_number)
    
    # Estatísticas (apenas ativos)
    eventos_ativos = Evento.objects.filter(ativo=True)
    total_eventos = eventos_ativos.count()
    eventos_futuros = eventos_ativos.filter(data_evento__gte=timezone.now().date()).count()
    eventos_mes = eventos_ativos.filter(
        data_evento__year=timezone.now().year,
        data_evento__month=timezone.now().month
    ).count()
    
    # Cidades únicas para filtro
    cidades = eventos_ativos.values_list('cidade', flat=True).distinct().order_by('cidade')
    
    context = {
        'eventos': eventos_page,
        'status_choices': Evento.STATUS_EVENTO,
        'status_filtro': status_filtro,
        'cidade_filtro': cidade_filtro,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'busca': busca,
        'cidades': cidades,
        'mostrar_inativos': mostrar_inativos,
        'total_eventos': total_eventos,
        'total_inativos': Evento.objects.filter(ativo=False).count(),
        'eventos_futuros': eventos_futuros,
        'eventos_mes': eventos_mes,
        'has_filters': bool(status_filtro or cidade_filtro or data_inicio or data_fim or busca),
    }
    
    return render(request, 'eventos_lista.html', context)


@csrf_protect
@require_http_methods(["GET", "POST"])
def cadastro_evento(request):
    """Cadastrar novo evento"""
    if request.method == "POST":
        try:
            with transaction.atomic():
                # Capturar dados do evento
                nome_escola = request.POST.get('nome_escola', '').strip()
                responsavel_escola = request.POST.get('responsavel_escola', '').strip()
                telefone_responsavel = request.POST.get('telefone_responsavel', '').strip()
                cidade = request.POST.get('cidade', '').strip()
                endereco = request.POST.get('endereco', '').strip()
                
                data_evento_str = request.POST.get('data_evento', '')
                hora_inicio_str = request.POST.get('hora_inicio', '')
                hora_fim_str = request.POST.get('hora_fim', '')
                
                qtd_tv = request.POST.get('qtd_tv', 0)
                qtd_computador = request.POST.get('qtd_computador', 0)
                status = request.POST.get('status', 'planejamento')
                observacoes = request.POST.get('observacoes', '').strip()
                
                # Validações
                errors = []
                
                if not nome_escola:
                    errors.append("Nome da escola é obrigatório.")
                
                if not responsavel_escola:
                    errors.append("Nome do responsável é obrigatório.")
                
                if not telefone_responsavel:
                    errors.append("Telefone do responsável é obrigatório.")
                
                if not cidade:
                    errors.append("Cidade é obrigatória.")
                
                if not endereco:
                    errors.append("Endereço é obrigatório.")
                
                # Validar data e hora
                try:
                    data_evento = datetime.strptime(data_evento_str, '%Y-%m-%d').date()
                except ValueError:
                    errors.append("Data do evento inválida.")
                    data_evento = None
                
                try:
                    hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
                except ValueError:
                    errors.append("Hora de início inválida.")
                    hora_inicio = None
                
                try:
                    hora_fim = datetime.strptime(hora_fim_str, '%H:%M').time()
                except ValueError:
                    errors.append("Hora de término inválida.")
                    hora_fim = None
                
                # Validar horários
                if hora_inicio and hora_fim:
                    if hora_inicio >= hora_fim:
                        errors.append("A hora de término deve ser posterior à hora de início.")
                
                # Validar quantidades
                try:
                    qtd_tv = int(qtd_tv)
                    if qtd_tv < 0:
                        errors.append("Quantidade de TVs deve ser positiva.")
                except ValueError:
                    qtd_tv = 0
                
                try:
                    qtd_computador = int(qtd_computador)
                    if qtd_computador < 0:
                        errors.append("Quantidade de computadores deve ser positiva.")
                except ValueError:
                    qtd_computador = 0
                
                if errors:
                    for error in errors:
                        messages.error(request, error)
                    return render(request, 'evento_cadastro.html', {
                        'form_data': request.POST,
                        'veiculos': Veiculo.objects.filter(status='disponivel', ativo=True),
                        'status_choices': Evento.STATUS_EVENTO,
                    })
                
                # Criar evento
                evento = Evento.objects.create(
                    nome_escola=nome_escola,
                    responsavel_escola=responsavel_escola,
                    telefone_responsavel=telefone_responsavel,
                    cidade=cidade,
                    endereco=endereco,
                    data_evento=data_evento,
                    hora_inicio=hora_inicio,
                    hora_fim=hora_fim,
                    qtd_tv=qtd_tv,
                    qtd_computador=qtd_computador,
                    status=status,
                    observacoes=observacoes,
                    criado_por=request.user.username if request.user.is_authenticated else 'Sistema'
                )
                
                messages.success(request, f'Evento "{evento.nome_escola}" cadastrado com sucesso!')
                return redirect('vmm:detalhe_evento', evento_id=evento.id)
                
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar evento: {str(e)}')
            return render(request, 'evento_cadastro.html', {
                'form_data': request.POST,
                'status_choices': Evento.STATUS_EVENTO,
            })
    
    return render(request, 'evento_cadastro.html', {
        'veiculos': Veiculo.objects.filter(status='disponivel', ativo=True),
        'status_choices': Evento.STATUS_EVENTO,
    })


def detalhe_evento(request, evento_id):
    """Visualizar detalhes completos do evento"""
    evento = get_object_or_404(
        Evento.objects.prefetch_related(
            Prefetch(
                'voluntarioevento_set',
                queryset=VoluntarioEvento.objects.select_related(
                    'voluntario', 
                    'evento_veiculo__veiculo'
                ).order_by('funcao')
            ),
            Prefetch(
                'eventoveiculo_set',
                queryset=EventoVeiculo.objects.select_related('veiculo', 'motorista')
            )
        ),
        id=evento_id
    )
    
    # Voluntários do evento
    voluntarios_evento = evento.voluntarioevento_set.all()
    
    # Voluntários disponíveis (não alocados neste horário)
    voluntarios_disponiveis = Voluntario.objects.filter(
        status='ativo'
    ).exclude(
        id__in=voluntarios_evento.values_list('voluntario_id', flat=True)
    )
    
    # Filtrar disponíveis no horário
    voluntarios_disponiveis_filtrados = []
    for vol in voluntarios_disponiveis:
        if vol.verificar_disponibilidade(evento.data_evento, evento.hora_inicio, evento.hora_fim):
            voluntarios_disponiveis_filtrados.append(vol)
    
    # Veículos disponíveis (não alocados neste evento e horário)
    veiculos_disponiveis = Veiculo.objects.filter(
        status='disponivel',
        ativo=True
    ).exclude(
        id__in=evento.eventoveiculo_set.values_list('veiculo_id', flat=True)
    )
    
    # Filtrar disponíveis no horário
    veiculos_disponiveis_filtrados = []
    for veiculo in veiculos_disponiveis:
        if veiculo.verificar_disponibilidade(evento.data_evento, evento.hora_inicio, evento.hora_fim):
            veiculos_disponiveis_filtrados.append(veiculo)
    
    # Estatísticas
    total_voluntarios = voluntarios_evento.count()
    confirmados = voluntarios_evento.filter(presenca='confirmado').count()
    presentes = voluntarios_evento.filter(presenca='presente').count()
    
    context = {
        'evento': evento,
        'voluntarios_evento': voluntarios_evento,
        'voluntarios_disponiveis': voluntarios_disponiveis_filtrados,
        'veiculos_disponiveis': veiculos_disponiveis_filtrados,
        'funcoes': VoluntarioEvento.FUNCOES,
        'total_voluntarios': total_voluntarios,
        'confirmados': confirmados,
        'presentes': presentes,
        'pode_editar': evento.status in ['planejamento', 'confirmado'],
    }
    
    return render(request, 'evento_detalhe.html', context)

@csrf_protect
def editar_evento(request, evento_id):
    """Editar evento existente"""
    evento = get_object_or_404(Evento, id=evento_id)
    
    if request.method == "POST":
        try:
            with transaction.atomic():
                evento.nome_escola = request.POST.get('nome_escola', '').strip()
                evento.responsavel_escola = request.POST.get('responsavel_escola', '').strip()
                evento.telefone_responsavel = request.POST.get('telefone_responsavel', '').strip()
                evento.cidade = request.POST.get('cidade', '').strip()
                evento.endereco = request.POST.get('endereco', '').strip()
                
                data_evento_str = request.POST.get('data_evento', '')
                hora_inicio_str = request.POST.get('hora_inicio', '')
                hora_fim_str = request.POST.get('hora_fim', '')
                
                evento.qtd_tv = int(request.POST.get('qtd_tv', 0))
                evento.qtd_computador = int(request.POST.get('qtd_computador', 0))
                evento.status = request.POST.get('status', '')
                evento.observacoes = request.POST.get('observacoes', '').strip()
                
                # Validações
                errors = []
                
                # Validar datas
                try:
                    evento.data_evento = datetime.strptime(data_evento_str, '%Y-%m-%d').date()
                except ValueError:
                    errors.append("Data do evento inválida.")
                
                try:
                    evento.hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
                except ValueError:
                    errors.append("Hora de início inválida.")
                
                try:
                    evento.hora_fim = datetime.strptime(hora_fim_str, '%H:%M').time()
                except ValueError:
                    errors.append("Hora de término inválida.")
                
                if errors:
                    for error in errors:
                        messages.error(request, error)
                    return render(request, 'evento_editar.html', {
                        'evento': evento,
                        'veiculos': Veiculo.objects.filter(status='disponivel', ativo=True),
                        'status_choices': Evento.STATUS_EVENTO,
                    })
                
                evento.save()
                messages.success(request, f'Evento "{evento.nome_escola}" atualizado com sucesso!')
                return redirect('vmm:detalhe_evento', evento_id=evento.id)
                
        except Exception as e:
            messages.error(request, f'Erro ao atualizar evento: {str(e)}')
    
    # Formatar data e hora para o formulário
    data_evento_formatted = evento.data_evento.strftime('%Y-%m-%d')
    hora_inicio_formatted = evento.hora_inicio.strftime('%H:%M')
    hora_fim_formatted = evento.hora_fim.strftime('%H:%M')
    
    context = {
        'evento': evento,
        'data_evento_formatted': data_evento_formatted,
        'hora_inicio_formatted': hora_inicio_formatted,
        'hora_fim_formatted': hora_fim_formatted,
        'status_choices': Evento.STATUS_EVENTO,
    }
    
    return render(request, 'evento_editar.html', context)

@csrf_protect
@require_http_methods(["POST"])
def excluir_evento(request, evento_id):
    """Soft delete de evento"""
    evento = get_object_or_404(Evento, id=evento_id)
    nome_escola = evento.nome_escola
    
    # Soft delete usando o método customizado do model
    evento.delete()
    
    # Inativar relacionamentos em cascata
    VoluntarioEvento.objects.filter(evento=evento, ativo=True).update(
        ativo=False,
        data_inativacao=timezone.now()
    )
    EventoVeiculo.objects.filter(evento=evento, ativo=True).update(
        ativo=False,
        data_inativacao=timezone.now()
    )
    
    messages.success(request, f'Evento "{nome_escola}" foi inativado com sucesso!')
    return redirect('vmm:lista_eventos')

@csrf_protect
@require_http_methods(["POST"])
def reativar_evento(request, evento_id):
    """Reativar evento"""
    evento = get_object_or_404(Evento, id=evento_id)
    
    evento.ativo = True
    evento.data_inativacao = None
    evento.save()
    
    messages.success(request, f"Evento na {evento.nome_escola} foi reativado com sucesso.")
    return redirect('vmm:lista_eventos')


@csrf_protect
@require_http_methods(["POST"])
def remover_voluntario_evento(request, voluntario_evento_id):
    """Soft delete - inativar voluntário de um evento"""
    vol_evento = get_object_or_404(VoluntarioEvento, id=voluntario_evento_id)
    evento_id = vol_evento.evento.id
    nome_voluntario = vol_evento.voluntario.nome_completo
    
    # Soft delete usando o método customizado do model
    vol_evento.delete()
    
    messages.success(request, f'{nome_voluntario} removido do evento.')
    return redirect('vmm:detalhe_evento', evento_id=evento_id)

@csrf_protect
@require_http_methods(["POST"])
def cancelar_evento(request, evento_id):
    """Cancelar evento - muda status mas mantém ativo=True"""
    evento = get_object_or_404(Evento, id=evento_id)
    nome_escola = evento.nome_escola
    
    try:
        if evento.status == 'concluido':
            messages.info(request, 'Eventos concluídos não podem ser cancelados.')
        elif evento.status == 'cancelado':
            messages.info(request, 'Este evento já está cancelado.')
        else:
            evento.status = 'cancelado'
            evento.save()
            
            voluntarios_count = evento.voluntarioevento_set.count()
            if voluntarios_count > 0:
                messages.warning(
                    request,
                    f'Evento cancelado. {voluntarios_count} voluntário(s) foram notificados.'
                )
            else:
                messages.success(request, f'Evento "{nome_escola}" foi cancelado!')
    except Exception as e:
        messages.error(request, 'Erro ao cancelar evento.')
    
    return redirect('vmm:detalhe_evento', evento_id=evento.id) 


# ==================== VIEWS DE VOLUNTÁRIOS EM EVENTOS ====================

@csrf_protect
@require_http_methods(["POST"])
def adicionar_voluntario_evento(request, evento_id):
    """Adicionar voluntário a um evento"""
    evento = get_object_or_404(Evento, id=evento_id)
    
    try:
        voluntario_id = request.POST.get('voluntario_id')
        funcao = request.POST.get('funcao')
        funcao_customizada = request.POST.get('funcao_customizada', '').strip()
        evento_veiculo_id = request.POST.get('evento_veiculo')  # MUDOU: novo campo
        
        if not voluntario_id or not funcao:
            messages.error(request, 'Voluntário e função são obrigatórios.')
            return redirect('vmm:detalhe_evento', evento_id=evento.id)
        
        voluntario = get_object_or_404(Voluntario, id=voluntario_id)
        
        # Verificar se já existe
        if VoluntarioEvento.objects.filter(evento=evento, voluntario=voluntario).exists():
            messages.warning(request, f'{voluntario.nome_completo} já está neste evento.')
            return redirect('vmm:detalhe_evento', evento_id=evento.id)
        
        # Verificar veículo
        evento_veiculo = None
        vai_no_veiculo = False
        if evento_veiculo_id:
            evento_veiculo = get_object_or_404(EventoVeiculo, id=evento_veiculo_id, evento=evento)
            vai_no_veiculo = True
            
            # Verificar capacidade
            ocupacao_atual = VoluntarioEvento.objects.filter(
                evento=evento,
                evento_veiculo=evento_veiculo
            ).count()
            
            if ocupacao_atual >= evento_veiculo.veiculo.capacidade:
                messages.error(
                    request, 
                    f'O veículo {evento_veiculo.veiculo.nome} já está na capacidade máxima '
                    f'({evento_veiculo.veiculo.capacidade} lugares).'
                )
                return redirect('vmm:detalhe_evento', evento_id=evento.id)
        
        # Criar vínculo
        vol_evento = VoluntarioEvento(
            evento=evento,
            voluntario=voluntario,
            funcao=funcao,
            funcao_customizada=funcao_customizada if funcao == 'outro' else '',
            vai_no_veiculo=vai_no_veiculo,
            evento_veiculo=evento_veiculo
        )
        
        # Validar (inclui verificação de conflitos)
        vol_evento.full_clean()
        vol_evento.save()
        
        messages.success(request, f'{voluntario.nome_completo} adicionado ao evento!')
        
    except ValidationError as e:
        for error in e.messages:
            messages.error(request, error)
    except Exception as e:
        messages.error(request, f'Erro ao adicionar voluntário: {str(e)}')
    
    return redirect('vmm:detalhe_evento', evento_id=evento.id)

@csrf_protect
@require_http_methods(["POST"])
def atualizar_presenca_voluntario(request, voluntario_evento_id):
    """Atualizar presença do voluntário no evento"""
    vol_evento = get_object_or_404(VoluntarioEvento, id=voluntario_evento_id)
    
    try:
        nova_presenca = request.POST.get('presenca')
        
        if nova_presenca not in [p[0] for p in VoluntarioEvento.STATUS_PRESENCA]:
            messages.error(request, 'Status de presença inválido.')
            return redirect('vmm:detalhe_evento', evento_id=vol_evento.evento.id)
        
        vol_evento.presenca = nova_presenca
        vol_evento.save()
        
        messages.success(
            request,
            f'Presença de {vol_evento.voluntario.nome_completo} atualizada para: '
            f'{vol_evento.get_presenca_display()}'
        )
    except Exception as e:
        messages.error(request, 'Erro ao atualizar presença.')
    
    return redirect('vmm:detalhe_evento', evento_id=vol_evento.evento.id)


# ==================== VIEWS AUXILIARES E API (continuação) ====================

def calendario_eventos(request):
    """View de calendário com todos os eventos"""
    # Pegar mês e ano da query string ou usar atual
    mes = int(request.GET.get('mes', timezone.now().month))
    ano = int(request.GET.get('ano', timezone.now().year))
    
    # Eventos do mês
    eventos = Evento.objects.filter(
        ativo=True,
        data_evento__year=ano,
        data_evento__month=mes
    ).prefetch_related('voluntarioevento_set')
    
    context = {
        'eventos': eventos,
        'mes': mes,
        'ano': ano,
        'mes_anterior': (mes - 1) if mes > 1 else 12,
        'ano_anterior': ano if mes > 1 else ano - 1,
        'mes_proximo': (mes + 1) if mes < 12 else 1,
        'ano_proximo': ano if mes < 12 else ano + 1,
    }
    
    return render(request, 'calendario_eventos.html', context)


def dashboard_admin(request):
    """Dashboard principal com visão geral do sistema (apenas dados ativos)"""
    hoje = timezone.now().date()
    
    # Estatísticas apenas de registros ativos
    total_voluntarios = Voluntario.objects.filter(ativo=True).count()
    voluntarios_ativos = Voluntario.objects.filter(status='ativo', ativo=True).count()
    total_eventos = Evento.objects.filter(ativo=True).count()
    total_veiculos = Veiculo.objects.filter(ativo=True).count()
    
    eventos_proximos = Evento.objects.filter(
        ativo=True,
        data_evento__gte=hoje,
        data_evento__lte=hoje + timedelta(days=30),
        status__in=['planejamento', 'confirmado']
    ).order_by('data_evento', 'hora_inicio')[:5]
    
    eventos_mes = Evento.objects.filter(
        ativo=True,
        data_evento__year=hoje.year,
        data_evento__month=hoje.month
    ).count()
    
    voluntarios_mais_ativos = Voluntario.objects.filter(ativo=True).annotate(
        num_eventos=Count('voluntarioevento', filter=Q(voluntarioevento__ativo=True))
    ).filter(num_eventos__gt=0).order_by('-num_eventos')[:5]
    
    veiculos_mais_usados = Veiculo.objects.filter(ativo=True).annotate(
        num_eventos=Count('eventoveiculo', filter=Q(eventoveiculo__ativo=True))
    ).filter(num_eventos__gt=0).order_by('-num_eventos')[:5]
    
    eventos_por_status = Evento.objects.filter(ativo=True).values('status').annotate(
        total=Count('id')
    )
    
    alertas = []
    
    eventos_sem_voluntarios = Evento.objects.filter(
        ativo=True,
        data_evento__gte=hoje,
        status__in=['planejamento', 'confirmado']
    ).annotate(
        num_voluntarios=Count('voluntarioevento', filter=Q(voluntarioevento__ativo=True))
    ).filter(num_voluntarios=0)
    
    if eventos_sem_voluntarios.exists():
        alertas.append({
            'tipo': 'warning',
            'mensagem': f'{eventos_sem_voluntarios.count()} evento(s) futuro(s) sem voluntários alocados'
        })
    
    veiculos_manutencao = Veiculo.objects.filter(status='manutencao', ativo=True).count()
    if veiculos_manutencao > 0:
        alertas.append({
            'tipo': 'info',
            'mensagem': f'{veiculos_manutencao} veículo(s) em manutenção'
        })
    
    context = {
        'total_voluntarios': total_voluntarios,
        'voluntarios_ativos': voluntarios_ativos,
        'total_eventos': total_eventos,
        'total_veiculos': total_veiculos,
        'eventos_mes': eventos_mes,
        'eventos_proximos': eventos_proximos,
        'voluntarios_mais_ativos': voluntarios_mais_ativos,
        'veiculos_mais_usados': veiculos_mais_usados,
        'eventos_por_status': eventos_por_status,
        'alertas': alertas,
    }
    
    return render(request, 'dashboard_admin.html', context)

# ==================== APIs JSON para AJAX ====================

def api_verificar_disponibilidade_voluntario(request):
    """API para verificar se voluntário está disponível em determinado horário"""
    if request.method == "GET":
        voluntario_id = request.GET.get('voluntario_id')
        data_evento = request.GET.get('data_evento')
        hora_inicio = request.GET.get('hora_inicio')
        hora_fim = request.GET.get('hora_fim')
        evento_id = request.GET.get('evento_id', None)  # Para excluir evento atual na edição
        
        try:
            voluntario = Voluntario.objects.get(id=voluntario_id)
            data_evento_obj = datetime.strptime(data_evento, '%Y-%m-%d').date()
            hora_inicio_obj = datetime.strptime(hora_inicio, '%H:%M').time()
            hora_fim_obj = datetime.strptime(hora_fim, '%H:%M').time()
            
            # Verificar conflitos
            conflitos = VoluntarioEvento.objects.filter(
                voluntario=voluntario,
                evento__data_evento=data_evento_obj,
                evento__hora_inicio__lt=hora_fim_obj,
                evento__hora_fim__gt=hora_inicio_obj
            )
            
            # Excluir evento atual se estiver editando
            if evento_id:
                conflitos = conflitos.exclude(evento_id=evento_id)
            
            if conflitos.exists():
                evento_conflito = conflitos.first().evento
                return JsonResponse({
                    'disponivel': False,
                    'mensagem': f'Voluntário já alocado no evento "{evento_conflito.nome_escola}" '
                               f'em {evento_conflito.data_evento.strftime("%d/%m/%Y")} '
                               f'das {evento_conflito.hora_inicio.strftime("%H:%M")} '
                               f'às {evento_conflito.hora_fim.strftime("%H:%M")}'
                })
            
            return JsonResponse({
                'disponivel': True,
                'mensagem': 'Voluntário disponível'
            })
            
        except Exception as e:
            return JsonResponse({
                'disponivel': False,
                'mensagem': f'Erro ao verificar disponibilidade: {str(e)}'
            }, status=400)
    
    return JsonResponse({'erro': 'Método não permitido'}, status=405)


def api_verificar_disponibilidade_veiculo(request):
    """API para verificar se veículo está disponível em determinado horário"""
    if request.method == "GET":
        veiculo_id = request.GET.get('veiculo_id')
        data_evento = request.GET.get('data_evento')
        hora_inicio = request.GET.get('hora_inicio')
        hora_fim = request.GET.get('hora_fim')
        evento_id = request.GET.get('evento_id', None)
        
        try:
            veiculo = Veiculo.objects.get(id=veiculo_id)
            data_evento_obj = datetime.strptime(data_evento, '%Y-%m-%d').date()
            hora_inicio_obj = datetime.strptime(hora_inicio, '%H:%M').time()
            hora_fim_obj = datetime.strptime(hora_fim, '%H:%M').time()
            
            if veiculo.status != 'disponivel':
                return JsonResponse({
                    'disponivel': False,
                    'mensagem': f'Veículo está {veiculo.get_status_display()}'
                })
            
            conflitos = EventoVeiculo.objects.filter(
                veiculo=veiculo,
                evento__data_evento=data_evento_obj,
                evento__hora_inicio__lt=hora_fim_obj,
                evento__hora_fim__gt=hora_inicio_obj
            )
            
            if evento_id:
                conflitos = conflitos.exclude(evento_id=evento_id)
            
            if conflitos.exists():
                evento_conflito = conflitos.first().evento
                return JsonResponse({
                    'disponivel': False,
                    'mensagem': f'Veículo já alocado no evento "{evento_conflito.nome_escola}" '
                               f'em {evento_conflito.data_evento.strftime("%d/%m/%Y")} '
                               f'das {evento_conflito.hora_inicio.strftime("%H:%M")} '
                               f'às {evento_conflito.hora_fim.strftime("%H:%M")}'
                })
            
            return JsonResponse({
                'disponivel': True,
                'mensagem': 'Veículo disponível'
            })
            
        except Exception as e:
            return JsonResponse({
                'disponivel': False,
                'mensagem': f'Erro ao verificar disponibilidade: {str(e)}'
            }, status=400)
    
    return JsonResponse({'erro': 'Método não permitido'}, status=405)

def api_voluntarios_disponiveis(request):
    """API para listar voluntários disponíveis em determinado horário (apenas ativos)"""
    if request.method == "GET":
        data_evento = request.GET.get('data_evento')
        hora_inicio = request.GET.get('hora_inicio')
        hora_fim = request.GET.get('hora_fim')
        evento_id = request.GET.get('evento_id', None)
        
        try:
            data_evento_obj = datetime.strptime(data_evento, '%Y-%m-%d').date()
            hora_inicio_obj = datetime.strptime(hora_inicio, '%H:%M').time()
            hora_fim_obj = datetime.strptime(hora_fim, '%H:%M').time()
            
            # Buscar apenas voluntários ativos
            voluntarios = Voluntario.objects.filter(status='ativo', ativo=True)
            
            # Filtrar disponíveis
            disponiveis = []
            for vol in voluntarios:
                conflitos = VoluntarioEvento.objects.filter(
                    voluntario=vol,
                    evento__data_evento=data_evento_obj,
                    evento__hora_inicio__lt=hora_fim_obj,
                    evento__hora_fim__gt=hora_inicio_obj,
                    evento__ativo=True,
                    ativo=True
                )
                
                if evento_id:
                    conflitos = conflitos.exclude(evento_id=evento_id)
                
                if not conflitos.exists():
                    disponiveis.append({
                        'id': vol.id,
                        'nome': vol.nome_completo,
                        'agencia': vol.get_agencia_display(),
                        'setor': vol.setor
                    })
            
            return JsonResponse({
                'total': len(disponiveis),
                'voluntarios': disponiveis
            })
            
        except Exception as e:
            return JsonResponse({
                'erro': f'Erro ao buscar voluntários: {str(e)}'
            }, status=400)
    
    return JsonResponse({'erro': 'Método não permitido'}, status=405)

def api_estatisticas_evento(request, evento_id):
    """API para retornar estatísticas de um evento específico"""
    try:
        evento = Evento.objects.get(id=evento_id)
        voluntarios_evento = VoluntarioEvento.objects.filter(evento=evento)
        
        stats = {
            'total_voluntarios': voluntarios_evento.count(),
            'confirmados': voluntarios_evento.filter(presenca='confirmado').count(),
            'presentes': voluntarios_evento.filter(presenca='presente').count(),
            'ausentes': voluntarios_evento.filter(presenca='ausente').count(),
            'cancelados': voluntarios_evento.filter(presenca='cancelado').count(),
        }

        
        # Voluntários por função
        por_funcao = {}
        for ve in voluntarios_evento:
            funcao = ve.funcao_customizada if ve.funcao == 'outro' else ve.get_funcao_display()
            por_funcao[funcao] = por_funcao.get(funcao, 0) + 1
        
        stats['por_funcao'] = por_funcao
        
        return JsonResponse(stats)
        
    except Evento.DoesNotExist:
        return JsonResponse({'erro': 'Evento não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=400)


# ==================== FUNÇÕES AUXILIARES ====================

def validar_cpf(cpf):
    """Valida se o CPF é válido usando o algoritmo oficial"""
    cpf = re.sub(r'[^\d]', '', cpf)
    
    if len(cpf) != 11:
        return False
    
    if cpf == cpf[0] * 11:
        return False
    
    # Primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf[9]) != digito1:
        return False
    
    # Segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    return int(cpf[10]) == digito2


# APIs JSON existentes
def get_agencias_json(request):
    """Retorna as agências em formato JSON para AJAX"""
    return JsonResponse({'agencias': Voluntario.AGENCIAS_CHOICES})


def get_tamanhos_json(request):
    """Retorna os tamanhos em formato JSON para AJAX"""
    return JsonResponse({'tamanhos': Voluntario.TAMANHOS_CAMISETA})