# Используем официальный Python
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем только файл зависимостей сначала (для кэша слоёв)
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта в контейнер
COPY . .

# Собираем статику, если нужно (раскомментируйте, если используете collectstatic)
# RUN python manage.py collectstatic --noinput

# Указываем команду по умолчанию: запускаем Gunicorn
# Предполагается, что ваш корневой Django-пакет называется foodgram_backend
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0.0.0.0:8000"]
