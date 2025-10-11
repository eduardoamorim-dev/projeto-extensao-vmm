# urls.py
from django.urls import path
from . import views

app_name = 'vmm'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard_admin, name='dashboard_admin'),
    
    # Voluntários 
    path('', views.cadastro_voluntario, name='cadastro_voluntario'),
    path('lista/', views.lista_voluntarios, name='lista_voluntarios'),
    path('editar/<int:voluntario_id>/', views.editar_voluntario, name='editar_voluntario'),
    path('excluir/<int:voluntario_id>/', views.excluir_voluntario, name='excluir_voluntario'),
    
    # Veículos
    path('veiculos/', views.lista_veiculos, name='lista_veiculos'),
    path('veiculos/cadastro/', views.cadastro_veiculo, name='cadastro_veiculo'),
    path('veiculos/editar/<int:veiculo_id>/', views.editar_veiculo, name='editar_veiculo'),
    path('veiculos/excluir/<int:veiculo_id>/', views.excluir_veiculo, name='excluir_veiculo'),


    
    # Eventos
    path('eventos/', views.lista_eventos, name='lista_eventos'),
    path('eventos/cadastro/', views.cadastro_evento, name='cadastro_evento'),
    path('eventos/<int:evento_id>/', views.detalhe_evento, name='detalhe_evento'),
    path('eventos/editar/<int:evento_id>/', views.editar_evento, name='editar_evento'),
    path('eventos/excluir/<int:evento_id>/', views.excluir_evento, name='excluir_evento'),
    path('eventos/calendario/', views.calendario_eventos, name='calendario_eventos'),
    path('eventos/<int:evento_id>/adicionar-veiculo/', views.adicionar_veiculo_evento, name='adicionar_veiculo_evento'),
    path('eventos/veiculo/<int:evento_veiculo_id>/remover/', views.remover_veiculo_evento, name='remover_veiculo_evento'),
    path('voluntario-evento/editar/<int:voluntario_evento_id>/', views.editar_voluntario_evento, name='editar_voluntario_evento'),
    
    # Voluntários em Eventos
    path('eventos/<int:evento_id>/adicionar-voluntario/', views.adicionar_voluntario_evento, name='adicionar_voluntario_evento'),
    path('eventos/voluntario/<int:voluntario_evento_id>/remover/', views.remover_voluntario_evento, name='remover_voluntario_evento'),
    path('eventos/voluntario/<int:voluntario_evento_id>/presenca/', views.atualizar_presenca_voluntario, name='atualizar_presenca_voluntario'),
    
    # APIs JSON
    path('api/verificar-disponibilidade-voluntario/', views.api_verificar_disponibilidade_voluntario, name='api_verificar_disponibilidade_voluntario'),
    path('api/verificar-disponibilidade-veiculo/', views.api_verificar_disponibilidade_veiculo, name='api_verificar_disponibilidade_veiculo'),
    path('api/voluntarios-disponiveis/', views.api_voluntarios_disponiveis, name='api_voluntarios_disponiveis'),
    path('api/evento/<int:evento_id>/estatisticas/', views.api_estatisticas_evento, name='api_estatisticas_evento'),
    path('api/agencias/', views.get_agencias_json, name='get_agencias_json'),
    path('api/tamanhos/', views.get_tamanhos_json, name='get_tamanhos_json'),


]