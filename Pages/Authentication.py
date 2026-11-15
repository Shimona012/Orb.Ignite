#Authtenticate for editing and admin uses, admins can edit/add/delete datasets, presets etc.
from datetime import datetime, timezone
import hmac
import json
import os
import re
import pandas as pd
import streamlit as st
from supabase import create_client
#Using multiple google cloud api's:
#cloud admin api,cloud build api,artifact registry, compute engine,cloud storage api,cloud logging api,secret manager api,cloud resource manager api,cloud deploy ap

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



PROTECTED_DATA_FILES = {
    "users.json",
    "saved_scenarios.json",
    "user_presets.json",
    "dataset_state.json",
    "contact_messages.json",
    "experiments.json",
    "ntrs_links.json",
    "vinyl.png",
    "filter_white.png",
    "filter_black.png",
}



def _sanitize_data_filename(name):
    base = os.path.basename(str(name or "").strip())
    clean = re.sub(r"[^a-zA-Z0-9._\- ()]", "_", base).lstrip(".")
    return clean



def _is_within_data_dir(target_path):
    base_real = os.path.realpath(_data_dir())
    target_real = os.path.realpath(target_path)
    return os.path.commonpath([base_real, target_real]) == base_real


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
    admin_email = os.getenv("ADMIN_EMAIL", "admin@orbignite.earth")
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
    admin_email = (admin_email or os.getenv("ADMIN_EMAIL", "admin@orbignite.earth")).lower()
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
    if email.strip().lower() in ("admin", "admin@orbignite.earth"):
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



def _load_physics_module():
    try:
        from Pages import combustion_physics
        return combustion_physics
    except ImportError:
        import combustion_physics
        return combustion_physics


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
  
    try:
        phys = _load_physics_module()
        res = phys.record_admin_change_and_retrain("Admin modified experiment records")
        st.session_state["_last_retrain_status"] = res
    except Exception:
        pass


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
    admin_email = admin_email or os.getenv("ADMIN_EMAIL", "admin@orbignite.earth")

    
    pw_match = hmac.compare_digest(str(password or ""), str(admin_pw or ""))
    if pw_match and (not email or email.strip().lower() == admin_email.strip().lower() or email.strip().lower() == "admin"):
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

        
        with st.expander("My Profile & Saved Scenarios", expanded=False):
            phys = _load_physics_module()
            saved_list = phys.load_user_scenarios(user)
            state_info = phys.get_dataset_and_model_state()
            latest_data_ts = state_info.get("last_admin_change_utc", "")
            latest_model_ts = state_info.get("model_trained_at_utc", "")

            if not saved_list:
                st.caption("No saved fire scenarios yet. Save one from the Fire Predictor section.")
            else:
                st.caption(f"{len(saved_list)} scenario(s) synced to `{user}`")
                for s_idx, scen in enumerate(saved_list):
                    sid = scen.get("id", f"s{s_idx}")
                    s_name = scen.get("name", "Untitled Scenario")
                    s_rank = int(scen.get("user_rank", 3))
                    scen_ver = scen.get("model_version_utc", "") or scen.get("evaluated_at_utc", "")
                    is_stale = bool(
                        (latest_data_ts and scen_ver < latest_data_ts)
                        or (latest_model_ts and scen_ver < latest_model_ts)
                    )
                    with st.container(border=True):
                        st.markdown(f"**{s_name}** (Rank `#{s_rank}`)")
                        inp = scen.get("inputs", {})
                        st.caption(
                            f"{inp.get('gravity_g', 0.0):.2f}g | {inp.get('o2_pct', 21.0):.1f}% O₂ | "
                            f"{scen.get('burn_duration_s', 0.0):.1f}s | `{scen.get('fire_regime', 'N/A')}`"
                        )
                        if is_stale:
                            st.warning("New admin data added — rerun & update this scenario in Fire Predictor.")

                        new_nm = st.text_input("Rename", value=s_name, key=f"prof_rn_{sid}_{s_idx}")
                        new_rk = st.number_input("Rank (1–5)", min_value=1, max_value=5, value=s_rank, step=1, key=f"prof_rk_{sid}_{s_idx}")
                        pc1, pc2, pc3 = st.columns(3)
                        with pc1:
                            if st.button("Load", key=f"prof_ld_{sid}_{s_idx}", use_container_width=True):
                                st.session_state["_pending_scenario_load"] = inp
                                st.session_state["show_admin_portal"] = False
                                st.rerun()
                        with pc2:
                            if st.button("Save", key=f"prof_sv_{sid}_{s_idx}", use_container_width=True):
                                phys.rename_user_scenario(user, sid, new_nm, new_rank=new_rk)
                                st.success("Updated.")
                                st.rerun()
                        with pc3:
                            if st.button("Delete", key=f"prof_dl_{sid}_{s_idx}", use_container_width=True):
                                phys.delete_user_scenario(user, sid)
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
                    adm_email = st.text_input("Admin Email (or 'admin')", placeholder="admin@orbignite.earth", key="u_adm_email")
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
            email = st.text_input("Admin Email", placeholder="admin@orbignite.earth", key="adm_direct_email")
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
   
                    phys = _load_physics_module()
                    retrain_res = phys.record_admin_change_and_retrain(f"Admin added {record_category} record {exp_id}")
                    st.session_state["_last_retrain_status"] = retrain_res
                    st.success(f"Added {record_category} record '{exp_id}' and retrained fire prediction models.")
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
            
            safe_name = _sanitize_data_filename(uploaded.name)
            raw_bytes = bytes(uploaded.getbuffer())
            if not safe_name or safe_name in PROTECTED_DATA_FILES:
                st.error("Blocked: Invalid or protected core system filename.")
            elif len(raw_bytes) > 25 * 1024 * 1024:
                st.error("Blocked: Uploaded file exceeds the 25 MB safety limit.")
            else:
                target = os.path.join(_data_dir(), safe_name)
                if not _is_within_data_dir(target):
                    st.error("Blocked: Path traversal detected.")
                else:
                    with open(target, "wb") as out:
                        out.write(raw_bytes)
                    if safe_name.lower().endswith(".pdf"):
                        rtype_map = {
                            "Experiment": "NASA Experiment / Guide",
                            "Paper": "External Research Paper",
                            "NTRS Report": "NTRS Technical Report",
                            "Other": "Other",
                        }
                        stem = os.path.splitext(safe_name)[0]
                        is_ntrs_num = stem.isdigit() and upload_type == "NTRS Report"
                        ntrs_items = _load_ntrs_file()
                        if not any(item.get("pdf_file") == safe_name for item in ntrs_items):
                            ntrs_items.append({
                                "id": f"NTRS-{stem}" if is_ntrs_num else f"RES-{stem[:18].upper()}",
                                "ntrs_id": stem if is_ntrs_num else "",
                                "resource_type": rtype_map.get(upload_type, "Other"),
                                "title": stem.replace("_", " ").replace("-", " "),
                                "citation_url": f"https://ntrs.nasa.gov/citations/{stem}" if is_ntrs_num else "",
                                "mission": upload_type,
                                "fuel": "Uploaded Document",
                                "year": 2025,
                                "pdf_file": safe_name,
                                "summary": f"Admin-uploaded {upload_type} document ({safe_name}).",
                            })
                            _save_ntrs_file(ntrs_items)
                    st.cache_data.clear()
  
                    phys = _load_physics_module()
                    retrain_res = phys.record_admin_change_and_retrain(f"Admin uploaded file {safe_name}")
                    st.session_state["_last_retrain_status"] = retrain_res
                    st.success(f"Saved {safe_name} as '{upload_type}' and retrained fire prediction models.")


        data_files = sorted(
            f for f in os.listdir(_data_dir())
            if os.path.isfile(os.path.join(_data_dir(), f)) and f not in PROTECTED_DATA_FILES
        )
        if data_files:
            del_file = st.selectbox("Select Data File to Delete", data_files, key="del_file_select")
            if st.button("Delete Selected File"):
                
                safe_del = _sanitize_data_filename(del_file)
                target = os.path.join(_data_dir(), safe_del)
                if safe_del and safe_del not in PROTECTED_DATA_FILES and _is_within_data_dir(target) and os.path.isfile(target):
                    os.remove(target)
                    
                    phys = _load_physics_module()
                    retrain_res = phys.record_admin_change_and_retrain(f"Admin deleted data file {safe_del}")
                    st.session_state["_last_retrain_status"] = retrain_res
                    st.success(f"Removed {safe_del} and retrained fire prediction models.")
                    st.rerun()

    st.subheader("NTRS Document Registry Links")
    ntrs_items = _load_ntrs_file()
    if ntrs_items:
        df_ntrs = pd.DataFrame(ntrs_items)
        edited_ntrs = st.data_editor(df_ntrs, num_rows="dynamic", use_container_width=True, key="admin_ntrs_editor")
        if st.button("Save NTRS Registry Changes"):
            updated_ntrs = edited_ntrs.dropna(how="all").to_dict(orient="records")
            _save_ntrs_file(updated_ntrs)
            
            phys = _load_physics_module()
            retrain_res = phys.record_admin_change_and_retrain("Admin updated NTRS registry")
            st.session_state["_last_retrain_status"] = retrain_res
            st.success("NTRS registry updated and fire prediction models retrained.")
            st.rerun()
    else:
        st.caption("No NTRS links indexed yet.")


    st.subheader("Model Retraining & Benchmark Status")
    phys_state = _load_physics_module().get_dataset_and_model_state()
    last_rt = st.session_state.get("_last_retrain_status")
    if last_rt:
        if last_rt.get("ok"):
            st.success(f"Auto-retrain completed cleanly at `{last_rt.get('changed_at_utc', '')}`.")
        else:
            st.error(f"Auto-retrain warning: {last_rt.get('error', 'Unknown error')}")
    st.caption(
        f"Latest Model Build: `{phys_state.get('model_trained_at_utc', 'N/A')}` | "
        f"Last Admin Dataset Change: `{phys_state.get('last_admin_change_utc') or 'None recorded yet'}`"
    )
    if st.button("Retrain Fire Models Now", key="adm_manual_retrain"):
        with st.spinner("Retraining XGBoost fire prediction suite..."):
            retrain_res = _load_physics_module().record_admin_change_and_retrain("Manual admin model retrain")
            st.session_state["_last_retrain_status"] = retrain_res
        if retrain_res.get("ok"):
            st.success("Fire prediction models retrained and bundle updated.")
        else:
            st.error(f"Retrain failed: {retrain_res.get('error')}")
        st.rerun()

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
        "**Admin Credentials Guide:** The demo administrative password is `orb-admin` with email `admin@orbignite.earth` (or username `admin`). "
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
