# AI-Operated E-Commerce Demo — Bangla Threads

A demo/testing project for a Bangladesh clothing store where an **AI agent**,
using controlled backend tools, is the primary operator of the customer
shopping workflow (search, price/stock lookup, cart, checkout, order status)
in **Bangla or English**. This is **not** a production store — no real
payments are ever processed.

```
Customer → React UI → FastAPI → AI Agent → Tool Selection → Backend Tool
    → PostgreSQL → Tool Result → AI Response → Customer
```

Everything below assumes **Windows + PowerShell**, per the course setup.

---

## 1. Prerequisites

Install these first (skip anything already installed):

- **Python 3.11+** — https://www.python.org/downloads/ (check "Add python.exe to PATH" during install)
- **Node.js 20 LTS** — https://nodejs.org/
- **PostgreSQL 16** — https://www.postgresql.org/download/windows/ (remember the password you set for the `postgres` user during install)

Verify installs in a new PowerShell window:

```powershell
python --version
node --version
psql --version
```

## 2. Create the database

Open PowerShell and run (enter the postgres password when prompted):

```powershell
psql -U postgres -c "CREATE DATABASE ai_ecommerce_bd;"
```

## 3. Backend setup

```powershell
cd "E:\ICT BD AI Software Engineer Course\ai_ecommerce_bd\backend"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> If `Activate.ps1` is blocked, run PowerShell as Administrator once and execute:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### Environment variables

```powershell
Copy-Item .env.example .env
notepad .env
```

Set `DATABASE_URL` to match your Postgres password, e.g.:

```
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/ai_ecommerce_bd
```

Leave `AI_PROVIDER=mock` for now — the whole demo works with **zero API
cost** using the built-in rule-based Bangla/English understanding. See
section 14 below to switch to Claude or Ollama later.

### Create the tables (database migrations)

The database schema is versioned with **Alembic**. On a NEW empty database:

```powershell
alembic upgrade head
```

If your database already has the tables (you set it up before migrations
existed), tell Alembic once that it is up to date instead:

```powershell
alembic stamp head
```

### Seed demo products

```powershell
python seed.py
```

This creates 20+ realistic clothing products (T-Shirts, Shirts, Polo Shirts,
Jeans, Pants, Hoodies, Jackets) in BDT, each with multiple size/color
variants and randomized stock levels.

### Start the backend

```powershell
uvicorn app.main:app --reload --port 8000
```

Leave this PowerShell window open. The API is now at `http://localhost:8000`.

## 4. Frontend setup

Open a **second** PowerShell window:

```powershell
cd "E:\ICT BD AI Software Engineer Course\ai_ecommerce_bd\frontend"
npm install
Copy-Item .env.example .env
npm run dev
```

Leave this window open too. The dev server prints a local URL (normally
`http://localhost:5173`).

## 5. Open the website

- **Customer storefront:** http://localhost:5173
- **Admin panel:** http://localhost:5173/admin
  - Username: `admin`
  - Password: `admin123` (or whatever you set as `ADMIN_PASSWORD` in `backend/.env`)
- **Swagger API docs:** http://localhost:8000/docs

## 6. How to run tests

```powershell
cd "E:\ICT BD AI Software Engineer Course\ai_ecommerce_bd\backend"
.venv\Scripts\Activate.ps1
python -m pytest tests/ -v
```

Tests run against a separate `ai_ecommerce_bd_test` database (created
automatically) so they never touch your seeded demo data. There's also a
manual testing checklist at `backend/tests/MANUAL_TESTING_CHECKLIST.md` —
walk through it once before demoing the project to someone.

## 7. Example customer conversations to try

English:
- "Show me men's T-shirts"
- "Show products under ৳1000"
- "Show black shirts"
- "What is the price of this product?"
- "Add this to my cart"
- "Show my cart"
- "I want to place an order"
- "What is my order status?"

Bangla:
- "কালো টি-শার্ট দেখাও"
- "এইটার দাম কত?"
- "আমাকে ১০০০ টাকার মধ্যে কালো টি-শার্ট দেখাও।"
- "এটা L সাইজের ২টা কার্টে যোগ করো।"
- "আমি অর্ডার করতে চাই।"
- "আমার অর্ডারের অবস্থা কী?"

## 8. What the AI can and cannot do

The AI **never** invents a product name, price, stock level, color, size,
or order status — every fact it states comes back from a real database
query through one of 15 backend tools (`search_products`,
`get_product_details`, `check_product_stock`, `get_product_variants`,
`add_to_cart`, `remove_from_cart`, `update_cart_quantity`, `get_cart`,
`calculate_cart_total`, `create_demo_order`, `get_order`,
`get_customer_orders`, `cancel_demo_order`, `check_order_status`,
`recommend_products`). The Admin → **AI Activity** tab shows exactly which
tool was called for every customer message, with arguments and results —
that transparency is the core of this project.

## 9. Project structure

```
ai_ecommerce_bd/
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI app, CORS, router mounting
│   │   ├── config.py          Settings from environment variables
│   │   ├── database.py        SQLAlchemy engine/session
│   │   ├── models/            SQLAlchemy ORM models (12 tables)
│   │   ├── schemas/           Pydantic request/response schemas
│   │   ├── api/                REST routers: products, cart, orders, chat, admin
│   │   ├── services/           Business logic (source of truth — used by both REST API and AI tools)
│   │   ├── ai/                 AIProvider interface + Mock/Claude/Ollama + agent.py orchestrator
│   │   ├── tools/               The 15 AI tools, backed by services/
│   │   └── utils/
│   ├── tests/                  pytest suite (56 tests) + manual checklist
│   ├── seed.py                 Demo product seeder
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/         Header, Hero, ProductGrid/Card, ChatPanel, CartDrawer, admin/*
│   │   ├── pages/               HomePage (/), AdminPage (/admin)
│   │   ├── services/api.js      Fetch wrapper for the backend
│   │   └── hooks/                useSession, useCart
│   ├── package.json
│   └── .env.example
└── .gitignore
```

## 10. Database design

12 tables: `users`, `categories`, `products`, `product_variants`, `carts`,
`cart_items`, `orders`, `order_items`, `payments`, `ai_conversations`,
`ai_messages`, `ai_tool_logs`.

- `products` (1) → `product_variants` (many): each size/color combination
  has its own stock count — this is what `check_product_stock` and
  `add_to_cart` actually check.
- `carts` (1) → `cart_items` (many): a demo cart is identified by a
  browser session id, no login required.
- `orders` (1) → `order_items` (many) + `payments` (1): order items are a
  price/name **snapshot** at order time, so editing a product later never
  rewrites history. `payments` simulates a payment outcome — never a real
  transaction.
- `ai_conversations` (1) → `ai_messages` + `ai_tool_logs`: full
  conversation memory (so "the second one" resolves correctly) and a full
  audit trail of every tool the AI called, which the Admin panel surfaces.

## 11. AI Agent + Tools workflow

1. Customer message hits `POST /api/chat`.
2. The agent (`app/ai/agent.py`) loads recent conversation history.
3. The active `AIProvider` (mock, Claude, or Ollama) decides: reply
   directly (small talk), or call one specific tool with specific
   arguments.
4. The tool runs against PostgreSQL through `app/services/*` — the same
   functions the plain REST API uses, so the AI and a human admin always
   see the same source of truth.
5. The call (arguments, result, timing, success/failure) is logged to
   `ai_tool_logs`.
6. The provider turns the tool's structured result into a short reply;
   the frontend renders the structured data as real product/cart/order
   cards, not just prose.

## 12. Free/development AI setup

`AI_PROVIDER=mock` (the default) uses deterministic Bangla+English
keyword/pattern matching — no API key, no cost, and it's what powers
everything demonstrated above. To upgrade the *language understanding*
(tool selection stays identical) without touching any business logic:

- **Claude:** set `AI_PROVIDER=claude` and `ANTHROPIC_API_KEY=...` in `backend/.env`.
- **Ollama (local, free):** install [Ollama](https://ollama.com), pull a
  tool-calling-capable model (e.g. `ollama pull llama3.1`), then set
  `AI_PROVIDER=ollama`, `OLLAMA_MODEL=llama3.1` in `backend/.env`.

If `AI_PROVIDER=ollama` is set but Ollama isn't reachable, the app replies
"AI provider unavailable" instead of silently faking a response.

## 13. Security notes (even in a demo)

- Database credentials and the admin password live only in `.env` (never committed — see `.gitignore`).
- All API input is validated with Pydantic.
- Admin routes require a bearer token (`/api/admin/login`); every admin
  endpoint is rejected with 401 without one.
- Order totals and stock are **always** computed/verified on the backend —
  the AI and the client can never set a price or a total directly.
- The AI only acts through the 15 controlled tools; it has no direct
  database access.
- **Order privacy:** order numbers are random 8-digit codes. Looking up or
  cancelling an order that was not placed in the current chat requires the
  phone number it was placed with; a wrong phone and an unknown order give the
  identical answer. Order *lists* show only number/status/total.
- **Stock safety:** order creation locks the product-variant rows
  (`SELECT ... FOR UPDATE`), so the last unit can never be sold twice.
- **Abuse protection:** chat (30/min) and admin login (5/min) are rate limited per IP.
- **Admin password:** set `ADMIN_PASSWORD_HASH` (`python -m app.utils.hash_password`)
  instead of a plain password. With `ENVIRONMENT=production` the app refuses to
  start on the default `SECRET_KEY` / `admin123`.

## 14. Changing the database later (Alembic)

Never edit tables by hand. After changing a model in `app/models`:

```powershell
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

Review the generated file in `alembic/versions/` before applying it.

## 15. Run everything with Docker (optional)

```powershell
docker compose up --build
docker compose exec backend python seed.py   # first run only
```

Store: http://localhost:8080 - API docs: http://localhost:8000/docs.
Run only ONE backend container: the AI fulfillment loop runs inside it.

## 16. Automatic checks (GitHub Actions)

On every push/PR, `.github/workflows/ci.yml` applies the migrations to a fresh
PostgreSQL, checks they match the models (`alembic check`), runs all tests and
builds the frontend.
