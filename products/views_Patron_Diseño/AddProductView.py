# products/views/add_product_view.py
from django.shortcuts import redirect, render
from .base_product_view import BaseProductView
from ..models import Product
from ..forms import ProductForm
from django.contrib import messages

class AddProductView(BaseProductView):
    model = Product
    form_class = ProductForm
    template_name = 'products/add_product.html'
    success_url = 'home'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, self.get_context(form=form))

    def handle_post(self, request, obj=None, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            messages.success(request, '¡Producto agregado exitosamente!')
            return redirect(self.success_url)
        messages.error(request, 'Por favor corrige los errores en el formulario.')
        return render(request, self.template_name, self.get_context(form=form))
