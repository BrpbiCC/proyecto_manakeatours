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

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from datetime import timedelta, date
from .models import Servicio, DetalleReserva, EstadoReserva

# --- API: Fechas ocupadas por hospedaje ---
def api_hospedaje_fechas_ocupadas(request, servicio_id):
    """
    Devuelve un JSON con las fechas ocupadas para un servicio de tipo 'hospedaje'.
    Se utiliza para deshabilitar fechas en el selector del frontend.
    """
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

def api_singleday_fechas_ocupadas(request, servicio_id):
    """
    Devuelve un JSON con las fechas ocupadas para servicios de un solo día 
    (actividad, gastronomia). Se utiliza para deshabilitar fechas en el frontend.
    """
    servicio = get_object_or_404(Servicio, pk=servicio_id)
    
    # Solo consideramos reservas que están confirmadas o aceptadas.
    try:
        estados_ocupados = EstadoReserva.objects.filter(estado__in=['Aceptada', 'Confirmada'])
    except EstadoReserva.DoesNotExist:
        return JsonResponse({'fechas_ocupadas': []})

    # Buscamos todas las reservas para este servicio que estén en los estados de ocupado
    # y que sean para hoy o una fecha futura.
    reservas_ocupadas = DetalleReserva.objects.filter(
        servicio=servicio,
        reserva__estado__in=estados_ocupados,
        reserva__fecha_inicio__gte=date.today()
    ).select_related('reserva')

    # Extraemos las fechas de inicio de esas reservas. Usamos un 'set' para evitar duplicados.
    fechas_ocupadas = sorted(list(set([dr.reserva.fecha_inicio.strftime('%Y-%m-%d') for dr in reservas_ocupadas])))

    return JsonResponse({'fechas_ocupadas': fechas_ocupadas})



# Nueva vista para procesar el pago y guardar las reservas
@login_required(login_url='login')
@require_POST # Asegura que solo se acepte peticiones POST
def procesar_pago(request):
    if not request.user.is_cliente:
        return JsonResponse({'success': False, 'message': 'Solo los clientes pueden realizar reservas.'}, status=403)

    try:
        data = json.loads(request.body)
        cart_items = data.get('cartItems', [])
        
        if not cart_items:
            return JsonResponse({'success': False, 'message': 'El carrito está vacío.'}, status=400)

        # Obtener estados de reserva
        estado_pendiente, created = EstadoReserva.objects.get_or_create(estado='Pendiente')
        # Si tienes un estado "Aceptada" para reservas ya confirmadas, puedes usarlo aquí después del pago
        # estado_confirmada, created = EstadoReserva.objects.get_or_create(estado='Confirmada')

        reservas_creadas = []
        total_acumulado_carrito = Decimal('0.00')

        for item_data in cart_items:
            try:
                servicio_id = item_data.get('id')
                # nombre_servicio = item_data.get('nombre') # No lo necesitamos, lo obtenemos del modelo
                tipo_servicio_str = item_data.get('tipoServicio')
                fechas = item_data.get('fechas', [])
                noches = item_data.get('noches', 0) # Solo para hospedaje
                cantidad_personas = item_data.get('cantidadPersonas', 1) # Solo para actividad/gastronomía
                subtotal_item = Decimal(str(item_data.get('subtotal', 0.00)))

                servicio = get_object_or_404(Servicio, pk=servicio_id)

                # Calcular el IVA para cada ítem (19%)
                iva_item = subtotal_item * Decimal('0.19')
                total_item = subtotal_item + iva_item

                # Determinar fechas de inicio y fin para la Reserva principal
                fecha_inicio_reserva = None
                fecha_fin_reserva = None

                if tipo_servicio_str == 'Hospedaje' and len(fechas) == 2:
                    # Validar fechas: que no sean fechas ocupadas y que la fecha de fin sea posterior a la de inicio
                    f_inicio_str = fechas[0]
                    f_fin_str = fechas[1]
                    fecha_inicio_reserva = date.fromisoformat(f_inicio_str)
                    fecha_fin_reserva = date.fromisoformat(f_fin_str)
                    
                    if fecha_fin_reserva <= fecha_inicio_reserva:
                        raise ValueError(f"La fecha de fin para {servicio.nombre} debe ser posterior a la fecha de inicio.")

                    # Aquí podrías añadir una validación más robusta para fechas ya ocupadas
                    # Pero el frontend ya debería haberlo evitado, esto es un doble chequeo
                    # if servicio.tipo_servicio.nombre.lower() == 'hospedaje':
                    #     # Re-verificar disponibilidad en el backend si es crítico
                    #     pass # Lógica de verificación de disponibilidad de fechas si es necesaria
                        
                    # En hospedaje, cantidad_dia será las noches
                    cantidad_dias_detalle = noches 
                    num_personas_detalle = 1 # Para hospedaje, num_persona suele ser 1 (la reserva es de la unidad de hospedaje)

                elif (tipo_servicio_str == 'Actividad' or tipo_servicio_str == 'Gastronomia') and len(fechas) == 1:
                    fecha_unica_str = fechas[0]
                    fecha_inicio_reserva = date.fromisoformat(fecha_unica_str)
                    fecha_fin_reserva = fecha_inicio_reserva # Para servicios de un día, fin = inicio
                    
                    cantidad_dias_detalle = 1 # Es un servicio de un día
                    num_personas_detalle = cantidad_personas

                else:
                    raise ValueError(f"Fechas inválidas para el servicio {servicio.nombre} de tipo {tipo_servicio_str}.")
                
                # Crear la Reserva
                reserva = Reserva.objects.create(
                    usuario=request.user,
                    fecha_reserva=timezone.now(),
                    fecha_inicio=fecha_inicio_reserva,
                    fecha_fin=fecha_fin_reserva,
                    estado=estado_pendiente, # Estado inicial 'Pendiente'
                    total=total_item # El total de esta reserva específica (subtotal + IVA del ítem)
                )

                # Crear el DetalleReserva asociado
                detalle_reserva = DetalleReserva.objects.create(
                    reserva=reserva,
                    servicio=servicio,
                    cantidad_dia=cantidad_dias_detalle,
                    num_persona=num_personas_detalle,
                    subtotal=subtotal_item # El subtotal del ítem, sin IVA
                )
                reservas_creadas.append(reserva.id)
                total_acumulado_carrito += total_item

            except Servicio.DoesNotExist:
                return JsonResponse({'success': False, 'message': f'Servicio con ID {item_data.get("id")} no encontrado.'}, status=404)
            except ValueError as ve:
                return JsonResponse({'success': False, 'message': str(ve)}, status=400)
            except Exception as e:
                # Si algo falla en la creación de una reserva, se registra el error
                # y se podría revertir la transacción si se usara una transacción atómica
                print(f"Error al procesar ítem del carrito: {e}")
                return JsonResponse({'success': False, 'message': f'Error interno al procesar el ítem: {e}'}, status=500)

        # Si todo fue exitoso, limpiar el carrito y devolver éxito
        # Nota: Aquí no se hace la "simulación de pago" real, solo el guardado
        # Una simulación real implicaría un POST a una pasarela de pago o similar.
        # Para la simulación, podemos considerar que al llegar aquí, el pago "se hizo".

        # Opcional: Actualizar el estado de las reservas a 'Confirmada' después de la "simulación de pago"
        estado_confirmada, created = EstadoReserva.objects.get_or_create(estado='Confirmada')
        for reserva_id in reservas_creadas:
            Reserva.objects.filter(id=reserva_id).update(estado=estado_confirmada)
        
        return JsonResponse({
            'success': True, 
            'message': 'Reservas procesadas y guardadas con éxito. Redirigiendo a tu perfil...',
            'total_pedido': float(total_acumulado_carrito) # Para información al frontend
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Petición JSON inválida.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error inesperado del servidor: {e}'}, status=500)