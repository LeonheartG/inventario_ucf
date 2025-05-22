# usuarios/management/commands/setup_roles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from usuarios.models import Rol, Departamento, PerfilUsuario


class Command(BaseCommand):
    help = 'Configura los roles iniciales del sistema y actualiza perfiles existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-users',
            action='store_true',
            help='Actualizar usuarios existentes sin rol asignado',
        )

        parser.add_argument(
            '--create-admin',
            type=str,
            help='Crear usuario administrador con username especificado',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Configurando sistema de roles UCF...\n')
        )

        # Configurar roles
        self.setup_roles()

        # Configurar departamentos básicos
        self.setup_departamentos()

        # Actualizar usuarios existentes si se solicita
        if options['update_users']:
            self.update_existing_users()

        # Crear administrador si se solicita
        if options['create_admin']:
            self.create_admin_user(options['create_admin'])

        self.stdout.write(
            self.style.SUCCESS('\n✅ Configuración completada exitosamente!')
        )

    def setup_roles(self):
        """Configurar roles del sistema"""
        self.stdout.write('📋 Configurando roles del sistema...')

        roles_data = [
            {
                'nombre': 'Superadministrador',
                'descripcion': 'Acceso completo a todo el sistema, incluyendo configuración y administración de usuarios.',
                'permisos': 'ALL'
            },
            {
                'nombre': 'Administrador',
                'descripcion': 'Acceso completo a inventario, reportes y gestión de departamento.',
                'permisos': 'INVENTARIO,REPORTES,USUARIOS,LOCALES,DIAGNOSTICO'
            },
            {
                'nombre': 'Supervisor',
                'descripcion': 'Acceso a reportes, visualización completa de inventario y diagnósticos.',
                'permisos': 'INVENTARIO_READ,REPORTES,LOCALES_READ,DIAGNOSTICO'
            },
            {
                'nombre': 'Coordinador',
                'descripcion': 'Acceso a gestión de su departamento y reportes básicos.',
                'permisos': 'INVENTARIO_DEPT,REPORTES_BASIC,LOCALES_DEPT,DIAGNOSTICO_DEPT'
            },
            {
                'nombre': 'Técnico',
                'descripcion': 'Acceso a gestión de inventario y mantenimientos.',
                'permisos': 'INVENTARIO,MANTENIMIENTO,LOCALES_READ'
            },
            {
                'nombre': 'Analista',
                'descripcion': 'Acceso a reportes y análisis de datos.',
                'permisos': 'REPORTES,INVENTARIO_READ,DIAGNOSTICO_READ'
            },
            {
                'nombre': 'Usuario Regular',
                'descripcion': 'Acceso básico de consulta a inventario y diagnósticos.',
                'permisos': 'INVENTARIO_READ,DIAGNOSTICO_BASIC'
            },
        ]

        created_count = 0
        updated_count = 0

        for rol_data in roles_data:
            rol, created = Rol.objects.get_or_create(
                nombre=rol_data['nombre'],
                defaults={
                    'descripcion': rol_data['descripcion'],
                    'permisos': rol_data['permisos']
                }
            )

            if created:
                created_count += 1
                self.stdout.write(f'   ✓ Rol creado: {rol.nombre}')
            else:
                # Actualizar descripción y permisos si el rol ya existe
                rol.descripcion = rol_data['descripcion']
                rol.permisos = rol_data['permisos']
                rol.save()
                updated_count += 1
                self.stdout.write(f'   ↻ Rol actualizado: {rol.nombre}')

        self.stdout.write(
            f'\n📊 Resumen de roles: {created_count} creados, {updated_count} actualizados'
        )

    def setup_departamentos(self):
        """Configurar departamentos básicos"""
        self.stdout.write('\n🏢 Configurando departamentos básicos...')

        departamentos_data = [
            {
                'nombre': 'General',
                'descripcion': 'Departamento general para usuarios sin asignación específica',
                'ubicacion': 'Campus Principal'
            },
            {
                'nombre': 'Tecnologías de la Información',
                'descripcion': 'Departamento de TI y soporte técnico',
                'ubicacion': 'Edificio Administrativo'
            },
            {
                'nombre': 'Administración',
                'descripcion': 'Departamento administrativo y financiero',
                'ubicacion': 'Edificio Administrativo'
            },
            {
                'nombre': 'Ingeniería',
                'descripcion': 'Facultad de Ingeniería',
                'ubicacion': 'Edificio de Ingeniería'
            },
            {
                'nombre': 'Ciencias Económicas',
                'descripcion': 'Facultad de Ciencias Económicas',
                'ubicacion': 'Edificio de Economía'
            },
        ]

        created_count = 0

        for dept_data in departamentos_data:
            dept, created = Departamento.objects.get_or_create(
                nombre=dept_data['nombre'],
                defaults={
                    'descripcion': dept_data['descripcion'],
                    'ubicacion': dept_data['ubicacion']
                }
            )

            if created:
                created_count += 1
                self.stdout.write(f'   ✓ Departamento creado: {dept.nombre}')

        if created_count > 0:
            self.stdout.write(f'📊 {created_count} departamentos creados')
        else:
            self.stdout.write('📊 Departamentos ya existían')

    def update_existing_users(self):
        """Actualizar usuarios existentes sin rol"""
        self.stdout.write('\n👥 Actualizando usuarios existentes...')

        # Obtener rol por defecto
        rol_regular = Rol.objects.get(nombre='Usuario Regular')
        rol_admin = Rol.objects.get(nombre='Administrador')
        departamento_general = Departamento.objects.get(nombre='General')

        updated_count = 0

        # Usuarios sin perfil
        users_without_profile = User.objects.filter(perfil__isnull=True)

        for user in users_without_profile:
            # Asignar rol según si es superusuario
            rol = rol_admin if user.is_superuser else rol_regular

            PerfilUsuario.objects.create(
                usuario=user,
                departamento=departamento_general,
                rol=rol
            )

            updated_count += 1
            self.stdout.write(
                f'   ✓ Perfil creado para: {user.username} ({rol.nombre})')

        # Usuarios con perfil pero sin rol
        users_without_role = User.objects.filter(
            perfil__isnull=False,
            perfil__rol__isnull=True
        )

        for user in users_without_role:
            rol = rol_admin if user.is_superuser else rol_regular
            user.perfil.rol = rol
            user.perfil.save()

            updated_count += 1
            self.stdout.write(
                f'   ↻ Rol asignado a: {user.username} ({rol.nombre})')

        self.stdout.write(f'📊 {updated_count} usuarios actualizados')

    def create_admin_user(self, username):
        """Crear usuario administrador"""
        self.stdout.write(f'\n👤 Creando usuario administrador: {username}...')

        try:
            # Verificar si el usuario ya existe
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'El usuario {username} ya existe')
                )
                return

            # Crear usuario
            user = User.objects.create_user(
                username=username,
                email=f'{username}@ucf.edu.cu',
                password='admin123',  # Cambiar en primera sesión
                first_name='Administrador',
                last_name='del Sistema',
                is_staff=True,
                is_superuser=True
            )

            # Asignar perfil de administrador
            rol_admin = Rol.objects.get(nombre='Administrador')
            dept_ti = Departamento.objects.get(
                nombre='Tecnologías de la Información')

            PerfilUsuario.objects.create(
                usuario=user,
                departamento=dept_ti,
                rol=rol_admin
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Usuario administrador creado: {username}\n'
                    f'  📧 Email: {user.email}\n'
                    f'  🔑 Contraseña temporal: admin123\n'
                    f'  ⚠️  IMPORTANTE: Cambiar contraseña en el primer acceso'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error creando usuario administrador: {str(e)}')
            )

    def show_summary(self):
        """Mostrar resumen final"""
        self.stdout.write('\n📋 Resumen del sistema:')

        # Contar roles
        total_roles = Rol.objects.count()
        self.stdout.write(f'   • Roles configurados: {total_roles}')

        # Contar departamentos
        total_departamentos = Departamento.objects.count()
        self.stdout.write(f'   • Departamentos: {total_departamentos}')

        # Contar usuarios por rol
        for rol in Rol.objects.all():
            count = PerfilUsuario.objects.filter(rol=rol).count()
            self.stdout.write(f'   • {rol.nombre}: {count} usuarios')

        # Usuarios sin perfil
        sin_perfil = User.objects.filter(perfil__isnull=True).count()
        if sin_perfil > 0:
            self.stdout.write(
                self.style.WARNING(f'   ⚠️  Usuarios sin perfil: {sin_perfil}')
            )
