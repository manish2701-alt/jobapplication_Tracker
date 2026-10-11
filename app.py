"""Job Application Tracker — authenticated Streamlit app backed by Supabase."""
from datetime import date
from uuid import uuid4
import csv
import io

import streamlit as st
from supabase import create_client

STATUSES = ["Applied", "Online Assessment", "Interview", "Offer", "Rejected", "Withdrawn"]
st.set_page_config(page_title="Job Application Tracker", page_icon="💼", layout="wide")
st.markdown("""<style>
.block-container {max-width: 1120px; padding-top: 2rem; padding-bottom: 3rem;}
h1 {font-weight: 750; letter-spacing: -.035em;}
[data-testid="stMetric"] {background: #172235; border: 1px solid #30435f; border-radius: 14px; padding: 18px;}
[data-testid="stMetricLabel"], [data-testid="stMetricValue"] {color: #f5f8ff !important;}
[data-testid="stMetricLabel"] p {color: #d3deef !important;}
</style>""", unsafe_allow_html=True)


def client():
    if "db_client" not in st.session_state:
        try:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_KEY"]
            st.session_state.db_client = create_client(url, key)
        except (KeyError, FileNotFoundError):
            st.error("Supabase credentials are missing. Follow README.md to configure Streamlit secrets.")
            st.stop()
    return st.session_state.db_client


def db_action(action):
    try:
        return action.execute().data
    except Exception as exc:
        st.error(f"Database request failed: {exc}")
        st.stop()


def label(record):
    return f"{record['company']} — {record['role']} ({record['applied_date']}) · {record['id'][:8]}"


st.title("💼 Job Application Tracker")
st.caption("Keep your job search organized — applications, interviews, and offers in one place.")
db = client()

# A client is kept only in this Streamlit browser session. Supabase enforces
# per-user access with row-level security policies (see schema.sql).
if "user_id" not in st.session_state:
    st.subheader("Sign in to your private tracker")
    sign_in, sign_up = st.tabs(["Sign in", "Create account"])
    with sign_in:
        with st.form("sign_in"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submit = st.form_submit_button("Sign in", type="primary")
        if submit:
            try:
                response = db.auth.sign_in_with_password({"email": email.strip(), "password": password})
                if response.user and response.session:
                    st.session_state.user_id = str(response.user.id)
                    st.rerun()
                else:
                    st.error("Sign-in was not completed.")
            except Exception as exc:
                st.error(f"Could not sign in: {exc}")
    with sign_up:
        with st.form("sign_up"):
            email_new = st.text_input("Email", key="register_email")
            password_new = st.text_input("Password (at least 6 characters)", type="password", key="register_password")
            register = st.form_submit_button("Create account")
        if register:
            if not email_new.strip() or len(password_new) < 6:
                st.error("Enter an email and a password with at least 6 characters.")
            else:
                try:
                    response = db.auth.sign_up({"email": email_new.strip(), "password": password_new})
                    if response.session and response.user:
                        st.session_state.user_id = str(response.user.id)
                        st.rerun()
                    st.success("Account request received. If email confirmation is enabled, check your inbox, then sign in.")
                except Exception as exc:
                    st.error(f"Could not create account: {exc}")
    st.stop()

with st.sidebar:
    st.write("🔐 Your private workspace")
    if st.button("Sign out"):
        try:
            db.auth.sign_out()
        finally:
            st.session_state.pop("user_id", None)
            st.session_state.pop("db_client", None)
        st.rerun()

user_id = st.session_state.user_id
records = db_action(db.table("applications").select("id,company,role,applied_date,status").eq("user_id", user_id).order("applied_date", desc=True)) or []

counts = [len(records)] + [sum(r["status"] == status for r in records) for status in ("Applied", "Interview", "Offer")]
for col, title, count in zip(st.columns(4), ("Total applications", "Applied", "Interviews", "Offers"), counts):
    col.metric(title, count)

st.divider()
tab_view, tab_add, tab_edit, tab_delete = st.tabs(["📋 Applications", "➕ Add", "✏️ Update", "🗑️ Delete"])

with tab_view:
    left, right = st.columns([2, 1])
    with left:
        search = st.text_input("Search company or role", placeholder="e.g. Python Developer").casefold().strip()
    with right:
        status_filter = st.selectbox("Filter by status", ["All"] + STATUSES)
    filtered = [r for r in records if (search in r["company"].casefold() or search in r["role"].casefold())
                and (status_filter == "All" or r["status"] == status_filter)]
    if filtered:
        rows = [{"Company": r["company"], "Role": r["role"], "Applied date": r["applied_date"], "Status": r["status"]} for r in filtered]
        st.dataframe(rows, use_container_width=True, hide_index=True)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        st.download_button("⬇️ Download filtered results (CSV)", output.getvalue(), file_name="job_applications.csv", mime="text/csv")
    else:
        st.info("No matching applications. Add your first application in the Add tab.")

with tab_add:
    st.subheader("Add a job application")
    with st.form("add_form", clear_on_submit=True):
        company = st.text_input("Company *", placeholder="e.g. Google")
        role = st.text_input("Role *", placeholder="e.g. Junior Python Engineer")
        applied_date = st.date_input("Application date", value=date.today(), max_value=date.today())
        status = st.selectbox("Application status", STATUSES)
        submitted = st.form_submit_button("Save application", type="primary")
    if submitted:
        if not company.strip() or not role.strip():
            st.error("Company and role cannot be empty.")
        elif len(company.strip()) > 120 or len(role.strip()) > 120:
            st.error("Company and role must be 120 characters or fewer.")
        else:
            db_action(db.table("applications").insert({"id": str(uuid4()), "user_id": user_id,
                "company": company.strip(), "role": role.strip(), "applied_date": applied_date.isoformat(), "status": status}))
            st.toast("Application saved successfully!")
            st.rerun()

with tab_edit:
    st.subheader("Update an application")
    if not records:
        st.info("Add an application first.")
    else:
        choices = {r["id"]: label(r) for r in records}
        selected_id = st.selectbox("Choose an application", list(choices), format_func=lambda key: choices[key])
        selected = next(r for r in records if r["id"] == selected_id)
        with st.form("update_form"):
            new_status = st.selectbox("New status", STATUSES, index=STATUSES.index(selected["status"]))
            update = st.form_submit_button("Update status", type="primary")
        if update:
            db_action(db.table("applications").update({"status": new_status}).eq("id", selected_id).eq("user_id", user_id))
            st.toast("Status updated successfully!")
            st.rerun()

with tab_delete:
    st.subheader("Delete an application")
    if not records:
        st.info("No applications to delete.")
    else:
        choices = {r["id"]: label(r) for r in records}
        selected_id = st.selectbox("Choose an application to delete", list(choices), format_func=lambda key: choices[key])
        confirm = st.checkbox("I understand this application will be permanently deleted")
        if st.button("Delete application", disabled=not confirm, type="primary"):
            db_action(db.table("applications").delete().eq("id", selected_id).eq("user_id", user_id))
            st.toast("Application deleted.")
            st.rerun()

st.divider()
st.caption("Built with Python + Streamlit + Supabase • Private accounts • Cloud database")
