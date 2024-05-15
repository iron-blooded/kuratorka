# Используем базовый образ Python
FROM python:3.11.3

# Установка зависимостей
COPY requirements.txt .
RUN apt-get update && apt-get install -y ffmpeg && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* requirements.txt

# Создание директории приложения
WORKDIR /kuratorka

# Копирование файлов в директорию приложения
COPY . .

# Установка переменных окружения
ENV ENV_VARIABLE=value

# Команда для запуска вашего скрипта
CMD ["python", "main.py"]
