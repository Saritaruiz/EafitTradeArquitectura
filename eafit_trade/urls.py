from django.contrib import admin
from django.urls import path, include, re_path
from products import views as products_views
from products.views_Patron_Diseño.AddProductView import AddProductView
from products.views_Patron_Diseño.EditProductView import EditProductView
from products.views_Patron_Diseño.DeleteProductView import DeleteProductView
from seller_profiles import views as profile_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),

    # Página principal
    path('', products_views.home, name='home'),

    # 🔹 NUEVAS vistas con Template Method Pattern
    path('add-product/', AddProductView.as_view(), name='add_product'),
    path('edit-product/<int:product_id>/', EditProductView.as_view(), name='edit_product'),
    path('delete-product/<int:product_id>/', DeleteProductView.as_view(), name='delete_product'),

    # Otras rutas existentes
    path('registrar-click-whatsapp/', products_views.register_whatsapp_click, name='register_whatsapp_click'),
    path('chat-search/', products_views.chat_search, name='chat_search'),

    path('demo/notifications/', products_views.notification_demo, name='notification_demo'),

    # Autenticación
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', products_views.register, name='register'),

    # Reset de contraseña
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),

    # Comentarios
    path('comment/add/<int:product_id>/', products_views.add_comment, name='add_comment'),
    path('comment/delete/<int:comment_id>/', products_views.delete_comment, name='delete_comment'),

    # Favoritos
    path('favorite/toggle/<int:product_id>/', products_views.toggle_favorite, name='toggle_favorite'),
    path('favorites/', products_views.favorites_list, name='favorites_list'),

    # Detalle de producto
    path('product/<int:product_id>/', products_views.product_detail, name='product_detail'),

    # Perfiles de vendedor
    path('profile/', profile_views.view_profile, name='view_profile'),
    path('profile/create/', profile_views.create_profile, name='create_profile'),
    path('profile/edit/', profile_views.edit_profile, name='edit_profile'),
    path('seller/<int:user_id>/', profile_views.public_profile, name='public_profile'),
    path('sellers/', profile_views.seller_list, name='seller_list'),

    # Ngrok
    path('start-ngrok/', products_views.start_ngrok_view, name='start_ngrok'),
]

# Configuración de archivos estáticos
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
