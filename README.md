# 💼 Job Application Tracker

A Streamlit web app to manage job applications with private accounts, search, status filters, a dashboard, CSV export, and permanent cloud storage via Supabase PostgreSQL.

## Features
- Create an account and sign in with email/password
- Add, view, search, filter, update, and delete your own applications
- Track total applications, applied roles, interviews, and offers
- Export filtered results to CSV
- PostgreSQL persistence and row-level security (RLS)

## One-time Supabase setup
1. Create a free project at Supabase.
2. In **SQL Editor**, run the complete `schema.sql` file once. Do not run it multiple times because policies will already exist.
3. Under **Project Settings → API** (or the API keys area in your dashboard), copy your **Project URL** and **publishable/anon key**. **Never use a service_role or secret key in this app.**
4. Under **Authentication → Providers → Email**, choose whether new accounts must confirm their email. If confirmation is enabled, ensure your email settings and allowed site URLs are configured.
5. Locally, create `.streamlit/secrets.toml` with the keys shown in `.streamlit/secrets.example.toml`, replacing placeholders. This file is ignored by Git.
6. On Streamlit Community Cloud, open your app's **Settings → Secrets** and paste the same TOML values there, then save/reboot the app.

## Run locally
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Deploy
Upload `app.py`, `requirements.txt`, `schema.sql`, `.streamlit/config.toml`, `README.md`, and `.gitignore` to the GitHub repository. Do not upload your real `.streamlit/secrets.toml`, `.venv`, or `applications.json`. Deploy `app.py` through Streamlit Community Cloud and set the secrets in the app dashboard.

## Privacy and limitations
- Supabase RLS restricts each signed-in user to their own records.
- The app does not automatically migrate data from the older local `applications.json`; add records manually after signing in.
- Email/password authentication depends on your Supabase Auth configuration. For a production app, configure email delivery, password recovery, rate limits, and operational monitoring.
- Supabase project retention and availability depend on your service plan and account; a hosted database avoids Streamlit's ephemeral local filesystem but does not replace backups.
