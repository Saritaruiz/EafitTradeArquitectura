from abc import ABC, abstractmethod
from django.db.models import Count

class RankingStrategy(ABC):
    """Interfaz para estrategias de ranking/ordenamiento de productos."""
    @abstractmethod
    def apply(self, queryset):
        """Recibe un queryset de Product y devuelve un queryset ordenado."""
        raise NotImplementedError

class RecentStrategy(RankingStrategy):
    """Ordena por fecha de publicación descendente (más recientes primero)."""
    def apply(self, queryset):
        return queryset.order_by('-published_at')

class PriceAscStrategy(RankingStrategy):
    """Ordena por precio ascendente."""
    def apply(self, queryset):
        return queryset.order_by('price')

class PriceDescStrategy(RankingStrategy):
    """Ordena por precio descendente."""
    def apply(self, queryset):
        return queryset.order_by('-price')

class PopularityStrategy(RankingStrategy):
    """
    Ordena por popularidad. Intenta anotar con número de favoritos.
    Intenta los related_name 'favorite' o 'favorites' y, en último caso,
    cae a orden por fecha.
    """
    def apply(self, queryset):
        try:
            return queryset.annotate(fav_count=Count('favorite')).order_by('-fav_count','-published_at')
        except Exception:
            try:
                return queryset.annotate(fav_count=Count('favorites')).order_by('-fav_count','-published_at')
            except Exception:
                # Fallback si no hay relación configurada como se espera
                return queryset.order_by('-published_at')

class ProductSorter:
    """Contexto del patrón Strategy."""
    def __init__(self, strategy: RankingStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: RankingStrategy):
        """Permite cambiar la estrategia en tiempo de ejecución."""
        self._strategy = strategy

    def sort(self, queryset):
        """Ejecuta el algoritmo definido por la estrategia actual."""
        return self._strategy.apply(queryset)
