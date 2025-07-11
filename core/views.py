from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from decimal import Decimal
from django.utils import timezone
import json
from datetime import date, timedelta
from .forms import RegistroClienteForm, LoginForm, PerfilUsuarioForm, ServicioForm
from .models import Usuario, TipoUsuario, Reserva, DetalleReserva, Servicio, TipoServicio, EstadoReserva, EstadoPago, MetodoPago, Pago

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
    reservas_queryset = Reserva.objects.filter(
        detallereserva__servicio__anfitrion=request.user
    ).distinct().order_by('-fecha_reserva')

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

    if request.method == 'POST':
        reserva_id = request.POST.get('reserva_id')
        action = request.POST.get('action') # 'aceptar' o 'rechazar'

        reserva = get_object_or_404(Reserva, id=reserva_id)

        if not DetalleReserva.objects.filter(reserva=reserva, servicio__anfitrion=request.user).exists():
            messages.error(request, "No tienes permiso para modificar esta reserva.")
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

        query_params = request.GET.urlencode()
        redirect_url = f"{request.path}?{query_params}" if query_params else request.path
        return redirect(redirect_url)

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


# --- API: Fechas ocupadas por hospedaje ---
def api_hospedaje_fechas_ocupadas(request, servicio_id):
    servicio = get_object_or_404(Servicio, pk=servicio_id, tipo_servicio__nombre='hospedaje')

    try:
        estados_ocupados = EstadoReserva.objects.filter(estado__in=['Aceptada', 'Confirmada'])
    except EstadoReserva.DoesNotExist:
        return JsonResponse({'fechas_ocupadas': []})

    reservas_ocupadas = DetalleReserva.objects.filter(
        servicio=servicio,
        reserva__estado__in=estados_ocupados,
        reserva__fecha_fin__gte=date.today()
    ).select_related('reserva')

    fechas_ocupadas = set()
    for dr in reservas_ocupadas:
        inicio = dr.reserva.fecha_inicio
        fin = dr.reserva.fecha_fin
        while inicio < fin:
            fechas_ocupadas.add(inicio.strftime('%Y-%m-%d'))
            inicio += timedelta(days=1)

    return JsonResponse({'fechas_ocupadas': sorted(fechas_ocupadas)})


# === INICIO DE LA SECCIÓN CORREGIDA ===
def api_singleday_fechas_ocupadas(request, servicio_id):
    """
    Devuelve un JSON con las fechas ocupadas para servicios de un solo día
    (actividad, gastronomia) SOLAMENTE para el usuario actual.
    """
    # Si el usuario no está autenticado, no tiene reservas, por lo que no se bloquea nada.
    if not request.user.is_authenticated:
        return JsonResponse({'fechas_ocupadas': []})
    
    servicio = get_object_or_404(Servicio, pk=servicio_id)
    
    # Se consideran todos los estados para evitar que un usuario reserve dos veces
    # mientras una reserva anterior está pendiente o ya fue aceptada.
    try:
        estados_validos = EstadoReserva.objects.filter(estado__in=['Aceptada', 'Confirmada', 'Pendiente'])
    except EstadoReserva.DoesNotExist:
        return JsonResponse({'fechas_ocupadas': []})

    # Filtrar las reservas por el servicio Y por el usuario que hace la solicitud.
    # El campo en el modelo Reserva es 'usuario'.
    reservas_del_usuario = DetalleReserva.objects.filter(
        servicio=servicio,
        reserva__usuario=request.user,  # <-- CORRECCIÓN APLICADA AQUÍ
        reserva__estado__in=estados_validos,
        reserva__fecha_inicio__gte=date.today()
    ).select_related('reserva')

    # Extraer las fechas de inicio de las reservas encontradas.
    fechas_ocupadas_por_usuario = sorted(list(set([dr.reserva.fecha_inicio.strftime('%Y-%m-%d') for dr in reservas_del_usuario])))

    return JsonResponse({'fechas_ocupadas': fechas_ocupadas_por_usuario})

@login_required(login_url='login')
def vista_pago(request):
    """
    Muestra la página de pago y le pasa el nombre completo del
    usuario para rellenar automáticamente el campo del titular.
    """
    # Obtenemos el nombre completo del usuario que ha iniciado sesión
    nombre_usuario = request.user.get_full_name()

    # Creamos un 'contexto' para enviar esa información a la plantilla
    context = {
        'nombre_completo_usuario': nombre_usuario
    }
    
    # Renderizamos la plantilla, pero ahora con el contexto que incluye el nombre
    return render(request, 'core/pago.html', context)

@login_required(login_url='login')
@require_POST # Solo permite que esta vista sea llamada con el método POST
def procesar_pago(request):
    """
    Procesa el formulario de pago simulado, guarda los datos en la BDD
    y redirige al perfil del usuario.
    """
    try:
        # Obtiene los datos del campo oculto del formulario
        cart_items_str = request.POST.get('cart_items')
        metodo_pago_nombre = request.POST.get('metodo_pago')

        if not cart_items_str or cart_items_str == '[]':
            messages.error(request, 'El carrito está vacío.')
            return redirect('carrito')

        cart_items = json.loads(cart_items_str)

        # Prepara los objetos de estado que usaremos
        estado_confirmada, _ = EstadoReserva.objects.get_or_create(estado='Confirmada')
        metodo_pago_obj, _ = MetodoPago.objects.get_or_create(nombre=metodo_pago_nombre)
        estado_pago_aprobado, _ = EstadoPago.objects.get_or_create(estado='Aprobado')

        # Recorre cada ítem del carrito
        for item_data in cart_items:
            servicio = get_object_or_404(Servicio, pk=item_data.get('id'))
            subtotal = Decimal(item_data.get('subtotal'))
            iva = subtotal * Decimal('0.19')
            total_con_iva = subtotal + iva

            fechas = item_data.get('fechas', [])
            fecha_inicio = date.fromisoformat(fechas[0])
            fecha_fin = date.fromisoformat(fechas[-1])

            # 1. Crea la Reserva
            reserva = Reserva.objects.create(
                usuario=request.user,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estado=estado_confirmada,
                total=total_con_iva
            )

            # 2. Crea el Detalle de la Reserva
            DetalleReserva.objects.create(
                reserva=reserva,
                servicio=servicio,
                cantidad_dia=item_data.get('noches', 1),
                num_persona=item_data.get('cantidadPersonas', 1),
                subtotal=subtotal
            )
            
            # 3. Crea el Pago (¡LA PARTE CLAVE!)
            Pago.objects.create(
                reserva=reserva,
                metodo_pago=metodo_pago_obj,
                estado_pago=estado_pago_aprobado,
                monto=total_con_iva,
                transaccion=f'SIM-{reserva.id}-{timezone.now().timestamp()}' # ID de transacción simulado
            )

        messages.success(request, '¡Tu pago ha sido procesado y tus reservas han sido confirmadas!')
        request.session['pago_exitoso'] = True # Para limpiar el carrito en la siguiente página
        return redirect('perfil')

    except Exception as e:
        print(f"Error en procesar_pago: {e}") # Para que veas el error en la consola
        messages.error(request, f'Hubo un problema inesperado al procesar tu pago.')
        return redirect('carrito')