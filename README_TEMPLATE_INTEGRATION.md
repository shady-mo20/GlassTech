# Envato template integration (Industris)

## Goal

Use the downloaded Envato **Industris** HTML template as the **frontend visual system** while keeping a real Flask backend (routes, DB, auth, admin).

This means:
- We do **not** serve `industris/index.html` directly.
- We **convert** the HTML layout into reusable Jinja templates.
- We **copy** the required CSS/JS/fonts/images into Flask `static/` and reference them via `url_for('static', ...)`.

## What was reused from the template

From `industris/`:
- `css/` → copied to `static/vendor/industris/css/`
- `js/` → copied to `static/vendor/industris/js/`
- `fonts/` → copied to `static/vendor/industris/fonts/`
- `images/` → copied to `static/vendor/industris/images/`
- `style.css` → copied to `static/vendor/industris/style.css`
- `favicon.png` → copied to `static/vendor/industris/favicon.png`

## What was converted into Jinja

### Base layout

- `templates/base.html`
  - Loads the Envato CSS + JS assets
  - Adds project overrides (`static/css/app.css`, `static/js/app.js`)
  - Applies `lang` and `dir` attributes for EN/AR + RTL/LTR

### Shared includes

- `templates/includes/navbar.html`
  - Envato header markup adapted to Flask routes
  - Adds visible **language switcher**
  - Adds login/admin/logout controls

- `templates/includes/footer.html`
  - Envato footer structure with clean, bilingual content

- `templates/includes/page_header.html`
  - Reusable “subheader” banner used on internal pages

### Public pages

`templates/public/`:
- `home.html`
- `machines.html`
- `machine_detail.html`
- `how_it_works.html`
- `specifications.html`
- `applications.html`
- `gallery.html`
- `about.html`
- `contact.html`
- `login.html`
- `error.html`

### Admin pages

`templates/admin/`:
- `layout.html` (admin wrapper + sidebar)
- `dashboard.html`
- `machines.html` / `machine_edit.html`
- `specifications.html` / `spec_edit.html`
- `gallery.html` / `gallery_edit.html`
- `inquiries.html`
- `users.html` (admin only)
- `review.html` / `review_detail.html` (admin only)

## Asset path rules

All template assets must be referenced like:

```jinja2
{{ url_for('static', filename='vendor/industris/css/bootstrap.css') }}
```

Machine images are referenced like:

```jinja2
{{ url_for('static', filename='images/machines/glass_tempering_furnace.png') }}
```

## Where to customize styling

- Keep Envato `static/vendor/industris/style.css` unchanged.
- Put all customizations in:
  - `static/css/app.css`

This keeps the integration maintainable and makes it easier to upgrade template assets later.

## Removed / cleaned template files (project purification)

To make the repository feel custom-built (not a template dump), the following **unused** template/source folders were removed after integration:

- `industris/` (original HTML pages and assets)
- `documentation/` (template docs)
- `Machine Images/` (source images folder after importing into `static/images/machines/`)
- `industris.zip` (original archive)

Why this is safe:
- The running Flask site references assets only from `static/vendor/industris/` and `static/images/machines/`.
- No Flask route renders the original template HTML pages.

## Final active structure (runtime-relevant)

```
.
├─ app.py
├─ config.py
├─ models.py
├─ schema.sql
├─ requirements.txt
├─ instance/app.sqlite3
├─ templates/
├─ static/
│  ├─ css/app.css
│  ├─ js/app.js
│  ├─ images/machines/
│  └─ vendor/industris/
└─ translations/
```

