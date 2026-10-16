# Udai Batta and Ayush Sharma co.ltd careers site

This repository contains the public GitHub Pages version of the fictional careers site and a Django version with an admin for managing its job listings. The listing API only serves active jobs. The application flow remains a joke: it stores no applicant data and asks visitors to use a made-up nickname.

## Run Django locally

Python 3.10 or newer is required.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_jobs
python manage.py createsuperuser
python -m uvicorn careers_project.asgi:application --reload
```

Open `http://127.0.0.1:8000/` for the site and `/admin/` to manage job listings. SQLite is used locally. Set `DATABASE_URL` to a PostgreSQL connection URL to use PostgreSQL instead.

## Publish the Django version

The GitHub Pages copy stays available at [udaibatta.github.io/shitty-website](https://udaibatta.github.io/shitty-website/). GitHub Pages only serves static files, so use the included `render.yaml` to run Django on Render and connect it to a PostgreSQL database on Neon.

1. Create a free PostgreSQL project at [Neon](https://console.neon.tech/). Copy its pooled connection string; keep it private.
2. In [Render](https://dashboard.render.com/), create a Blueprint from this GitHub repository and branch. Render will read `render.yaml` and prompt for `DATABASE_URL`; paste the Neon connection string there.
3. Wait for the Render deploy to pass its `/api/health/` health check, then open the service's `onrender.com` address. The website fetches listings from Django; the GitHub Pages copy keeps its built-in listing snapshot.
4. Open Render's service shell and run `python manage.py createsuperuser` once. Sign in at `/admin/` to add, edit, hide, search, and reorder the listings.

The first deployment requires `DATABASE_URL` and seeds the 35 fictional listings only when the database is empty. Later starts preserve edits made in the admin. No database password or Django secret belongs in Git; Render generates the Django secret, and Neon supplies the database URL privately. Free Render services sleep when idle and can take about a minute to wake. Check both providers' current free-plan limits before publishing the backend URL.

## Checks

```powershell
python manage.py check
python manage.py test
```
