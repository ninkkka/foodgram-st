from django.shortcuts import get_object_or_404
from django.db.models import F, Sum
from django.http import HttpResponse

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .permissions import IsAuthorOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from users.models import User, Subscription
from recipes.models import (
    Ingredient, Recipe,
    IngredientInRecipe, Favorite, ShoppingCart
)
from .serializers import (
    UserReadSerializer, UserCreateSerializer, SubscriptionSerializer,
    IngredientSerializer, SubscriptionReadSerializer,
    RecipeReadSerializer, RecipeWriteSerializer, RecipeShortSerializer,
    FavoriteSerializer, ShoppingCartSerializer, AvatarSerializer
)
from .filters import RecipeFilter, IngredientFilter
from .pagination import CustomPagination


class CustomUserViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.all()
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ('create',):
            return UserCreateSerializer
        return UserReadSerializer

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request):
        """Вернуть свой профиль."""
        serializer = UserReadSerializer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='set_password'
    )
    def set_password(self, request):
        """
        POST /api/users/set_password/
        Тесты ожидают:
         - если аноним → 401
         - если не переданы поля current_password/new_password → 400
         - если current_password неверный → 400
         - если всё корректно → смена пароля и 204 No Content
        """
        user = request.user
        current = request.data.get('current_password')
        new = request.data.get('new_password')

        if current is None or new is None:
            return Response(
                {'detail': 'Требуются поля current_password и new_password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.check_password(current):
            return Response(
                {'current_password': 'Неверный текущий пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(new, str) or new.strip() == '':
            return Response(
                {'new_password': 'Новый пароль не может быть пустым'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new)
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, pk=None):
        """Подписаться/отписаться от автора."""
        author = get_object_or_404(User, pk=pk)
        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data={'user': request.user.id, 'author': author.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            out = SubscriptionReadSerializer(
                author,
                context={'request': request}
            ).data
            return Response(out, status=status.HTTP_201_CREATED)
            # return Response(
            #     UserReadSerializer(author,
            #                        context={'request': request}).data,
            #     status=status.HTTP_201_CREATED
            # )
        request.user.subscriptions.filter(
            author=author
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        """Список подписок текущего пользователя."""
        authors_qs = User.objects.filter(subscribers__user=request.user)
        page = self.paginate_queryset(authors_qs)
        serializer = SubscriptionReadSerializer(
            page or authors_qs,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=('put', 'delete'),
        permission_classes=(IsAuthenticated),
        parser_classes=(MultiPartParser, FormParser, JSONParser),
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user

        if request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

        if 'avatar' not in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = AvatarSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user.refresh_from_db()

        full_url = request.build_absolute_uri(user.avatar.url)

        return Response(
            {"avatar": full_url},
            status=status.HTTP_200_OK
        )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Эндпоинт /api/ingredients/."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    """Эндпоинт /api/recipes/."""
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPagination
    permission_classes = (IsAuthorOrReadOnly,)

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'get_link'):
            return [AllowAny()]
        return [IsAuthorOrReadOnly()]

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        if self.action in ('favorite', 'shopping_cart'):
            return RecipeShortSerializer
        return RecipeWriteSerializer

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        """Добавить/удалить рецепт в/из избранного."""
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data={'user': request.user.id, 'recipe': recipe.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                RecipeShortSerializer(
                    recipe,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        request.user.favorites.filter(
            recipe=recipe
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        """Добавить/удалить рецепт в/из списка покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            serializer = ShoppingCartSerializer(
                data={'user': request.user.id, 'recipe': recipe.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                RecipeShortSerializer(
                    recipe,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        request.user.shopping_cart.filter(
            recipe=recipe
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        """Скачать файл со списком покупок."""
        user = request.user
        ingredients = IngredientInRecipe.objects.filter(
            recipe__in_shopping_cart__user=user
        ).values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')
        ).annotate(amount=Sum('amount'))

        lines = [
            f'{item["name"]} — '
            f'{item["amount"]} '
            f'{item["measurement_unit"]}'
            for item in ingredients
        ]
        content = 'Список покупок:\n\n' + '\n'.join(lines)
        response = HttpResponse(
            content,
            content_type='text/plain'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(
        detail=True,
        methods=('get',),
        permission_classes=(AllowAny,),
        url_path='get-link',
    )
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        link = request.build_absolute_uri()
        return Response(
            {'short-link': link},
            status=status.HTTP_200_OK
        )

    def partial_update(self, request, *args, **kwargs):
        if 'ingredients' not in request.data:
            return Response(
                {'ingredients': ['Это поле является обязательным.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().partial_update(request, *args, **kwargs)
