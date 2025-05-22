from django import forms
from decimal import Decimal
from .models import Activo, Hardware, Software
from usuarios.models import Departamento, LogActividad


class HardwareForm(forms.ModelForm):
    nombre = forms.CharField(max_length=200, required=True)
    descripcion = forms.CharField(widget=forms.Textarea, required=False)
    fecha_adquisicion = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}))
    valor_adquisicion = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        localize=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )
    estado = forms.ChoiceField(choices=Activo.ESTADO_CHOICES)
    departamento = forms.ModelChoiceField(queryset=Departamento.objects.all())
    ubicacion = forms.CharField(max_length=100, required=False)
    imagen = forms.ImageField(required=False)

    marca = forms.CharField(max_length=100, required=True)
    modelo = forms.CharField(max_length=100, required=True)
    numero_serie = forms.CharField(max_length=100, required=True)
    especificaciones = forms.CharField(widget=forms.Textarea, required=False)
    fecha_garantia = forms.DateField(widget=forms.DateInput(
        attrs={'type': 'date'}), required=False)
    periodicidad_mantenimiento = forms.IntegerField(initial=180)

    class Meta:
        model = Hardware
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Agregar clases CSS a todos los campos
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-control'

        # Si tenemos una instancia (estamos editando), cargar los datos
        if self.instance and self.instance.pk:
            activo = self.instance.activo

            # Establecer valores iniciales para los campos del activo
            self.initial['nombre'] = activo.nombre
            self.initial['descripcion'] = activo.descripcion
            self.initial['fecha_adquisicion'] = activo.fecha_adquisicion

            # CLAVE: Convertir explícitamente a formato con punto decimal
            valor_decimal = activo.valor_adquisicion
            if isinstance(valor_decimal, Decimal):
                # Convertir a string con formato americano (punto decimal)
                valor_formateado = str(valor_decimal).replace(',', '.')
                self.initial['valor_adquisicion'] = valor_formateado
            else:
                self.initial['valor_adquisicion'] = str(valor_decimal)

            self.initial['estado'] = activo.estado
            self.initial['departamento'] = activo.departamento_id
            self.initial['ubicacion'] = activo.ubicacion

            # Establecer valores iniciales para los campos del hardware
            self.initial['marca'] = self.instance.marca
            self.initial['modelo'] = self.instance.modelo
            self.initial['numero_serie'] = self.instance.numero_serie
            self.initial['especificaciones'] = self.instance.especificaciones
            self.initial['fecha_garantia'] = self.instance.fecha_garantia
            self.initial['periodicidad_mantenimiento'] = self.instance.periodicidad_mantenimiento

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def save(self, commit=True, user=None):
        activo_id = self.instance.activo_id if hasattr(
            self.instance, 'activo_id') and self.instance.activo_id else None

        if activo_id:
            # Actualizar activo existente
            activo = Activo.objects.get(id=activo_id)
            activo.nombre = self.cleaned_data['nombre']
            activo.descripcion = self.cleaned_data.get('descripcion', '')
            activo.fecha_adquisicion = self.cleaned_data['fecha_adquisicion']
            activo.valor_adquisicion = self.cleaned_data['valor_adquisicion']
            activo.estado = self.cleaned_data['estado']
            activo.departamento = self.cleaned_data['departamento']
            activo.ubicacion = self.cleaned_data.get('ubicacion', '')

            if 'imagen' in self.cleaned_data and self.cleaned_data['imagen']:
                activo.imagen = self.cleaned_data['imagen']

            if user:
                activo.actualizado_por = user

            activo.save()

            # Actualizar hardware
            hardware = self.instance
            hardware.marca = self.cleaned_data['marca']
            hardware.modelo = self.cleaned_data['modelo']
            hardware.numero_serie = self.cleaned_data['numero_serie']
            hardware.especificaciones = self.cleaned_data.get(
                'especificaciones', '')
            hardware.fecha_garantia = self.cleaned_data.get('fecha_garantia')
            hardware.periodicidad_mantenimiento = self.cleaned_data.get(
                'periodicidad_mantenimiento', 180)
            hardware.save()
        else:
            # Crear nuevo activo
            activo = Activo.objects.create(
                tipo='hardware',
                nombre=self.cleaned_data['nombre'],
                descripcion=self.cleaned_data.get('descripcion', ''),
                fecha_adquisicion=self.cleaned_data['fecha_adquisicion'],
                valor_adquisicion=self.cleaned_data['valor_adquisicion'],
                estado=self.cleaned_data['estado'],
                departamento=self.cleaned_data['departamento'],
                ubicacion=self.cleaned_data.get('ubicacion', ''),
                creado_por=user,
                actualizado_por=user
            )

            if 'imagen' in self.cleaned_data and self.cleaned_data['imagen']:
                activo.imagen = self.cleaned_data['imagen']
                activo.save()

            # Crear nuevo hardware
            hardware = Hardware.objects.create(
                activo=activo,
                marca=self.cleaned_data['marca'],
                modelo=self.cleaned_data['modelo'],
                numero_serie=self.cleaned_data['numero_serie'],
                especificaciones=self.cleaned_data.get('especificaciones', ''),
                fecha_garantia=self.cleaned_data.get('fecha_garantia'),
                periodicidad_mantenimiento=self.cleaned_data.get(
                    'periodicidad_mantenimiento', 180)
            )

        return hardware


class SoftwareForm(forms.ModelForm):
    nombre = forms.CharField(max_length=200, required=True, label='Nombre')
    descripcion = forms.CharField(
        widget=forms.Textarea, required=False, label='Descripción')
    fecha_adquisicion = forms.DateField(widget=forms.DateInput(
        attrs={'type': 'date'}), label='Fecha de adquisición')
    valor_adquisicion = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label='Valor de adquisición',
        localize=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )
    estado = forms.ChoiceField(choices=Activo.ESTADO_CHOICES, label='Estado')
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(), label='Departamento')
    ubicacion = forms.CharField(
        max_length=100, required=False, label='Ubicación')
    imagen = forms.ImageField(required=False, label='Imagen')

    version = forms.CharField(max_length=50, required=True, label='Versión')
    tipo_licencia = forms.ChoiceField(
        choices=Software.TIPO_LICENCIA_CHOICES, label='Tipo de licencia')
    clave_activacion = forms.CharField(
        max_length=200, required=False, label='Clave de activación')
    fecha_vencimiento = forms.DateField(widget=forms.DateInput(
        attrs={'type': 'date'}), required=False, label='Fecha de vencimiento')
    numero_licencias = forms.IntegerField(
        initial=1, label='Número de licencias')

    class Meta:
        model = Software
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Agregar clases CSS a todos los campos
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-control'

        # Si tenemos una instancia (estamos editando), cargar los datos
        if self.instance and self.instance.pk:
            activo = self.instance.activo

            # Establecer valores iniciales para los campos del activo
            self.initial['nombre'] = activo.nombre
            self.initial['descripcion'] = activo.descripcion
            self.initial['fecha_adquisicion'] = activo.fecha_adquisicion

            # CLAVE: Convertir explícitamente a formato con punto decimal
            valor_decimal = activo.valor_adquisicion
            if isinstance(valor_decimal, Decimal):
                # Convertir a string con formato americano (punto decimal)
                valor_formateado = str(valor_decimal).replace(',', '.')
                self.initial['valor_adquisicion'] = valor_formateado
            else:
                self.initial['valor_adquisicion'] = str(valor_decimal)

            self.initial['estado'] = activo.estado
            self.initial['departamento'] = activo.departamento_id
            self.initial['ubicacion'] = activo.ubicacion

            # Establecer valores iniciales para los campos del software
            self.initial['version'] = self.instance.version
            self.initial['tipo_licencia'] = self.instance.tipo_licencia
            self.initial['clave_activacion'] = self.instance.clave_activacion
            self.initial['fecha_vencimiento'] = self.instance.fecha_vencimiento
            self.initial['numero_licencias'] = self.instance.numero_licencias

    def save(self, commit=True, user=None):
        try:
            # Primero creamos o actualizamos el activo
            activo_id = self.instance.activo_id if hasattr(
                self.instance, 'activo_id') and self.instance.activo_id else None

            if activo_id:
                activo = Activo.objects.get(id=activo_id)
                activo.nombre = self.cleaned_data['nombre']
                activo.descripcion = self.cleaned_data['descripcion']
                activo.fecha_adquisicion = self.cleaned_data['fecha_adquisicion']
                activo.valor_adquisicion = self.cleaned_data['valor_adquisicion']
                activo.estado = self.cleaned_data['estado']
                activo.departamento = self.cleaned_data['departamento']
                activo.ubicacion = self.cleaned_data['ubicacion']

                if self.cleaned_data.get('imagen'):
                    activo.imagen = self.cleaned_data['imagen']

                if user:
                    activo.actualizado_por = user

                activo.save()
            else:
                activo = Activo.objects.create(
                    tipo='software',
                    nombre=self.cleaned_data['nombre'],
                    descripcion=self.cleaned_data['descripcion'],
                    fecha_adquisicion=self.cleaned_data['fecha_adquisicion'],
                    valor_adquisicion=self.cleaned_data['valor_adquisicion'],
                    estado=self.cleaned_data['estado'],
                    departamento=self.cleaned_data['departamento'],
                    ubicacion=self.cleaned_data['ubicacion'],
                    imagen=self.cleaned_data.get('imagen'),
                    creado_por=user,
                    actualizado_por=user
                )

            # Ahora creamos o actualizamos el software
            if activo_id:
                software = self.instance
                software.version = self.cleaned_data['version']
                software.tipo_licencia = self.cleaned_data['tipo_licencia']
                software.clave_activacion = self.cleaned_data.get(
                    'clave_activacion', '')
                software.fecha_vencimiento = self.cleaned_data.get(
                    'fecha_vencimiento')
                software.numero_licencias = self.cleaned_data.get(
                    'numero_licencias', 1)
                software.save()
            else:
                software = Software.objects.create(
                    activo=activo,
                    version=self.cleaned_data['version'],
                    tipo_licencia=self.cleaned_data['tipo_licencia'],
                    clave_activacion=self.cleaned_data.get(
                        'clave_activacion', ''),
                    fecha_vencimiento=self.cleaned_data.get(
                        'fecha_vencimiento'),
                    numero_licencias=self.cleaned_data.get(
                        'numero_licencias', 1)
                )

            return software
        except Exception as e:
            # Capturar y reenviar la excepción para que se pueda mostrar en la vista
            print(f"Error guardando software: {str(e)}")
            raise
