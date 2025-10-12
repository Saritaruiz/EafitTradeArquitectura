from django.db import models

class FoodType(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Tipo de comida')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Tipo de comida'
        verbose_name_plural = 'Tipos de comida'
