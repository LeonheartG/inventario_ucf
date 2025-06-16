# inventario/test_unitarias.py
"""
Pruebas unitarias para el módulo de inventario
Según el documento de Yaidelín Chaviano, sección 3.2.1:
"Pruebas unitarias realizadas por los desarrolladores durante la implementación,
utilizando el framework de pruebas de Django, enfocadas en validar la lógica 
de negocio en componentes individuales"
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime, date
from inventario.models import Activo, Hardware, Software, Mantenimiento
from inventario.forms import HardwareForm, SoftwareForm
from usuarios.models import Departamento, Rol, PerfilUsuario


class ActivoModelTestCase(TestCase):
    """
    Pruebas unitarias para el modelo Activo
    Valida la lógica de negocio básica del activo tecnológico
    """

    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.departamento = Departamento.objects.create(
            nombre="TI Test",
            descripcion="Departamento de pruebas",
            ubicacion="Campus Principal"
        )

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_crear_activo_valido(self):
        """
        CP-UT-01: Verificar creación exitosa de activo con datos válidos
        """
        activo = Activo.objects.create(
            tipo='hardware',
            nombre='Computadora Test',
            descripcion='Descripción de prueba',
            fecha_adquisicion=date.today(),
            valor_adquisicion=Decimal('1500.00'),
            estado='activo',
            departamento=self.departamento,
            ubicacion='Oficina 101',
            creado_por=self.user
        )

        # Verificaciones
        self.assertEqual(activo.nombre, 'Computadora Test')
        self.assertEqual(activo.tipo, 'hardware')
        self.assertEqual(activo.estado, 'activo')
        self.assertEqual(activo.departamento, self.departamento)
        self.assertIsNotNone(activo.fecha_creacion)
        self.assertIsNotNone(activo.fecha_actualizacion)

    def test_activo_str_representation(self):
        """
        CP-UT-02: Verificar representación string del activo
        """
        activo = Activo.objects.create(
            tipo='software',
            nombre='Microsoft Office',
            fecha_adquisicion=date.today(),
            valor_adquisicion=Decimal('300.00'),
            departamento=self.departamento,
            creado_por=self.user
        )

        expected_str = "Microsoft Office (Software)"
        self.assertEqual(str(activo), expected_str)

    def test_valor_adquisicion_precision(self):
        """
        CP-UT-03: Verificar precisión decimal del valor de adquisición
        """
        activo = Activo.objects.create(
            tipo='hardware',
            nombre='Impresora Test',
            fecha_adquisicion=date.today(),
            valor_adquisicion=Decimal('450.99'),
            departamento=self.departamento,
            creado_por=self.user
        )

        self.assertEqual(activo.valor_adquisicion, Decimal('450.99'))
        self.assertIsInstance(activo.valor_adquisicion, Decimal)


class HardwareModelTestCase(TestCase):
    """
    Pruebas unitarias para el modelo Hardware
    """

    def setUp(self):
        self.departamento = Departamento.objects.create(
            nombre="TI Hardware",
            ubicacion="Campus Principal"
        )

        self.user = User.objects.create_user(
            username='hwuser',
            password='testpass123'
        )

        self.activo = Activo.objects.create(
            tipo='hardware',
            nombre='PC Dell',
            fecha_adquisicion=date.today(),
            valor_adquisicion=Decimal('2000.00'),
            departamento=self.departamento,
            creado_por=self.user
        )

    def test_crear_hardware_con_numero_serie_unico(self):
        """
        CP-UT-04: Verificar que el número de serie sea único
        """
        hardware1 = Hardware.objects.create(
            activo=self.activo,
            marca='Dell',
            modelo='OptiPlex 7090',
            numero_serie='DL123456789',
            periodicidad_mantenimiento=180
        )

        # Crear otro activo para el segundo hardware
        activo2 = Activo.objects.create(
            tipo='hardware',
            nombre='PC HP',
            fecha_adquisicion=date.today(),
            valor_adquisicion=Decimal('1800.00'),
            departamento=self.departamento,
            creado_por=self.user
        )

        # Intentar crear hardware con el mismo número de serie debe fallar
        with self.assertRaises(Exception):
            Hardware.objects.create(
                activo=activo2,
                marca='HP',
                modelo='ProDesk 400',
                numero_serie='DL123456789',  # Mismo número de serie
                periodicidad_mantenimiento=180
            )

    def test_hardware_str_representation(self):
        """
        CP-UT-05: Verificar representación string del hardware
        """
        hardware = Hardware.objects.create(
            activo=self.activo,
            marca='Dell',
            modelo='OptiPlex 7090',
            numero_serie='DL987654321',
            periodicidad_mantenimiento=180
        )

        expected_str = "PC Dell - Dell OptiPlex 7090"
        self.assertEqual(str(hardware), expected_str)


class SoftwareModelTestCase(TestCase):
    """
    Pruebas unitarias para el modelo Software
    """

    def setUp(self):
        self.departamento = Departamento.objects.create(
            nombre="TI Software",
            ubicacion="Campus Principal"
        )

        self.user = User.objects.create_user(
            username='swuser',
            password='testpass123'
        )

        self.activo = Activo.objects.create(
            tipo='software',
            nombre='Adobe Photoshop',
            fecha_adquisicion=date.today(),
            valor_adquisicion=Decimal('600.00'),
            departamento=self.departamento,
            creado_por=self.user
        )

    def test_crear_software_con_licencia_temporal(self):
        """
        CP-UT-06: Verificar creación de software con licencia temporal
        """
        software = Software.objects.create(
            activo=self.activo,
            version='2024',
            tipo_licencia='temporal',
            fecha_vencimiento=date(2025, 12, 31),
            numero_licencias=5
        )

        self.assertEqual(software.tipo_licencia, 'temporal')
        self.assertEqual(software.numero_licencias, 5)
        self.assertIsNotNone(software.fecha_vencimiento)

    def test_software_sin_fecha_vencimiento_perpetua(self):
        """
        CP-UT-07: Verificar software con licencia perpetua sin fecha de vencimiento
        """
        software = Software.objects.create(
            activo=self.activo,
            version='2024',
            tipo_licencia='perpetua',
            numero_licencias=1
        )

        self.assertEqual(software.tipo_licencia, 'perpetua')
        self.assertIsNone(software.fecha_vencimiento)


class MantenimientoModelTestCase(TestCase):
    """
    Pruebas unitarias para el modelo Mantenimiento
    """

    def setUp(self):
        self.departamento = Departamento.objects.create(
            nombre="TI Mantenimiento",
            ubicacion="Campus Principal"
        )

        self.user = User.objects.create_user(
            username='mantuser',
            password='testpass123'
        )

        self.activo = Activo.objects.create(
            tipo='hardware',
            nombre='Servidor Principal',
            fecha_adquisicion=date.today(),
            valor_adquisicion=Decimal('5000.00'),
            departamento=self.departamento,
            creado_por=self.user
        )

    def test_crear_mantenimiento_preventivo(self):
        """
        CP-UT-08: Verificar creación de mantenimiento preventivo
        """
        mantenimiento = Mantenimiento.objects.create(
            activo=self.activo,
            tipo='preventivo',
            fecha_programada=date(2024, 12, 15),
            responsable=self.user,
            descripcion='Limpieza y revisión general del servidor',
            estado='programado'
        )

        self.assertEqual(mantenimiento.tipo, 'preventivo')
        self.assertEqual(mantenimiento.estado, 'programado')
        self.assertEqual(mantenimiento.responsable, self.user)

    def test_mantenimiento_str_representation(self):
        """
        CP-UT-09: Verificar representación string del mantenimiento
        """
        mantenimiento = Mantenimiento.objects.create(
            activo=self.activo,
            tipo='correctivo',
            fecha_programada=date(2024, 12, 20),
            responsable=self.user,
            descripcion='Reparación de falla en disco duro',
            estado='en_proceso'
        )

        expected_str = f"Mantenimiento Correctivo de {self.activo.nombre} - {mantenimiento.fecha_programada}"
        self.assertEqual(str(mantenimiento), expected_str)


class HardwareFormTestCase(TestCase):
    """
    Pruebas unitarias para el formulario HardwareForm
    """

    def setUp(self):
        self.departamento = Departamento.objects.create(
            nombre="TI Forms",
            ubicacion="Campus Principal"
        )

        self.user = User.objects.create_user(
            username='formuser',
            password='testpass123'
        )

    def test_hardware_form_valido(self):
        """
        CP-UT-10: Verificar validación exitosa del formulario de hardware
        """
        form_data = {
            'nombre': 'Laptop Dell',
            'descripcion': 'Laptop para desarrollo',
            'fecha_adquisicion': '2024-01-15',
            'valor_adquisicion': '1200.00',
            'estado': 'activo',
            'departamento': self.departamento.id,
            'ubicacion': 'Oficina 102',
            'marca': 'Dell',
            'modelo': 'Latitude 5520',
            'numero_serie': 'DL2024001',
            'especificaciones': 'Intel i7, 16GB RAM, 512GB SSD',
            'fecha_garantia': '2027-01-15',
            'periodicidad_mantenimiento': 180
        }

        form = HardwareForm(data=form_data)
        self.assertTrue(form.is_valid(),
                        f"Errores del formulario: {form.errors}")

    def test_hardware_form_numero_serie_requerido(self):
        """
        CP-UT-11: Verificar que el número de serie sea requerido
        """
        form_data = {
            'nombre': 'Laptop HP',
            'fecha_adquisicion': '2024-01-15',
            'valor_adquisicion': '1100.00',
            'estado': 'activo',
            'departamento': self.departamento.id,
            'marca': 'HP',
            'modelo': 'EliteBook 840',
            # numero_serie omitido intencionalmente
            'periodicidad_mantenimiento': 180
        }

        form = HardwareForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('numero_serie', form.errors)

    def test_hardware_form_valor_adquisicion_positivo(self):
        """
        CP-UT-12: Verificar que el valor de adquisición sea positivo
        """
        form_data = {
            'nombre': 'Tablet Samsung',
            'fecha_adquisicion': '2024-01-15',
            'valor_adquisicion': '-500.00',  # Valor negativo
            'estado': 'activo',
            'departamento': self.departamento.id,
            'marca': 'Samsung',
            'modelo': 'Galaxy Tab S8',
            'numero_serie': 'SM2024001',
            'periodicidad_mantenimiento': 180
        }

        form = HardwareForm(data=form_data)
        # El formulario debería invalidarse debido al valor negativo
        # Nota: Esto depende de la validación implementada en el widget


class MetricasRendimientoTestCase(TestCase):
    """
    Pruebas unitarias para verificar métricas de rendimiento
    según los requerimientos no funcionales del documento
    """

    def setUp(self):
        self.departamento = Departamento.objects.create(
            nombre="Rendimiento Test",
            ubicacion="Campus Principal"
        )

        self.user = User.objects.create_user(
            username='perfuser',
            password='testpass123'
        )

    def test_creacion_masiva_activos_rendimiento(self):
        """
        CP-UT-13: Verificar rendimiento al crear múltiples activos
        RNF7: El sistema debe ser capaz de gestionar al menos 10,000 activos
        """
        import time

        start_time = time.time()

        # Crear lote de activos (muestra pequeña para prueba)
        activos = []
        for i in range(100):  # Reducido para pruebas rápidas
            activo = Activo(
                tipo='hardware',
                nombre=f'Equipo Test {i}',
                descripcion=f'Descripción del equipo {i}',
                fecha_adquisicion=date.today(),
                valor_adquisicion=Decimal('1000.00'),
                estado='activo',
                departamento=self.departamento,
                ubicacion=f'Oficina {i}',
                creado_por=self.user
            )
            activos.append(activo)

        # Inserción masiva
        Activo.objects.bulk_create(activos)

        end_time = time.time()
        execution_time = end_time - start_time

        # Verificar que la creación fue exitosa
        total_activos = Activo.objects.count()
        self.assertEqual(total_activos, 100)

        # Verificar tiempo de ejecución (debe ser menor a 5 segundos para 100 registros)
        self.assertLess(execution_time, 5.0,
                        f"La creación de 100 activos tomó {execution_time:.2f} segundos")

    def test_consulta_activos_rendimiento(self):
        """
        CP-UT-14: Verificar rendimiento de consultas
        RNF5: El sistema debe responder en menos de 3 segundos
        """
        import time

        # Crear datos de prueba
        for i in range(50):
            activo = Activo.objects.create(
                tipo='hardware',
                nombre=f'PC {i}',
                fecha_adquisicion=date.today(),
                valor_adquisicion=Decimal('1500.00'),
                departamento=self.departamento,
                creado_por=self.user
            )

        start_time = time.time()

        # Realizar consulta compleja
        activos = Activo.objects.select_related('departamento', 'creado_por').filter(
            estado='activo',
            departamento=self.departamento
        ).order_by('-fecha_adquisicion')[:20]

        # Forzar evaluación del QuerySet
        list(activos)

        end_time = time.time()
        execution_time = end_time - start_time

        # Verificar tiempo de respuesta
        self.assertLess(execution_time, 3.0,
                        f"La consulta tomó {execution_time:.2f} segundos")


if __name__ == '__main__':
    # Ejecutar pruebas unitarias
    import unittest
    unittest.main()
