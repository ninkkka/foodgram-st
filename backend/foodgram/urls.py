from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Djoser: регистрация, профиль
    path('auth/', include('djoser.urls')),

    # Djoser: маршруты для токенов (/auth/token/login/, /auth/token/logout/)
    path('auth/', include('djoser.urls.authtoken')),

    # Ваше API
    path('api/', include('api.urls', namespace='api')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
