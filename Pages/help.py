#Contact US corner, used SI for supabase integration
from datetime import datetime, timezone
from email.message import EmailMessage
import json
import os
import smtplib
import streamlit as st
import Authentication


def _save_contact_message(payload):
    client = Authentication._get_supabase_client()
    if client is not None:
        try:
            client.table("contact_messages").insert(payload).execute()
        except Exception:
            pass

    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Data")
    msg_path = os.path.join(data_dir, "contact_messages.json")
    existing = []
    if os.path.exists(msg_path):
        try:
            with open(msg_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []
    existing.append(payload)
    with open(msg_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)


def _send_email_if_configured(name, email, message):
    smtp_email = None
    smtp_password = None
    receiver_email = None
    try:
        smtp_email = st.secrets.get("SMTP_EMAIL")
        smtp_password = st.secrets.get("SMTP_PASSWORD")
        receiver_email = st.secrets.get("CONTACT_RECEIVER_EMAIL")
    except Exception:
        pass
    smtp_email = smtp_email or os.getenv("SMTP_EMAIL")
    smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
    receiver_email = receiver_email or os.getenv("CONTACT_RECEIVER_EMAIL") or smtp_email
    if not smtp_email or not smtp_password or not receiver_email:
        return
    msg = EmailMessage()
    msg["Subject"] = f"Orb.Ignite Contact: {name}"
    msg["From"] = smtp_email
    msg["To"] = receiver_email
    msg["Reply-To"] = email
    msg.set_content(f"From: {name} <{email}>\n\n{message}")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
        server.login(smtp_email, smtp_password)
        server.send_message(msg)


def render():
    with st.form("contact_us_form", clear_on_submit=True):
        name = st.text_input("Name")
        email = st.text_input("Email")
        message = st.text_area("Message")
        submitted = st.form_submit_button("Send")
        if submitted:
            if not name.strip() or not email.strip() or not message.strip():
                st.error("Please fill in your name, email, and message.")
            else:
                payload = {
                    "name": name.strip(),
                    "email": email.strip(),
                    "message": message.strip(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                _save_contact_message(payload)
                try:
                    _send_email_if_configured(name.strip(), email.strip(), message.strip())
                except Exception:
                    pass
                st.success("Message sent.")
