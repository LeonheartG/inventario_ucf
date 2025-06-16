#!/usr/bin/env python3
"""
Script para ejecutar todas las pruebas del Sistema UCF
Basado en las especificaciones del documento de Yaidelín Chaviano

Estrategia de pruebas implementada:
- Pruebas unitarias (módulo inventario)
- Pruebas de integración (módulo usuarios)
- Pruebas de aceptación (módulo diagnóstico)

Uso:
    python ejecutar_pruebas_ucf.py [opciones]
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
from django.core.management import execute_from_command_line
import time
import subprocess
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr


class TestRunner:
    """
    Ejecutor de pruebas del Sistema UCF
    Implementa la estrategia de pruebas del documento de Yaidelín Chaviano
    """

    def __init__(self):
        self.setup_project_paths()
        self.setup_django()
        self.resultados = {
            'unitarias': {'total': 0, 'exitosas': 0, 'fallidas': 0, 'tiempo': 0},
            'integracion': {'total': 0, 'exitosas': 0, 'fallidas': 0, 'tiempo': 0},
            'aceptacion': {'total': 0, 'exitosas': 0, 'fallidas': 0, 'tiempo': 0}
        }

    def setup_project_paths(self):
        """Configurar paths del proyecto para ejecución sin entorno virtual"""
        # Obtener directorio actual (raíz del proyecto)
        project_root = os.path.dirname(os.path.abspath(__file__))

        # Agregar raíz del proyecto al Python path si no está
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        # Cambiar al directorio del proyecto
        os.chdir(project_root)

        print(f"📁 Directorio de trabajo: {project_root}")

    def setup_django(self):
        """Configurar entorno Django para las pruebas"""
        try:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                                  'inventario_ucf.settings')
            django.setup()
        except Exception as e:
            print(f"❌ Error configurando Django: {e}")
            print(
                "   Verifica que el archivo settings.py esté en inventario_ucf/settings.py")
            sys.exit(1)

    def print_header(self, titulo):
        """Imprimir encabezado de sección"""
        print("\n" + "="*80)
        print(f"   {titulo}")
        print("="*80)

    def print_subheader(self, subtitulo):
        """Imprimir subencabezado"""
        print(f"\n{'-'*60}")
        print(f"   {subtitulo}")
        print(f"{'-'*60}")

    def verificar_dependencias(self):
        """Verificar dependencias necesarias para las pruebas - Mejorado para sin entorno virtual"""
        self.print_subheader("VERIFICACIÓN DE DEPENDENCIAS")

        dependencias = [
            ('Django', 'django'),
            ('Pillow', 'PIL'),
            ('ReportLab', 'reportlab'),
            ('XlsxWriter', 'xlsxwriter'),
        ]

        dependencias_faltantes = []
        dependencias_instaladas = []

        for nombre, modulo in dependencias:
            try:
                # Intentar importar el módulo
                imported_module = __import__(modulo)

                # Verificar si realmente se importó correctamente
                if hasattr(imported_module, '__version__'):
                    version = imported_module.__version__
                elif hasattr(imported_module, 'VERSION'):
                    version = str(imported_module.VERSION)
                elif hasattr(imported_module, 'version'):
                    version = str(imported_module.version)
                else:
                    version = "instalado"

                print(f"✅ {nombre} - Instalado ({version})")
                dependencias_instaladas.append(nombre)

            except ImportError as e:
                print(f"❌ {nombre} - NO INSTALADO")
                print(f"   Error: {str(e)}")
                dependencias_faltantes.append(nombre)
            except Exception as e:
                print(f"⚠️  {nombre} - ERROR AL VERIFICAR: {str(e)}")
                dependencias_faltantes.append(nombre)

        print(f"\n📊 Resumen de dependencias:")
        print(f"   ✅ Instaladas: {len(dependencias_instaladas)}")
        print(f"   ❌ Faltantes: {len(dependencias_faltantes)}")

        if dependencias_faltantes:
            print(
                f"\n⚠️  Dependencias faltantes: {', '.join(dependencias_faltantes)}")
            print("   Para instalar manualmente:")
            for dep in dependencias_faltantes:
                if dep == 'Pillow':
                    print("     pip install Pillow")
                elif dep == 'ReportLab':
                    print("     pip install reportlab")
                elif dep == 'XlsxWriter':
                    print("     pip install XlsxWriter")
                else:
                    print(f"     pip install {dep}")
            print("\n   O instalar todas desde requirements.txt:")
            print("     pip install -r requirements.txt")

            # Intentar autoinstalación
            respuesta = input(
                "\n¿Deseas intentar instalar automáticamente las dependencias faltantes? (s/n): ")
            if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
                self.autoinstalar_dependencias(dependencias_faltantes)
                return self.verificar_dependencias()  # Re-verificar después de la instalación
            else:
                return False
        else:
            print("\n✅ Todas las dependencias están instaladas")
            return True

    def autoinstalar_dependencias(self, dependencias_faltantes):
        """Intentar instalar automáticamente las dependencias faltantes"""
        print("\n🔧 Intentando instalar dependencias automáticamente...")

        # Mapeo de nombres de dependencias a nombres de paquetes pip
        pip_names = {
            'Pillow': 'Pillow',
            'ReportLab': 'reportlab',
            'XlsxWriter': 'XlsxWriter',
            'Django': 'Django'
        }

        for dep in dependencias_faltantes:
            if dep in pip_names:
                package_name = pip_names[dep]
                try:
                    print(f"   Instalando {package_name}...")
                    subprocess.check_call(
                        [sys.executable, '-m', 'pip', 'install', package_name])
                    print(f"   ✅ {dep} instalado correctamente")
                except subprocess.CalledProcessError as e:
                    print(f"   ❌ Error instalando {dep}: {e}")
                except Exception as e:
                    print(f"   ❌ Error inesperado instalando {dep}: {e}")

    def ejecutar_pruebas_unitarias(self):
        """
        Ejecutar pruebas unitarias del módulo inventario
        Sección 3.2.1: Pruebas unitarias para componentes individuales
        """
        self.print_subheader("PRUEBAS UNITARIAS - MÓDULO INVENTARIO")
        print("Validando lógica de negocio en componentes individuales...")

        start_time = time.time()

        try:
            # Configurar runner de pruebas
            TestRunner = get_runner(settings)
            test_runner = TestRunner(
                verbosity=2, interactive=False, keepdb=True)

            # Ejecutar pruebas unitarias del inventario
            failures = test_runner.run_tests(['inventario.test_unitarias'])

            end_time = time.time()
            self.resultados['unitarias']['tiempo'] = round(
                end_time - start_time, 2)

            if failures == 0:
                print("✅ TODAS LAS PRUEBAS UNITARIAS PASARON")
                self.resultados['unitarias']['exitosas'] = 1
            else:
                print(f"❌ {failures} PRUEBAS UNITARIAS FALLARON")
                self.resultados['unitarias']['fallidas'] = failures

        except Exception as e:
            print(f"❌ ERROR EJECUTANDO PRUEBAS UNITARIAS: {str(e)}")
            self.resultados['unitarias']['fallidas'] = 1

        print(
            f"⏱️  Tiempo de ejecución: {self.resultados['unitarias']['tiempo']} segundos")

    def ejecutar_pruebas_integracion(self):
        """
        Ejecutar pruebas de integración del módulo usuarios
        Sección 3.2.2: Pruebas de interacción entre componentes
        """
        self.print_subheader("PRUEBAS DE INTEGRACIÓN - MÓDULO USUARIOS")
        print("Validando interacción entre componentes del sistema...")

        start_time = time.time()

        try:
            TestRunner = get_runner(settings)
            test_runner = TestRunner(
                verbosity=2, interactive=False, keepdb=True)

            # Ejecutar pruebas de integración
            failures = test_runner.run_tests(['usuarios.test_integracion'])

            end_time = time.time()
            self.resultados['integracion']['tiempo'] = round(
                end_time - start_time, 2)

            if failures == 0:
                print("✅ TODAS LAS PRUEBAS DE INTEGRACIÓN PASARON")
                self.resultados['integracion']['exitosas'] = 1
            else:
                print(f"❌ {failures} PRUEBAS DE INTEGRACIÓN FALLARON")
                self.resultados['integracion']['fallidas'] = failures

        except Exception as e:
            print(f"❌ ERROR EJECUTANDO PRUEBAS DE INTEGRACIÓN: {str(e)}")
            self.resultados['integracion']['fallidas'] = 1

        print(
            f"⏱️  Tiempo de ejecución: {self.resultados['integracion']['tiempo']} segundos")

    def ejecutar_pruebas_aceptacion(self):
        """
        Ejecutar pruebas de aceptación del módulo diagnóstico
        Sección 3.2.3: Pruebas de usabilidad y satisfacción de requisitos
        """
        self.print_subheader("PRUEBAS DE ACEPTACIÓN - MÓDULO DIAGNÓSTICO")
        print("Validando usabilidad y satisfacción de requisitos...")

        start_time = time.time()

        try:
            TestRunner = get_runner(settings)
            test_runner = TestRunner(
                verbosity=2, interactive=False, keepdb=True)

            # Ejecutar pruebas de aceptación
            failures = test_runner.run_tests(['diagnostico.test_aceptacion'])

            end_time = time.time()
            self.resultados['aceptacion']['tiempo'] = round(
                end_time - start_time, 2)

            if failures == 0:
                print("✅ TODAS LAS PRUEBAS DE ACEPTACIÓN PASARON")
                self.resultados['aceptacion']['exitosas'] = 1
            else:
                print(f"❌ {failures} PRUEBAS DE ACEPTACIÓN FALLARON")
                self.resultados['aceptacion']['fallidas'] = failures

        except Exception as e:
            print(f"❌ ERROR EJECUTANDO PRUEBAS DE ACEPTACIÓN: {str(e)}")
            self.resultados['aceptacion']['fallidas'] = 1

        print(
            f"⏱️  Tiempo de ejecución: {self.resultados['aceptacion']['tiempo']} segundos")

    def verificar_cobertura_codigo(self):
        """
        Verificar cobertura de código (si coverage está instalado)
        Objetivo: >80% según buenas prácticas
        """
        self.print_subheader("ANÁLISIS DE COBERTURA DE CÓDIGO")

        try:
            # Verificar si coverage está instalado
            subprocess.run([sys.executable, '-m', 'coverage', '--version'],
                           capture_output=True, check=True)

            print("📊 Generando reporte de cobertura...")

            # Ejecutar pruebas con coverage
            subprocess.run([
                sys.executable, '-m', 'coverage', 'run', '--source=.',
                'manage.py', 'test',
                'inventario.test_unitarias',
                'usuarios.test_integracion',
                'diagnostico.test_aceptacion'
            ], check=True)

            # Generar reporte
            result = subprocess.run([sys.executable, '-m', 'coverage', 'report'],
                                    capture_output=True, text=True)

            print("📈 Reporte de Cobertura:")
            print(result.stdout)

            # Generar reporte HTML
            subprocess.run(
                [sys.executable, '-m', 'coverage', 'html'], check=True)
            print("📊 Reporte HTML generado en htmlcov/index.html")

        except subprocess.CalledProcessError:
            print("⚠️  Coverage no está instalado o falló")
            print("   Instalar con: pip install coverage")
        except FileNotFoundError:
            print("⚠️  Coverage no encontrado")

    def generar_reporte_resultados(self):
        """Generar reporte final de resultados"""
        self.print_header("REPORTE FINAL DE PRUEBAS")

        # Calcular totales
        total_exitosas = sum(r['exitosas'] for r in self.resultados.values())
        total_fallidas = sum(r['fallidas'] for r in self.resultados.values())
        tiempo_total = sum(r['tiempo'] for r in self.resultados.values())

        print(f"""
📋 RESUMEN EJECUTIVO:
   • Pruebas exitosas: {total_exitosas}/3 módulos
   • Pruebas fallidas:  {total_fallidas}
   • Tiempo total:      {tiempo_total:.2f} segundos

📊 DETALLE POR TIPO DE PRUEBA:
""")

        tipos_prueba = {
            'unitarias': 'Pruebas Unitarias (Inventario)',
            'integracion': 'Pruebas de Integración (Usuarios)',
            'aceptacion': 'Pruebas de Aceptación (Diagnóstico)'
        }

        for tipo, nombre in tipos_prueba.items():
            resultado = self.resultados[tipo]
            estado = "✅ ÉXITO" if resultado['exitosas'] > 0 else "❌ FALLÓ"
            print(f"   • {nombre}: {estado} ({resultado['tiempo']:.2f}s)")

        # Indicadores de calidad según el documento
        print(f"""
🎯 INDICADORES DE CALIDAD:
   • Reducción de errores: {"✅ Logrado" if total_fallidas == 0 else "❌ Pendiente"}
   • Tiempo de respuesta:  {"✅ <3s por módulo" if all(r['tiempo'] < 3 for r in self.resultados.values()) else "⚠️  Revisar"}
   • Cobertura de código:  {"📊 Ver reporte coverage" if self.verificar_coverage_disponible() else "⚠️  No medido"}

🏆 NIVEL DE CALIDAD ALCANZADO:
""")

        if total_fallidas == 0:
            print("   🥇 EXCELENTE - Todas las pruebas pasaron")
            print("   ✅ Sistema listo para producción")
        elif total_fallidas <= 2:
            print("   🥈 BUENO - Algunas pruebas requieren atención")
            print("   ⚠️  Revisar fallos antes de despliegue")
        else:
            print("   🥉 MEJORABLE - Múltiples fallos detectados")
            print("   ❌ Requiere correcciones antes de continuar")

    def verificar_coverage_disponible(self):
        """Verificar si coverage está disponible"""
        try:
            subprocess.run([sys.executable, '-m', 'coverage', '--version'],
                           capture_output=True, check=True)
            return True
        except:
            return False

    def ejecutar_suite_completa(self):
        """Ejecutar suite completa de pruebas"""
        self.print_header("SISTEMA DE PRUEBAS UCF - YAIDELÍN CHAVIANO")
        print("Implementando estrategia de pruebas del documento de investigación")
        print("Universidad de Cienfuegos - Sistema de Gestión de Inventarios Tecnológicos")

        # Verificar dependencias
        if not self.verificar_dependencias():
            print("\n❌ No se pueden ejecutar las pruebas sin las dependencias")
            return

        # Ejecutar cada tipo de prueba
        self.ejecutar_pruebas_unitarias()
        self.ejecutar_pruebas_integracion()
        self.ejecutar_pruebas_aceptacion()

        # Verificar cobertura si está disponible
        self.verificar_cobertura_codigo()

        # Generar reporte final
        self.generar_reporte_resultados()

    def ejecutar_por_tipo(self, tipo_prueba):
        """Ejecutar solo un tipo específico de pruebas"""
        if tipo_prueba == 'unitarias':
            self.ejecutar_pruebas_unitarias()
        elif tipo_prueba == 'integracion':
            self.ejecutar_pruebas_integracion()
        elif tipo_prueba == 'aceptacion':
            self.ejecutar_pruebas_aceptacion()
        else:
            print(f"❌ Tipo de prueba no válido: {tipo_prueba}")
            print("   Tipos válidos: unitarias, integracion, aceptacion")


def main():
    """Función principal del script"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Ejecutor de pruebas del Sistema UCF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python ejecutar_pruebas_ucf.py                    # Ejecutar todas las pruebas
  python ejecutar_pruebas_ucf.py --tipo unitarias   # Solo pruebas unitarias
  python ejecutar_pruebas_ucf.py --tipo integracion # Solo pruebas de integración
  python ejecutar_pruebas_ucf.py --tipo aceptacion  # Solo pruebas de aceptación
  python ejecutar_pruebas_ucf.py --coverage         # Incluir análisis de cobertura
        """
    )

    parser.add_argument(
        '--tipo',
        choices=['unitarias', 'integracion', 'aceptacion'],
        help='Tipo específico de pruebas a ejecutar'
    )

    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Incluir análisis de cobertura de código'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Salida detallada'
    )

    args = parser.parse_args()

    # Crear runner
    runner = TestRunner()

    try:
        if args.tipo:
            # Ejecutar tipo específico
            runner.ejecutar_por_tipo(args.tipo)
        else:
            # Ejecutar suite completa
            runner.ejecutar_suite_completa()

    except KeyboardInterrupt:
        print("\n\n⚠️  Ejecución interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
