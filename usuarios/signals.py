from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import PerfilUsuario, Departamento, Rol


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crea automáticamente un perfil para cada usuario nuevo"""
    if created:
        # Verificar si ya tiene perfil para evitar duplicados
        if not hasattr(instance, 'perfil'):
            try:
                # Obtener o crear un departamento predeterminado
                departamento, _ = Departamento.objects.get_or_create(
                    nombre="General",
                    defaults={
                        'descripcion': 'Departamento general para nuevos usuarios'
                    }
                )

                # Obtener o crear un rol predeterminado
                rol, _ = Rol.objects.get_or_create(
                    nombre="Usuario Regular",
                    defaults={
                        'descripcion': 'Usuario con permisos básicos'
                    }
                )

                # Crear el perfil con valores por defecto
                PerfilUsuario.objects.create(
                    usuario=instance,
                    departamento=departamento,
                    rol=rol
                )

                print(
                    f"Perfil creado automáticamente para {instance.username}")

            except Exception as e:
                print(
                    f"Error creando perfil automático para {instance.username}: {str(e)}")
        else:
            print(f"El usuario {instance.username} ya tiene perfil")
    else:
        print(f"Usuario {instance.username} actualizado (no creado)")
