# products/views/edit_product_view.py
from django.shortcuts import render, redirect
from .base_product_view import BaseProductView
from ..models import Product
from ..forms import ProductForm
from django.contrib import messages

class EditProductView(BaseProductView):
    model = Product
    form_class = ProductForm
    template_name = 'products/edit_product.html'
    success_url = 'home'

    def get(self, request, product_id, *args, **kwargs):
        product = self.get_object(product_id)
        form = self.form_class(instance=product)
        return render(request, self.template_name, self.get_context(form=form, product=product))

    def handle_post(self, request, obj=None, *args, **kwargs):
        product = obj
        form = self.form_class(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Producto actualizado exitosamente!')
            return redirect(self.success_url)
        messages.error(request, 'Por favor corrige los errores en el formulario.')
        return render(request, self.template_name, self.get_context(form=form, product=product))
