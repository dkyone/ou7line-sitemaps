# Contributing to Spotify Player Image Tool

Спасибо за интерес к нашему проекту! Ниже приведены инструкции для разработчиков.

## 🛠️ Настройка окружения

### Требования
- Python 3.9+
- pip
- git

### Установка

1. **Клонируйте репозиторий:**
   ```bash
   git clone <repository-url>
   cd ou7line-sitemaps/spotify_player_tool
   ```

2. **Создайте файл `.env`:**
   ```bash
   cp .env.example .env
   # Отредактируйте .env и добавьте учетные данные Spotify
   ```

3. **Установите зависимости:**
   ```bash
   make install-dev
   ```

## 🚀 Разработка

### Запуск разработческого сервера
```bash
make dev
# или
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Сервер будет доступен по адресу: http://localhost:8000

### Запуск тестов
```bash
make test
# С покрытием кода:
make test-cov
```

### Проверка кода
```bash
# Проверка форматирования (black)
make format-check

# Линтинг (flake8)
make lint

# Автоматическое форматирование
make format
```

## 📝 Структура кода

```
spotify_player_tool/
├── main.py              # FastAPI приложение и API endpoints
├── renderer.py          # Логика рендеринга изображений плеера
├── spotify_client.py    # Клиент для работы со Spotify API
├── batch_playlist.py    # Обработка плейлистов в batch режиме
├── static/
│   └── index.html      # Веб-интерфейс
├── tests/              # Тестовые файлы
│   ├── test_main.py
│   ├── test_renderer.py
│   └── test_spotify_client.py
└── Makefile            # Команды для разработки
```

## 🎨 Рекомендации по кодированию

### Стиль кода
- Следуем [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Используем [Black](https://github.com/psf/black) для форматирования
- Используем [isort](https://github.com/PyCPA/isort) для сортировки импортов

### Типизация
- Добавляйте type hints для функций
- Используйте современные аннотации типов (`from __future__ import annotations`)

### Тестирование
- Пишите тесты для новых функций
- Убедитесь, что все тесты проходят перед отправкой PR
- Стремитесь к покрытию кода > 80%

### Комментарии
- Добавляйте docstrings к функциям и классам
- Комментарии должны объяснять _почему_, а не _что_

## 📋 Процесс внесения изменений

### 1. Создайте веку для своего изменения
```bash
git checkout -b feature/my-feature
# или для багов:
git checkout -b fix/my-bug
```

### 2. Внесите изменения
- Напишите код
- Добавьте/обновите тесты
- Запустите тесты и проверку кода:
  ```bash
  make test
  make lint
  make format
  ```

### 3. Коммитьте изменения
```bash
git add .
git commit -m "type: description

Longer description of the change if needed.

Fixes #123"
```

**Типы коммитов:**
- `feat`: Новая функция
- `fix`: Исправление ошибки
- `docs`: Документация
- `style`: Форматирование, пропущенные точки с запятой и т. д.
- `refactor`: Переписка кода без изменения функциональности
- `perf`: Улучшение производительности
- `test`: Добавление или обновление тестов
- `chore`: Обновление зависимостей, конфигурации и т. д.

### 4. Отправьте pull request
- Опишите что вы изменили
- Объясните почему это нужно
- Ссылайтесь на related issues

## 🐛 Сообщение об ошибках

При сообщении об ошибке, пожалуйста, включите:
- Версию Python (`python --version`)
- Что вы пытались сделать
- Полное сообщение об ошибке
- Как воспроизвести ошибку (минимальный пример)

## 💡 Предложения функций

Перед тем как начать разрабатывать новую функцию, откройте issue и обсудите идею с мейнтейнерами.

## 📚 Дополнительные ресурсы

- [FastAPI документация](https://fastapi.tiangolo.com/)
- [Pillow документация](https://pillow.readthedocs.io/)
- [Spotify API документация](https://developer.spotify.com/documentation/web-api)
- [pytest документация](https://docs.pytest.org/)

## ❓ Вопросы?

Откройте issue или напишите в discussions.

---

Спасибо за вклад! 🙏
