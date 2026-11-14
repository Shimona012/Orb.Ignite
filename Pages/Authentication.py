#Authtenticate for editing and admin uses, admins can edit/add/delete datasets, presets etc.
import json
import os
import pandas as pd
import streamlit as st
from supabase import create_client

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
    return create_client(url, key)


def _data_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Data")


def _load_experiments_file():
    path = os.path.join(_data_dir(), "experiments.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_experiments_file(records, client=None):
    path = os.path.join(_data_dir(), "experiments.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    if client is not None and records:
        try:
            client.table("experiments").upsert(records).execute()
        except Exception:
            pass
    st.cache_data.clear()


def render_admin_portal():
    st.header("Admin Portal")
    client = _get_supabase_client()

    if client is None:
        st.warning("Configure SUPABASE_URL and SUPABASE_KEY in .streamlit/secrets.toml to enable Supabase authentication.")
        return

    user = st.session_state.get("admin_user")

    if not user:
        with st.form("supabase_login_form"):
            email = st.text_input("Admin Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In")
            if submitted:
                try:
                    res = client.auth.sign_in_with_password({"email": email, "password": password})
                    if res.user:
                        st.session_state["admin_user"] = res.user.email
                        st.rerun()
                except Exception as exc:
                    st.error(f"Authentication failed: {exc}")
        return

    col_u1, col_u2 = st.columns([4, 1])
    with col_u1:
        st.caption(f"Signed in as {user}")
    with col_u2:
        if st.button("Sign Out"):
            try:
                client.auth.sign_out()
            except Exception:
                pass
            st.session_state.pop("admin_user", None)
            st.rerun()

    records = _load_experiments_file()

    st.subheader("Edit or Delete Experiment Records")
    df = pd.DataFrame(records)
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="admin_editor")
    if st.button("Save Changes"):
        updated = edited_df.dropna(how="all").to_dict(orient="records")
        _save_experiments_file(updated, client)
        st.success("Dataset updated.")
        st.rerun()

    with st.expander("Add Experiment"):
        with st.form("add_exp_form"):
            c1, c2 = st.columns(2)
            with c1:
                exp_id = st.text_input("ID")
                mission = st.text_input("Mission")
                name = st.text_input("Name")
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
                ntrs_id = st.text_input("NTRS Document ID")
                ntrs_link = st.text_input("NTRS Link (optional)")
            key_phenomenon = st.text_area("Key Phenomenon")

            if st.form_submit_button("Add Record"):
                if not exp_id or not name:
                    st.error("ID and Name are required.")
                else:
                    records.append({
                        "id": exp_id,
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
                    st.success(f"Added {exp_id}.")
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
        uploaded = st.file_uploader("Upload Dataset File", type=["json", "csv", "pdf"])
        if uploaded is not None and st.button("Save Uploaded File"):
            target = os.path.join(_data_dir(), uploaded.name)
            with open(target, "wb") as out:
                out.write(uploaded.getbuffer())
            st.success(f"Saved {uploaded.name}.")

        data_files = sorted(os.listdir(_data_dir()))
        if data_files:
            del_file = st.selectbox("Select Data File to Delete", data_files, key="del_file_select")
            if st.button("Delete Selected File"):
                target = os.path.join(_data_dir(), del_file)
                if os.path.exists(target):
                    os.remove(target)
                    st.success(f"Removed {del_file}.")
                    st.rerun()

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
