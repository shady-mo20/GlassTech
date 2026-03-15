"""
Database access layer (SQLite).

Design goals:
- Keep the project easy to run on Windows without additional services.
- Use explicit SQL and small, well-named functions instead of a heavy ORM.
- Centralize ALL DB access here so templates/routes remain clean.
- Provide seed data that matches the machine image set and bilingual content.

Important:
- This repository originally contained only the Envato frontend template.
  The backend is implemented here to satisfy the requested architecture.
"""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any, Iterable, Optional

from werkzeug.security import generate_password_hash


def _ensure_instance_dir(db_path: str) -> None:
    instance_dir = os.path.dirname(db_path)
    if instance_dir and not os.path.exists(instance_dir):
        os.makedirs(instance_dir, exist_ok=True)


def connect(db_path: str) -> sqlite3.Connection:
    _ensure_instance_dir(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str, schema_path: str = "schema.sql") -> None:
    """
    Initialize tables. Safe to run multiple times.
    """
    with connect(db_path) as conn:
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())


def query_one(conn: sqlite3.Connection, sql: str, args: Iterable[Any] = ()) -> Optional[sqlite3.Row]:
    cur = conn.execute(sql, tuple(args))
    return cur.fetchone()


def query_all(conn: sqlite3.Connection, sql: str, args: Iterable[Any] = ()) -> list[sqlite3.Row]:
    cur = conn.execute(sql, tuple(args))
    return cur.fetchall()


def execute(conn: sqlite3.Connection, sql: str, args: Iterable[Any] = ()) -> int:
    cur = conn.execute(sql, tuple(args))
    return int(cur.lastrowid or 0)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> Optional[sqlite3.Row]:
    return query_one(conn, "SELECT * FROM users WHERE id = ?", (user_id,))


def get_user_by_username_or_email(conn: sqlite3.Connection, identifier: str) -> Optional[sqlite3.Row]:
    return query_one(
        conn,
        "SELECT * FROM users WHERE lower(username)=lower(?) OR lower(email)=lower(?)",
        (identifier, identifier),
    )


def list_users(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return query_all(conn, "SELECT * FROM users ORDER BY created_at DESC")


def create_user(conn: sqlite3.Connection, username: str, email: str, password: str, role: str) -> int:
    return execute(
        conn,
        """
        INSERT INTO users (username, email, password_hash, role)
        VALUES (?, ?, ?, ?)
        """,
        (username, email, generate_password_hash(password), role),
    )


def set_user_active(conn: sqlite3.Connection, user_id: int, is_active: bool) -> None:
    execute(conn, "UPDATE users SET is_active=? WHERE id=?", (1 if is_active else 0, user_id))


def update_last_login(conn: sqlite3.Connection, user_id: int) -> None:
    execute(conn, "UPDATE users SET last_login_at=datetime('now') WHERE id=?", (user_id,))


# ---------------------------------------------------------------------------
# Machines
# ---------------------------------------------------------------------------

def list_machines(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return query_all(conn, "SELECT * FROM machines ORDER BY is_featured DESC, sort_order ASC, id ASC")


def get_machine_by_slug(conn: sqlite3.Connection, slug: str) -> Optional[sqlite3.Row]:
    return query_one(conn, "SELECT * FROM machines WHERE slug = ?", (slug,))


def get_machine_by_id(conn: sqlite3.Connection, machine_id: int) -> Optional[sqlite3.Row]:
    return query_one(conn, "SELECT * FROM machines WHERE id = ?", (machine_id,))


def upsert_machine(conn: sqlite3.Connection, machine_id: Optional[int], data: dict[str, Any]) -> int:
    fields = [
        "slug",
        "title_en",
        "title_ar",
        "short_desc_en",
        "short_desc_ar",
        "long_desc_en",
        "long_desc_ar",
        "category",
        "image_path",
        "is_featured",
        "sort_order",
    ]
    values = [data.get(f) for f in fields]
    if machine_id is None:
        return execute(
            conn,
            f"""
            INSERT INTO machines ({",".join(fields)})
            VALUES ({",".join(["?"] * len(fields))})
            """,
            values,
        )
    execute(
        conn,
        f"""
        UPDATE machines SET
            {",".join([f"{f}=?" for f in fields])},
            updated_at=datetime('now')
        WHERE id=?
        """,
        values + [machine_id],
    )
    return int(machine_id)


def delete_machine(conn: sqlite3.Connection, machine_id: int) -> None:
    execute(conn, "DELETE FROM machines WHERE id=?", (machine_id,))


# ---------------------------------------------------------------------------
# Specifications
# ---------------------------------------------------------------------------

def list_specs_for_machine(conn: sqlite3.Connection, machine_id: int) -> list[sqlite3.Row]:
    return query_all(
        conn,
        "SELECT * FROM specifications WHERE machine_id=? ORDER BY sort_order ASC, id ASC",
        (machine_id,),
    )


def upsert_spec(conn: sqlite3.Connection, spec_id: Optional[int], data: dict[str, Any]) -> int:
    fields = ["machine_id", "field_key", "value_en", "value_ar", "unit", "sort_order"]
    values = [data.get(f) for f in fields]
    if spec_id is None:
        return execute(
            conn,
            f"INSERT INTO specifications ({','.join(fields)}) VALUES ({','.join(['?']*len(fields))})",
            values,
        )
    execute(
        conn,
        f"""
        UPDATE specifications SET
            {",".join([f"{f}=?" for f in fields])},
            updated_at=datetime('now')
        WHERE id=?
        """,
        values + [spec_id],
    )
    return int(spec_id)


def delete_spec(conn: sqlite3.Connection, spec_id: int) -> None:
    execute(conn, "DELETE FROM specifications WHERE id=?", (spec_id,))


# ---------------------------------------------------------------------------
# Gallery
# ---------------------------------------------------------------------------

def list_gallery_items(conn: sqlite3.Connection, include_unpublished: bool = False) -> list[sqlite3.Row]:
    if include_unpublished:
        return query_all(conn, "SELECT * FROM gallery_items ORDER BY sort_order ASC, id ASC")
    return query_all(
        conn, "SELECT * FROM gallery_items WHERE is_published=1 ORDER BY sort_order ASC, id ASC"
    )


def upsert_gallery_item(conn: sqlite3.Connection, item_id: Optional[int], data: dict[str, Any]) -> int:
    fields = [
        "machine_id",
        "title_en",
        "title_ar",
        "description_en",
        "description_ar",
        "category",
        "image_path",
        "is_published",
        "sort_order",
    ]
    values = [data.get(f) for f in fields]
    if item_id is None:
        return execute(
            conn,
            f"INSERT INTO gallery_items ({','.join(fields)}) VALUES ({','.join(['?']*len(fields))})",
            values,
        )
    execute(
        conn,
        f"""
        UPDATE gallery_items SET
            {",".join([f"{f}=?" for f in fields])},
            updated_at=datetime('now')
        WHERE id=?
        """,
        values + [item_id],
    )
    return int(item_id)


def delete_gallery_item(conn: sqlite3.Connection, item_id: int) -> None:
    execute(conn, "DELETE FROM gallery_items WHERE id=?", (item_id,))


# ---------------------------------------------------------------------------
# Process Steps
# ---------------------------------------------------------------------------

def list_process_steps(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return query_all(conn, "SELECT * FROM process_steps ORDER BY step_no ASC, id ASC")


def upsert_process_step(conn: sqlite3.Connection, step_id: Optional[int], data: dict[str, Any]) -> int:
    fields = ["step_no", "title_en", "title_ar", "description_en", "description_ar", "icon"]
    values = [data.get(f) for f in fields]
    if step_id is None:
        return execute(
            conn,
            f"INSERT INTO process_steps ({','.join(fields)}) VALUES ({','.join(['?']*len(fields))})",
            values,
        )
    execute(
        conn,
        f"""
        UPDATE process_steps SET
            {",".join([f"{f}=?" for f in fields])},
            updated_at=datetime('now')
        WHERE id=?
        """,
        values + [step_id],
    )
    return int(step_id)


def delete_process_step(conn: sqlite3.Connection, step_id: int) -> None:
    execute(conn, "DELETE FROM process_steps WHERE id=?", (step_id,))


# ---------------------------------------------------------------------------
# Inquiries
# ---------------------------------------------------------------------------

def create_inquiry(
    conn: sqlite3.Connection,
    *,
    name: str,
    email: str,
    phone: str | None,
    message: str,
    preferred_lang: str,
    source_page: str | None,
) -> int:
    return execute(
        conn,
        """
        INSERT INTO inquiries (name, email, phone, message, preferred_lang, source_page)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, email, phone, message, preferred_lang, source_page),
    )


def list_inquiries(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return query_all(conn, "SELECT * FROM inquiries ORDER BY created_at DESC")


def set_inquiry_status(conn: sqlite3.Connection, inquiry_id: int, status: str) -> None:
    execute(conn, "UPDATE inquiries SET status=? WHERE id=?", (status, inquiry_id))


# ---------------------------------------------------------------------------
# Submissions (approval workflow)
# ---------------------------------------------------------------------------

def list_submissions(conn: sqlite3.Connection, status: Optional[str] = None) -> list[sqlite3.Row]:
    if status:
        return query_all(conn, "SELECT * FROM submissions WHERE status=? ORDER BY created_at DESC", (status,))
    return query_all(conn, "SELECT * FROM submissions ORDER BY created_at DESC")


def create_submission(
    conn: sqlite3.Connection,
    *,
    created_by_user_id: int,
    target_table: str,
    action: str,
    target_id: int | None,
    payload: dict[str, Any],
) -> int:
    return execute(
        conn,
        """
        INSERT INTO submissions (created_by_user_id, target_table, action, target_id, payload_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (created_by_user_id, target_table, action, target_id, json.dumps(payload, ensure_ascii=False)),
    )


def get_submission(conn: sqlite3.Connection, submission_id: int) -> Optional[sqlite3.Row]:
    return query_one(conn, "SELECT * FROM submissions WHERE id=?", (submission_id,))


def review_submission(
    conn: sqlite3.Connection,
    *,
    submission_id: int,
    reviewer_user_id: int,
    approve: bool,
    reviewer_note: str | None,
) -> None:
    """
    Approve or reject a submission.

    Approvals apply the payload to the target table. This keeps a single source of truth
    and makes developer/non-admin contributions reviewable.
    """
    sub = get_submission(conn, submission_id)
    if not sub or sub["status"] != "pending":
        return

    if approve:
        payload = json.loads(sub["payload_json"])
        _apply_submission_payload(conn, sub["target_table"], sub["action"], sub["target_id"], payload)
        status = "approved"
    else:
        status = "rejected"

    execute(
        conn,
        """
        UPDATE submissions
        SET status=?, reviewer_user_id=?, reviewer_note=?, reviewed_at=datetime('now')
        WHERE id=?
        """,
        (status, reviewer_user_id, reviewer_note, submission_id),
    )


def _apply_submission_payload(
    conn: sqlite3.Connection, target_table: str, action: str, target_id: int | None, payload: dict[str, Any]
) -> None:
    """
    Internal: apply approved changes. Only supports explicitly allowed tables.

    This is deliberately restrictive to reduce risk of SQL injection or accidental
    schema violations.
    """
    if target_table == "machines":
        if action in ("create", "update"):
            upsert_machine(conn, None if action == "create" else int(target_id), payload)
        elif action == "delete" and target_id is not None:
            delete_machine(conn, int(target_id))
        return
    if target_table == "specifications":
        if action in ("create", "update"):
            upsert_spec(conn, None if action == "create" else int(target_id), payload)
        elif action == "delete" and target_id is not None:
            delete_spec(conn, int(target_id))
        return
    if target_table == "gallery_items":
        if action in ("create", "update"):
            upsert_gallery_item(conn, None if action == "create" else int(target_id), payload)
        elif action == "delete" and target_id is not None:
            delete_gallery_item(conn, int(target_id))
        return
    if target_table == "process_steps":
        if action in ("create", "update"):
            upsert_process_step(conn, None if action == "create" else int(target_id), payload)
        elif action == "delete" and target_id is not None:
            delete_process_step(conn, int(target_id))
        return
    if target_table == "users":
        # We intentionally do not allow user deletion/creation via submissions in this
        # simplified implementation. User management stays direct-admin only.
        return


# ---------------------------------------------------------------------------
# Seeding (machines + gallery + process steps + an initial admin account)
# ---------------------------------------------------------------------------

def seed_if_empty(db_path: str) -> None:
    """
    Seed database with premium bilingual content and machine images if tables are empty.
    """
    with connect(db_path) as conn:
        user_count = query_one(conn, "SELECT COUNT(*) AS c FROM users")["c"]
        if user_count == 0:
            # Default credentials are documented in README and intended for local development only.
            create_user(conn, username="admin", email="admin@example.com", password="Admin@12345", role="admin_developer")
            create_user(conn, username="dev", email="dev@example.com", password="Dev@12345", role="developer")

        machine_count = query_one(conn, "SELECT COUNT(*) AS c FROM machines")["c"]
        if machine_count == 0:
            machines = [
                {
                    "slug": "glass-tempering-furnace",
                    "title_en": "Glass Tempering Furnace",
                    "title_ar": "فرن تقسية الزجاج",
                    "short_desc_en": "High-capacity thermal processing system engineered for controlled heating and stable industrial tempering.",
                    "short_desc_ar": "نظام معالجة حرارية عالي الكفاءة مصمم للتحكم الدقيق في التسخين وتحقيق أداء صناعي ثابت في التقسية.",
                    "long_desc_en": (
                        "A production-grade tempering platform designed for consistent heat distribution, controlled transfer, and repeatable quenching. "
                        "Built to support safety glass manufacturing with stable output quality, operator safety, and scalable throughput."
                    ),
                    "long_desc_ar": (
                        "منصة تقسية صناعية مصممة لتوزيع حراري متوازن، ونقل مُتحكم به، وتبريد سريع قابل للتكرار. "
                        "مجهزة لدعم تصنيع الزجاج الآمن بجودة ثابتة، وسلامة تشغيل عالية، وقدرة إنتاج قابلة للتوسع."
                    ),
                    "category": "Tempering",
                    "image_path": "images/machines/glass_tempering_furnace.png",
                    "is_featured": 1,
                    "sort_order": 1,
                },
                {
                    "slug": "integrated-production-line",
                    "title_en": "Integrated Glass Production Line",
                    "title_ar": "خط إنتاج زجاج متكامل",
                    "short_desc_en": "Continuous processing line optimized for throughput, workflow control, and large-scale manufacturing stability.",
                    "short_desc_ar": "خط تشغيل مستمر مُحسن لرفع الإنتاجية وتنظيم تدفق العمل وتحقيق الاستقرار في التصنيع واسع النطاق.",
                    "long_desc_en": (
                        "An integrated line that connects upstream preparation with downstream processing to reduce idle time and stabilize production. "
                        "Designed for predictable scheduling, efficient material movement, and clean handoffs between stations."
                    ),
                    "long_desc_ar": (
                        "خط متكامل يربط مراحل التحضير بالمراحل اللاحقة لتقليل التوقفات وتحقيق استقرار الإنتاج. "
                        "مصمم لجدولة واضحة، وحركة مواد فعالة، وتسليم منظم بين محطات التشغيل."
                    ),
                    "category": "Production Line",
                    "image_path": "images/machines/production_line.png",
                    "is_featured": 0,
                    "sort_order": 2,
                },
                {
                    "slug": "cnc-glass-cutting-machine",
                    "title_en": "CNC Glass Cutting Machine",
                    "title_ar": "ماكينة CNC لقطع الزجاج",
                    "short_desc_en": "Precision cutting equipment for accurate sheet preparation, repeatable quality, and optimized material utilization.",
                    "short_desc_ar": "معدات قطع دقيقة لتجهيز الألواح بدقة عالية وجودة متكررة وتحسين استغلال الخامات.",
                    "long_desc_en": (
                        "CNC-driven cutting designed for stable positioning, accurate paths, and repeatable outcomes across production batches. "
                        "Supports improved yield and clean preparation for tempering, laminating, and finishing stages."
                    ),
                    "long_desc_ar": (
                        "نظام قطع يعمل بالتحكم الرقمي CNC لضمان تثبيت مستقر ومسارات دقيقة ونتائج قابلة للتكرار عبر دفعات الإنتاج. "
                        "يساعد على رفع العائد وتقليل الهدر وتجهيز نظيف لمراحل التقسية والتغليف والتشطيب."
                    ),
                    "category": "Cutting",
                    "image_path": "images/machines/cnc_glass_cutting_machine.png",
                    "is_featured": 0,
                    "sort_order": 3,
                },
                {
                    "slug": "cnc-glass-engraving-center",
                    "title_en": "CNC Glass Engraving Center",
                    "title_ar": "مركز CNC لنقش وتشغيل الزجاج",
                    "short_desc_en": "Advanced engraving system for controlled shaping, fine detailing, and consistent machining accuracy.",
                    "short_desc_ar": "نظام نقش وتشغيل متقدم للتحكم في التشكيل وتحقيق تفاصيل دقيقة وثبات في دقة التشغيل.",
                    "long_desc_en": (
                        "A machining and engraving center built for reliable motion control and fine detailing on glass surfaces. "
                        "Designed for decorative applications and functional markings with stable accuracy."
                    ),
                    "long_desc_ar": (
                        "مركز نقش وتشغيل مصمم للتحكم الدقيق في الحركة وإنتاج تفاصيل دقيقة على أسطح الزجاج. "
                        "مناسب للتطبيقات الزخرفية والعلامات الوظيفية مع ثبات في الدقة."
                    ),
                    "category": "Engraving",
                    "image_path": "images/machines/cnc_glass_engraving_center.png",
                    "is_featured": 0,
                    "sort_order": 4,
                },
                {
                    "slug": "glass-storage-rack",
                    "title_en": "Glass Storage Rack",
                    "title_ar": "راك تخزين الزجاج",
                    "short_desc_en": "Industrial storage solution for safe positioning, workflow organization, and efficient movement inside facilities.",
                    "short_desc_ar": "حل صناعي لتخزين الزجاج يضمن تموضعًا آمنًا وتنظيم تدفق العمل وحركة فعالة داخل المصنع.",
                    "long_desc_en": (
                        "A handling and storage system engineered to reduce breakage risk and improve shop-floor organization. "
                        "Supports controlled access, safer transport, and cleaner staging between processes."
                    ),
                    "long_desc_ar": (
                        "نظام تخزين ومناولة مصمم لتقليل مخاطر الكسر وتحسين تنظيم أرضية المصنع. "
                        "يوفر وصولًا منظمًا ونقلًا أكثر أمانًا وتجهيزًا أفضل بين مراحل التشغيل."
                    ),
                    "category": "Storage",
                    "image_path": "images/machines/glass_storage_rack.png",
                    "is_featured": 0,
                    "sort_order": 5,
                },
                {
                    "slug": "fully-automatic-line-cutting-system",
                    "title_en": "Fully Automatic Glass Line Cutting System",
                    "title_ar": "نظام أوتوماتيكي كامل لخط قطع الزجاج",
                    "short_desc_en": "Automated feeding and preparation built for streamlined movement and efficient front-end processing.",
                    "short_desc_ar": "حل أوتوماتيكي لتغذية الألواح وتحريكها بشكل منظم وتحضير فعال لمراحل التشغيل الأولى.",
                    "long_desc_en": (
                        "A front-end automation module focused on stable feeding, controlled movement, and smooth preparation for cutting/processing stations. "
                        "Optimized for predictable cycle times and reduced manual handling."
                    ),
                    "long_desc_ar": (
                        "وحدة أتمتة للمرحلة الأولى تركز على تغذية مستقرة وحركة مُتحكم بها وتجهيز سلس لمحطات القطع والتشغيل. "
                        "محسنة لزمن دورة متوقع وتقليل المناولة اليدوية."
                    ),
                    "category": "Automation",
                    "image_path": "images/machines/line_cutting_automatic.png",
                    "is_featured": 0,
                    "sort_order": 6,
                },
                {
                    "slug": "precision-high-sankin-processing-line",
                    "title_en": "Precision High SANKIN Processing Line",
                    "title_ar": "خط تشغيل عالي الدقة من SANKIN",
                    "short_desc_en": "High-precision processing line designed for refined finishing and consistent production quality.",
                    "short_desc_ar": "خط معالجة عالي الدقة للتشطيب المتقن والثبات الميكانيكي والحفاظ على جودة إنتاج متسقة.",
                    "long_desc_en": (
                        "A precision-focused line for finishing and process stability, built to reduce variance and maintain consistent output quality. "
                        "Supports industrial-grade operation under continuous production conditions."
                    ),
                    "long_desc_ar": (
                        "خط معالجة يركز على الدقة في التشطيب واستقرار العمليات، لتقليل التفاوت والحفاظ على جودة خرج متسقة. "
                        "يدعم التشغيل الصناعي تحت ظروف إنتاج مستمر."
                    ),
                    "category": "Processing",
                    "image_path": "images/machines/precision_high_sankin.png",
                    "is_featured": 0,
                    "sort_order": 7,
                },
                {
                    "slug": "2436sktf-industrial-glass-unit",
                    "title_en": "2436SKTF Industrial Glass Unit",
                    "title_ar": "وحدة تشغيل زجاج صناعية 2436SKTF",
                    "short_desc_en": "Industrial processing unit built for reliable operation, continuity, and stable performance in demanding environments.",
                    "short_desc_ar": "وحدة تشغيل صناعية مصممة للاعتمادية واستمرارية الإنتاج وأداء مستقر في بيئات تشغيل قاسية.",
                    "long_desc_en": (
                        "A robust industrial unit designed to keep production moving with stable mechanical performance and simplified maintenance access. "
                        "Built for long operating hours and repeatable results."
                    ),
                    "long_desc_ar": (
                        "وحدة صناعية متينة مصممة لضمان استمرارية الإنتاج بأداء ميكانيكي ثابت وإتاحة صيانة مبسطة. "
                        "مجهزة لساعات تشغيل طويلة ونتائج قابلة للتكرار."
                    ),
                    "category": "Industrial Unit",
                    "image_path": "images/machines/2436sktf.png",
                    "is_featured": 0,
                    "sort_order": 8,
                },
            ]
            for m in machines:
                upsert_machine(conn, None, m)

        # Seed process steps if missing
        steps_count = query_one(conn, "SELECT COUNT(*) AS c FROM process_steps")["c"]
        if steps_count == 0:
            steps = [
                (
                    1,
                    "Glass Loading",
                    "تحميل الزجاج",
                    "Sheets are staged and aligned for stable transfer into the heating zone with minimal handling risk.",
                    "يتم تجهيز الألواح ومحاذاتها لضمان نقل مستقر إلى منطقة التسخين مع تقليل مخاطر المناولة.",
                    "ion-ios-filing",
                ),
                (
                    2,
                    "Controlled Heating",
                    "تسخين مُتحكم به",
                    "Temperature is raised under controlled profiles to achieve uniform thermal distribution across the glass.",
                    "ترتفع درجة الحرارة وفق منحنيات تشغيل مُتحكم بها لتحقيق توزيع حراري متوازن على كامل اللوح.",
                    "ion-ios-rocket",
                ),
                (
                    3,
                    "Transfer to Quenching",
                    "النقل إلى منطقة التبريد السريع",
                    "Heated glass is transferred with synchronized motion to preserve flatness and timing precision.",
                    "يتم نقل الزجاج الساخن بحركة متزامنة للحفاظ على الاستواء ودقة التوقيت.",
                    "ion-md-football",
                ),
                (
                    4,
                    "Rapid Cooling / Tempering",
                    "تبريد سريع / تقسية",
                    "High-flow air quenching strengthens the glass structure, producing safety-grade tempered output.",
                    "يؤدي التبريد السريع بتدفق هواء قوي إلى تقوية بنية الزجاج وإنتاج زجاج مقسّى بمواصفات أمان.",
                    "ion-ios-briefcase",
                ),
                (
                    5,
                    "Inspection & Unloading",
                    "فحص وتفريغ",
                    "Outputs are checked for quality indicators before safe unloading and staging for downstream processes.",
                    "يتم فحص المخرجات وفق مؤشرات جودة قبل التفريغ الآمن وتجهيزها للمراحل اللاحقة.",
                    "ion-md-checkmark-circle",
                ),
                (
                    6,
                    "Downstream Integration",
                    "تكامل المراحل اللاحقة",
                    "Cutting, engraving, storage, and automated handling are integrated to maintain throughput and reduce downtime.",
                    "يتم دمج القطع والنقش والتخزين والمناولة الآلية للحفاظ على الإنتاجية وتقليل التوقفات.",
                    "ion-md-paper-plane",
                ),
            ]
            for s in steps:
                upsert_process_step(
                    conn,
                    None,
                    {
                        "step_no": s[0],
                        "title_en": s[1],
                        "title_ar": s[2],
                        "description_en": s[3],
                        "description_ar": s[4],
                        "icon": s[5],
                    },
                )

        # Seed gallery from machines if missing
        gallery_count = query_one(conn, "SELECT COUNT(*) AS c FROM gallery_items")["c"]
        if gallery_count == 0:
            machines_rows = list_machines(conn)
            for idx, m in enumerate(machines_rows, start=1):
                upsert_gallery_item(
                    conn,
                    None,
                    {
                        "machine_id": m["id"],
                        "title_en": m["title_en"],
                        "title_ar": m["title_ar"],
                        "description_en": m["short_desc_en"],
                        "description_ar": m["short_desc_ar"],
                        "category": m["category"],
                        "image_path": m["image_path"],
                        "is_published": 1,
                        "sort_order": idx,
                    },
                )

        # Seed baseline specs for the featured tempering furnace if none exist
        spec_count = query_one(conn, "SELECT COUNT(*) AS c FROM specifications")["c"]
        if spec_count == 0:
            featured = query_one(conn, "SELECT id FROM machines WHERE is_featured=1 ORDER BY sort_order ASC LIMIT 1")
            if featured:
                mid = int(featured["id"])
                specs = [
                    ("machine_name", "Glass Tempering Furnace", "فرن تقسية الزجاج", None, 1),
                    ("machine_type", "Continuous Industrial Tempering", "تقسية صناعية مستمرة", None, 2),
                    ("production_function", "Controlled heating + air quenching", "تسخين مُتحكم به + تبريد هوائي سريع", None, 3),
                    ("heating_temperature", "Up to 700°C (process dependent)", "حتى 700°م (حسب العملية)", "°C", 4),
                    ("capacity", "Configurable line throughput", "سعة قابلة للضبط حسب الخط", None, 5),
                    ("power_consumption", "Optimized industrial load profile", "استهلاك مُحسن للأحمال الصناعية", None, 6),
                    ("voltage", "380V / 50Hz (configurable)", "380 فولت / 50 هرتز (قابل للتهيئة)", None, 7),
                    ("dimensions", "Site-dependent configuration", "تكوين حسب موقع التركيب", None, 8),
                    ("weight", "Depends on furnace size", "يعتمد على حجم الفرن", None, 9),
                    ("material_compatibility", "Float glass / safety glass workflow", "زجاج فلوت / مسار زجاج الأمان", None, 10),
                    ("automation_level", "PLC-assisted automation", "أتمتة بمساعدة PLC", None, 11),
                    ("control_method", "HMI + sensor feedback", "واجهة تشغيل HMI + حساسات مراقبة", None, 12),
                    ("safety_features", "Interlocks, emergency stop, thermal safeguards", "أقفال أمان، إيقاف طوارئ، حماية حرارية", None, 13),
                    ("output_quality", "Stable tempering consistency", "ثبات في جودة التقسية", None, 14),
                ]
                for field_key, ve, va, unit, order in specs:
                    upsert_spec(
                        conn,
                        None,
                        {
                            "machine_id": mid,
                            "field_key": field_key,
                            "value_en": ve,
                            "value_ar": va,
                            "unit": unit,
                            "sort_order": order,
                        },
                    )

