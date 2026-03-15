# i18n (English / Arabic) + RTL/LTR switching

## Behavior

- The site supports **English (`en`)** and **Arabic (`ar`)**.
- The current language is stored in the session: `session["lang"]`.
- Layout direction is derived automatically:
  - Arabic → `dir="rtl"`
  - English → `dir="ltr"`

## Language switcher

The switcher is implemented as a POST form:

- `POST /lang/<lang_code>`

This:
- Validates the language code against `SUPPORTED_LANGS`
- Sets `session["lang"]`
- Redirects back to the current page

## Translation files

Translations are stored as JSON dictionaries:

- `translations/en.json`
- `translations/ar.json`

Keys are structured, e.g.:

- `nav.home`
- `home.hero.title`
- `spec.field.heating_temperature`

## Using translations in templates

Use `t()`:

```jinja2
{{ t('nav.home') }}
```

If a key is missing, the key itself is returned (safe fallback).

## RTL/LTR CSS strategy

We keep the Envato template CSS intact and apply RTL fixes in:

- `static/css/app.css`

Examples:
- swap margins for icons
- adjust text alignment
- fix borders that assume LTR

## Adding a new translated label

1) Choose a key, e.g. `contact.form.company`
2) Add it to:
   - `translations/en.json`
   - `translations/ar.json`
3) Use it in templates:

```jinja2
{{ t('contact.form.company') }}
```

## Notes on Arabic quality

- Keep Arabic strings **Modern Standard Arabic**
- Avoid mixing EN/AR in a single sentence
- Prefer concise, technical vocabulary suitable for industrial contexts

