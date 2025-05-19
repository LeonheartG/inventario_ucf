from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import PerfilUsuario, Departamento, Rol


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crea automáticamente un perfil para cada usuario nuevo"""
    if created:
        # Verificar si ya tiene perfil
        if not hasattr(instance, 'perfil'):
            # Obtener o crear un departamento predeterminado
            departamento, _ = Departamento.objects.get_or_create(
                nombre="General",
                defaults={
                    'descripcion': 'Departamento general para nuevos usuarios'}
            )

            # Obtener o crear un rol predeterminado
            rol, _ = Rol.objects.get_or_create(
                nombre="Usuario Regular",
                defaults={'descripcion': 'Usuario con permisos básicos'}
            )

            # Crear el perfil
            PerfilUsuario.objects.create(
                usuario=instance,
                departamento=departamento,
                rol=rol
            )
