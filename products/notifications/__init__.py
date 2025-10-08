"""
Módulo de Notificaciones con Inversión de Dependencias
=====================================================

Este módulo implementa el principio de Inversión de Dependencias (DIP) para
el sistema de notificaciones de EafitTrade.

El patrón permite que el sistema de notificaciones sea flexible y extensible,
permitiendo cambiar entre diferentes canales de notificación (email, WhatsApp,
push notifications, etc.) sin modificar el código cliente.

Estructura:
- NotificationInterface: Abstracción que define el contrato
- Implementaciones concretas: EmailNotifier, WhatsAppNotifier, LogNotifier
- NotificationManager: Gestor que depende de la abstracción
- NotificationService: Servicio principal que coordina las notificaciones

Autor: Equipo EafitTrade
Fecha: Octubre 2024
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging
import urllib.parse

# Configurar logger específico para notificaciones
logger = logging.getLogger('eafit_trade.notifications')


class NotificationInterface(ABC):
    """
    Interfaz abstracta que define el contrato para todos los notificadores.
    
    Esta abstracción permite implementar el principio de Inversión de Dependencias,
    haciendo que el código cliente dependa de esta interfaz en lugar de 
    implementaciones concretas.
    """
    
    @abstractmethod
    def send_notification(self, user: User, message: str, context: Dict[str, Any] = None) -> bool:
        """
        Envía una notificación al usuario especificado.
        
        Args:
            user: Usuario destino de la notificación
            message: Mensaje a enviar
            context: Contexto adicional para personalizar la notificación
            
        Returns:
            bool: True si la notificación se envió exitosamente, False en caso contrario
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Verifica si el canal de notificación está disponible.
        
        Returns:
            bool: True si el canal está disponible, False en caso contrario
        """
        pass
    
    @abstractmethod
    def get_channel_name(self) -> str:
        """
        Retorna el nombre del canal de notificación.
        
        Returns:
            str: Nombre del canal (e.g., 'email', 'whatsapp', 'log')
        """
        pass


class EmailNotifier(NotificationInterface):
    """
    Implementación concreta del notificador por email.
    
    Utiliza el sistema de email de Django para enviar notificaciones
    por correo electrónico a los usuarios.
    """
    
    def __init__(self, from_email: str = None):
        self.from_email = from_email or settings.DEFAULT_FROM_EMAIL
    
    def send_notification(self, user: User, message: str, context: Dict[str, Any] = None) -> bool:
        """
        Envía notificación por email usando templates de Django.
        """
        try:
            if not user.email:
                logger.warning(f"Usuario {user.username} no tiene email configurado")
                return False
            
            context = context or {}
            context.update({
                'user': user,
                'message': message,
                'site_name': 'EafitTrade'
            })
            
            # Renderizar template HTML
            html_message = render_to_string('notifications/email_notification.html', context)
            plain_message = strip_tags(html_message)
            
            subject = context.get('subject', 'Notificación de EafitTrade')
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=self.from_email,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Email enviado exitosamente a {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email a {user.email}: {str(e)}")
            return False
    
    def is_available(self) -> bool:
        """
        Verifica si la configuración de email está disponible.
        """
        return hasattr(settings, 'EMAIL_HOST') and bool(settings.EMAIL_HOST)
    
    def get_channel_name(self) -> str:
        return 'email'


class WhatsAppNotifier(NotificationInterface):
    """
    Implementación concreta del notificador por WhatsApp.
    
    Genera enlaces de WhatsApp Web con mensajes preconfigurados
    que pueden ser enviados automáticamente o mostrados al usuario.
    """
    
    def send_notification(self, user: User, message: str, context: Dict[str, Any] = None) -> bool:
        """
        Genera enlace de WhatsApp y opcionalmente lo envía.
        """
        try:
            # Obtener número de WhatsApp del perfil del vendedor
            whatsapp_number = None
            if hasattr(user, 'seller_profile') and user.seller_profile.whatsapp:
                whatsapp_number = user.seller_profile.whatsapp
            
            if not whatsapp_number:
                logger.warning(f"Usuario {user.username} no tiene WhatsApp configurado")
                return False
            
            context = context or {}
            
            # Personalizar mensaje con contexto
            full_message = f"Hola {user.first_name or user.username}! {message}"
            if context.get('product_name'):
                full_message += f" Producto: {context['product_name']}"
            
            # Generar enlace de WhatsApp
            whatsapp_url = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(full_message)}"
            
            # En un entorno real, aquí podrías integrar con una API de WhatsApp Business
            # Por ahora, solo registramos la notificación
            logger.info(f"Notificación WhatsApp generada para {user.username}: {whatsapp_url}")
            
            # Opcional: Guardar el enlace en el contexto para uso posterior
            if context:
                context['whatsapp_url'] = whatsapp_url
            
            return True
            
        except Exception as e:
            logger.error(f"Error generando notificación WhatsApp para {user.username}: {str(e)}")
            return False
    
    def is_available(self) -> bool:
        """
        WhatsApp está siempre disponible si el usuario tiene número configurado.
        """
        return True
    
    def get_channel_name(self) -> str:
        return 'whatsapp'


class LogNotifier(NotificationInterface):
    """
    Implementación concreta del notificador por logs.
    
    Útil para desarrollo, testing y como fallback cuando otros
    canales no están disponibles.
    """
    
    def send_notification(self, user: User, message: str, context: Dict[str, Any] = None) -> bool:
        """
        Registra la notificación en los logs del sistema.
        """
        try:
            context_info = ""
            if context:
                context_info = f" | Contexto: {context}"
            
            log_message = f"NOTIFICACIÓN para {user.username} ({user.email}): {message}{context_info}"
            logger.info(log_message)
            
            # También imprimir en consola para desarrollo
            print(f"🔔 {log_message}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error en LogNotifier para {user.username}: {str(e)}")
            return False
    
    def is_available(self) -> bool:
        """
        El log notifier siempre está disponible.
        """
        return True
    
    def get_channel_name(self) -> str:
        return 'log'


class InAppNotifier(NotificationInterface):
    """
    Implementación concreta para notificaciones dentro de la aplicación.
    
    Utiliza el sistema de mensajes de Django para mostrar notificaciones
    en la interfaz web.
    """
    
    def __init__(self, request=None):
        self.request = request
    
    def send_notification(self, user: User, message: str, context: Dict[str, Any] = None) -> bool:
        """
        Crea una notificación in-app usando Django messages.
        """
        try:
            from django.contrib import messages
            
            if not self.request:
                logger.warning("InAppNotifier requiere request object para funcionar")
                return False
            
            # Personalizar mensaje según contexto
            if context and context.get('notification_type'):
                if context['notification_type'] == 'comment':
                    messages.success(self.request, f"💬 {message}")
                elif context['notification_type'] == 'favorite':
                    messages.info(self.request, f"⭐ {message}")
                else:
                    messages.info(self.request, f"🔔 {message}")
            else:
                messages.info(self.request, f"🔔 {message}")
            
            logger.info(f"Notificación in-app creada para {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error en InAppNotifier para {user.username}: {str(e)}")
            return False
    
    def is_available(self) -> bool:
        """
        Disponible si hay un request object.
        """
        return self.request is not None
    
    def get_channel_name(self) -> str:
        return 'in_app'