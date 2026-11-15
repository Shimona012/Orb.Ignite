#Authtenticate for editing and admin uses, admins can edit/add/delete datasets, presets etc.
from datetime import datetime, timezone
import json
import os
import re
import pandas as pd
import streamlit as st
from supabase import create_client
#Using multiple google cloud api's:

#need to add common login, and a basic admin login-logout system.
def _get_supabase_client():
    url = None
    key = None
    try:
        url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase_url")
        key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_ANON_KEY") or st.secrets.get("supabase_key")
        if (not url or not key) and "supabase" in st.secrets:
            sb = st.secrets["supabase"]
            url = url or sb.get("url") or sb.get("SUPABASE_URL")
            key = key or sb.get("key") or sb.get("anon_key") or sb.get("SUPABASE_KEY")
    except Exception:
        pass
    url = url or os.getenv("SUPABASE_URL")
    key = key or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None


def _data_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Data")


def _users_file_path():
    return os.path.join(_data_dir(), "users.json")


def _load_users_file():
    p = _users_file_path()
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                users = json.load(f)
                if isinstance(users, list) and users:
                    return users
        except Exception:
            pass
    admin_email = os.getenv("ADMIN_EMAIL", "admin@orbignite.org")
    default_users = [
        {"email": admin_email, "role": "Administrator", "created_at": datetime.now(timezone.utc).isoformat()}
    ]
    _save_users_file(default_users)
    return default_users


def _save_users_file(users):
    p = _users_file_path()
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)
    except Exception:
        pass


def _get_user_role(email):
    if not email:
        return "Viewer"
    clean_e = email.strip().lower()
    admin_email = None
    try:
        admin_email = st.secrets.get("ADMIN_EMAIL") or st.secrets.get("admin_email")
    except Exception:
        pass
    admin_email = (admin_email or os.getenv("ADMIN_EMAIL", "admin@orbignite.org")).lower()
    if clean_e in (admin_email, "admin"):
        return "Administrator"
    users = _load_users_file()
    for u in users:
        if u.get("email", "").strip().lower() == clean_e:
            return u.get("role", "Researcher")
    return "Researcher"


def _set_user_role(email, new_role):
    clean_e = email.strip().lower()
    users = _load_users_file()
    found = False
    for u in users:
        if u.get("email", "").strip().lower() == clean_e:
            u["role"] = new_role
            found = True
            break
    if not found:
        users.append({
            "email": clean_e,
            "role": new_role,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    _save_users_file(users)


def _validate_password_strength(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter (A-Z)."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter (a-z)."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number (0-9)."
    if not re.search(r"[@$!%*?&#^+=_\-~]", password):
        return False, "Password must contain at least one special character (@$!%*?&#^+=_-~)."
    return True, ""


def _validate_email_format(email):
    if not email:
        return False
    if email.strip().lower() in ("admin", "admin@orbignite.org"):
        return True
    pattern = r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+$"
    return bool(re.match(pattern, email.strip()))


def _load_experiments_file():
    path = os.path.join(_data_dir(), "experiments.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _load_ntrs_file():
    path = os.path.join(_data_dir(), "ntrs_links.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_ntrs_file(ntrs_items):
    path = os.path.join(_data_dir(), "ntrs_links.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ntrs_items, f, indent=2)
    except Exception:
        pass


def _sync_ntrs_registry(records):
    existing = _load_ntrs_file()
    existing_by_doc = {str(item.get("ntrs_id", "")).strip(): item for item in existing if item.get("ntrs_id")}
    existing_by_id = {str(item.get("id", "")).strip(): item for item in existing if item.get("id")}

    updated = list(existing)
    for r in records:
        raw_ntrs = str(r.get("ntrs_document_id") or "").strip()
        custom_link = str(r.get("ntrs_link") or "").strip()
        if not raw_ntrs and not custom_link:
            continue
        clean_num = raw_ntrs.replace("NASA-NTRS-", "").replace("NTRS-", "").strip()
        key_id = f"NTRS-{clean_num}" if clean_num else f"NTRS-{r.get('id', 'DOC')}"
        link_url = custom_link or (f"https://ntrs.nasa.gov/citations/{clean_num}" if clean_num.isdigit() else f"https://ntrs.nasa.gov/search?q={raw_ntrs}")

        raw_rtype = str(r.get("resource_type") or "").strip()
        mapped_rtype = (
            "External Research Paper" if raw_rtype == "Paper"
            else ("NASA Experiment / Guide" if raw_rtype in ("Experiment", "NASA Experiment / Guide")
                  else ("Other" if raw_rtype == "Other" else "NTRS Technical Report"))
        )

        if key_id not in existing_by_id and (not clean_num or clean_num not in existing_by_doc):
            new_item = {
                "id": key_id,
                "ntrs_id": clean_num if clean_num.isdigit() else "",
                "resource_type": mapped_rtype if not clean_num.isdigit() else "NTRS Technical Report",
                "title": f"{r.get('name', 'Technical Report')} ({r.get('mission', 'NASA')})",
                "citation_url": link_url,
                "mission": r.get("mission", ""),
                "fuel": r.get("fuel_name", ""),
                "year": int(r.get("year", 2024)),
                "pdf_file": "",
                "summary": r.get("key_phenomenon", ""),
            }
            updated.append(new_item)
            existing_by_id[key_id] = new_item
            if clean_num:
                existing_by_doc[clean_num] = new_item

    _save_ntrs_file(updated)


def _save_experiments_file(records, client=None):
    path = os.path.join(_data_dir(), "experiments.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    _sync_ntrs_registry(records)
    if client is not None and records:
        try:
            client.table("experiments").upsert(records).execute()
        except Exception:
            pass
    st.cache_data.clear()


def _verify_admin_credentials(email, password, client=None):
    if client is not None and email:
        try:
            res = client.auth.sign_in_with_password({"email": email.strip(), "password": password})
            if res.user:
                return True, res.user.email
        except Exception:
            pass

    admin_pw = None
    try:
        admin_pw = st.secrets.get("ADMIN_PASSWORD") or st.secrets.get("admin_password")
    except Exception:
        pass
    admin_pw = admin_pw or os.getenv("ADMIN_PASSWORD", "orb-admin")

    admin_email = None
    try:
        admin_email = st.secrets.get("ADMIN_EMAIL") or st.secrets.get("admin_email")
    except Exception:
        pass
    admin_email = admin_email or os.getenv("ADMIN_EMAIL", "admin@orbignite.org")

    if password == admin_pw and (not email or email.strip().lower() == admin_email.strip().lower() or email.strip().lower() == "admin"):
        return True, admin_email
    return False, None


def render_sidebar_auth():
    client = _get_supabase_client()
    user = st.session_state.get("auth_user")
    is_admin = st.session_state.get("is_admin", False)

    st.markdown("#### User Authentication")

    if user:
        current_role = _get_user_role(user)
        is_admin = is_admin or (current_role == "Administrator")
        st.session_state["is_admin"] = is_admin
        role_badge = "Administrator" if is_admin else current_role
        st.markdown(f"**Status:** `{role_badge}`")
        st.caption(f"Signed in as `{user}`")
        if st.button("Sign Out", key="auth_btn_signout", use_container_width=True):
            if client is not None and not is_admin:
                try:
                    client.auth.sign_out()
                except Exception:
                    pass
            st.session_state.pop("auth_user", None)
            st.session_state.pop("admin_user", None)
            st.session_state["is_admin"] = False
            st.session_state["show_admin_portal"] = False
            try:
                from Pages import combustion_physics
                combustion_physics.ensure_preset_state()
            except Exception:
                pass
            st.rerun()
    else:
        st.caption("Access experimental controls or admin records.")
        with st.expander("Sign In / Sign Up", expanded=False):
            auth_tab1, auth_tab2, auth_tab3 = st.tabs(["Sign In", "Sign Up", "Admin"])

            with auth_tab1:
                with st.form("sidebar_signin_form", clear_on_submit=True):
                    u_email = st.text_input("Email", placeholder="researcher@agency.org", key="u_sign_in_email")
                    u_pw = st.text_input("Password", type="password", placeholder="Enter your password", key="u_sign_in_pw")
                    u_submit = st.form_submit_button("Sign In as Researcher", use_container_width=True)
                    if u_submit:
                        if not u_email or not u_pw:
                            st.error("Please enter email and password.")
                        elif not _validate_email_format(u_email):
                            st.error("Please enter a valid email address.")
                        elif client is not None:
                            try:
                                res = client.auth.sign_in_with_password({"email": u_email.strip(), "password": u_pw})
                                if res.user:
                                    role = _get_user_role(res.user.email)
                                    st.session_state["auth_user"] = res.user.email
                                    st.session_state["is_admin"] = (role == "Administrator")
                                    try:
                                        from Pages import combustion_physics
                                        combustion_physics.ensure_preset_state()
                                    except Exception:
                                        pass
                                    st.success(f"Welcome, {res.user.email}!")
                                    st.rerun()
                            except Exception as exc:
                                st.error(f"Sign in failed: {exc}")
                        else:
                            role = _get_user_role(u_email)
                            st.session_state["auth_user"] = u_email.strip()
                            st.session_state["is_admin"] = (role == "Administrator")
                            try:
                                from Pages import combustion_physics
                                combustion_physics.ensure_preset_state()
                            except Exception:
                                pass
                            st.success(f"Signed in as {role} (Local Session).")
                            st.rerun()

            with auth_tab2:
                st.warning(
                    "Notice: No real live admin exists right now. Induction of administrative privileges is handled developer-side. "
                    "User sign-ups are disabled for this demonstration phase."
                )
                with st.form("sidebar_signup_form", clear_on_submit=True):
                    su_email = st.text_input("Email", placeholder="researcher@agency.org", key="u_sign_up_email")
                    su_pw = st.text_input(
                        "Password (min 8 chars, 1 uppercase, 1 num, 1 special)",
                        type="password",
                        placeholder="e.g. Apollo#2026",
                        key="u_sign_up_pw",
                    )
                    su_submit = st.form_submit_button("Register Account", use_container_width=True)
                    if su_submit:
                        st.warning("User sign-ups are currently disabled. Admin induction is handled on the developer side.")

            with auth_tab3:
                st.info(
                    "Notice: Demonstration mode. Default demo credentials are provided as placeholders below. "
                    "No real live admin exists right now; admin induction is handled developer-side."
                )
                with st.form("sidebar_admin_login_form", clear_on_submit=True):
                    adm_email = st.text_input("Admin Email (or 'admin')", placeholder="admin@orbignite.org", key="u_adm_email")
                    adm_pw = st.text_input("Admin Password", type="password", placeholder="orb-admin", key="u_adm_pw")
                    adm_submit = st.form_submit_button("Unlock Admin Portal", use_container_width=True)
                    if adm_submit:
                        ok, adm_id = _verify_admin_credentials(adm_email, adm_pw, client)
                        if ok:
                            st.session_state["auth_user"] = adm_id
                            st.session_state["admin_user"] = adm_id
                            st.session_state["is_admin"] = True
                            st.session_state["show_admin_portal"] = True
                            try:
                                from Pages import combustion_physics
                                combustion_physics.ensure_preset_state()
                            except Exception:
                                pass
                            st.success("Admin unlocked.")
                            st.rerun()
                        else:
                            st.error("Invalid admin credentials. Check password or environment settings.")


def render_admin_portal():
    st.header("Admin Portal")
    client = _get_supabase_client()
    is_admin = st.session_state.get("is_admin", False)
    user = st.session_state.get("admin_user") or st.session_state.get("auth_user")

    if not is_admin:
        st.info("Demonstration Mode: Default demo credentials are shown as placeholders below. No real live admin exists currently; administrative induction is performed developer-side.")
        with st.form("admin_login_direct_form", clear_on_submit=True):
            email = st.text_input("Admin Email", placeholder="admin@orbignite.org", key="adm_direct_email")
            password = st.text_input("Admin Password", type="password", placeholder="orb-admin", key="adm_direct_pw")
            submitted = st.form_submit_button("Sign In as Admin")
            if submitted:
                ok, adm_id = _verify_admin_credentials(email, password, client)
                if ok:
                    st.session_state["auth_user"] = adm_id
                    st.session_state["admin_user"] = adm_id
                    st.session_state["is_admin"] = True
                    st.success("Admin authorized.")
                    st.rerun()
                else:
                    st.error("Authentication failed. Check your admin password or Supabase credentials.")
        return

    col_u1, col_u2 = st.columns([4, 1])
    with col_u1:
        storage_mode = "Supabase Cloud" if client is not None else "Local Storage"
        st.caption(f"Signed in as `{user}` (Administrator) | Backend: **{storage_mode}**")
    with col_u2:
        if st.button("Exit Admin"):
            st.session_state["show_admin_portal"] = False
            st.rerun()

    records = _load_experiments_file()

    st.subheader("Edit or Delete Experiment Records")
    df = pd.DataFrame(records)
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="admin_editor")
    if st.button("Save Changes to Experiments"):
        updated = edited_df.dropna(how="all").to_dict(orient="records")
        _save_experiments_file(updated, client)
        st.success("Dataset and NTRS registry updated.")
        st.rerun()

    with st.expander("Add Experiment / Resource"):
        with st.form("add_exp_form"):
            record_category = st.selectbox(
                "Resource / Addition Type",
                ["Experiment", "Paper", "NTRS Report", "Other"],
                key="admin_add_record_type",
            )
            c1, c2 = st.columns(2)
            with c1:
                exp_id = st.text_input("ID")
                mission = st.text_input("Mission")
                name = st.text_input("Name / Title")
                year = st.number_input("Year", min_value=1960, max_value=2035, value=2024, step=1)
                platform = st.text_input("Platform")
                fuel_name = st.text_input("Fuel Name")
                fuel_category = st.text_input("Fuel Category")
            with c2:
                gravity_g = st.number_input("Gravity (g)", min_value=0.0, max_value=2.0, value=0.0, step=0.01)
                oxygen_pct = st.number_input("Oxygen (%)", min_value=0.0, max_value=100.0, value=21.0, step=0.5)
                pressure_atm = st.number_input("Pressure (atm)", min_value=0.0, max_value=5.0, value=1.0, step=0.05)
                burn_duration_s = st.number_input("Burn Duration (s)", min_value=0.0, value=0.0, step=1.0)
                safety_risk_level = st.selectbox("Safety Risk Level", ["LOW", "MODERATE", "CRITICAL"])
                cool_flame = st.checkbox("Cool Flame Observed")
                ntrs_id = st.text_input("NTRS Document ID (for numbered NTRS reports)")
                ntrs_link = st.text_input("Reference / Citation Link (optional)")
            key_phenomenon = st.text_area("Key Phenomenon / Summary")

            if st.form_submit_button("Add Record"):
                if not exp_id or not name:
                    st.error("ID and Name / Title are required.")
                elif record_category == "Experiment":
                    records.append({
                        "id": exp_id,
                        "resource_type": "Experiment",
                        "mission": mission,
                        "name": name,
                        "year": int(year),
                        "platform": platform,
                        "fuel_name": fuel_name,
                        "fuel_category": fuel_category,
                        "gravity_g": float(gravity_g),
                        "oxygen_pct": float(oxygen_pct),
                        "pressure_atm": float(pressure_atm),
                        "burn_duration_s": float(burn_duration_s),
                        "safety_risk_level": safety_risk_level,
                        "cool_flame_observed": bool(cool_flame),
                        "key_phenomenon": key_phenomenon,
                        "ntrs_document_id": ntrs_id,
                        "ntrs_link": ntrs_link,
                    })
                    _save_experiments_file(records, client)
                    st.success(f"Added Experiment {exp_id}.")
                    st.rerun()
                else:
                    rtype_map = {
                        "Paper": "External Research Paper",
                        "NTRS Report": "NTRS Technical Report",
                        "Other": "NASA Experiment / Guide",
                    }
                    clean_num = ntrs_id.replace("NASA-NTRS-", "").replace("NTRS-", "").strip()
                    ntrs_items = _load_ntrs_file()
                    ntrs_items.append({
                        "id": exp_id,
                        "ntrs_id": clean_num if record_category == "NTRS Report" else "",
                        "resource_type": rtype_map.get(record_category, "Other"),
                        "title": name,
                        "citation_url": ntrs_link or (f"https://ntrs.nasa.gov/citations/{clean_num}" if clean_num.isdigit() else ""),
                        "mission": mission or record_category,
                        "fuel": fuel_name or fuel_category,
                        "year": int(year),
                        "pdf_file": "",
                        "summary": key_phenomenon,
                    })
                    _save_ntrs_file(ntrs_items)
                    st.cache_data.clear()
                    st.success(f"Added {record_category} record '{exp_id}' to Resource Registry.")
                    st.rerun()

    st.subheader("Delete Record or Manage Data Files")
    c_del1, c_del2 = st.columns(2)
    with c_del1:
        ids = [r.get("id", "") for r in records if r.get("id")]
        if ids:
            del_id = st.selectbox("Select ID to Delete", ids, key="del_exp_select")
            if st.button("Delete Selected Record"):
                remaining = [r for r in records if r.get("id") != del_id]
                _save_experiments_file(remaining, client)
                try:
                    client.table("experiments").delete().eq("id", del_id).execute()
                except Exception:
                    pass
                st.success(f"Deleted {del_id}.")
                st.rerun()

    with c_del2:
        upload_type = st.selectbox(
            "Uploaded Resource Category",
            ["Experiment", "Paper", "NTRS Report", "Other"],
            key="admin_upload_file_type",
        )
        uploaded = st.file_uploader("Upload Dataset / Resource File", type=["json", "csv", "pdf"])
        if uploaded is not None and st.button("Save Uploaded File"):
            target = os.path.join(_data_dir(), uploaded.name)
            with open(target, "wb") as out:
                out.write(uploaded.getbuffer())
            if uploaded.name.lower().endswith(".pdf"):
                rtype_map = {
                    "Experiment": "NASA Experiment / Guide",
                    "Paper": "External Research Paper",
                    "NTRS Report": "NTRS Technical Report",
                    "Other": "Other",
                }
                stem = os.path.splitext(uploaded.name)[0]
                is_ntrs_num = stem.isdigit() and upload_type == "NTRS Report"
                ntrs_items = _load_ntrs_file()
                if not any(item.get("pdf_file") == uploaded.name for item in ntrs_items):
                    ntrs_items.append({
                        "id": f"NTRS-{stem}" if is_ntrs_num else f"RES-{stem[:18].upper()}",
                        "ntrs_id": stem if is_ntrs_num else "",
                        "resource_type": rtype_map.get(upload_type, "Other"),
                        "title": stem.replace("_", " ").replace("-", " "),
                        "citation_url": f"https://ntrs.nasa.gov/citations/{stem}" if is_ntrs_num else "",
                        "mission": upload_type,
                        "fuel": "Uploaded Document",
                        "year": 2025,
                        "pdf_file": uploaded.name,
                        "summary": f"Admin-uploaded {upload_type} document ({uploaded.name}).",
                    })
                    _save_ntrs_file(ntrs_items)
            st.cache_data.clear()
            st.success(f"Saved {uploaded.name} as '{upload_type}'.")

        data_files = sorted(os.listdir(_data_dir()))
        if data_files:
            del_file = st.selectbox("Select Data File to Delete", data_files, key="del_file_select")
            if st.button("Delete Selected File"):
                target = os.path.join(_data_dir(), del_file)
                if os.path.exists(target):
                    os.remove(target)
                    st.success(f"Removed {del_file}.")
                    st.rerun()

    st.subheader("NTRS Document Registry Links")
    ntrs_items = _load_ntrs_file()
    if ntrs_items:
        df_ntrs = pd.DataFrame(ntrs_items)
        edited_ntrs = st.data_editor(df_ntrs, num_rows="dynamic", use_container_width=True, key="admin_ntrs_editor")
        if st.button("Save NTRS Registry Changes"):
            updated_ntrs = edited_ntrs.dropna(how="all").to_dict(orient="records")
            _save_ntrs_file(updated_ntrs)
            st.success("NTRS registry updated successfully.")
            st.rerun()
    else:
        st.caption("No NTRS links indexed yet.")

    st.subheader("User Directory & Role Management")
    st.caption("Inspect registered researcher accounts and assign administrative or viewer roles.")
    users = _load_users_file()
    if users:
        st.dataframe(pd.DataFrame(users), use_container_width=True)
        c_u1, c_u2, c_u3 = st.columns([2.5, 1.5, 1.2])
        with c_u1:
            user_list = [u.get("email", "") for u in users if u.get("email")]
            selected_u = st.selectbox("Select Account", user_list, key="adm_user_select")
        with c_u2:
            curr_role = next((u.get("role", "Researcher") for u in users if u.get("email") == selected_u), "Researcher")
            roles = ["Researcher", "Administrator", "Viewer"]
            r_idx = roles.index(curr_role) if curr_role in roles else 0
            new_role = st.selectbox("Assign Role", roles, index=r_idx, key="adm_role_select")
        with c_u3:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            if st.button("Save User Role", use_container_width=True, key="adm_btn_save_role"):
                _set_user_role(selected_u, new_role)
                if selected_u == user:
                    st.session_state["is_admin"] = (new_role == "Administrator")
                st.success(f"Updated role for {selected_u} to {new_role}.")
                st.rerun()
    else:
        st.caption("No registered users yet.")

    st.info(
        "**Admin Credentials Guide:** The demo administrative password is `orb-admin` with email `admin@orbignite.org` (or username `admin`). "
        "Notice: No real live admin exists right now. Induction of administrative privileges is handled developer-side. "
        "To set your own custom password, add `ADMIN_PASSWORD = \"your_secret_password\"` in `.streamlit/secrets.toml` or set the system environment variable `ADMIN_PASSWORD`."
    )

    st.subheader("Contact Messages")
    messages = []
    try:
        resp = client.table("contact_messages").select("*").execute()
        messages = resp.data or []
    except Exception:
        msg_path = os.path.join(_data_dir(), "contact_messages.json")
        if os.path.exists(msg_path):
            try:
                with open(msg_path, "r", encoding="utf-8") as mf:
                    messages = json.load(mf)
            except Exception:
                messages = []
    if messages:
        st.dataframe(pd.DataFrame(messages), use_container_width=True)
    else:
        st.caption("No messages yet.")


if __name__ == "__main__":
    try:
        st.set_page_config(page_title="Admin Portal", layout="wide")
    except Exception:
        pass
    render_admin_portal()
