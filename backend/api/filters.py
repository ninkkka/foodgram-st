from distutils.util import strtobool

from django_filters import rest_framework as filters

from recipes.models import (Ingredient, Recipe, Tag,
                            Favorite, ShoppingCart)
from .constants import CHOICES_LIST


class IngredientFilter(filters.FilterSet):
    """Фильтрация по имени ингредиента (начало названия)."""
    name = filters.CharFilter(
        field_name='name', lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """Фильтрация рецептов: по автору, тегам, избранному и списку покупок."""
    author = filters.NumberFilter(
        field_name='author__id', lookup_expr='exact'
    )
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug', to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = filters.ChoiceFilter(
        choices=CHOICES_LIST, method='filter_favorited'
    )
    is_in_shopping_cart = filters.ChoiceFilter(
        choices=CHOICES_LIST,
        method='filter_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'author', 'tags',
            'is_favorited', 'is_in_shopping_cart'
        )

    def filter_favorited(self, queryset, name, value):
        """Фильтр по избранному блюда пользователя."""
        user = getattr(self.request, 'user', None)
        if not user or user.is_anonymous:
            return queryset.none()
        fav_recipes = Favorite.objects.filter(user=user).values_list(
            'recipe__id', flat=True
        )
        flag = strtobool(value)
        if flag:
            return queryset.filter(id__in=fav_recipes)
        return queryset.exclude(id__in=fav_recipes)

    def filter_in_shopping_cart(self, queryset, name, value):
        """Фильтр по списку покупок пользователя."""
        user = getattr(self.request, 'user', None)
        if not user or user.is_anonymous:
            return queryset.none()
        cart_recipes = ShoppingCart.objects.filter(
            user=user
        ).values_list('recipe__id', flat=True)
        flag = strtobool(value)
        if flag:
            return queryset.filter(id__in=cart_recipes)
        return queryset.exclude(id__in=cart_recipes)
