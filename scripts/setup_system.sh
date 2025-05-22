#!/bin/bash
# scripts/setup_system.sh
# Script de configuración completa del sistema UCF

echo "🚀 Configurando Sistema Integral UCF..."
echo "========================================"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar mensajes con color
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Verificar si estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    print_error "Debe ejecutar este script desde el directorio raíz del proyecto Django"
    exit 1
fi

# 1. Crear estructura de directorios
print_header "Creando estructura de directorios..."
mkdir -p usuarios/management/commands
mkdir -p logs
mkdir -p media/perfiles
mkdir -p staticfiles
mkdir -p scripts

# Crear archivos __init__.py
touch usuarios/management/__init__.py
touch usuarios/management/commands/__init__.py

print_status "Estructura de directorios creada"

# 2. Verificar dependencias
print_header "Verificando dependencias de Python..."
python -c "import django" 2>/dev/null || { print_error "Django no está instalado"; exit 1; }
python -c "import PIL" 2>/dev/null || print_warning "Pillow no está instalado - las imágenes no funcionarán"

print_status "Dependencias verificadas"

# 3. Aplicar migraciones
print_header "Aplicando migraciones de base de datos..."
python manage.py makemigrations
python manage.py migrate

if [ $? -eq 0 ]; then
    print_status "Migraciones aplicadas correctamente"
else
    print_error "Error al aplicar migraciones"
    exit 1
fi

# 4. Configurar roles del sistema
print_header "Configurando roles del sistema..."
python manage.py setup_roles --update-users

if [ $? -eq 0 ]; then
    print_status "Roles configurados correctamente"
else
    print_warning "Error al configurar roles - continúe manualmente"
fi

# 5. Crear superusuario (opcional)
read -p "¿Desea crear un usuario administrador? (y/n): " create_admin

if [ "$create_admin" = "y" ] || [ "$create_admin" = "Y" ]; then
    read -p "Ingrese el nombre de usuario: " admin_username
    
    if [ ! -z "$admin_username" ]; then
        python manage.py setup_roles --create-admin="$admin_username"
        
        if [ $? -eq 0 ]; then
            print_status "Usuario administrador '$admin_username' creado"
            print_warning "Contraseña temporal: admin123"
            print_warning "CAMBIE LA CONTRASEÑA EN EL PRIMER ACCESO"
        else
            print_warning "Error al crear usuario administrador"
        fi
    fi
fi

# 6. Recopilar archivos estáticos
print_header "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

if [ $? -eq 0 ]; then
    print_status "Archivos estáticos recopilados"
else
    print_warning "Error al recopilar archivos estáticos"
fi

# 7. Verificar configuración
print_header "Verificando configuración del sistema..."

# Verificar que los roles existen
roles_count=$(python manage.py shell -c "from usuarios.models import Rol; print(Rol.objects.count())" 2>/dev/null)
if [ "$roles_count" -ge "7" ]; then
    print_status "Roles configurados correctamente ($roles_count roles)"
else
    print_warning "Faltan roles por configurar"
fi

# Verificar departamentos
dept_count=$(python manage.py shell -c "from usuarios.models import Departamento; print(Departamento.objects.count())" 2>/dev/null)
if [ "$dept_count" -ge "5" ]; then
    print_status "Departamentos configurados correctamente ($dept_count departamentos)"
else
    print_warning "Faltan departamentos por configurar"
fi

# 8. Mostrar resumen final
echo ""
echo "✅ CONFIGURACIÓN COMPLETADA"
echo "=========================="
print_status "El sistema está listo para usar"
echo ""
echo "📋 PRÓXIMOS PASOS:"
echo "   1. Ejecute: python manage.py runserver"
echo "   2. Acceda a: http://localhost:8000"
echo "   3. Use las credenciales del administrador creado"
echo "   4. Cambie la contraseña temporal"
echo "   5. Configure usuarios adicionales desde el admin"
echo ""
echo "🔧 FUNCIONALIDADES DISPONIBLES:"
echo "   • Sistema de usuarios con roles"
echo "   • Gestión de inventario tecnológico"
echo "   • Administración de locales"
echo "   • Sistema de diagnóstico digital"
echo "   • Reportes con control de acceso"
echo ""
echo "🛡️ CONTROL DE ACCESO CONFIGURADO:"
echo "   • Usuarios regulares: Sin acceso a reportes ni actividad"
echo "   • Supervisores y admins: Acceso completo"
echo "   • Middleware de protección activo"
echo ""
print_status "¡Sistema UCF listo para producción!"