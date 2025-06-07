from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    RegexValidator,
)
from django.db import models

from users.models import User

COOKING_TIME_MIN = 1
COOKING_TIME_MAX = 32_000
AMOUNT_MIN = 1
AMOUNT_MAX = 32_000


class Ingredient(models.Model):
    """Ингредиент с единицей измерения."""
    name = models.CharField(
        'Название',
        max_length=200,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-zА-Яа-яЁё -]+$',
                message='Недопустимые символы в имени.'
            )
        ],
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=50,
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Tag(models.Model):
    """Тэг для рецептов."""
    name = models.CharField(
        'Название тэга',
        max_length=200,
        unique=True,
    )
    color = models.CharField(
        'Цвет (HEX)',
        max_length=7,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^#([A-Fa-f0-9]{6})$',
                message='Цвет в формате HEX, например #FF0000.'
            )
        ],
    )
    slug = models.SlugField(
        'Slug',
        max_length=200,
        unique=True,
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Рецепт блюда."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        'Название',
        max_length=200,
    )
    image = models.ImageField(
        'Фото',
        upload_to='recipes/images/',
    )
    text = models.TextField(
        'Описание',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тэги',
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (мин.)',
        validators=[
            MinValueValidator(COOKING_TIME_MIN, f'Не меньше {COOKING_TIME_MIN} минуты.'),
            MaxValueValidator(COOKING_TIME_MAX, f'Не больше {COOKING_TIME_MAX} минут.')
        ],
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    """Связь рецепт–ингредиент с указанием количества."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_amounts',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_amounts',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(AMOUNT_MIN, f'Минимум {AMOUNT_MIN}.'),
            MaxValueValidator(AMOUNT_MAX, f'Максимум {AMOUNT_MAX}.')
        ],
    )

    class Meta:
        ordering = ['recipe', 'ingredient']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient_in_recipe'
            )
        ]
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'

    def __str__(self):
        return f'{self.ingredient.name}: {self.amount}'


class Favorite(models.Model):
    """Избранное пользователя."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
    )

    class Meta:
        ordering = ['user', 'recipe']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        return f'{self.user.username} → {self.recipe.name}'


class ShoppingCart(models.Model):
    """Рецепты в списке покупок пользователя."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
    )

    class Meta:
        ordering = ['user', 'recipe']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'{self.user.username} → {self.recipe.name}'
