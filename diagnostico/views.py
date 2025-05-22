# Al principio del archivo diagnostico/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import formset_factory
from django.db import transaction, models
from .models import Cuestionario, Pregunta, Diagnostico, Respuesta, IndicadorDiagnostico
from .forms import CuestionarioForm, PreguntaForm, PreguntaInlineFormSet, DiagnosticoForm, RespuestaForm
from usuarios.models import LogActividad, Departamento


@login_required
def index(request):
    """Vista principal del módulo de diagnóstico"""
    return render(request, 'diagnostico/index.html')

# Cuestionario views


@login_required
def cuestionario_list(request):
    """Lista de cuestionarios"""
    cuestionarios = Cuestionario.objects.all().select_related('creado_por')

    # Filtros
    search = request.GET.get('search', '')
    activo = request.GET.get('activo', '')

    if search:
        cuestionarios = cuestionarios.filter(
            titulo__icontains=search) | cuestionarios.filter(descripcion__icontains=search)

    if activo:
        cuestionarios = cuestionarios.filter(activo=activo == 'true')

    return render(request, 'diagnostico/cuestionario_list.html', {
        'cuestionarios': cuestionarios,
        'search': search,
        'activo': activo
    })


@login_required
def cuestionario_create(request):
    """Crear cuestionario"""
    if request.method == 'POST':
        form = CuestionarioForm(request.POST)
        if form.is_valid():
            cuestionario = form.save(commit=False)
            cuestionario.creado_por = request.user
            cuestionario.save()

            # Registrar actividad
            LogActividad.objects.create(
                usuario=request.user,
                accion=f"Creación de cuestionario: {cuestionario.titulo}",
                detalles=f"Cuestionario ID: {cuestionario.id}"
            )

            messages.success(request, 'Cuestionario creado correctamente.')
            return redirect('cuestionario_detail', pk=cuestionario.id)
    else:
        form = CuestionarioForm()

    return render(request, 'diagnostico/cuestionario_form.html', {'form': form, 'is_new': True})


@login_required
def cuestionario_detail(request, pk):
    """Detalle de cuestionario"""
    cuestionario = get_object_or_404(Cuestionario, pk=pk)
    preguntas = Pregunta.objects.filter(
        cuestionario=cuestionario).order_by('orden')

    # Registrar actividad
    LogActividad.objects.create(
        usuario=request.user,
        accion=f"Consulta de cuestionario: {cuestionario.titulo}",
        detalles=f"Cuestionario ID: {cuestionario.id}"
    )

    return render(request, 'diagnostico/cuestionario_detail.html', {
        'cuestionario': cuestionario,
        'preguntas': preguntas
    })


@login_required
def cuestionario_update(request, pk):
    """Actualizar cuestionario"""
    cuestionario = get_object_or_404(Cuestionario, pk=pk)

    if request.method == 'POST':
        form = CuestionarioForm(request.POST, instance=cuestionario)
        formset = PreguntaInlineFormSet(request.POST, instance=cuestionario)

        if form.is_valid() and formset.is_valid():
            cuestionario = form.save()
            formset.save()

            # Registrar actividad
            LogActividad.objects.create(
                usuario=request.user,
                accion=f"Actualización de cuestionario: {cuestionario.titulo}",
                detalles=f"Cuestionario ID: {cuestionario.id}"
            )

            messages.success(
                request, 'Cuestionario actualizado correctamente.')
            return redirect('cuestionario_detail', pk=cuestionario.id)
    else:
        form = CuestionarioForm(instance=cuestionario)
        formset = PreguntaInlineFormSet(instance=cuestionario)

    return render(request, 'diagnostico/cuestionario_update.html', {
        'form': form,
        'formset': formset,
        'cuestionario': cuestionario
    })


@login_required
def cuestionario_delete(request, pk):
    """Eliminar cuestionario"""
    cuestionario = get_object_or_404(Cuestionario, pk=pk)

    if request.method == 'POST':
        titulo = cuestionario.titulo

        # Eliminar el cuestionario
        cuestionario.delete()

        # Registrar actividad
        LogActividad.objects.create(
            usuario=request.user,
            accion=f"Eliminación de cuestionario: {titulo}",
            detalles=f"ID: {pk}"
        )

        messages.success(
            request, f'Cuestionario "{titulo}" eliminado correctamente.')
        return redirect('cuestionario_list')

    return render(request, 'diagnostico/cuestionario_confirm_delete.html', {'cuestionario': cuestionario})

# Evaluación views


@login_required
def evaluacion_list(request):
    """Lista de evaluaciones"""
    diagnosticos = Diagnostico.objects.all().select_related(
        'departamento', 'responsable', 'cuestionario')

    # Filtros
    search = request.GET.get('search', '')
    departamento = request.GET.get('departamento', '')

    if search:
        diagnosticos = diagnosticos.filter(
            departamento__nombre__icontains=search
        ) | diagnosticos.filter(
            cuestionario__titulo__icontains=search
        )

    if departamento:
        diagnosticos = diagnosticos.filter(departamento_id=departamento)

    # AGREGAR DEPARTAMENTOS PARA EL DROPDOWN
    departamentos = Departamento.objects.all()

    return render(request, 'diagnostico/evaluacion_list.html', {
        'diagnosticos': diagnosticos,
        'search': search,
        'departamento': departamento,
        'departamentos': departamentos
    })


@login_required
def evaluacion_create(request):
    """Crear evaluación"""
    if request.method == 'POST':
        form = DiagnosticoForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                diagnostico = form.save(commit=False)
                diagnostico.responsable = request.user
                diagnostico.save()

                # Redireccionar a la página de respuestas
                return redirect('evaluacion_respuestas', pk=diagnostico.id)
    else:
        form = DiagnosticoForm()

    return render(request, 'diagnostico/evaluacion_form.html', {'form': form, 'is_new': True})


@login_required
def evaluacion_respuestas(request, pk):
    """Responder preguntas de evaluación"""
    diagnostico = get_object_or_404(Diagnostico, pk=pk)
    preguntas = Pregunta.objects.filter(
        cuestionario=diagnostico.cuestionario).order_by('orden')

    if request.method == 'POST':
        forms = []
        valid = True

        for pregunta in preguntas:
            prefix = f"pregunta_{pregunta.id}"
            form = RespuestaForm(
                request.POST, prefix=prefix, pregunta=pregunta)
            forms.append((pregunta, form))
            valid = valid and form.is_valid()

        if valid:
            with transaction.atomic():
                for pregunta, form in forms:
                    respuesta, created = Respuesta.objects.get_or_create(
                        diagnostico=diagnostico,
                        pregunta=pregunta,
                        defaults={
                            'valor_numerico': form.cleaned_data.get('valor_numerico'),
                            'valor_texto': form.cleaned_data.get('valor_texto')
                        }
                    )
                    if not created:
                        respuesta.valor_numerico = form.cleaned_data.get(
                            'valor_numerico')
                        respuesta.valor_texto = form.cleaned_data.get(
                            'valor_texto')
                        respuesta.save()

                # Calcular indicadores
                calcular_indicadores(diagnostico)

                # Registrar actividad
                LogActividad.objects.create(
                    usuario=request.user,
                    accion=f"Evaluación completada",
                    detalles=f"Departamento: {diagnostico.departamento.nombre}"
                )

                messages.success(
                    request, 'Evaluación completada correctamente.')
                return redirect('evaluacion_detail', pk=diagnostico.id)
    else:
        forms = []
        for pregunta in preguntas:
            try:
                respuesta = Respuesta.objects.get(
                    diagnostico=diagnostico, pregunta=pregunta)
                form = RespuestaForm(
                    instance=respuesta, prefix=f"pregunta_{pregunta.id}", pregunta=pregunta)
            except Respuesta.DoesNotExist:
                form = RespuestaForm(
                    prefix=f"pregunta_{pregunta.id}", pregunta=pregunta)
            forms.append((pregunta, form))

    return render(request, 'diagnostico/evaluacion_respuestas.html', {
        'diagnostico': diagnostico,
        'forms': forms
    })


@login_required
def evaluacion_detail(request, pk):
    """Detalle de evaluación"""
    diagnostico = get_object_or_404(Diagnostico, pk=pk)
    respuestas = Respuesta.objects.filter(
        diagnostico=diagnostico).select_related('pregunta')
    indicadores = IndicadorDiagnostico.objects.filter(diagnostico=diagnostico)

    # Registrar actividad
    LogActividad.objects.create(
        usuario=request.user,
        accion=f"Consulta de evaluación",
        detalles=f"Departamento: {diagnostico.departamento.nombre}"
    )

    return render(request, 'diagnostico/evaluacion_detail.html', {
        'diagnostico': diagnostico,
        'respuestas': respuestas,
        'indicadores': indicadores
    })


@login_required
def evaluacion_update(request, pk):
    """Actualizar evaluación"""
    diagnostico = get_object_or_404(Diagnostico, pk=pk)

    if request.method == 'POST':
        form = DiagnosticoForm(request.POST, instance=diagnostico)
        if form.is_valid():
            diagnostico = form.save()

            # Registrar actividad
            LogActividad.objects.create(
                usuario=request.user,
                accion=f"Actualización de evaluación",
                detalles=f"Departamento: {diagnostico.departamento.nombre}"
            )

            messages.success(
                request, 'Información de evaluación actualizada correctamente.')
            return redirect('evaluacion_detail', pk=diagnostico.id)
    else:
        form = DiagnosticoForm(instance=diagnostico)

    return render(request, 'diagnostico/evaluacion_form.html', {'form': form, 'diagnostico': diagnostico, 'is_new': False})

# Indicador views


@login_required
def indicador_list(request):
    """Lista de indicadores"""
    indicadores = IndicadorDiagnostico.objects.all().select_related(
        'diagnostico', 'diagnostico__departamento')

    # Filtros
    search = request.GET.get('search', '')
    departamento = request.GET.get('departamento', '')

    if search:
        indicadores = indicadores.filter(
            nombre__icontains=search
        ) | indicadores.filter(
            diagnostico__departamento__nombre__icontains=search
        )

    if departamento:
        indicadores = indicadores.filter(
            diagnostico__departamento_id=departamento)

    # AGREGAR DEPARTAMENTOS PARA EL DROPDOWN
    departamentos = Departamento.objects.all()

    return render(request, 'diagnostico/indicador_list.html', {
        'indicadores': indicadores,
        'search': search,
        'departamento': departamento,
        'departamentos': departamentos
    })


@login_required
def indicador_detail(request, pk):
    """Detalle de indicador"""
    indicador = get_object_or_404(IndicadorDiagnostico, pk=pk)

    # Registrar actividad
    LogActividad.objects.create(
        usuario=request.user,
        accion=f"Consulta de indicador: {indicador.nombre}",
        detalles=f"Departamento: {indicador.diagnostico.departamento.nombre}"
    )

    return render(request, 'diagnostico/indicador_detail.html', {'indicador': indicador})


def calcular_indicadores(diagnostico):
    """Calcular indicadores de diagnóstico"""
    # Eliminar indicadores existentes
    IndicadorDiagnostico.objects.filter(diagnostico=diagnostico).delete()

    # Obtener respuestas numéricas
    respuestas = Respuesta.objects.filter(
        diagnostico=diagnostico, valor_numerico__isnull=False)

    # Calcular nivel general
    if respuestas.exists():
        nivel_general = respuestas.aggregate(
            avg=models.Avg('valor_numerico'))['avg']
        diagnostico.nivel_general = nivel_general
        diagnostico.save()

    # Calcular indicadores por categoría
    categorias = Pregunta.objects.filter(
        cuestionario=diagnostico.cuestionario
    ).values_list('categoria', flat=True).distinct()

    for categoria in categorias:
        respuestas_categoria = Respuesta.objects.filter(
            diagnostico=diagnostico,
            pregunta__categoria=categoria,
            valor_numerico__isnull=False
        )

        if respuestas_categoria.exists():
            valor = respuestas_categoria.aggregate(
                avg=models.Avg('valor_numerico'))['avg']

            # Crear indicador
            IndicadorDiagnostico.objects.create(
                diagnostico=diagnostico,
                nombre=f"Nivel de {categoria}",
                valor=valor,
                descripcion=f"Indicador de {categoria}",
                recomendacion=generar_recomendacion(categoria, valor)
            )


def generar_recomendacion(categoria, valor):
    """Generar recomendaciones basadas en el valor del indicador"""
    if valor < 2:
        return f"El nivel de {categoria} es muy bajo. Se recomienda priorizar acciones inmediatas en esta área."
    elif valor < 3:
        return f"El nivel de {categoria} es bajo. Se recomienda implementar mejoras en esta área."
    elif valor < 4:
        return f"El nivel de {categoria} es moderado. Se recomienda continuar mejorando esta área."
    else:
        return f"El nivel de {categoria} es alto. Se recomienda mantener las buenas prácticas en esta área."
