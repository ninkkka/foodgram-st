import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from djoser.serializers import UserSerializer as DjoserUserSerializer
from recipes.models import (
    Ingredient,
    Tag,
    Recipe,
    IngredientInRecipe,
    Favorite,
    ShoppingCart,
    AMOUNT_MIN,
    AMOUNT_MAX,
    COOKING_TIME_MIN,
    COOKING_TIME_MAX,
)
from users.models import User, Subscription


class Base64ImageField(serializers.ImageField):
    """Поле для приёма картинки в виде base64-строки."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            header, img_str = data.split(';base64,')
            ext = header.split('/')[-1]
            data = ContentFile(
                base64.b64decode(img_str),
                name=f'temp.{ext}'
            )
        return super().to_internal_value(data)


class UserCreateSerializer(serializers.ModelSerializer):
    """Регистрация пользователя: только нужные поля и хеширование пароля."""
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password'],
        )
        return user


class UserReadSerializer(DjoserUserSerializer):
    """Чтение профиля пользователя."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True) 

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return user.subscriptions.filter(
            author=obj
        ).exists()


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписки на автора."""
    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого автора.'
            )
        ]

    def validate_author(self, value):
        user = self.context['request'].user
        if user == value:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        return value

    def create(self, validated_data):
        return Subscription.objects.create(
            user=self.context['request'].user,
            **validated_data
        )


class IngredientSerializer(serializers.ModelSerializer):
    """Чтение ингредиента."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Ингредиент в рецепте с указанием количества."""
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )
    amount = serializers.IntegerField(
        min_value=AMOUNT_MIN,
        max_value=AMOUNT_MAX,
        error_messages={
            'min_value': f'Минимум {AMOUNT_MIN}.',
            'max_value': f'Максимум {AMOUNT_MAX}.'
        }
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeShortSerializer(serializers.ModelSerializer):
    """Краткое представление рецепта."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Полное чтение рецепта."""
    author = UserReadSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='ingredient_amounts',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return user.shopping_cart.filter(recipe=obj).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Создание/обновление рецепта."""
    ingredients = IngredientInRecipeSerializer(
        source='ingredient_amounts',
        many=True
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=COOKING_TIME_MIN,
        max_value=COOKING_TIME_MAX,
        error_messages={
            'min_value': f'Не меньше {COOKING_TIME_MIN} минуты.',
            'max_value': f'Не больше {COOKING_TIME_MAX} минут.'
        }
    )

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент.'
            )
        ids = [item['ingredient'].id for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
        return value

    def _save_ingredients(self, recipe, ingredients):
        recipe.ingredient_amounts.all().delete()
        objs = [
            IngredientInRecipe(
                recipe=recipe,
                ingredient=ing['ingredient'],
                amount=ing['amount']
            )
            for ing in ingredients
        ]
        IngredientInRecipe.objects.bulk_create(objs)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredient_amounts')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        self._save_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredient_amounts')
        self._save_ingredients(instance, ingredients)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context=self.context
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Добавление/удаление в избранное."""
    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Уже в избранном.'
            )
        ]

    def create(self, validated_data):
        return Favorite.objects.create(
            user=self.context['request'].user,
            **validated_data
        )


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Добавление/удаление в список покупок."""
    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Уже в списке покупок.'
            )
        ]

    def create(self, validated_data):
        return ShoppingCart.objects.create(
            user=self.context['request'].user,
            **validated_data
        )
