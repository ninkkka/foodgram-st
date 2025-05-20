from django.contrib import admin
from .models import User, Subscription


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Настройка отображения пользователей в админке."""
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'role',
    )
    search_fields = ('username', 'email')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Настройка отображения подписок в админке."""
    list_display = (
        'user',
        'author',
        'created_at',  # именно так, с _at
    )
    search_fields = (
        'user__username',
        'author__username',
    )
    list_filter = ('user', 'author')
