from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.http import JsonResponse # ¡IMPORTAR ESTO!
from datetime import date, timedelta # ¡IMPORTAR ESTO!

from .forms import RegistroClienteForm, LoginForm, PerfilUsuarioForm, ServicioForm
from .models import Usuario, TipoUsuario, Reserva, DetalleReserva, Servicio, TipoServicio, EstadoReserva

# --- Funciones de Ayuda ---
def is_anfitrion(user):
    """Verifica si el usuario autenticado es un anfitrión."""
    return user.is_authenticated and user.is_anfitrion

def is_cliente(user):
    """Verifica si el usuario autenticado es un cliente."""
    return user.is_authenticated and user.is_cliente

def es_administrador_plataforma(user):
    return user.is_authenticated and user.is_administrador

# --- Vistas Públicas ---
def inicio(request):
    """Página de inicio pública."""
    return render(request, 'core/inicio.html')

def registro(request):
    """Vista para el registro de nuevos usuarios."""
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, '¡Su registro fue exitoso! Ahora puede iniciar sesión.')
            return redirect('login')
    else:
        form = RegistroClienteForm()
    return render(request, 'core/registro.html', {'form': form})

def login(request):
    """Vista para el inicio de sesión."""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            if user:
                auth_login(request, user)
                messages.success(request, f'¡Bienvenido de nuevo, {user.nombre} {user.apellido}!')
                return redirect('inicioregistrado')
            else:
                messages.error(request, 'Ocurrió un error inesperado al iniciar sesión.')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    """Vista para cerrar sesión."""
    auth_logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('inicio')

# --- Vistas para Usuarios Autenticados ---
@login_required(login_url='login')
def inicioregistrado(request):
    """Página de inicio para usuarios registrados."""
    return render(request, 'core/inicioregistrado.html')

@login_required(login_url='login')
def perfil(request):
    """Vista del perfil de usuario, incluyendo "Mis Reservas" para clientes."""
    usuario_actual = request.user
    form_submitted_with_errors = False

    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, instance=usuario_actual)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Tus datos han sido actualizados correctamente!')
            return redirect('perfil')
        else:
            messages.error(request, 'Hubo un error al actualizar tus datos. Por favor, revisa el formulario.')
            form_submitted_with_errors = True
    else:
        form = PerfilUsuarioForm(instance=usuario_actual)

    reservas_data = []
    if is_cliente(usuario_actual):
        reservas_usuario = Reserva.objects.filter(usuario=usuario_actual).order_by('-fecha_reserva')

        for reserva in reservas_usuario:
            servicios_reserva = DetalleReserva.objects.filter(reserva=reserva).select_related('servicio__tipo_servicio')

            nombres_servicios_list = []
            tipos_servicios_list = []
            for dr in servicios_reserva:
                nombres_servicios_list.append(dr.servicio.nombre)
                tipos_servicios_list.append(dr.servicio.tipo_servicio.nombre)

            nombres_servicios = ", ".join(sorted(list(set(nombres_servicios_list))))
            tipos_servicios = ", ".join(sorted(list(set(tipos_servicios_list))))

            reservas_data.append({
                'id': reserva.id,
                'tipo_servicio': tipos_servicios if tipos_servicios else 'N/A',
                'nombre_servicio': nombres_servicios if nombres_servicios else 'N/A',
                'fecha_inicio': reserva.fecha_inicio,
                'fecha_fin': reserva.fecha_fin,
                'estado_display': reserva.estado.estado if reserva.estado else 'Desconocido',
                'total': reserva.total,
            })

    context = {
        'form': form,
        'reservas': reservas_data,
        'form_submitted': form_submitted_with_errors,
        'user': usuario_actual,
    }
    return render(request, 'core/perfil.html', context)

# --- Vistas Específicas para Administrador ---

@login_required
@user_passes_test(es_administrador_plataforma, login_url='/acceso_denegado/')
def listar_servicios_administrador(request):
    servicios = Servicio.objects.all().order_by('nombre')

    form = ServicioForm()
    servicio_a_editar = None

    # Manejar POST para AGREGAR SERVICIO
    if request.method == 'POST' and 'action' in request.POST and request.POST['action'] == 'agregar':
        form = ServicioForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # Puedes añadir mensajes de éxito aquí
            return redirect('listar_servicios_administrador')

    # Manejar GET para entrar en modo MODIFICAR
    elif request.method == 'GET' and 'modificar_id' in request.GET:
        try:
            servicio_a_editar = get_object_or_404(Servicio, pk=request.GET['modificar_id'])
            form = ServicioForm(instance=servicio_a_editar)
        except Exception as e:
            print(f"Error al cargar servicio para modificar: {e}")
            return redirect('listar_servicios_administrador')

    # Manejar POST para GUARDAR CAMBIOS de MODIFICACIÓN
    elif request.method == 'POST' and 'action' in request.POST and request.POST['action'] == 'modificar':
        servicio_id = request.POST.get('servicio_id_modificar')
        servicio_instancia = get_object_or_404(Servicio, pk=servicio_id)
        form = ServicioForm(request.POST, request.FILES, instance=servicio_instancia)
        if form.is_valid():
            form.save()
            return redirect('listar_servicios_administrador')

    # Manejar POST para ELIMINAR SERVICIO
    elif request.method == 'POST' and 'eliminar_id' in request.POST:
        servicio_id = request.POST['eliminar_id']
        servicio_a_eliminar = get_object_or_404(Servicio, pk=servicio_id)
        servicio_a_eliminar.delete()
        return redirect('listar_servicios_administrador')

    context = {
        'servicios': servicios,
        'form': form,
        'servicio_a_editar': servicio_a_editar,
    }
    return render(request, 'core/listar_servicios_administrador.html', context)

# --- Vistas Específicas para Anfitriones ---

@login_required(login_url='login')
@user_passes_test(is_anfitrion, login_url='login')
def listar_reservas_anfitrion(request):
    """
    Permite al anfitrión listar, filtrar y gestionar (aceptar/rechazar) las reservas
    relacionadas con sus servicios, todo en la misma vista.
    """
    # Obtener todas las reservas relacionadas con los servicios del anfitrión logueado
    reservas_queryset = Reserva.objects.filter(
        detallereserva__servicio__anfitrion=request.user
    ).distinct().order_by('-fecha_reserva')

    # --- Lógica de Filtrado (GET request) ---
    search_tipo_servicio = request.GET.get('tipo_servicio', '').strip()
    search_cliente_correo = request.GET.get('cliente_correo', '').strip()
    search_estado = request.GET.get('estado', '').strip()

    if search_tipo_servicio:
        reservas_queryset = reservas_queryset.filter(
            detallereserva__servicio__tipo_servicio__nombre__icontains=search_tipo_servicio
        ).distinct()

    if search_cliente_correo:
        reservas_queryset = reservas_queryset.filter(
            usuario__correo__icontains=search_cliente_correo
        ).distinct()

    if search_estado:
        reservas_queryset = reservas_queryset.filter(
            estado__estado__icontains=search_estado
        ).distinct()

    # --- Lógica de Actualización de Estado (POST request) ---
    # ESTO VUELVE A ESTAR AQUÍ PARA GESTIONAR LAS ACCIONES EN LA MISMA PÁGINA
    if request.method == 'POST':
        reserva_id = request.POST.get('reserva_id')
        action = request.POST.get('action') # 'aceptar' o 'rechazar'

        reserva = get_object_or_404(Reserva, id=reserva_id)

        # Verificación de seguridad: Asegurarse de que la reserva pertenece
        # a uno de los servicios del anfitrión logueado.
        if not DetalleReserva.objects.filter(reserva=reserva, servicio__anfitrion=request.user).exists():
            messages.error(request, "No tienes permiso para modificar esta reserva.")
            # Redirigir manteniendo los filtros actuales
            query_params = request.GET.urlencode()
            redirect_url = f"{request.path}?{query_params}" if query_params else request.path
            return redirect(redirect_url)

        try:
            if action == 'aceptar':
                estado_aceptada, created = EstadoReserva.objects.get_or_create(estado='Aceptada')
                reserva.estado = estado_aceptada
                reserva.save()
                messages.success(request, f"¡Reserva #{reserva.id} aceptada con éxito!")
            elif action == 'rechazar':
                estado_rechazada, created = EstadoReserva.objects.get_or_create(estado='Rechazada')
                reserva.estado = estado_rechazada
                reserva.save()
                messages.info(request, f"Reserva #{reserva.id} rechazada.")
            else:
                messages.error(request, "Acción no válida.")
        except Exception as e:
            messages.error(request, f"Error al procesar la reserva: {e}")

        # Después de una actualización, redirigir manteniendo los filtros actuales
        query_params = request.GET.urlencode()
        redirect_url = f"{request.path}?{query_params}" if query_params else request.path
        return redirect(redirect_url)

    # Preparar los datos de las reservas para mostrarlos en la tabla
    reservas_data = []
    for reserva in reservas_queryset:
        servicios_reserva = DetalleReserva.objects.filter(reserva=reserva).select_related('servicio')

        nombres_servicios_list = []
        for dr in servicios_reserva:
            nombres_servicios_list.append(dr.servicio.nombre)

        nombres_servicios = ", ".join(sorted(list(set(nombres_servicios_list))))

        reservas_data.append({
            'id': reserva.id,
            'cliente_nombre': reserva.usuario.get_full_name(),
            'cliente_correo': reserva.usuario.correo,
            'nombre_servicio': nombres_servicios if nombres_servicios else 'N/A',
            'fecha_reserva': reserva.fecha_reserva,
            'fecha_inicio': reserva.fecha_inicio,
            'fecha_fin': reserva.fecha_fin,
            'estado_actual_id': reserva.estado.id if reserva.estado else None,
            'estado_actual_nombre': reserva.estado.estado if reserva.estado else 'Desconocido',
            'total': reserva.total,
        })

    # Obtener todos los posibles estados de reserva y tipos de servicio para los filtros
    estados_disponibles = EstadoReserva.objects.all()
    tipos_servicio_disponibles = TipoServicio.objects.all()

    context = {
        'reservas': reservas_data,
        'estados_disponibles': estados_disponibles,
        'tipos_servicio_disponibles': tipos_servicio_disponibles,
        'user': request.user,
        'search_tipo_servicio': search_tipo_servicio,
        'search_cliente_correo': search_cliente_correo,
        'search_estado': search_estado,
    }
    return render(request, 'core/listar_reservas_anfitrion.html', context)


# --- Vistas de Categorías de Servicios ---
def hospedaje(request):
    try:
        tipo_hospedaje = TipoServicio.objects.get(nombre='hospedaje')
        servicios_hospedaje = Servicio.objects.filter(tipo_servicio=tipo_hospedaje).order_by('nombre')
    except TipoServicio.DoesNotExist:
        servicios_hospedaje = []
        messages.warning(request, "No se ha configurado el tipo de servicio 'hospedaje' en el sistema.")

    context = {
        'servicios': servicios_hospedaje
    }
    return render(request, 'core/hospedaje.html', context)


def actividad(request):
    try:
        tipo_actividad = TipoServicio.objects.get(nombre='actividad') # O el nombre exacto de tu tipo de actividad
        servicios_actividad = Servicio.objects.filter(tipo_servicio=tipo_actividad).order_by('nombre')
    except TipoServicio.DoesNotExist:
        servicios_actividad = []
        messages.warning(request, "No se ha configurado el tipo de servicio 'actividad' en el sistema.")

    context = {
        'servicios': servicios_actividad
    }
    return render(request, 'core/actividad.html', context)


def gastronomia(request):
    try:
        tipo_gastronomia = TipoServicio.objects.get(nombre='gastronomia') # O el nombre exacto de tu tipo de gastronomía
        servicios_gastronomia = Servicio.objects.filter(tipo_servicio=tipo_gastronomia).order_by('nombre')
    except TipoServicio.DoesNotExist:
        servicios_gastronomia = []
        messages.warning(request, "No se ha configurado el tipo de servicio 'gastronomia' en el sistema.")

    context = {
        'servicios': servicios_gastronomia
    }
    return render(request, 'core/gastronomia.html', context)


def carrito(request):
    return render(request, 'core/carrito.html')

def detalle_hospedaje(request, servicio_id):
    servicio = get_object_or_404(Servicio, pk=servicio_id, tipo_servicio__nombre='hospedaje')
    context = {
        'servicio': servicio,
    }
    return render(request, 'core/detalle_hospedaje.html', context)

def detalle_actividad(request, servicio_id):
    servicio = get_object_or_404(Servicio, pk=servicio_id, tipo_servicio__nombre='actividad')
    context = {
        'servicio': servicio,
    }
    return render(request, 'core/detalle_actividad.html', context)

def detalle_gastronomia(request, servicio_id):
    servicio = get_object_or_404(Servicio, pk=servicio_id, tipo_servicio__nombre='gastronomia')
    context = {
        'servicio': servicio,
    }
    return render(request, 'core/detalle_gastronomia.html', context)

# --- Nueva Vista para obtener fechas ocupadas ---
def get_fechas_ocupadas_hospedaje(request, servicio_id):
    # Asegúrate de que el servicio es un hospedaje
    servicio = get_object_or_404(Servicio, pk=servicio_id, tipo_servicio__nombre='hospedaje')

    # Obtener el estado 'Aceptada' para filtrar solo reservas confirmadas
    try:
        estado_aceptada = EstadoReserva.objects.get(estado='Aceptada')
    except EstadoReserva.DoesNotExist:
        # Si no existe el estado 'Aceptada', no hay reservas confirmadas que considerar
        return JsonResponse({'fechas_ocupadas': []})

    # Buscar todas las reservas aceptadas para este hospedaje
    # Que se solapen con fechas futuras o actuales
    reservas_ocupadas = DetalleReserva.objects.filter(
        servicio=servicio,
        reserva__estado=estado_aceptada,
        reserva__fecha_fin__gte=date.today() # Solo reservas que aún no han terminado
    ).select_related('reserva').order_by('reserva__fecha_inicio')

    fechas_ocupadas_list = []
    for dr in reservas_ocupadas:
        fecha_inicio = dr.reserva.fecha_inicio
        fecha_fin = dr.reserva.fecha_fin

        # Generar todas las fechas entre fecha_inicio y fecha_fin (excluyendo fecha_fin)
        # Esto es crucial porque fecha_fin es la fecha de SALIDA, lo que significa que la noche anterior es la última noche ocupada.
        current_date = fecha_inicio
        while current_date < fecha_fin:
            fechas_ocupadas_list.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)

    # Eliminar duplicados y ordenar para asegurar un JSON limpio
    fechas_ocupadas_unicas = sorted(list(set(fechas_ocupadas_list)))

    return JsonResponse({'fechas_ocupadas': fechas_ocupadas_unicas})