"""
Flask application entrypoint.

This codebase integrates an Envato HTML template as the **public visual system**
while keeping a **database-driven, role-protected** backend:
- Session-based auth (no JWT)
- Admin + Developer roles
- Admin pages for managing machines/specs/gallery/users
- Review & approval workflow via `submissions`
- Bilingual support (Arabic/English) with RTL/LTR switching

Why we avoid "static-only":
- Public pages are rendered with Jinja and populated from SQLite.
- Contact form stores inquiries in DB.
- Admin pages update DB and support review/approval for developer submissions.
"""

from __future__ import annotations

import json
import os
from functools import wraps
from typing import Any, Callable

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from config import Config, DevConfig
import models


def create_app(config: type[Config] = DevConfig) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config)

    # Ensure DB exists and has baseline data
    models.init_db(app.config["DB_PATH"], schema_path="schema.sql")
    models.seed_if_empty(app.config["DB_PATH"])

    # ---------------------------------------------------------------------
    # i18n + direction helpers
    # ---------------------------------------------------------------------

    def load_translations(lang: str) -> dict[str, str]:
        path = os.path.join("translations", f"{lang}.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    _translation_cache: dict[str, dict[str, str]] = {}

    def get_lang() -> str:
        lang = session.get("lang") or app.config.get("DEFAULT_LANG", "en")
        if lang not in app.config.get("SUPPORTED_LANGS", ("en", "ar")):
            lang = app.config.get("DEFAULT_LANG", "en")
        return lang

    @app.before_request
    def _inject_globals() -> None:
        g.lang = get_lang()
        g.dir = "rtl" if g.lang == "ar" else "ltr"
        if g.lang not in _translation_cache:
            _translation_cache[g.lang] = load_translations(g.lang)
        g.translations = _translation_cache[g.lang]

        # Current user (if logged in)
        g.user = None
        uid = session.get("user_id")
        if uid:
            with models.connect(app.config["DB_PATH"]) as conn:
                user = models.get_user_by_id(conn, int(uid))
                if user and user["is_active"] == 1:
                    g.user = user
                else:
                    session.clear()

    def t(key: str, default: str | None = None) -> str:
        """
        Translation lookup used by templates: `{{ t('nav.home') }}`.
        """
        return str(g.translations.get(key) or default or key)

    app.jinja_env.globals["t"] = t

    # ---------------------------------------------------------------------
    # Auth / permissions
    # ---------------------------------------------------------------------

    def login_required(view: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(view)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            if not g.user:
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)

        return wrapped

    def role_required(*roles: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(view: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(view)
            def wrapped(*args: Any, **kwargs: Any) -> Any:
                if not g.user:
                    return redirect(url_for("login", next=request.path))
                if g.user["role"] not in roles:
                    abort(403)
                return view(*args, **kwargs)

            return wrapped

        return decorator

    # ---------------------------------------------------------------------
    # Public routes
    # ---------------------------------------------------------------------

    @app.get("/")
    def home() -> str:
        with models.connect(app.config["DB_PATH"]) as conn:
            machines = models.list_machines(conn)
            featured = next((m for m in machines if m["is_featured"] == 1), machines[0] if machines else None)
            gallery = models.list_gallery_items(conn)[:6]
            steps = models.list_process_steps(conn)[:4]
        return render_template(
            "public/home.html",
            machines=machines,
            featured=featured,
            gallery=gallery,
            steps=steps,
        )

    @app.get("/machines")
    def machines() -> str:
        with models.connect(app.config["DB_PATH"]) as conn:
            machines_list = models.list_machines(conn)
        return render_template("public/machines.html", machines=machines_list)

    @app.get("/machines/<slug>")
    def machine_detail(slug: str) -> str:
        with models.connect(app.config["DB_PATH"]) as conn:
            machine = models.get_machine_by_slug(conn, slug)
            if not machine:
                abort(404)
            specs = models.list_specs_for_machine(conn, int(machine["id"]))
            related_gallery = [g for g in models.list_gallery_items(conn) if g["machine_id"] == machine["id"]][:6]
        return render_template("public/machine_detail.html", machine=machine, specs=specs, related_gallery=related_gallery)

    @app.get("/how-it-works")
    def how_it_works() -> str:
        with models.connect(app.config["DB_PATH"]) as conn:
            steps = models.list_process_steps(conn)
        return render_template("public/how_it_works.html", steps=steps)

    @app.get("/specifications")
    def specifications() -> str:
        with models.connect(app.config["DB_PATH"]) as conn:
            machines_list = models.list_machines(conn)
            featured = next((m for m in machines_list if m["is_featured"] == 1), machines_list[0] if machines_list else None)
            specs = models.list_specs_for_machine(conn, int(featured["id"])) if featured else []
        return render_template("public/specifications.html", machines=machines_list, featured=featured, specs=specs)

    @app.get("/applications")
    def applications() -> str:
        with models.connect(app.config["DB_PATH"]) as conn:
            machines_list = models.list_machines(conn)
        return render_template("public/applications.html", machines=machines_list)

    @app.get("/gallery")
    def gallery() -> str:
        with models.connect(app.config["DB_PATH"]) as conn:
            items = models.list_gallery_items(conn)
        categories = sorted({(i["category"] or "Other") for i in items})
        return render_template("public/gallery.html", items=items, categories=categories)

    @app.get("/about")
    def about() -> str:
        return render_template("public/about.html")

    @app.route("/contact", methods=["GET", "POST"])
    def contact() -> str:
        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            email = (request.form.get("email") or "").strip()
            phone = (request.form.get("phone") or "").strip()
            message = (request.form.get("message") or "").strip()
            if not name or not email or not message:
                flash(t("form.required_error"), "danger")
            else:
                with models.connect(app.config["DB_PATH"]) as conn:
                    models.create_inquiry(
                        conn,
                        name=name,
                        email=email,
                        phone=phone or None,
                        message=message,
                        preferred_lang=g.lang,
                        source_page=request.path,
                    )
                flash(t("contact.success"), "success")
                return redirect(url_for("contact"))
        return render_template("public/contact.html")

    # ---------------------------------------------------------------------
    # Language switching
    # ---------------------------------------------------------------------

    @app.post("/lang/<lang_code>")
    def set_lang(lang_code: str) -> Any:
        supported = app.config.get("SUPPORTED_LANGS", ("en", "ar"))
        if lang_code not in supported:
            abort(400)
        session["lang"] = lang_code
        next_url = request.form.get("next") or request.referrer or url_for("home")
        return redirect(next_url)

    # ---------------------------------------------------------------------
    # Login / logout
    # ---------------------------------------------------------------------

    @app.route("/login", methods=["GET", "POST"])
    def login() -> str:
        if request.method == "POST":
            identifier = (request.form.get("identifier") or "").strip()
            password = request.form.get("password") or ""
            with models.connect(app.config["DB_PATH"]) as conn:
                user = models.get_user_by_username_or_email(conn, identifier)
                if user and user["is_active"] == 1 and check_password_hash(user["password_hash"], password):
                    session.clear()
                    session["user_id"] = int(user["id"])
                    models.update_last_login(conn, int(user["id"]))
                    next_url = request.args.get("next") or url_for("admin_dashboard")
                    return redirect(next_url)
            flash(t("login.error"), "danger")
        return render_template("public/login.html")

    @app.post("/logout")
    def logout() -> Any:
        session.clear()
        return redirect(url_for("home"))

    # ---------------------------------------------------------------------
    # Admin routes
    # ---------------------------------------------------------------------

    @app.get("/admin")
    @login_required
    def admin_dashboard() -> str:
        with models.connect(app.config["DB_PATH"]) as conn:
            machines_count = models.query_one(conn, "SELECT COUNT(*) AS c FROM machines")["c"]
            gallery_count = models.query_one(conn, "SELECT COUNT(*) AS c FROM gallery_items")["c"]
            inquiries_new = models.query_one(conn, "SELECT COUNT(*) AS c FROM inquiries WHERE status='new'")["c"]
            pending_subs = models.query_one(conn, "SELECT COUNT(*) AS c FROM submissions WHERE status='pending'")["c"]
        return render_template(
            "admin/dashboard.html",
            machines_count=machines_count,
            gallery_count=gallery_count,
            inquiries_new=inquiries_new,
            pending_subs=pending_subs,
        )

    @app.get("/admin/machines")
    @login_required
    def admin_machines() -> str:
        with models.connect(app.config["DB_PATH"]) as conn:
            machines_list = models.list_machines(conn)
        return render_template("admin/machines.html", machines=machines_list)

    @app.route("/admin/machines/edit", methods=["GET", "POST"])
    @login_required
    def admin_machine_edit() -> Any:
        machine_id = request.args.get("id")
        with models.connect(app.config["DB_PATH"]) as conn:
            machine = models.get_machine_by_id(conn, int(machine_id)) if machine_id else None

            if request.method == "POST":
                data = {
                    "slug": (request.form.get("slug") or "").strip(),
                    "title_en": (request.form.get("title_en") or "").strip(),
                    "title_ar": (request.form.get("title_ar") or "").strip(),
                    "short_desc_en": (request.form.get("short_desc_en") or "").strip(),
                    "short_desc_ar": (request.form.get("short_desc_ar") or "").strip(),
                    "long_desc_en": (request.form.get("long_desc_en") or "").strip(),
                    "long_desc_ar": (request.form.get("long_desc_ar") or "").strip(),
                    "category": (request.form.get("category") or "").strip() or None,
                    "image_path": (request.form.get("image_path") or "").strip() or None,
                    "is_featured": 1 if request.form.get("is_featured") == "1" else 0,
                    "sort_order": int(request.form.get("sort_order") or 0),
                }

                if g.user["role"] == "developer":
                    models.create_submission(
                        conn,
                        created_by_user_id=int(g.user["id"]),
                        target_table="machines",
                        action="update" if machine else "create",
                        target_id=int(machine["id"]) if machine else None,
                        payload=data,
                    )
                    flash(t("flash.submitted_for_approval"), "info")
                    return redirect(url_for("admin_machines"))

                models.upsert_machine(conn, int(machine["id"]) if machine else None, data)
                flash(t("flash.saved"), "success")
                return redirect(url_for("admin_machines"))

        return render_template("admin/machine_edit.html", machine=machine)

    @app.post("/admin/machines/delete")
    @role_required("admin_developer")
    def admin_machine_delete() -> Any:
        machine_id = int(request.form.get("id") or 0)
        with models.connect(app.config["DB_PATH"]) as conn:
            models.delete_machine(conn, machine_id)
        flash(t("flash.deleted"), "success")
        return redirect(url_for("admin_machines"))

    @app.get("/admin/gallery")
    @login_required
    def admin_gallery() -> str:
        with models.connect(app.config["DB_PATH"]) as conn:
            items = models.list_gallery_items(conn, include_unpublished=True)
        return render_template("admin/gallery.html", items=items)

    @app.route("/admin/gallery/edit", methods=["GET", "POST"])
    @login_required
    def admin_gallery_edit() -> Any:
        item_id = request.args.get("id")
        with models.connect(app.config["DB_PATH"]) as conn:
            item = models.query_one(conn, "SELECT * FROM gallery_items WHERE id=?", (int(item_id),)) if item_id else None
            machines_list = models.list_machines(conn)

            if request.method == "POST":
                data = {
                    "machine_id": int(request.form.get("machine_id") or 0) or None,
                    "title_en": (request.form.get("title_en") or "").strip(),
                    "title_ar": (request.form.get("title_ar") or "").strip(),
                    "description_en": (request.form.get("description_en") or "").strip(),
                    "description_ar": (request.form.get("description_ar") or "").strip(),
                    "category": (request.form.get("category") or "").strip() or None,
                    "image_path": (request.form.get("image_path") or "").strip(),
                    "is_published": 1 if request.form.get("is_published") == "1" else 0,
                    "sort_order": int(request.form.get("sort_order") or 0),
                }

                if g.user["role"] == "developer":
                    models.create_submission(
                        conn,
                        created_by_user_id=int(g.user["id"]),
                        target_table="gallery_items",
                        action="update" if item else "create",
                        target_id=int(item["id"]) if item else None,
                        payload=data,
                    )
                    flash(t("flash.submitted_for_approval"), "info")
                    return redirect(url_for("admin_gallery"))

                models.upsert_gallery_item(conn, int(item["id"]) if item else None, data)
                flash(t("flash.saved"), "success")
                return redirect(url_for("admin_gallery"))

        return render_template("admin/gallery_edit.html", item=item, machines=machines_list)

    @app.post("/admin/gallery/delete")
    @role_required("admin_developer")
    def admin_gallery_delete() -> Any:
        item_id = int(request.form.get("id") or 0)
        with models.connect(app.config["DB_PATH"]) as conn:
            models.delete_gallery_item(conn, item_id)
        flash(t("flash.deleted"), "success")
        return redirect(url_for("admin_gallery"))

    @app.get("/admin/specifications")
    @login_required
    def admin_specifications() -> str:
        with models.connect(app.config["DB_PATH"]) as conn:
            machines_list = models.list_machines(conn)
            rows = models.query_all(
                conn,
                """
                SELECT s.*, m.title_en AS machine_title_en, m.title_ar AS machine_title_ar
                FROM specifications s
                JOIN machines m ON m.id = s.machine_id
                ORDER BY m.sort_order ASC, s.sort_order ASC
                """,
            )
        return render_template("admin/specifications.html", machines=machines_list, specs=rows)

    @app.route("/admin/specifications/edit", methods=["GET", "POST"])
    @login_required
    def admin_spec_edit() -> Any:
        spec_id = request.args.get("id")
        with models.connect(app.config["DB_PATH"]) as conn:
            spec = models.query_one(conn, "SELECT * FROM specifications WHERE id=?", (int(spec_id),)) if spec_id else None
            machines_list = models.list_machines(conn)

            if request.method == "POST":
                data = {
                    "machine_id": int(request.form.get("machine_id") or 0),
                    "field_key": (request.form.get("field_key") or "").strip(),
                    "value_en": (request.form.get("value_en") or "").strip(),
                    "value_ar": (request.form.get("value_ar") or "").strip(),
                    "unit": (request.form.get("unit") or "").strip() or None,
                    "sort_order": int(request.form.get("sort_order") or 0),
                }

                if g.user["role"] == "developer":
                    models.create_submission(
                        conn,
                        created_by_user_id=int(g.user["id"]),
                        target_table="specifications",
                        action="update" if spec else "create",
                        target_id=int(spec["id"]) if spec else None,
                        payload=data,
                    )
                    flash(t("flash.submitted_for_approval"), "info")
                    return redirect(url_for("admin_specifications"))

                models.upsert_spec(conn, int(spec["id"]) if spec else None, data)
                flash(t("flash.saved"), "success")
                return redirect(url_for("admin_specifications"))

        return render_template("admin/spec_edit.html", spec=spec, machines=machines_list)

    @app.post("/admin/specifications/delete")
    @role_required("admin_developer")
    def admin_spec_delete() -> Any:
        spec_id = int(request.form.get("id") or 0)
        with models.connect(app.config["DB_PATH"]) as conn:
            models.delete_spec(conn, spec_id)
        flash(t("flash.deleted"), "success")
        return redirect(url_for("admin_specifications"))

    @app.get("/admin/inquiries")
    @login_required
    def admin_inquiries() -> str:
        with models.connect(app.config["DB_PATH"]) as conn:
            inquiries = models.list_inquiries(conn)
        return render_template("admin/inquiries.html", inquiries=inquiries)

    @app.post("/admin/inquiries/status")
    @login_required
    def admin_inquiry_status() -> Any:
        inquiry_id = int(request.form.get("id") or 0)
        status = (request.form.get("status") or "new").strip()
        with models.connect(app.config["DB_PATH"]) as conn:
            models.set_inquiry_status(conn, inquiry_id, status)
        flash(t("flash.updated"), "success")
        return redirect(url_for("admin_inquiries"))

    @app.get("/admin/users")
    @role_required("admin_developer")
    def admin_users() -> str:
        with models.connect(app.config["DB_PATH"]) as conn:
            users = models.list_users(conn)
        return render_template("admin/users.html", users=users)

    @app.post("/admin/users/toggle")
    @role_required("admin_developer")
    def admin_user_toggle() -> Any:
        user_id = int(request.form.get("id") or 0)
        is_active = request.form.get("is_active") == "1"
        with models.connect(app.config["DB_PATH"]) as conn:
            models.set_user_active(conn, user_id, is_active)
        flash(t("flash.updated"), "success")
        return redirect(url_for("admin_users"))

    @app.route("/admin/users/create", methods=["GET", "POST"])
    @role_required("admin_developer")
    def admin_user_create() -> Any:
        """
        User creation is restricted to admin_developer.

        This exists to satisfy typical QA expectations for "user management" in
        graduation/portfolio demos, while keeping the workflow simple.
        """
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            email = (request.form.get("email") or "").strip()
            role = (request.form.get("role") or "developer").strip()
            password = request.form.get("password") or ""

            if not username or not email or not password or role not in ("admin_developer", "developer"):
                flash(t("form.required_error"), "danger")
            else:
                with models.connect(app.config["DB_PATH"]) as conn:
                    try:
                        models.create_user(conn, username=username, email=email, password=password, role=role)
                    except Exception:
                        # Avoid leaking DB details in UI; keep message user-friendly.
                        flash(t("login.error"), "danger")
                        return redirect(url_for("admin_user_create"))
                flash(t("flash.saved"), "success")
                return redirect(url_for("admin_users"))

        return render_template("admin/user_create.html")

    @app.get("/admin/review")
    @role_required("admin_developer")
    def admin_review() -> str:
        with models.connect(app.config["DB_PATH"]) as conn:
            pending = models.list_submissions(conn, status="pending")
        return render_template("admin/review.html", submissions=pending)

    @app.get("/admin/review/<int:submission_id>")
    @role_required("admin_developer")
    def admin_review_detail(submission_id: int) -> str:
        with models.connect(app.config["DB_PATH"]) as conn:
            sub = models.get_submission(conn, submission_id)
            if not sub:
                abort(404)
            creator = models.get_user_by_id(conn, int(sub["created_by_user_id"]))
        payload = json.loads(sub["payload_json"])
        return render_template("admin/review_detail.html", submission=sub, creator=creator, payload=payload)

    @app.post("/admin/review/<int:submission_id>/decision")
    @role_required("admin_developer")
    def admin_review_decision(submission_id: int) -> Any:
        decision = request.form.get("decision")
        note = (request.form.get("note") or "").strip() or None
        approve = decision == "approve"
        with models.connect(app.config["DB_PATH"]) as conn:
            models.review_submission(
                conn,
                submission_id=submission_id,
                reviewer_user_id=int(g.user["id"]),
                approve=approve,
                reviewer_note=note,
            )
        flash(t("flash.decision_recorded"), "success")
        return redirect(url_for("admin_review"))

    # ---------------------------------------------------------------------
    # Errors
    # ---------------------------------------------------------------------

    @app.errorhandler(403)
    def _403(_: Any) -> Any:
        return render_template("public/error.html", code=403, message="Forbidden"), 403

    @app.errorhandler(404)
    def _404(_: Any) -> Any:
        return render_template("public/error.html", code=404, message="Not found"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run()

