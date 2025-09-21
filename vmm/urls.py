from django.urls import path
from . import views

app_name = 'vmm'

urlpatterns = [
    # Página principal de inscrição
    path('', views.cadastro_voluntario, name='cadastro_voluntario'),
    
    # Área administrativa (apenas para staff)
    path('lista/', views.lista_voluntarios, name='lista_voluntarios'),
    path('editar/<int:voluntario_id>/', views.editar_voluntario, name='editar_voluntario'),
    path('excluir/<int:voluntario_id>/', views.excluir_voluntario, name='excluir_voluntario'),
]