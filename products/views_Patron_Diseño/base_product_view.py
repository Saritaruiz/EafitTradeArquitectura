# products/views/base_product_view.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin

class BaseProductView(LoginRequiredMixin, View):
    """
    Base class para vistas CRUD de Product.
    Define la estructura (Template Method) y hooks que las subclases deben
    implementar o sobrescribir.
    """
    model = None
    form_class = None
    template_name = None
    success_url = 'home'  # nombre de la url o path

    def get_object(self, pk=None):
        if pk is None:
            return None
        return get_object_or_404(self.model, pk=pk)

    def has_permission(self, request, obj=None):
        """
        Hook: sobrescribir para permisos adicionales.
        Por defecto devuelve True (permite) si no hay objeto o si el usuario es staff.
        """
        if obj is None:
            return True
        # ejemplo por defecto: el vendedor (seller) es el owner
        owner = getattr(obj, 'seller', None)
        return owner is None or owner == request.user or request.user.is_staff

    def get_context(self, **kwargs):
        return kwargs

    # GET handler por defecto (render form o confirm)
    def get(self, request, *args, **kwargs):
        obj = self.get_object(kwargs.get('pk') or kwargs.get('product_id'))
        context = self.get_context(obj=obj, **kwargs)
        return render(request, self.template_name, context)

    # POST handler: delega en hook `handle_post`
    def post(self, request, *args, **kwargs):
        obj = self.get_object(kwargs.get('pk') or kwargs.get('product_id'))
        if not self.has_permission(request, obj):
            return HttpResponseForbidden("No tienes permiso para realizar esta acción.")
        return self.handle_post(request, obj=obj, *args, **kwargs)

    def handle_post(self, request, obj=None, *args, **kwargs):
        """
        Hook obligatorio para que la subclase procese POST.
        Debe devolver un HttpResponse (redirect/render).
        """
        raise NotImplementedError("handle_post debe ser implementada en la subclase")

    def add_messages(self, level, message):
        messages.add_message(self.request, level, message)
