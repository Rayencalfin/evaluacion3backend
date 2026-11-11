from django.shortcuts import render


def inicio(request):
    """Muestra la página pública de inicio de Rentis."""
    return render(request, 'core/inicio.html')