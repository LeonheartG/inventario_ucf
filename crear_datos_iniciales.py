from locales.models import Local
from diagnostico.models import Cuestionario, Pregunta
from inventario.models import Proveedor
from usuarios.models import Rol, Departamento
from django.contrib.auth.models import User
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario_ucf.settings')
django.setup()


# Ya tienes implementado Roles y Departamentos

# Crear algunos proveedores iniciales
proveedores = [
    {"nombre": "Proveedor General", "telefono": "555-1234",
        "email": "contacto@proveedorgeneral.com"},
    {"nombre": "Tecnología S.A.", "telefono": "555-5678",
        "email": "ventas@tecnologiasa.com"}
]

for prov_data in proveedores:
    Proveedor.objects.get_or_create(
        nombre=prov_data["nombre"],
        defaults={
            'telefono': prov_data["telefono"],
            'email': prov_data["email"]
        }
    )

# Crear un cuestionario inicial para diagnóstico
cuestionario, created = Cuestionario.objects.get_or_create(
    titulo="Cuestionario de Evaluación Básica",
    defaults={
        'descripcion': "Cuestionario básico para evaluar el nivel de transformación digital",
        'activo': True
    }
)

if created:
    # Si se creó el cuestionario, agregar algunas preguntas
    preguntas = [
        {"texto": "¿Se utilizan herramientas digitales para la gestión administrativa?",
            "tipo": "si_no", "categoria": "Administración", "orden": 1},
        {"texto": "¿Qué nivel de adopción de tecnología tienen los procesos académicos?",
            "tipo": "escala", "categoria": "Académico", "orden": 2},
        {"texto": "¿Qué nivel de capacitación digital tiene el personal?",
            "tipo": "escala", "categoria": "Recursos Humanos", "orden": 3}
    ]

    for preg_data in preguntas:
        Pregunta.objects.create(
            cuestionario=cuestionario,
            texto=preg_data["texto"],
            tipo=preg_data["tipo"],
            categoria=preg_data["categoria"],
            orden=preg_data["orden"]
        )

# Crear algunos locales iniciales
locales = [
    {"nombre": "Laboratorio General", "tipo": "laboratorio",
        "capacidad": 20, "ubicacion": "Edificio Central, Planta 1"},
    {"nombre": "Aula Magna", "tipo": "aula",
        "capacidad": 50, "ubicacion": "Edificio Principal"}
]

for local_data in locales:
    departamento = Departamento.objects.first()
    Local.objects.get_or_create(
        nombre=local_data["nombre"],
        defaults={
            'tipo': local_data["tipo"],
            'capacidad': local_data["capacidad"],
            'ubicacion': local_data["ubicacion"],
            'departamento': departamento,
            'estado': 'disponible'
        }
    )

print("Datos iniciales para todos los módulos creados con éxito")
