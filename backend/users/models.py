from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


def validate_not_me(value):
    """Запрещаем имя пользователя 'me'."""
    if value.lower() == 'me':
        raise ValidationError('Имя пользователя не может быть "me".')


class User(AbstractUser):
    """Кастомная модель пользователя."""
    USER = 'user'
    ADMIN = 'admin'
    ROLE_CHOICES = [
        (USER, 'user'),
        (ADMIN, 'admin'),
    ]

    email = models.EmailField(
        'email',
        unique=True,
        blank=False,
        max_length=254,
    )
    first_name = models.CharField(
        'Имя',
        max_length=150,
        blank=False,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-zА-Яа-яЁё -]+$',
                message='Введите корректное имя.'
            ),
            validate_not_me,
        ],
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=150,
        blank=False,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-zА-Яа-яЁё -]+$',
                message='Введите корректную фамилию.'
            ),
            validate_not_me,
        ],
    )
    avatar = models.ImageField(
        'Фото пользователя',
        upload_to='avatars/',
        blank=True,
        null=True,
    )
    role = models.CharField(
        'Роль',
        max_length=5,
        choices=ROLE_CHOICES,
        default=USER,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Подписки пользователя на авторов."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор',
    )
    created_at = models.DateTimeField(
        'Дата подписки',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} → {self.author.username}'
