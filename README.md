# Glass Machinery System (Flask) — Premium Bilingual Industrial Website

This project is a **database-driven Flask website** (SQLite + Jinja + session auth) integrated with the **Envato “Industris” HTML template** as the public-facing design language. It is fully bilingual (**English + Arabic**) with **LTR/RTL switching**, and includes an **admin + developer role workflow** with **review/approval**.

## Features

- **Premium industrial UI** based on Envato template assets (CSS/JS/fonts/images)
- **Bilingual i18n (EN/AR)** with **RTL/LTR** layout switching
- **Session-based authentication**
- **Role-based access**
  - **admin_developer**: full admin + approval permissions
  - **developer**: can submit changes for approval (cannot publish directly)
- **Admin system**
  - Manage machines
  - Manage specifications
  - Manage gallery items
  - Manage users (activation)
  - Review & approve developer submissions
  - View inquiries and update statuses
- **Contact / Inquiry storage** in SQLite
- **Real machine images integrated** and seeded into DB

## Tech stack

- **Backend**: Python + Flask
- **Database**: SQLite
- **Templates**: Jinja2
- **Frontend**: Envato template assets (Bootstrap + template CSS/JS)

## Run (quick start)

```bash
python -m pip install -r requirements.txt
python app.py
```

Then open:
- Public site: `http://127.0.0.1:5000/`

## Default local credentials (seeded)

These are created automatically when the DB is empty (local dev only).

- **Admin**: `admin` / `Admin@12345`
- **Developer**: `dev` / `Dev@12345`

## Public pages (routes)

- `/` Home
- `/machines` Machine overview
- `/machines/<slug>` Machine detail
- `/how-it-works` How it works
- `/specifications` Technical specifications (DB-driven)
- `/applications` Applications
- `/gallery` Media gallery
- `/about` About
- `/contact` Contact / Inquiry (stores in DB)
- `/login` Login
- `POST /lang/<en|ar>` Language switch (session persisted)
- `POST /logout` Logout

## Admin pages (routes)

- `/admin` Dashboard
- `/admin/machines` List machines
- `/admin/machines/edit` Add/edit machine
- `/admin/gallery` List gallery
- `/admin/gallery/edit` Add/edit gallery item
- `/admin/specifications` List specs
- `/admin/specifications/edit` Add/edit spec
- `/admin/inquiries` Inquiry inbox
- `/admin/users` User activation (admin only)
- `/admin/users/create` Create user (admin only)
- `/admin/review` Review submissions (admin only)
- `/admin/review/<id>` Submission detail (admin only)

## Folder structure

```
.
├─ app.py
├─ config.py
├─ models.py
├─ schema.sql
├─ requirements.txt
├─ instance/
│  └─ app.sqlite3
├─ templates/
│  ├─ base.html
│  ├─ includes/
│  ├─ public/
│  └─ admin/
├─ static/
│  ├─ css/
│  │  └─ app.css
│  ├─ js/
│  │  └─ app.js
│  ├─ images/
│  │  └─ machines/
│  └─ vendor/
│     └─ industris/   (Envato template assets copied here)
└─ translations/
   ├─ en.json
   └─ ar.json
```

## Key documentation

- `README_WINDOWS_SETUP.md`
- `README_TEMPLATE_INTEGRATION.md`
- `README_I18N.md`
- `README_ADMIN_SYSTEM.md`
- `README_MACHINE_CONTENT.md`

## Implementation notes (high level)

- The original Envato HTML pages are **not served directly**. Instead, their layout sections were converted into:
  - `templates/base.html`
  - `templates/includes/navbar.html`
  - `templates/includes/footer.html`
  - `templates/public/*.html`
  - `templates/admin/*.html`
- All CSS/JS/images/fonts used by the public site are served from:
  - `static/vendor/industris/`
- Bilingual switching uses `POST /lang/<code>` and persists the selected language in `session["lang"]`.

