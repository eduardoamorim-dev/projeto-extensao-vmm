from django.urls import path
from . import views

app_name = 'vmm'

urlpatterns = [
    # Cadastro e Lista de Voluntários
    path('', views.cadastro_voluntario, name='cadastro_voluntario'),
    path('voluntarios/', views.lista_voluntarios, name='lista_voluntarios'),
    path('voluntarios/<int:voluntario_id>/editar/', views.editar_voluntario, name='editar_voluntario'),
    path('voluntarios/<int:voluntario_id>/excluir/', views.excluir_voluntario, name='excluir_voluntario'),
    path('voluntarios/<int:voluntario_id>/reativar/', views.reativar_voluntario, name='reativar_voluntario'),
    
    # Veículos
    path('veiculos/', views.lista_veiculos, name='lista_veiculos'),
    path('veiculos/cadastro/', views.cadastro_veiculo, name='cadastro_veiculo'),
    path('veiculos/<int:veiculo_id>/editar/', views.editar_veiculo, name='editar_veiculo'),
    path('veiculos/<int:veiculo_id>/excluir/', views.excluir_veiculo, name='excluir_veiculo'),
    path('veiculos/<int:veiculo_id>/reativar/', views.reativar_veiculo, name='reativar_veiculo'),
    
    # Eventos
    path('eventos/', views.lista_eventos, name='lista_eventos'),
    path('eventos/cadastro/', views.cadastro_evento, name='cadastro_evento'),
    path('eventos/<int:evento_id>/', views.detalhe_evento, name='detalhe_evento'),
    path('eventos/<int:evento_id>/editar/', views.editar_evento, name='editar_evento'),
    path('eventos/<int:evento_id>/excluir/', views.excluir_evento, name='excluir_evento'),
    path('eventos/<int:evento_id>/reativar/', views.reativar_evento, name='reativar_evento'),
    path('eventos/<int:evento_id>/cancelar/', views.cancelar_evento, name='cancelar_evento'),
    
    # Voluntários em Eventos
    path('eventos/<int:evento_id>/voluntarios/adicionar/', views.adicionar_voluntario_evento, name='adicionar_voluntario_evento'),
    path('eventos/voluntarios/<int:voluntario_evento_id>/remover/', views.remover_voluntario_evento, name='remover_voluntario_evento'),
    path('eventos/voluntarios/<int:voluntario_evento_id>/editar/', views.editar_voluntario_evento, name='editar_voluntario_evento'),
    path('eventos/voluntarios/<int:voluntario_evento_id>/atualizar-presenca/', views.atualizar_presenca_voluntario, name='atualizar_presenca_voluntario'),
    
    # Veículos em Eventos
    path('eventos/<int:evento_id>/veiculos/adicionar/', views.adicionar_veiculo_evento, name='adicionar_veiculo_evento'),
    path('eventos/veiculos/<int:evento_veiculo_id>/remover/', views.remover_veiculo_evento, name='remover_veiculo_evento'),
    
    # Dashboard e Calendário
    path('dashboard/', views.dashboard_admin, name='dashboard_admin'),
    path('calendario/', views.calendario_eventos, name='calendario_eventos'),
]