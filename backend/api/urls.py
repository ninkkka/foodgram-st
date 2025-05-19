from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.documentation import include_docs_urls

from .views import (
    CustomUserViewSet,
    IngredientViewSet,
    TagViewSet,
    RecipeViewSet
)

app_name = 'api'

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),            # регистрация, просмотр, смена пароля
    path('auth/', include('djoser.urls.authtoken')),  # получение токена
]
