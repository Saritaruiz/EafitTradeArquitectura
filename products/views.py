from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from .models import Product, Comment, Favorite, ChatQuery
from seller_profiles.models import SellerProfile
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ProductForm, CommentForm, CustomUserCreationForm
from django.views.decorators.http import require_POST
from django.conf import settings
import urllib.parse
from django.http import JsonResponse
from seller_profiles.models import SellerProfile, ProfileClick
from django.contrib.auth.models import User
from .gemini_processor import GeminiProcessor
import json
import logging

# Importar pyngrok para poder iniciar ngrok desde Django
from pyngrok import ngrok, conf

# Importar el sistema de notificaciones con Inversión de Dependencias
from .notifications.manager import NotificationService

# Configurar el logger para ngrok
logger = logging.getLogger(__name__)

# Esta función inicia ngrok y devuelve la URL pública
def start_ngrok():
    try:
        # Puedes establecer tu token de autenticación aquí
        # (Reemplaza 'TU_TOKEN_AQUI' con tu token real de ngrok)
        # ngrok.set_auth_token('TU_TOKEN_AQUI')
        
        # Eliminar cualquier túnel existente
        for tunnel in ngrok.get_tunnels():
            ngrok.disconnect(tunnel.public_url)
        
        # Iniciar un nuevo túnel HTTP hacia el puerto 8000 (donde se ejecuta Django)
        http_tunnel = ngrok.connect(8000)
        
        # Registrar la URL pública en los logs
        logger.info(f"Ngrok iniciado: {http_tunnel.public_url}")
        
        return http_tunnel.public_url
    except Exception as e:
        logger.error(f"Error al iniciar ngrok: {str(e)}")
        return None

# Puedes llamar a esta función en alguna vista para iniciar ngrok
def start_ngrok_view(request):
    if request.user.is_superuser:  # Solo permitir a administradores
        url = start_ngrok()
        if url:
            messages.success(request, f"Ngrok iniciado en: {url}")
        else:
            messages.error(request, "Error al iniciar ngrok")
    else:
        messages.error(request, "No tienes permisos para realizar esta acción")
    return redirect('home')

def home(request):
    products = Product.objects.all()
    
    # Búsqueda por nombre
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    # Filtro por categoría
    category = request.GET.get('category', '')
    if category:
        products = products.filter(category=category)
    
    # Filtro por tipo de comida
    food_type = request.GET.get('food_type', '')
    if category == 'Comida' and food_type:
        products = products.filter(food_type=food_type)
    
    # Filtro por rango de precios
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    
    if min_price:
        try:
            min_price = float(min_price)
            products = products.filter(price__gte=min_price)
        except ValueError:
            pass
    
    if max_price:
        try:
            max_price = float(max_price)
            products = products.filter(price__lte=max_price)
        except ValueError:
            pass
    
    # Ordenar por fecha de publicación
    products = products.order_by('-published_at')
    
    # Obtener favoritos del usuario
    user_favorites = []
    if request.user.is_authenticated:
        user_favorites = Favorite.objects.filter(user=request.user).values_list('product_id', flat=True)
    
    context = {
        'products': products,
        'user_favorites': user_favorites,
        'search_query': search_query,
        'selected_category': category,
        'selected_food_type': food_type,
        'min_price': min_price,
        'max_price': max_price,
        'categories': Product.CATEGORY_CHOICES,
        'food_types': Product.FOOD_TYPE_CHOICES,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, 'products/home.html', context)

# @login_required
# def add_product(request):
#     if request.method == 'POST':
#         form = ProductForm(request.POST, request.FILES)
#         if form.is_valid():
#             product = form.save(commit=False)
#             product.seller = request.user
#             product.save()
#             messages.success(request, '¡Producto agregado exitosamente!')
#             return redirect('home')
#         else:
#             messages.error(request, 'Por favor corrige los errores en el formulario.')
#     else:
#         form = ProductForm()
    
#     return render(request, 'products/add_product.html', {'form': form})


# @login_required
# def edit_product(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
    
#     # Verificar que el usuario sea el dueño del producto
#     if product.seller != request.user:
#         return HttpResponseForbidden("No tienes permiso para editar este producto.")
    
#     if request.method == 'POST':
#         form = ProductForm(request.POST, request.FILES, instance=product)
#         if form.is_valid():
#             form.save()
#             messages.success(request, '¡Producto actualizado exitosamente!')
#             return redirect('home')
#         else:
#             messages.error(request, 'Por favor corrige los errores en el formulario.')
#     else:
#         form = ProductForm(instance=product)
    
#     return render(request, 'products/edit_product.html', {
#         'form': form,
#         'product': product
#     })

# @login_required
# def delete_product(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
    
#     # Verificar que el usuario sea el dueño del producto
#     if product.seller != request.user:
#         return HttpResponseForbidden("No tienes permiso para eliminar este producto.")
    
#     if request.method == 'POST':
#         product.delete()
#         messages.success(request, '¡Producto eliminado exitosamente!')
#         return redirect('home')
    
#     return render(request, 'products/confirm_delete.html', {'product': product})


@login_required
@require_POST
def add_comment(request, product_id):
    """
    Agrega un nuevo comentario a un producto e implementa Inversión de Dependencias
    para el sistema de notificaciones.
    
    Esta función demuestra cómo el código cliente (esta vista) depende de la
    abstracción (NotificationService) en lugar de implementaciones concretas
    de notificadores específicos.
    """
    product = get_object_or_404(Product, id=product_id)
    form = CommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.product = product
        comment.user = request.user
        comment.save()
        
        # Aplicación del principio de Inversión de Dependencias
        # El código no depende de EmailNotifier o WhatsAppNotifier específicos,
        # sino de la abstracción NotificationService
        try:
            notification_service = NotificationService()
            
            # Solo notificar si el comentador no es el vendedor
            if comment.user != product.seller:
                # El servicio internamente usa el patrón DIP para decidir
                # qué notificadores usar según la configuración
                results = notification_service.notify_new_comment(comment, request)
                
                # Log de resultados para debugging
                successful_channels = [channel for channel, success in results.items() if success]
                if successful_channels:
                    logger.info(f"Notificación de comentario enviada por: {', '.join(successful_channels)}")
                
        except Exception as e:
            # Error en notificaciones no debe afectar la funcionalidad principal
            logger.error(f"Error en sistema de notificaciones: {str(e)}")
        
        messages.success(request, '¡Comentario agregado exitosamente!')
    else:
        messages.error(request, 'Error al agregar el comentario. Por favor, inténtalo de nuevo.')
    
    return redirect('product_detail', product_id=product_id)

@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    if comment.user != request.user:
        messages.error(request, 'No tienes permiso para eliminar este comentario.')
        return redirect('product_detail', product_id=comment.product.id)
    
    product_id = comment.product.id
    comment.delete()
    messages.success(request, 'Comentario eliminado exitosamente.')
    
    return redirect('product_detail', product_id=product_id)

@login_required
@require_POST
def toggle_favorite(request, product_id):
    """
    Alterna el estado de favorito de un producto e implementa notificaciones
    usando el principio de Inversión de Dependencias.
    
    Demuestra cómo diferentes tipos de notificaciones (in-app, WhatsApp)
    pueden ser manejadas por el mismo código sin acoplar a implementaciones específicas.
    """
    product = get_object_or_404(Product, id=product_id)
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if not created:
        favorite.delete()
        return JsonResponse({'status': 'removed'})
    
    # Aplicar Inversión de Dependencias para notificaciones
    try:
        notification_service = NotificationService()
        
        # Solo notificar si el usuario no es el vendedor
        if request.user != product.seller:
            # El servicio decide internamente qué canales usar
            # Preferimos notificaciones inmediatas (in-app, WhatsApp)
            results = notification_service.notify_new_favorite(favorite, request)
            
            # Opcional: incluir información de canales exitosos en la respuesta
            successful_channels = [channel for channel, success in results.items() if success]
            logger.info(f"Notificación de favorito enviada por: {', '.join(successful_channels)}")
            
    except Exception as e:
        # Error en notificaciones no debe afectar la funcionalidad principal
        logger.error(f"Error en notificación de favorito: {str(e)}")
    
    return JsonResponse({'status': 'added'})

@login_required
def favorites_list(request):
    favorites = Favorite.objects.filter(user=request.user)
    if not favorites.exists():
        messages.info(request, 'No tienes productos favoritos. Explora la tienda para agregar algunos.')
    return render(request, 'products/favorites.html', {
        'favorites': favorites
    })

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    comments = product.comments.all().order_by('-created_at')
    comment_form = CommentForm() if request.user.is_authenticated else None
    
    # Verify if product is in favorites
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, product=product).exists()
    
    # Get seller profile and prepare WhatsApp link if available
    seller_profile = None
    whatsapp_link = None
    try:
        seller_profile = product.seller.seller_profile
        if seller_profile and seller_profile.whatsapp:
            # Usar el método get_whatsapp_link del modelo SellerProfile
            whatsapp_link = seller_profile.get_whatsapp_link(product.name)
    except SellerProfile.DoesNotExist:
        pass
    
    return render(request, 'products/product_detail.html', {
        'product': product,
        'comments': comments,
        'comment_form': comment_form,
        'is_favorite': is_favorite,
        'seller_profile': seller_profile,
        'whatsapp_link': whatsapp_link
    })

def register_whatsapp_click(request):
    """
    Registra clicks en WhatsApp y envía notificación de interés.
    
    Esta función demuestra el patrón DIP permitiendo notificaciones
    flexibles según el contexto (preferencia por WhatsApp para interés directo).
    """
    if request.method == 'POST':
        profile_id = request.POST.get('profile_id')
        product_id = request.POST.get('product_id')  # Nuevo parámetro
        
        try:
            profile = SellerProfile.objects.get(id=profile_id)
            ProfileClick.objects.create(
                profile=profile,
                user=request.user if request.user.is_authenticated else None
            )
            
            # Si hay información del producto y usuario autenticado, notificar interés
            if product_id and request.user.is_authenticated:
                try:
                    product = Product.objects.get(id=product_id)
                    
                    # Demostración de flexibilidad del patrón DIP:
                    # Crear servicio con preferencia específica por WhatsApp
                    from .notifications.manager import NotificationManager, WhatsAppNotifier, LogNotifier
                    
                    # Inyección de dependencia específica para este caso
                    whatsapp_manager = NotificationManager([
                        WhatsAppNotifier(),  # Primera prioridad
                        LogNotifier()        # Fallback
                    ])
                    
                    notification_service = NotificationService(whatsapp_manager)
                    notification_service.notify_product_interest(product, request.user, request)
                    
                except Product.DoesNotExist:
                    pass  # Producto no encontrado, continuar sin notificar
                except Exception as e:
                    logger.error(f"Error notificando interés en producto: {str(e)}")
            
            return JsonResponse({'success': True})
            
        except SellerProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Perfil no encontrado'}, status=404)
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


@login_required
def notification_demo(request):
    """
    Vista de demostración que muestra la flexibilidad del patrón de Inversión de Dependencias.
    
    Esta vista permite a los usuarios probar diferentes canales de notificación
    y ver cómo el mismo código puede usar diferentes implementaciones sin cambios.
    """
    if request.method == 'POST':
        channel = request.POST.get('channel', 'default')
        message = request.POST.get('message', 'Mensaje de prueba del sistema de notificaciones')
        
        try:
            from .notifications.manager import (
                NotificationManager, NotificationService,
                EmailNotifier, WhatsAppNotifier, LogNotifier, InAppNotifier
            )
            
            # Demostración de diferentes configuraciones usando DIP
            if channel == 'email':
                # Configuración específica para email
                email_manager = NotificationManager([EmailNotifier()])
                service = NotificationService(email_manager)
                results = service._get_manager().send_notification(request.user, message)
                
            elif channel == 'whatsapp':
                # Configuración específica para WhatsApp
                whatsapp_manager = NotificationManager([WhatsAppNotifier(), LogNotifier()])
                service = NotificationService(whatsapp_manager)
                results = service._get_manager().send_notification(request.user, message)
                
            elif channel == 'multi':
                # Configuración multi-canal con fallbacks
                multi_manager = NotificationManager([
                    InAppNotifier(request),    # Inmediato
                    WhatsAppNotifier(),        # Rápido
                    EmailNotifier(),           # Confiable
                    LogNotifier()              # Fallback
                ])
                service = NotificationService(multi_manager)
                results = service._get_manager().send_notification(request.user, message)
                
            else:
                # Configuración por defecto (demuestra factory pattern)
                service = NotificationService()
                results = service._get_manager(request).send_notification(request.user, message)
            
            # Mostrar resultados al usuario
            successful = [ch for ch, success in results.items() if success]
            failed = [ch for ch, success in results.items() if not success]
            
            if successful:
                messages.success(request, f"✅ Notificación enviada por: {', '.join(successful)}")
            if failed:
                messages.warning(request, f"❌ Falló en canales: {', '.join(failed)}")
                
        except Exception as e:
            messages.error(request, f"Error en demostración: {str(e)}")
    
    return render(request, 'products/notification_demo.html', {
        'user': request.user
    })

@require_POST
def chat_search(request):
    """
    Process a natural language query using Gemini API and return search results
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False, 
            'error': 'Debes iniciar sesión para usar el chatbot'
        }, status=403)
        
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        query = request.POST.get('query', '').strip()
        
        if not query:
            return JsonResponse({'success': False, 'error': 'La consulta no puede estar vacía'})
        
        # Process the query using the Gemini API
        processor = GeminiProcessor()
        result = processor.process_query(query)
        
        # Store the query in the database
        chat_query = ChatQuery(
            query=query,
            user=request.user,
            success=result.get('success', False)
        )
        
        if result.get('success', False):
            chat_query.processed_keywords = result.get('keywords', '')
            chat_query.save()
            
            # Split the keywords and filter products
            keywords = [k.strip() for k in result.get('keywords', '').split(',')]
            products = Product.objects.all()
            
            # Filter products by keywords
            from django.db.models import Q
            query_filters = Q()
            
            for keyword in keywords:
                if keyword:
                    query_filters |= Q(name__icontains=keyword)
                    query_filters |= Q(description__icontains=keyword)
                    query_filters |= Q(category__icontains=keyword)
                    
                    # If the category is "Comida", also search in food_type
                    if keyword.lower() in [ft[0].lower() for ft in Product.FOOD_TYPE_CHOICES]:
                        query_filters |= Q(food_type__icontains=keyword)
            
            products = products.filter(query_filters).distinct().order_by('-published_at')
            
            # Serialize the products for JSON response
            products_data = []
            for product in products:
                product_data = {
                    'id': product.id,
                    'name': product.name,
                    'price': float(product.price),
                    'category': product.get_category_display(),
                    'image_url': product.image.url if product.image else None,
                    'available': product.available,
                    'description': product.description[:100] + '...' if len(product.description) > 100 else product.description,
                    'detail_url': f'/product/{product.id}/'
                }
                products_data.append(product_data)
            
            return JsonResponse({
                'success': True,
                'keywords': result.get('keywords', ''),
                'products': products_data,
                'count': len(products_data)
            })
        else:
            # Save the failed query anyway for analysis
            chat_query.save()
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Error al procesar la consulta')
            })
    
    return JsonResponse({'success': False, 'error': 'Petición inválida'})

# Create your views here.