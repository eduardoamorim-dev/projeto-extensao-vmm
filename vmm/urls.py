from django.urls import path
from . import views

app_name = 'vmm'

urlpatterns = [
    # Página principal de inscrição
    path('', views.cadastro_voluntario, name='cadastro_voluntario'),
    
    
    # Área administrativa (apenas para staff)
    path('lista/', views.lista_voluntarios, name='lista_voluntarios'),
]