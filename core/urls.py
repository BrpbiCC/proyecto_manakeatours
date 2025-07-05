from django.urls import path
from . import views # Importa tus vistas desde el mismo directorio

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('registro/', views.registro, name='registro'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'), 
    path('hospedaje/', views.hospedaje, name='hospedaje'),
    path('actividad/', views.actividad, name='actividad'),
    path('gastronomia/', views.gastronomia, name='gastronomia'),
    path('carrito/', views.carrito, name='carrito'),
    path('inicioregistrado/', views.inicioregistrado, name='inicioregistrado'),
    path('perfil/', views.perfil, name='perfil'),
    path('listar_reservas_anfitrion/', views.listar_reservas_anfitrion, name='listar_reservas_anfitrion'),
    path('listar_servicios_admimistrador/', views.listar_servicios_administrador, name='listar_servicios_administrador'),
    path('detalle_hospedaje/<int:servicio_id>/', views.detalle_hospedaje, name='detalle_hospedaje'),
    path('detalle_actividad/<int:servicio_id>/', views.detalle_actividad, name='detalle_actividad'),
    path('detalle_gastronomia/<int:servicio_id>/', views.detalle_gastronomia, name='detalle_gastronomia'),
]