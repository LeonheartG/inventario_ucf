# inventario/forms.py
from django import forms
from .models import Activo, Hardware, Proveedor, Software
from usuarios.models import Departamento


class HardwareForm(forms.ModelForm):
    nombre = forms.CharField(max_length=200, required=True, label='Nombre')
    descripcion = forms.CharField(
        widget=forms.Textarea, required=False, label='Descripción')
    fecha_adquisicion = forms.DateField(widget=forms.DateInput(
        attrs={'type': 'date'}), label='Fecha de adquisición')
    valor_adquisicion = forms.DecimalField(
        max_digits=10, decimal_places=2, label='Valor de adquisición')
    estado = forms.ChoiceField(choices=Activo.ESTADO_CHOICES, label='Estado')
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(), label='Departamento')
    ubicacion = forms.CharField(
        max_length=100, required=False, label='Ubicación')
    imagen = forms.ImageField(required=False, label='Imagen')

    marca = forms.CharField(max_length=100, required=True, label='Marca')
    modelo = forms.CharField(max_length=100, required=True, label='Modelo')
    numero_serie = forms.CharField(
        max_length=100, required=True, label='Número de serie')
    especificaciones = forms.CharField(
        widget=forms.Textarea, required=False, label='Especificaciones')
    fecha_garantia = forms.DateField(widget=forms.DateInput(
        attrs={'type': 'date'}), required=False, label='Fecha de garantía')
    proveedor = forms.ModelChoiceField(
        queryset=Proveedor.objects.all(), required=False, label='Proveedor')
    periodicidad_mantenimiento = forms.IntegerField(
        initial=180, label='Periodicidad de mantenimiento (días)')

    class Meta:
        model = Hardware
        fields = []  # No usamos los campos del modelo directamente, ya que trabajamos con dos modelos

    def save(self, commit=True, user=None):
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

            if self.cleaned_data['imagen']:
                activo.imagen = self.cleaned_data['imagen']

            if user:
                activo.actualizado_por = user

            activo.save()
        else:
            activo = Activo.objects.create(
                tipo='hardware',
                nombre=self.cleaned_data['nombre'],
                descripcion=self.cleaned_data['descripcion'],
                fecha_adquisicion=self.cleaned_data['fecha_adquisicion'],
                valor_adquisicion=self.cleaned_data['valor_adquisicion'],
                estado=self.cleaned_data['estado'],
                departamento=self.cleaned_data['departamento'],
                ubicacion=self.cleaned_data['ubicacion'],
                imagen=self.cleaned_data['imagen'] if self.cleaned_data['imagen'] else None,
                creado_por=user,
                actualizado_por=user
            )

        # Ahora creamos o actualizamos el hardware
        if activo_id:
            hardware = self.instance
            hardware.marca = self.cleaned_data['marca']
            hardware.modelo = self.cleaned_data['modelo']
            hardware.numero_serie = self.cleaned_data['numero_serie']
            hardware.especificaciones = self.cleaned_data['especificaciones']
            hardware.fecha_garantia = self.cleaned_data['fecha_garantia']
            hardware.proveedor = self.cleaned_data['proveedor']
            hardware.periodicidad_mantenimiento = self.cleaned_data['periodicidad_mantenimiento']
            hardware.save()
        else:
            hardware = Hardware.objects.create(
                activo=activo,
                marca=self.cleaned_data['marca'],
                modelo=self.cleaned_data['modelo'],
                numero_serie=self.cleaned_data['numero_serie'],
                especificaciones=self.cleaned_data['especificaciones'],
                fecha_garantia=self.cleaned_data['fecha_garantia'],
                proveedor=self.cleaned_data['proveedor'],
                periodicidad_mantenimiento=self.cleaned_data['periodicidad_mantenimiento']
            )

        return hardware

# Agregar a inventario/forms.py


class SoftwareForm(forms.ModelForm):
    nombre = forms.CharField(max_length=200, required=True, label='Nombre')
    descripcion = forms.CharField(
        widget=forms.Textarea, required=False, label='Descripción')
    fecha_adquisicion = forms.DateField(widget=forms.DateInput(
        attrs={'type': 'date'}), label='Fecha de adquisición')
    valor_adquisicion = forms.DecimalField(
        max_digits=10, decimal_places=2, label='Valor de adquisición')
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
    proveedor = forms.ModelChoiceField(
        queryset=Proveedor.objects.all(), required=False, label='Proveedor')

    class Meta:
        model = Software
        fields = []  # No usamos los campos del modelo directamente, ya que trabajamos con dos modelos

    def save(self, commit=True, user=None):
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

            if self.cleaned_data['imagen']:
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
                imagen=self.cleaned_data['imagen'] if self.cleaned_data['imagen'] else None,
                creado_por=user,
                actualizado_por=user
            )

        # Ahora creamos o actualizamos el software
        if activo_id:
            software = self.instance
            software.version = self.cleaned_data['version']
            software.tipo_licencia = self.cleaned_data['tipo_licencia']
            software.clave_activacion = self.cleaned_data['clave_activacion']
            software.fecha_vencimiento = self.cleaned_data['fecha_vencimiento']
            software.numero_licencias = self.cleaned_data['numero_licencias']
            software.proveedor = self.cleaned_data['proveedor']
            software.save()
        else:
            software = Software.objects.create(
                activo=activo,
                version=self.cleaned_data['version'],
                tipo_licencia=self.cleaned_data['tipo_licencia'],
                clave_activacion=self.cleaned_data['clave_activacion'],
                fecha_vencimiento=self.cleaned_data['fecha_vencimiento'],
                numero_licencias=self.cleaned_data['numero_licencias'],
                proveedor=self.cleaned_data['proveedor']
            )

        return software
