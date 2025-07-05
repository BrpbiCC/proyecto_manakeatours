from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django import forms

# Formularios personalizados
class UsuarioAdminCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ('correo', 'nombre', 'apellido', 'telefono', 'tipo_usuario')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password1"])
        if commit:
            usuario.save()
        return usuario

class UsuarioAdminChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = Usuario
        fields = ('correo', 'nombre', 'apellido', 'telefono', 'tipo_usuario', 'password', 'is_active', 'is_staff', 'is_superuser')

    def clean_password(self):
        return self.initial["password"]

# Clase admin personalizada
class UsuarioAdmin(BaseUserAdmin):
    form = UsuarioAdminChangeForm
    add_form = UsuarioAdminCreationForm

    list_display = ('correo', 'nombre', 'apellido', 'tipo_usuario', 'is_staff', 'is_superuser')
    list_filter = ('tipo_usuario', 'is_staff', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('correo', 'password')}),
        ('Información personal', {'fields': ('nombre', 'apellido', 'telefono', 'tipo_usuario')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('correo', 'nombre', 'apellido', 'telefono', 'tipo_usuario', 'password1', 'password2'),
        }),
    )
    search_fields = ('correo', 'nombre', 'apellido')
    ordering = ('correo',)
    filter_horizontal = ('groups', 'user_permissions')

admin.site.register(TipoUsuario)
admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(TipoServicio)
admin.site.register(Servicio)
admin.site.register(EstadoReserva)
admin.site.register(Reserva)
admin.site.register(DetalleReserva)
admin.site.register(Carrito)
admin.site.register(DetalleCarrito)
admin.site.register(MetodoPago)
admin.site.register(EstadoPago)
admin.site.register(Pago)