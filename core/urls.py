from django.urls import path
from . import views
# 👇 Se importa la vista que faltaba
from .views import api_hospedaje_fechas_ocupadas, api_singleday_fechas_ocupadas 

urlpatterns = [
    # Rutas Principales
    path('', views.inicio, name='inicio'),
    path('inicioregistrado/', views.inicioregistrado, name='inicioregistrado'),
    path('carrito/', views.carrito, name='carrito'),

    # Autenticación y Perfil
    path('registro/', views.registro, name='registro'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil, name='perfil'),

    # Listas de Servicios y Reservas
    path('hospedaje/', views.hospedaje, name='hospedaje'),
    path('actividad/', views.actividad, name='actividad'),
    path('gastronomia/', views.gastronomia, name='gastronomia'),
    
    # Vistas de Anfitrión y Administrador
    path('listar_reservas_anfitrion/', views.listar_reservas_anfitrion, name='listar_reservas_anfitrion'),
    path('listar_servicios_admimistrador/', views.listar_servicios_administrador, name='listar_servicios_administrador'),

    # Rutas de Detalles y sus APIs de Fechas Ocupadas
    path('detalle_hospedaje/<int:servicio_id>/', views.detalle_hospedaje, name='detalle_hospedaje'),
    path('api/hospedaje/<int:servicio_id>/fechas_ocupadas/', api_hospedaje_fechas_ocupadas, name='api_hospedaje_fechas_ocupadas'),
    
    path('detalle_actividad/<int:servicio_id>/', views.detalle_actividad, name='detalle_actividad'),
    # 👇 Se añade la ruta que causaba el error
    path('api/actividad/<int:servicio_id>/fechas_ocupadas/', views.api_singleday_fechas_ocupadas, name='api_actividad_fechas_ocupadas'),
    
    path('detalle_gastronomia/<int:servicio_id>/', views.detalle_gastronomia, name='detalle_gastronomia'),
    path('api/gastronomia/<int:servicio_id>/fechas_ocupadas/', views.api_singleday_fechas_ocupadas, name='api_gastronomia_fechas_ocupadas'),

    # API de Pago
    path('api/procesar_pago/', views.procesar_pago, name='procesar_pago'),
    path('pago/', views.vista_pago, name='vista_pago'),
    path('procesar_pago/', views.procesar_pago, name='procesar_pago'),
]