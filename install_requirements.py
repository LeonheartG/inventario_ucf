#!/usr/bin/env python3
"""
Script para instalar automáticamente las dependencias de un proyecto Django
"""

import os
import sys
import subprocess
import platform


def print_step(message):
    """Imprime un mensaje de paso con formato"""
    print(f"\n{'='*60}")
    print(f"{message}")
    print(f"{'='*60}")


def check_python_version():
    """Verifica que la versión de Python sea compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("ERROR: Se requiere Python 3.8 o superior")
        print(f"Versión actual: {platform.python_version()}")
        sys.exit(1)
    print(f"Python {platform.python_version()} detectado")


def check_requirements_file():
    """Verifica que existe el archivo requirements.txt"""
    if not os.path.exists('requirements.txt'):
        print("ERROR: No se encontró el archivo requirements.txt")
        print("Asegúrate de ejecutar este script desde la raíz de tu proyecto Django")
        sys.exit(1)
    print("Archivo requirements.txt encontrado")


def upgrade_pip():
    """Actualiza pip a la última versión"""
    try:
        print("Actualizando pip...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
                       check=True, capture_output=True)
        print("pip actualizado correctamente")
    except subprocess.CalledProcessError as e:
        print(f"Advertencia: No se pudo actualizar pip: {e}")


def install_requirements():
    """Instala las dependencias del requirements.txt"""
    try:
        print("Instalando dependencias...")

        # Comando para instalar dependencias
        cmd = [sys.executable, '-m', 'pip',
               'install', '-r', 'requirements.txt']

        # Ejecutar con output en tiempo real
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True, bufsize=1)

        for line in process.stdout:
            print(line.strip())

        process.wait()

        if process.returncode == 0:
            print("Todas las dependencias se instalaron correctamente")
        else:
            print("ERROR: Error durante la instalación de dependencias")
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Error al instalar dependencias: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nERROR: Instalación cancelada por el usuario")
        sys.exit(1)


def check_django_installation():
    """Verifica que Django se haya instalado correctamente"""
    try:
        import django
        print(f"Django {django.get_version()} instalado correctamente")
    except ImportError:
        print("ADVERTENCIA: Django no parece estar instalado correctamente")


def show_next_steps():
    """Muestra los siguientes pasos recomendados"""
    print_step("INSTALACIÓN COMPLETADA")
    print("Las dependencias se han instalado correctamente!")
    print("\nPróximos pasos recomendados:")
    print("   1. Ejecuta las migraciones: python manage.py migrate")
    print("   2. Crea un superusuario: python manage.py createsuperuser")
    print("   3. Inicia el servidor: python manage.py runserver")
    print("\nTip: Asegúrate de tener configurada tu base de datos en settings.py")


def create_virtual_env_suggestion():
    """Sugiere crear un entorno virtual si no se está usando uno"""
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("\nRECOMENDACIÓN: No pareces estar usando un entorno virtual")
        print("   Para crear uno ejecuta:")
        print("   python -m venv venv")
        print("   # En Windows: venv\\Scripts\\activate")
        print("   # En Linux/Mac: source venv/bin/activate")
        print("\n¿Quieres continuar sin entorno virtual? (y/n): ", end="")

        response = input().lower().strip()
        if response not in ['y', 'yes', 'sí', 'si']:
            print("ERROR: Instalación cancelada. Crea un entorno virtual primero.")
            sys.exit(1)


def main():
    """Función principal del script"""
    print_step("INICIANDO INSTALACIÓN DE DEPENDENCIAS DJANGO")

    try:
        # Verificaciones previas
        check_python_version()
        check_requirements_file()
        create_virtual_env_suggestion()

        # Proceso de instalación
        upgrade_pip()
        install_requirements()
        check_django_installation()

        # Finalización
        show_next_steps()

    except KeyboardInterrupt:
        print("\nERROR: Instalación interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
