# KG Tours

Стек: FastAPI + PostgreSQL + статический фронтенд (ky/en/ru/es) + Telegram-бот.

## Запуск
1. Telegram: создайте бота в @BotFather → `TG_BOT_TOKEN`.
   Напишите боту (или добавьте в группу), затем откройте
   `https://api.telegram.org/bot<TOKEN>/getUpdates` → `chat.id` → `TG_CHAT_ID`.
2. `cp .env.example .env` и заполните значения, включая `ADMIN_PASSWORD` (задайте свой длинный пароль).
3. `docker compose up -d --build` → http://localhost:8000

В админку можно войти по ссылке «Админка» на главной странице, введя `ADMIN_PASSWORD`. Сессия действует 8 часов.

## Как устроено
- `db/init.sql` — таблицы `tours` (названия/описания в JSONB по 4 языкам) и `bookings`, плюс 4 тура.
- `POST /api/bookings` — сохраняет заявку в Postgres и шлёт её в Telegram.
- Новый тур: `INSERT INTO tours ...` — карточка появится на сайте сама.
