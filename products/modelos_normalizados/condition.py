from django.db import models

class Condition(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Condición')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Condición'
        verbose_name_plural = 'Condiciones'
