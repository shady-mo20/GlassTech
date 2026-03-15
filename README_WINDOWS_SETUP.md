# Windows setup (PowerShell) — Flask + SQLite

This guide assumes Windows 10/11 + PowerShell and that you are inside the project folder.

## 1) Verify Python

```powershell
python -V
python -m pip -V
```

If `python` is not found, install Python 3.11+ and check “Add to PATH”.

## 2) (Recommended) Create a virtual environment

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then re-run the activation command.

## 3) Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4) Run the app

Option A (simple):

```powershell
python app.py
```

Option B (Flask CLI):

```powershell
$env:FLASK_APP="app.py"
python -m flask run
```

Open:
- `http://127.0.0.1:5000/`

## 5) Default local credentials

Created automatically when the DB is empty:

- Admin: `admin` / `Admin@12345`
- Developer: `dev` / `Dev@12345`

## Troubleshooting

### “Address already in use”

Run on another port:

```powershell
python -m flask run --port 5001
```

### “sqlite3.OperationalError: unable to open database file”

Ensure the `instance/` folder is writable. The app creates it automatically, but restricted folders can cause issues.

### “Maximum redirection count exceeded” (when testing with Invoke-WebRequest)

This can happen when PowerShell follows redirects unexpectedly. Use a web browser for manual testing, or avoid automatic redirects in scripts.

