import html, logging, os
from contextlib import asynccontextmanager
from datetime import date

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel, Field

import secrets
from typing import Literal
from fastapi import Depends
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from psycopg.types.json import Jsonb

pool = AsyncConnectionPool(os.environ["DATABASE_URL"], open=False,
                           kwargs={"row_factory": dict_row})

@asynccontextmanager
async def lifespan(_):
    await pool.open()
    async with pool.connection() as c:
        await c.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS "
                        "status TEXT NOT NULL DEFAULT 'new'")
    yield
    await pool.close()

app = FastAPI(lifespan=lifespan)

class Booking(BaseModel):
    tour_id: int
    name: str = Field(min_length=2, max_length=100)
    contact: str = Field(min_length=3, max_length=100)
    start_date: date | None = None
    people: int = Field(1, ge=1, le=50)
    comment: str | None = Field(None, max_length=1000)
    lang: str = "en"

@app.get("/api/tours")
async def tours():
    async with pool.connection() as c:
        cur = await c.execute(
            "SELECT id, slug, title, description, days, price_usd, region, color "
            "FROM tours WHERE active ORDER BY id")
        return await cur.fetchall()

async def notify(text: str):
    token, chat = os.getenv("TG_BOT_TOKEN"), os.getenv("TG_CHAT_ID")
    if not token or not chat:
        logging.error("Telegram: TG_BOT_TOKEN or TG_CHAT_ID is empty")
        return
    try:
        async with httpx.AsyncClient(timeout=10) as h:
            r = await h.post(f"https://api.telegram.org/bot{token}/sendMessage",
                             json={"chat_id": chat, "text": text, "parse_mode": "HTML"})
            if r.status_code != 200:
                logging.error("Telegram error %s: %s", r.status_code, r.text)
    except Exception:
        logging.exception("Telegram notify failed")

@app.post("/api/bookings")
async def book(b: Booking):
    async with pool.connection() as c:
        cur = await c.execute("SELECT title FROM tours WHERE id=%s AND active", (b.tour_id,))
        tour = await cur.fetchone()
        if not tour:
            raise HTTPException(404, "Tour not found")
        cur = await c.execute(
            "INSERT INTO bookings (tour_id,name,contact,start_date,people,comment,lang) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (b.tour_id, b.name, b.contact, b.start_date, b.people, b.comment, b.lang))
        row = await cur.fetchone()
    e = html.escape
    await notify(
        f"🆕 <b>Заявка #{row['id']}</b>\n"
        f"Тур: {e(tour['title'].get('ru') or tour['title']['en'])}\n"
        f"Имя: {e(b.name)}\nКонтакт: {e(b.contact)}\n"
        f"Дата: {b.start_date or '—'}\nЧеловек: {b.people}\n"
        f"Язык сайта: {e(b.lang)}\nКомментарий: {e(b.comment or '—')}")
    return {"ok": True, "id": row["id"]}

# ---------- ADMIN ----------
security = HTTPBasic()

def admin(c: HTTPBasicCredentials = Depends(security)):
    u, p = os.getenv("ADMIN_USER"), os.getenv("ADMIN_PASSWORD")
    ok = bool(u and p) and \
        secrets.compare_digest(c.username.encode(), u.encode()) and \
        secrets.compare_digest(c.password.encode(), p.encode())
    if not ok:
        raise HTTPException(401, "Unauthorized", headers={"WWW-Authenticate": "Basic"})

class TourIn(BaseModel):
    slug: str = Field(min_length=2)
    title: dict[str, str]
    description: dict[str, str]
    days: int = Field(ge=1)
    price_usd: int = Field(ge=0)
    region: str | None = None
    color: str = "#0E3B4F"
    active: bool = True

class StatusIn(BaseModel):
    status: Literal["new", "contacted", "confirmed", "cancelled"]

@app.get("/admin", dependencies=[Depends(admin)])
async def admin_page():
    return FileResponse("admin.html")

@app.get("/api/admin/bookings", dependencies=[Depends(admin)])
async def a_bookings():
    async with pool.connection() as c:
        cur = await c.execute(
            "SELECT b.id, b.name, b.contact, b.start_date, b.people, b.comment, "
            "b.lang, b.status, b.created_at, t.title->>'ru' AS tour "
            "FROM bookings b JOIN tours t ON t.id=b.tour_id ORDER BY b.id DESC")
        return await cur.fetchall()

@app.patch("/api/admin/bookings/{bid}", dependencies=[Depends(admin)])
async def a_booking_status(bid: int, s: StatusIn):
    async with pool.connection() as c:
        await c.execute("UPDATE bookings SET status=%s WHERE id=%s", (s.status, bid))
    return {"ok": True}

@app.get("/api/admin/tours", dependencies=[Depends(admin)])
async def a_tours():
    async with pool.connection() as c:
        cur = await c.execute("SELECT * FROM tours ORDER BY id")
        return await cur.fetchall()

@app.post("/api/admin/tours", dependencies=[Depends(admin)])
async def a_tour_new(t: TourIn):
    async with pool.connection() as c:
        cur = await c.execute(
            "INSERT INTO tours (slug,title,description,days,price_usd,region,color,active) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (t.slug, Jsonb(t.title), Jsonb(t.description), t.days, t.price_usd,
             t.region, t.color, t.active))
        return await cur.fetchone()

@app.put("/api/admin/tours/{tid}", dependencies=[Depends(admin)])
async def a_tour_edit(tid: int, t: TourIn):
    async with pool.connection() as c:
        await c.execute(
            "UPDATE tours SET slug=%s,title=%s,description=%s,days=%s,price_usd=%s,"
            "region=%s,color=%s,active=%s WHERE id=%s",
            (t.slug, Jsonb(t.title), Jsonb(t.description), t.days, t.price_usd,
             t.region, t.color, t.active, tid))
    return {"ok": True}
# ---------- /ADMIN ----------

app.mount("/", StaticFiles(directory="static", html=True), name="static")
