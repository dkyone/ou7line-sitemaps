# Spotify Player Image Tool

Инструмент для создания готовых изображений плеера Spotify с обложкой, названием трека/альбома и исполнителем в различных стилях оформления.

## 🎨 Функциональность

- ✅ Получение информации о треке/альбоме из Spotify API
- ✅ Загрузка обложки альбома
- ✅ Генерация изображения плеера в 4 стилях:
  - **Dark** — классический тёмный фон (чёрный)
  - **Light** — светлый фон
  - **Blur** — размытая обложка в качестве фона
  - **Gradient** — градиент, извлечённый из доминирующих цветов обложки

- ✅ Веб-интерфейс для генерации изображений
- ✅ Прямая загрузка отдельных стилей через URL
- ✅ Пакетная обработка плейлистов (скрипт `batch_playlist.py`)

## 📋 Требования

- Python 3.9+
- pip (менеджер пакетов Python)
- Аккаунт Spotify Developer (для получения Client ID и Secret)

## 🔧 Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd ou7line-sitemaps/spotify_player_tool
```

### 2. Создание файла конфигурации

Скопируйте `.env.example` в `.env` и заполните учетные данные:

```bash
cp .env.example .env
```

Отредактируйте `.env` и добавьте ваши учетные данные:

```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

### 3. Получение учетных данных Spotify

1. Перейдите на [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Создайте новое приложение (Create App)
3. Примите условия использования и создайте приложение
4. Скопируйте **Client ID** и **Client Secret** из приложения
5. Вставьте значения в `.env`

### 4. Установка зависимостей

```bash
pip install -r requirements.txt
```

## 🚀 Использование

### Веб-приложение (локально)

Запустите FastAPI сервер:

```bash
python main.py
```

или используйте uvicorn напрямую:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Затем откройте браузер:
- **http://localhost:8000/**

### Использование через веб-интерфейс

1. Вставьте ссылку на трек или альбом Spotify:
   - Пример трека: `https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp`
   - Пример альбома: `https://open.spotify.com/album/4VqSWnL3KL0u1vHx6q1D6T`

2. Нажмите "Generate"
3. Выберите нужный стиль и скачайте изображение

### Прямая загрузка через URL

Загрузить изображение конкретного стиля напрямую:

```
GET /download/{style}?url=<spotify_url>
```

**Параметры:**
- `style`: `dark`, `light`, `blur` или `gradient`
- `url`: URL трека или альбома Spotify

**Пример:**
```
http://localhost:8000/download/dark?url=https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp
```

### Пакетная обработка плейлиста

Сгенерируйте изображения для всех треков в плейлисте:

```bash
SPOTIFY_CLIENT_ID=xxx SPOTIFY_CLIENT_SECRET=yyy \
    python batch_playlist.py <spotify_playlist_url> [--style dark|light|blur|gradient|all]
```

**Примеры:**

```bash
# Все стили для плейлиста
SPOTIFY_CLIENT_ID=xxx SPOTIFY_CLIENT_SECRET=yyy \
    python batch_playlist.py https://open.spotify.com/playlist/37i9dQZF1DX... --style all

# Только стиль "gradient"
SPOTIFY_CLIENT_ID=xxx SPOTIFY_CLIENT_SECRET=yyy \
    python batch_playlist.py https://open.spotify.com/playlist/37i9dQZF1DX... --style gradient
```

Изображения сохраняются в папку `output/<playlist_id>/`

### Запуск в Docker

Если у вас установлен Docker и Docker Compose:

```bash
# Запуск с docker-compose
docker-compose up

# Или через docker напрямую
docker build -t spotify-player .
docker run -e SPOTIFY_CLIENT_ID=xxx -e SPOTIFY_CLIENT_SECRET=yyy \
    -p 8000:8000 spotify-player
```

### Быстрые команды (Makefile)

Для удобства разработки используются команды Make:

```bash
# Установка зависимостей
make install          # Установить основные зависимости
make install-dev      # Установить зависимости для разработки

# Разработка
make dev             # Запустить dev сервер с auto-reload
make run             # Запустить production сервер

# Тестирование и качество кода
make test            # Запустить тесты
make test-cov        # Тесты с покрытием кода
make lint            # Проверить код (flake8)
make format          # Форматировать код (black)
make format-check    # Проверить форматирование

# Batch обработка
make batch URL=https://... STYLE=all

# Очистка
make clean           # Удалить кэш и сгенерированные файлы
make help            # Показать все доступные команды
```

## 🏗️ Структура проекта

```
spotify_player_tool/
├── main.py                 # FastAPI приложение
├── renderer.py             # Рендеринг плеера и стили
├── spotify_client.py       # Интеграция со Spotify API
├── batch_playlist.py       # Обработка плейлистов
├── static/
│   └── index.html         # Веб-интерфейс
├── requirements.txt       # Зависимости Python
├── .env.example          # Пример конфигурации
└── README.md             # Эта документация
```

## 📐 Размеры изображения

- **Размер:** 1200x630 px
- **Соотношение сторон:** 16:9
- **Формат:** JPEG (качество 95%)
- **Идеально для:** социальные сети, превью ссылок, шеринг

## 🎨 Особенности стилей

### Dark Theme
- Фон: чёрный (#121212)
- Текст: белый и серый
- Управление: контрастное

### Light Theme
- Фон: светло-серый (#F0F0F0)
- Текст: тёмный и средне-серый
- Управление: тёмное

### Blur Style
- Фон: размытая обложка с полупрозрачной чёрной маской
- Текст и элементы на полупрозрачной карточке
- Атмосферный эффект

### Gradient Style
- Фон: вертикальный градиент из доминирующих цветов обложки
- Динамически адаптируется к каждой обложке
- Самый стильный вариант

## 📝 API Endpoints

### `POST /generate`
Генерирует все 4 стиля для трека/альбома

**Request:**
```json
{
  "url": "https://open.spotify.com/track/..."
}
```

**Response:**
```json
{
  "track": {
    "title": "Song Name",
    "artist": "Artist Name",
    "album": "Album Name",
    "duration": "3:45"
  },
  "images": {
    "dark": "data:image/jpeg;base64,...",
    "light": "data:image/jpeg;base64,...",
    "blur": "data:image/jpeg;base64,...",
    "gradient": "data:image/jpeg;base64,..."
  }
}
```

### `GET /download/{style}`
Загружает одно изображение в виде файла

**Query params:**
- `url` (обязателен): URL трека или альбома Spotify
- `style`: `dark`, `light`, `blur`, `gradient`

**Returns:** JPEG файл с именем `track_title_style.jpg`

### `GET /health`
Проверка статуса API

## 🐛 Решение проблем

### Ошибка: "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET are not configured"
- Убедитесь, что файл `.env` создан и содержит ваши учетные данные
- Убедитесь, что среда имеет доступ к переменным окружения

### Ошибка при загрузке обложки
- Проверьте интернет соединение
- Убедитесь, что URL трека/альбома корректен

### Ошибка "Cannot parse Spotify URL"
- Поддерживаются только URLs вида `spotify.com/track/...` или `spotify:track:...`
- Проверьте, что скопировали полный URL

## 📦 Зависимости

- **fastapi** — веб-фреймворк
- **uvicorn** — ASGI сервер
- **Pillow** — обработка изображений
- **requests** — HTTP клиент
- **python-dotenv** — загрузка переменных окружения

## 📄 Лицензия

[Укажите лицензию]

## 👨‍💻 Разработка

Для локальной разработки:

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск с автоперезагрузкой
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🤝 Вклад

Приветствуются pull requests с улучшениями!

---

**Created with ❤️ for Spotify lovers**
