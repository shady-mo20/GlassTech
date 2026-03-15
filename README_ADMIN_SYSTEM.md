# Admin system, roles, and approval workflow

## Roles

### `admin_developer`

- Full access to admin routes
- Can create/update/delete content directly
- Can review and approve/reject submissions
- Can activate/deactivate users

### `developer`

- Can access admin dashboard and management pages
- When editing Machines / Gallery / Specs:
  - The change is **saved as a submission** (pending)
  - It is **not applied** to the live database until approved by an admin

## Authentication

- Session-based authentication (server-side session cookie)
- Login route: `/login`
- Logout route: `POST /logout`

Users are stored in `users` table:
- `username`, `email`
- `password_hash` (Werkzeug)
- `role`
- `is_active`

## Admin pages

- `/admin` Dashboard
- `/admin/machines` Machines CRUD
- `/admin/specifications` Specifications CRUD
- `/admin/gallery` Gallery CRUD
- `/admin/inquiries` Inquiry inbox
- `/admin/users` User activation (**admin only**)
- `/admin/users/create` Create user (**admin only**)
- `/admin/review` Submissions review (**admin only**)

## Review & approval workflow

Changes submitted by Developers are stored in the `submissions` table:

- `target_table`: which table is affected
- `action`: create/update/delete
- `target_id`: row id (nullable for create)
- `payload_json`: proposed fields as JSON
- `status`: pending/approved/rejected

### Approval behavior

When an Admin approves:
- The payload is applied to the database by `models.review_submission()`
- The submission status is marked `approved`

When rejected:
- The payload is not applied
- The submission status is marked `rejected`

### Why store the payload as JSON

- Keeps the workflow flexible without needing a custom table for every change type
- Makes review readable and auditable
- Prevents developers from pushing unreviewed updates live

## Where to modify permissions

- Auth decorators live in `app.py`:
  - `login_required`
  - `role_required`

- Submission application rules live in `models.py`:
  - `_apply_submission_payload()`

