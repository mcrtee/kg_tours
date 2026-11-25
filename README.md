# KG Tours

A tourism website for Kyrgyzstan in four languages (Kyrgyz, English, Russian, Spanish). Visitors browse tour cards and send a booking request. Every request is saved to PostgreSQL and sent to a Telegram chat. An admin panel lets you manage requests and tours.

## Stack

- **Backend:** Python, FastAPI
- **Database:** PostgreSQL 16
- **Frontend:** plain HTML, CSS and JavaScript (no build step)
- **Notifications:** Telegram Bot API
- **Run with:** Docker Compose

## Project structure

```
kg-tours/
├── docker-compose.yml
├── .env.example          # template for your settings
├── db/
│   └── init.sql          # tables and sample tours
└── app/
    ├── Dockerfile
    ├── requirements.txt
    ├── main.py           # API, Telegram, admin endpoints
    ├── admin.html        # admin panel (password protected)
    └── static/
        ├── index.html    # public site
        └── admin-login.html
```

## Quick start

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and make sure it is running.
2. Create your settings file:

   ```bash
   cp .env.example .env        # Windows PowerShell: copy .env.example .env
   ```

3. Edit `.env` (see [Configuration](#configuration)).
4. Start the project:

   ```bash
   docker compose up -d --build
   ```

5. Open the site at http://localhost:8000. Use the **Admin** link on the homepage to sign in.

## Configuration

Put these values in `.env`. Use one line per variable, with no spaces around `=`, no quotes, and no comments on the same line.

```
DB_PASSWORD=choose_a_strong_password
TG_BOT_TOKEN=123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TG_CHAT_ID=123456789
ADMIN_PASSWORD=choose_a_long_password
```

If `ADMIN_PASSWORD` is empty, admin sign-in is disabled. If the Telegram values are empty, requests are still saved to the database but no message is sent. Never commit `.env`.

## Telegram bot setup

1. In Telegram, open **@BotFather**, send `/newbot` and follow the steps. You get a token for `TG_BOT_TOKEN`.
2. Open your new bot and press **Start**. A bot cannot message you until you do this.
3. Open `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser and copy the number at `chat` → `id`. Use it for `TG_CHAT_ID`.
4. To receive requests in a group, add the bot to the group, write a message there, then repeat step 3. Group ids are negative (supergroups start with `-100`).
5. Test the values before using them:

   ```powershell
   Invoke-RestMethod "https://api.telegram.org/bot<YOUR_TOKEN>/sendMessage?chat_id=<YOUR_ID>&text=test"
   ```

6. After editing `.env`, recreate the container so it picks up the change:

   ```bash
   docker compose up -d --force-recreate app
   ```

## Admin panel

Use the **Admin** link on the homepage, then sign in with `ADMIN_PASSWORD`. The signed, HTTP-only session lasts 8 hours.

- **Requests:** see every booking request and change its status (new, contacted, confirmed, cancelled).
- **Tours:** add a tour, edit one, or hide it from the site. Titles and descriptions are required in all four languages.

Tours are never deleted, so old requests always keep their tour. Hide a tour instead.

## Deploy to Render

The repository includes a `render.yaml` Blueprint for the FastAPI app and PostgreSQL database.

1. Push this repository to GitHub.
2. In Render, choose **New → Blueprint**, connect `mcrtee/kg_tours`, and deploy the Blueprint from the repository root.
3. Enter a strong `ADMIN_PASSWORD` when prompted. Render builds the Docker image, creates the database, and assigns its connection URL.
4. After deployment, open the Render service URL. Use **Admin** on the homepage to sign in.
5. To enable Telegram notifications, add `TG_BOT_TOKEN` and `TG_CHAT_ID` as environment variables in the Render web service and redeploy.

The Blueprint uses Render's free plans for a demo. Check Render's current free-tier limits before relying on it for real bookings; use a persistent database plan for production data.

GitHub Pages cannot run this project's FastAPI backend or PostgreSQL database. Deploy the full app on Render (or another server host) rather than Pages to keep booking and admin features working.

## Connecting to the database (DBeaver)

Add a port mapping to the `db` service in `docker-compose.yml`:

```yaml
    ports:
      - "127.0.0.1:5433:5432"
```

Then run `docker compose up -d` and create a PostgreSQL connection in DBeaver:

| Field    | Value                              |
|----------|------------------------------------|
| Host     | `127.0.0.1`                        |
| Port     | `5433`                             |
| Database | `tours`                            |
| Username | `tours`                            |
| Password | the `DB_PASSWORD` from your `.env` |

Port 5433 is used on purpose: if you have another PostgreSQL installed on your computer, it usually occupies 5432 and DBeaver would connect to it by mistake.

## API

| Method | Path                           | Auth  | Description                 |
|--------|--------------------------------|-------|-----------------------------|
| GET    | `/api/tours`                   | none  | Active tours for the site   |
| POST   | `/api/bookings`                | none  | Create a booking request    |
| GET    | `/admin`                       | admin | Admin panel                 |
| GET    | `/api/admin/bookings`          | admin | List requests               |
| PATCH  | `/api/admin/bookings/{id}`     | admin | Change request status       |
| GET    | `/api/admin/tours`             | admin | List all tours              |
| POST   | `/api/admin/tours`             | admin | Create a tour               |
| PUT    | `/api/admin/tours/{id}`        | admin | Update a tour               |

Admin endpoints require the signed admin session cookie.

## Database

- `tours`: `title` and `description` are JSONB with keys `ky`, `en`, `ru`, `es`.
- `bookings`: linked to `tours`, stores name, contact, date, number of guests, comment, site language, status and creation time.

The app applies `db/init.sql` on startup. It is safe to run on an existing database; the `status` column is also added automatically.

## Useful commands

```bash
docker compose up -d --build        # start or rebuild
docker compose ps                   # check status
docker compose logs app --tail 30   # app logs
docker compose down                 # stop
docker compose down -v              # stop and DELETE all data
```

## Troubleshooting

- **`.env not found`:** create it with `copy .env.example .env`. Check that it is not named `.env.txt`.
- **Telegram: `chat not found`:** press Start in the bot, then take the id from `getUpdates` (the number at `chat` → `id`).
- **Telegram 404 in the app logs:** the token in `.env` is malformed (extra text, quotes, spaces, or a `bot` prefix). Rewrite the line.
- **No message and no error in the logs:** the variables did not reach the container. Run `docker compose exec app env` and look for `TG_`, then recreate the container.
- **DBeaver: `role "tours" does not exist`:** you connected to a different PostgreSQL on your machine. Use port 5433 as described above.

## Before going live

- Use strong values for `DB_PASSWORD` and `ADMIN_PASSWORD`.
- Serve the site over HTTPS (for example with Caddy or Nginx). Basic authentication sends the password almost in clear text without it.
- Do not expose the database port to the internet.
- Never commit `.env`. It is listed in `.gitignore`. If a bot token ever leaks, revoke it with `/revoke` in @BotFather.
