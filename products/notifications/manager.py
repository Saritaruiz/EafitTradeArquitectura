"""
Gestor de Notificaciones - Implementación del Principio de Inversión de Dependencias
===================================================================================

Este módulo contiene el NotificationManager que demuestra la aplicación práctica
del principio de Inversión de Dependencias (DIP).

Características clave:
1. Depende de la abstracción (NotificationInterface), no de implementaciones concretas
2. Permite inyección de dependencias para máxima flexibilidad
3. Soporte para múltiples canales de notificación
4. Estrategias de fallback automático
5. Configuración dinámica de notificadores

Autor: Equipo EafitTrade
Fecha: Octubre 2024
"""

from typing import List, Dict, Any, Optional
from django.contrib.auth.models import User
from django.conf import settings
import logging

# Importar la interfaz y implementaciones
from . import (
    NotificationInterface, 
    EmailNotifier, 
    WhatsAppNotifier, 
    LogNotifier, 
    InAppNotifier
)

logger = logging.getLogger('eafit_trade.notifications')


class NotificationManager:
    """
    Gestor principal de notificaciones que implementa Inversión de Dependencias.
    
    Este gestor demuestra el principio DIP al:
    1. Depender de NotificationInterface (abstracción) en lugar de clases concretas
    2. Permitir inyección de dependencias mediante el constructor
    3. Ser extensible sin modificar código existente
    
    Ejemplo de uso:
        # Inyección de dependencia específica
        email_notifier = EmailNotifier()
        manager = NotificationManager([email_notifier])
        
        # Configuración automática
        manager = NotificationManager.create_default()
        
        # Múltiples canales con fallback
        manager = NotificationManager([
            InAppNotifier(request),
            EmailNotifier(),
            LogNotifier()
        ])
    """
    
    def __init__(self, notifiers: List[NotificationInterface] = None):
        """
        Inicializa el gestor con los notificadores especificados.
        
        Args:
            notifiers: Lista de notificadores que implementan NotificationInterface
                      Si es None, se usará LogNotifier como fallback
        """
        self.notifiers = notifiers or [LogNotifier()]
        self._validate_notifiers()
    
    def _validate_notifiers(self):
        """
        Valida que todos los notificadores implementen la interfaz correcta.
        """
        for notifier in self.notifiers:
            if not isinstance(notifier, NotificationInterface):
                raise TypeError(
                    f"Notificador {type(notifier)} no implementa NotificationInterface"
                )
    
    @classmethod
    def create_default(cls, request=None) -> 'NotificationManager':
        """
        Factory method que crea un gestor con configuración por defecto.
        
        La configuración se basa en:
        1. Settings de Django
        2. Disponibilidad de servicios
        3. Entorno (desarrollo vs producción)
        
        Args:
            request: Request object para notificaciones in-app
            
        Returns:
            NotificationManager configurado con notificadores apropiados
        """
        notifiers = []
        
        # Notificaciones in-app siempre son primera prioridad si hay request
        if request:
            notifiers.append(InAppNotifier(request))
        
        # Email en producción si está configurado
        email_notifier = EmailNotifier()
        if email_notifier.is_available() and not settings.DEBUG:
            notifiers.append(email_notifier)
        
        # WhatsApp disponible siempre
        notifiers.append(WhatsAppNotifier())
        
        # Log como fallback (siempre disponible)
        notifiers.append(LogNotifier())
        
        return cls(notifiers)
    
    @classmethod
    def create_for_channel(cls, channel: str, **kwargs) -> 'NotificationManager':
        """
        Factory method para crear gestor con un canal específico.
        
        Args:
            channel: Nombre del canal ('email', 'whatsapp', 'log', 'in_app')
            **kwargs: Argumentos adicionales para el notificador
            
        Returns:
            NotificationManager con el notificador especificado
        """
        channel_map = {
            'email': EmailNotifier,
            'whatsapp': WhatsAppNotifier,
            'log': LogNotifier,
            'in_app': InAppNotifier
        }
        
        if channel not in channel_map:
            raise ValueError(f"Canal '{channel}' no soportado. Canales disponibles: {list(channel_map.keys())}")
        
        notifier_class = channel_map[channel]
        notifier = notifier_class(**kwargs)
        
        return cls([notifier])
    
    def send_notification(
        self, 
        user: User, 
        message: str, 
        context: Dict[str, Any] = None,
        preferred_channels: List[str] = None
    ) -> Dict[str, bool]:
        """
        Envía notificación usando los canales disponibles.
        
        Args:
            user: Usuario destino
            message: Mensaje a enviar
            context: Contexto adicional para personalización
            preferred_channels: Lista de canales preferidos en orden de prioridad
            
        Returns:
            Dict con resultado de cada canal {channel_name: success}
        """
        results = {}
        context = context or {}
        
        # Filtrar notificadores según canales preferidos
        active_notifiers = self._get_active_notifiers(preferred_channels)
        
        for notifier in active_notifiers:
            channel_name = notifier.get_channel_name()
            
            try:
                if notifier.is_available():
                    success = notifier.send_notification(user, message, context)
                    results[channel_name] = success
                    
                    if success:
                        logger.info(f"Notificación enviada exitosamente por {channel_name} a {user.username}")
                    else:
                        logger.warning(f"Fallo al enviar notificación por {channel_name} a {user.username}")
                else:
                    logger.info(f"Canal {channel_name} no disponible para {user.username}")
                    results[channel_name] = False
                    
            except Exception as e:
                logger.error(f"Error en canal {channel_name} para {user.username}: {str(e)}")
                results[channel_name] = False
        
        return results
    
    def _get_active_notifiers(self, preferred_channels: List[str] = None) -> List[NotificationInterface]:
        """
        Obtiene notificadores activos según canales preferidos.
        """
        if not preferred_channels:
            return self.notifiers
        
        # Ordenar notificadores según preferencias
        ordered_notifiers = []
        
        for channel in preferred_channels:
            for notifier in self.notifiers:
                if notifier.get_channel_name() == channel and notifier not in ordered_notifiers:
                    ordered_notifiers.append(notifier)
        
        # Agregar notificadores no especificados al final
        for notifier in self.notifiers:
            if notifier not in ordered_notifiers:
                ordered_notifiers.append(notifier)
        
        return ordered_notifiers
    
    def send_bulk_notification(
        self, 
        users: List[User], 
        message: str, 
        context: Dict[str, Any] = None
    ) -> Dict[str, Dict[str, bool]]:
        """
        Envía notificación a múltiples usuarios.
        
        Args:
            users: Lista de usuarios destino
            message: Mensaje a enviar
            context: Contexto adicional
            
        Returns:
            Dict {username: {channel: success}}
        """
        results = {}
        
        for user in users:
            user_results = self.send_notification(user, message, context)
            results[user.username] = user_results
        
        return results
    
    def get_available_channels(self) -> List[str]:
        """
        Retorna lista de canales disponibles.
        """
        return [
            notifier.get_channel_name() 
            for notifier in self.notifiers 
            if notifier.is_available()
        ]
    
    def add_notifier(self, notifier: NotificationInterface):
        """
        Agrega un notificador al gestor dinámicamente.
        
        Args:
            notifier: Instancia que implementa NotificationInterface
        """
        if not isinstance(notifier, NotificationInterface):
            raise TypeError("El notificador debe implementar NotificationInterface")
        
        if notifier not in self.notifiers:
            self.notifiers.append(notifier)
            logger.info(f"Notificador {notifier.get_channel_name()} agregado al gestor")
    
    def remove_notifier(self, channel_name: str):
        """
        Remueve un notificador por nombre de canal.
        
        Args:
            channel_name: Nombre del canal a remover
        """
        self.notifiers = [
            notifier for notifier in self.notifiers 
            if notifier.get_channel_name() != channel_name
        ]
        logger.info(f"Notificador {channel_name} removido del gestor")


class NotificationService:
    """
    Servicio de alto nivel que proporciona métodos específicos para
    diferentes tipos de notificaciones en EafitTrade.
    
    Este servicio encapsula la lógica de negocio específica de cada
    tipo de notificación, manteniendo la flexibilidad del patrón DIP.
    """
    
    def __init__(self, manager: NotificationManager = None):
        """
        Inicializa el servicio con un gestor específico.
        
        Args:
            manager: NotificationManager a usar. Si es None, se crea uno por defecto.
        """
        self.manager = manager
    
    def _get_manager(self, request=None) -> NotificationManager:
        """
        Obtiene el gestor de notificaciones, creando uno por defecto si es necesario.
        """
        if self.manager:
            return self.manager
        return NotificationManager.create_default(request)
    
    def notify_new_comment(self, comment, request=None):
        """
        Notifica al vendedor sobre un nuevo comentario en su producto.
        """
        seller = comment.product.seller
        commenter = comment.user
        product = comment.product
        
        message = f"¡Tienes un nuevo comentario de {commenter.get_full_name() or commenter.username}!"
        
        context = {
            'notification_type': 'comment',
            'product_name': product.name,
            'comment_text': comment.text,
            'comment_rating': comment.rating,
            'commenter': commenter.get_full_name() or commenter.username,
            'subject': f'Nuevo comentario en {product.name}'
        }
        
        manager = self._get_manager(request)
        return manager.send_notification(seller, message, context)
    
    def notify_new_favorite(self, favorite, request=None):
        """
        Notifica al vendedor sobre un nuevo favorito en su producto.
        """
        seller = favorite.product.seller
        user = favorite.user
        product = favorite.product
        
        message = f"¡{user.get_full_name() or user.username} marcó tu producto como favorito!"
        
        context = {
            'notification_type': 'favorite',
            'product_name': product.name,
            'user': user.get_full_name() or user.username,
            'subject': f'Nuevo favorito en {product.name}'
        }
        
        manager = self._get_manager(request)
        return manager.send_notification(seller, message, context)
    
    def notify_product_interest(self, product, interested_user, request=None):
        """
        Notifica al vendedor sobre interés en un producto.
        """
        seller = product.seller
        
        message = f"¡{interested_user.get_full_name() or interested_user.username} está interesado en tu producto!"
        
        context = {
            'notification_type': 'interest',
            'product_name': product.name,
            'interested_user': interested_user.get_full_name() or interested_user.username,
            'subject': f'Interés en {product.name}'
        }
        
        manager = self._get_manager(request)
        return manager.send_notification(seller, message, context, preferred_channels=['in_app', 'whatsapp'])
    
    def notify_low_stock(self, product):
        """
        Notifica al vendedor sobre stock bajo (funcionalidad futura).
        """
        seller = product.seller
        
        message = f"Tu producto '{product.name}' tiene stock bajo."
        
        context = {
            'notification_type': 'stock',
            'product_name': product.name,
            'subject': f'Stock bajo: {product.name}'
        }
        
        manager = self._get_manager()
        return manager.send_notification(seller, message, context, preferred_channels=['email', 'in_app'])