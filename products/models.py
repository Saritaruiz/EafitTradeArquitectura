from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import pytz

# Importar modelos normalizados
from .modelos_normalizados.category import Category
from .modelos_normalizados.condition import Condition
from .modelos_normalizados.foodType import FoodType

# Configuración para la zona horaria de Colombia (UTC-5)
COLOMBIA_TIMEZONE = pytz.timezone('America/Bogota')


class Product(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name='Nombre',
        help_text='Nombre del producto'
    )

    # Relaciones normalizadas en lugar de CharFields con choices
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='Categoría'
    )

    food_type = models.ForeignKey(
        FoodType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='food_products',
        verbose_name='Tipo de comida'
    )

    condition = models.ForeignKey(
        Condition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='condition_products',
        verbose_name='Condición'
    )

    description = models.TextField(
        verbose_name='Descripción',
        help_text='Describe tu producto detalladamente'
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name='Precio',
        help_text='Precio en pesos colombianos'
    )

    published_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de publicación'
    )

    image = models.ImageField(
        upload_to='products/',
        verbose_name='Imagen',
        help_text='Imagen del producto'
    )

    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Vendedor',
        related_name='products'
    )

    available = models.BooleanField(
        default=True,
        verbose_name='Disponible'
    )

    def clean(self):
        """Validación contextual: asegura coherencia entre categoría y otros campos."""
        if self.category and self.category.name == 'Comida':
            self.condition = None  # No aplica condición para productos de comida
        else:
            self.food_type = None  # No aplica tipo de comida para otras categorías

    def save(self, *args, **kwargs):
        """Valida antes de guardar el modelo."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """Representación legible del producto."""
        category_name = self.category.name if self.category else "Sin categoría"
        return f"{self.name} - {category_name}"

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['available']),
        ]

    @property
    def average_rating(self):
        """Calcula el promedio de calificaciones del producto."""
        comments = self.comments.all()
        if not comments:
            return 0
        return round(sum(comment.rating for comment in comments) / len(comments), 1)

    @property
    def total_ratings(self):
        """Cuenta el número total de calificaciones."""
        return self.comments.count()


class Comment(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField(
        max_length=500,
        verbose_name='Comentario'
    )
    rating = models.PositiveSmallIntegerField(
        verbose_name='Calificación',
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text='Calificación de 0 a 5 estrellas'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de publicación'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'

    def __str__(self):
        return f'Comentario de {self.user.username} en {self.product.name}'

    def save(self, *args, **kwargs):
        """Guarda la fecha de creación con zona horaria de Colombia."""
        if not self.pk:
            now_utc = timezone.now()
            self.created_at = now_utc.astimezone(COLOMBIA_TIMEZONE)
        super().save(*args, **kwargs)


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de agregado'
    )

    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-created_at']
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'

    def __str__(self):
        return f'{self.user.username} ♥ {self.product.name}'


class ChatQuery(models.Model):
    query = models.TextField(
        verbose_name='Consulta',
        help_text='Consulta en lenguaje natural del usuario'
    )
    processed_keywords = models.TextField(
        verbose_name='Palabras clave procesadas',
        help_text='Palabras clave extraídas por Gemini API',
        blank=True,
        null=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_queries'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de consulta'
    )
    success = models.BooleanField(
        default=True,
        verbose_name='Procesamiento exitoso'
    )

    class Meta:
        verbose_name = 'Consulta de chatbot'
        verbose_name_plural = 'Consultas de chatbot'
        ordering = ['-created_at']

    def __str__(self):
        return f"Consulta: {self.query[:50]}..."
