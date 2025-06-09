**О проекте**
FoodGram — это сервис для публикации и обмена рецептами с тегами, ингредиентами, избранным, подписками и списком покупок.

## Как запустить проект через Docker

1. Клонируйте репозиторий и перейдите в папку infra:

'''bash

git clone https://github.com/ninkkka/foodgram-st
cd foodgram-st/infra

2. Запустите контейнеры с помощью Docker Compose:

'''bash

docker compose up -d --build

3. Проверьте статус контейнеров:

'''bash

docker compose ps

Контейнеры backend, db, frontend и nginx должны быть в статусе Up.

## Миграции и база данных

Миграции уже применены при старте контейнеров. Если нужно применить миграции вручную:

'''bash

docker compose exec backend sh
python manage.py migrate
exit

## Основные эндпоинты API

Публичные (без токена):

GET /api/tags/ — список тегов

GET /api/ingredients/ — список ингредиентов

GET /api/ingredients/?name=<префикс> — фильтрация ингредиентов по названию


Аутентификация:

POST /auth/users/ — регистрация пользователя

POST /auth/token/login/ — получение токена

POST /auth/token/logout/ — выход (удаление токена)


Приватные (требуется токен):
Избранное рецепты:

POST /api/recipes/{id}/favorite/

DELETE /api/recipes/{id}/favorite/


Подписки:

POST /api/users/{author_id}/subscribe/

DELETE /api/users/{author_id}/subscribe/

GET /api/users/subscriptions/


Список покупок:

POST /api/recipes/{id}/shopping_cart/

DELETE /api/recipes/{id}/shopping_cart/

GET /api/recipes/download_shopping_cart/ (plain-text)


## Что не реализовано / не полноценно сделано (MVP)

1. Нет наполненной базы данных (рецептов, тегов, ингредиентов) — в базе сейчас пусто.

2. Нет полноценного скачивания списка покупок в формате PDF (только plain-text).

3. Нет автоматизированных тестов для всех сценариев.

4. Страницы «О проекте» и «Технологии» пока отключены.

5. Фронтенд работает частично (см. состояние контейнера).


## Проверка работы (рекомендации)

Открыть браузер и проверить публичные эндпоинты, например:

'''bash

http://localhost:8000/api/tags/

Зарегистрировать пользователя:

'''bash

curl -X POST http://localhost:8000/auth/users/ -H "Content-Type: application/json" -d "{\"username\":\"testuser\",\"password\":\"TestPass123\",\"email\":\"test@example.com\"}"

Получить токен:

'''bash

curl -X POST http://localhost:8000/auth/token/login/ -H "Content-Type: application/json" -d "{\"username\":\"testuser\",\"password\":\"TestPass123\"}"

Использовать токен в заголовке для доступа к приватным эндпоинтам, например:

'''bash

curl -X POST http://localhost:8000/api/recipes/1/favorite/ -H "Authorization: Token <твой_токен>"

перед повторным запуском тестов через постман сначала очищается база данных через команду 

python manage.py flush

Затем в базу данных через shell добавляются ингредиенты

python manage.py shell

import json
from pathlib import Path
from recipes.models import Ingredient

# Строим путь: из папки backend идём наверх и в data
fixture_path = Path('..') / 'data' / 'ingredients.json'

# Читаем и грузим
with fixture_path.open(encoding='utf-8') as f:
    data = json.load(f)

# Создаём/обновляем ингредиенты
for item in data:
    Ingredient.objects.update_or_create(
        name=item['name'],
        defaults={'measurement_unit': item['measurement_unit']}
    )