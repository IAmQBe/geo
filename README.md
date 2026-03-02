# Geo / Jam Bot

Первый исполняемый инкремент по `ARCHITECTURE.md`.

## Что уже реализовано
- Базовый каркас проекта (`bot`, `db`, `scripts`)
- Асинхронная SQLAlchemy модель данных по ключевым таблицам
- Минимально рабочий Telegram-бот на aiogram 3:
  - `/start`
  - выбор города
  - главное меню категорий
- Seed-скрипт для городов и категорий из архитектурного документа

## Быстрый старт
1. Создайте окружение и установите зависимости:
   - `python3.11 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`
2. Поднимите Postgres (например, через Docker Compose):
   - `docker compose up -d postgres`
3. Создайте таблицы:
   - `python -m scripts.init_db`
4. Заполните базовые данные:
   - `python -m scripts.seed_data`
5. Запустите бота:
   - `python -m bot.main`

## Переменные окружения
Скопируйте шаблон:
- `cp .env.example .env`
