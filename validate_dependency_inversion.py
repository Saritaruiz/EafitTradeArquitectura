#!/usr/bin/env python3
"""
Script de Validación - Inversión de Dependencias
===============================================

Este script valida que la implementación del principio de Inversión de Dependencias
funcione correctamente en el sistema de notificaciones de EafitTrade.

Uso:
    python validate_dependency_inversion.py
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eafit_trade.settings')
django.setup()

from django.contrib.auth.models import User
from products.notifications import (
    NotificationInterface, 
    EmailNotifier, 
    WhatsAppNotifier, 
    LogNotifier, 
    InAppNotifier
)
from products.notifications.manager import NotificationManager, NotificationService


class TestNotifier(NotificationInterface):
    """Notificador de prueba para validar el patrón DIP."""
    
    def __init__(self):
        self.sent_notifications = []
        self.available = True
    
    def send_notification(self, user, message, context=None):
        self.sent_notifications.append({
            'user': user.username,
            'message': message,
            'context': context
        })
        return True
    
    def is_available(self):
        return self.available
    
    def get_channel_name(self):
        return 'test'


def test_interface_implementation():
    """Valida que todas las implementaciones cumplan con la interfaz."""
    print("🔍 Validando implementaciones de NotificationInterface...")
    
    notifiers = [
        EmailNotifier(),
        WhatsAppNotifier(),
        LogNotifier(),
        TestNotifier()
    ]
    
    for notifier in notifiers:
        assert isinstance(notifier, NotificationInterface), f"{type(notifier)} no implementa NotificationInterface"
        assert hasattr(notifier, 'send_notification'), f"{type(notifier)} falta send_notification"
        assert hasattr(notifier, 'is_available'), f"{type(notifier)} falta is_available"
        assert hasattr(notifier, 'get_channel_name'), f"{type(notifier)} falta get_channel_name"
        
        # Validar que los métodos sean callable
        assert callable(notifier.send_notification), f"send_notification no es callable en {type(notifier)}"
        assert callable(notifier.is_available), f"is_available no es callable en {type(notifier)}"
        assert callable(notifier.get_channel_name), f"get_channel_name no es callable en {type(notifier)}"
    
    print("✅ Todas las implementaciones cumplen con NotificationInterface")


def test_dependency_injection():
    """Valida que el gestor funcione con diferentes notificadores (DIP)."""
    print("🔄 Validando inyección de dependencias...")
    
    # Crear usuario de prueba
    test_user = User(username='testuser', email='test@eafit.edu.co')
    
    # Test con notificador específico
    test_notifier = TestNotifier()
    manager = NotificationManager([test_notifier])
    
    result = manager.send_notification(test_user, "Mensaje de prueba DIP")
    
    assert 'test' in result, "No se encontró resultado del notificador test"
    assert result['test'] == True, "La notificación test no fue exitosa"
    assert len(test_notifier.sent_notifications) == 1, "No se registró la notificación"
    assert test_notifier.sent_notifications[0]['user'] == 'testuser', "Usuario incorrecto"
    assert test_notifier.sent_notifications[0]['message'] == "Mensaje de prueba DIP", "Mensaje incorrecto"
    
    print("✅ Inyección de dependencias funciona correctamente")


def test_multiple_notifiers():
    """Valida que el gestor maneje múltiples notificadores."""
    print("📡 Validando múltiples notificadores...")
    
    test_user = User(username='multiuser', email='multi@eafit.edu.co')
    
    # Crear múltiples notificadores
    test_notifier1 = TestNotifier()
    test_notifier2 = TestNotifier()
    test_notifier2.get_channel_name = lambda: 'test2'  # Cambiar nombre del canal
    
    manager = NotificationManager([test_notifier1, test_notifier2])
    results = manager.send_notification(test_user, "Mensaje multi-canal")
    
    assert len(results) == 2, f"Se esperaban 2 resultados, se obtuvieron {len(results)}"
    assert 'test' in results, "Falta resultado del primer notificador"
    assert 'test2' in results, "Falta resultado del segundo notificador"
    assert all(results.values()), "No todos los notificadores fueron exitosos"
    
    print("✅ Múltiples notificadores funcionan correctamente")


def test_factory_patterns():
    """Valida que los factory methods funcionen."""
    print("🏭 Validando factory patterns...")
    
    # Test configuración por defecto
    default_manager = NotificationManager.create_default()
    channels = default_manager.get_available_channels()
    assert len(channels) > 0, "No hay canales disponibles en configuración por defecto"
    
    # Test configuración por canal específico
    log_manager = NotificationManager.create_for_channel('log')
    log_channels = log_manager.get_available_channels()
    assert 'log' in log_channels, "Canal log no está disponible"
    assert len(log_channels) == 1, "Debería haber solo un canal (log)"
    
    print("✅ Factory patterns funcionan correctamente")


def test_service_integration():
    """Valida que el servicio de alto nivel funcione."""
    print("🎯 Validando integración del servicio...")
    
    test_notifier = TestNotifier()
    manager = NotificationManager([test_notifier])
    service = NotificationService(manager)
    
    # Simular objetos necesarios
    class MockComment:
        def __init__(self):
            self.product = MockProduct()
            self.user = User(username='commenter')
            self.text = "Gran producto!"
            self.rating = 5
    
    class MockProduct:
        def __init__(self):
            self.seller = User(username='seller', email='seller@eafit.edu.co')
            self.name = "Producto de prueba"
    
    # Test notificación de comentario
    comment = MockComment()
    results = service.notify_new_comment(comment)
    
    assert len(test_notifier.sent_notifications) == 1, "No se registró la notificación del comentario"
    notification = test_notifier.sent_notifications[0]
    assert 'commenter' in notification['message'], "El mensaje no incluye el nombre del comentador"
    assert notification['context']['notification_type'] == 'comment', "Tipo de notificación incorrecto"
    
    print("✅ Integración del servicio funciona correctamente")


def test_error_handling():
    """Valida el manejo de errores."""
    print("🛡️ Validando manejo de errores...")
    
    class FailingNotifier(NotificationInterface):
        def send_notification(self, user, message, context=None):
            raise Exception("Error simulado")
        
        def is_available(self):
            return True
        
        def get_channel_name(self):
            return 'failing'
    
    test_user = User(username='erroruser')
    failing_notifier = FailingNotifier()
    manager = NotificationManager([failing_notifier])
    
    # Debería manejar errores gracefully
    try:
        results = manager.send_notification(test_user, "Test error handling")
        assert 'failing' in results, "Falta resultado del notificador que falla"
        assert results['failing'] == False, "Debería reportar fallo"
    except Exception as e:
        assert False, f"El gestor no manejó el error correctamente: {e}"
    
    print("✅ Manejo de errores funciona correctamente")


def run_all_tests():
    """Ejecuta todas las validaciones."""
    print("🚀 Iniciando validación de Inversión de Dependencias en EafitTrade")
    print("="*60)
    
    try:
        test_interface_implementation()
        test_dependency_injection()
        test_multiple_notifiers()
        test_factory_patterns()
        test_service_integration()
        test_error_handling()
        
        print("="*60)
        print("🎉 ¡TODAS LAS VALIDACIONES PASARON EXITOSAMENTE!")
        print("✅ El principio de Inversión de Dependencias está correctamente implementado")
        print("✅ El sistema de notificaciones es flexible y extensible")
        print("✅ La arquitectura cumple con los principios SOLID")
        
    except AssertionError as e:
        print("="*60)
        print(f"❌ VALIDACIÓN FALLIDA: {e}")
        sys.exit(1)
    except Exception as e:
        print("="*60)
        print(f"🚨 ERROR INESPERADO: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()