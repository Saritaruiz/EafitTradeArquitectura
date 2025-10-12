# products/views/delete_product_view.py
from django.shortcuts import redirect, render
from .base_product_view import BaseProductView
from ..models import Product
from django.contrib import messages

class DeleteProductView(BaseProductView):
    model = Product
    template_name = 'products/confirm_delete.html'
    success_url = 'home'

    def get(self, request, product_id, *args, **kwargs):
        product = self.get_object(product_id)
        return render(request, self.template_name, self.get_context(product=product))

    def handle_post(self, request, obj=None, *args, **kwargs):
        product = obj
        product.delete()
        messages.success(request, '¡Producto eliminado exitosamente!')
        return redirect(self.success_url)
