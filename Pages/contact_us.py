#Contact US corner, used SI for supabase integration
from datetime import datetime, timezone
from email.message import EmailMessage
import json
import os
import re
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


def _send_email_if_configured(name, email, message, receiver_email=None):
    smtp_email = None
    smtp_password = None
    try:
        smtp_email = st.secrets.get("SMTP_EMAIL")
        smtp_password = st.secrets.get("SMTP_PASSWORD")
        if not receiver_email:
            receiver_email = st.secrets.get("CONTACT_RECEIVER_EMAIL")
    except Exception:
        pass
    smtp_email = smtp_email or os.getenv("SMTP_EMAIL")
    smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
    receiver_email = receiver_email or os.getenv("CONTACT_RECEIVER_EMAIL") or smtp_email
    if not smtp_email or not smtp_password or not receiver_email:
        return
    msg = EmailMessage()
    clean_name = re.sub(r"[\r\n]+", " ", str(name or "")).strip()[:120]
    clean_email = re.sub(r"[\r\n]+", "", str(email or "")).strip()[:180]
    clean_receiver = re.sub(r"[\r\n]+", "", str(receiver_email or "")).strip()[:180]
    clean_message = str(message or "").strip()[:5000]
    msg["Subject"] = f"Orb.Ignite Contact: {clean_name}"
    msg["From"] = smtp_email
    msg["To"] = clean_receiver
    msg["Reply-To"] = clean_email
    msg.set_content(f"From: {clean_name} <{clean_email}>\nTo: {clean_receiver}\n\n{clean_message}")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
        server.login(smtp_email, smtp_password)
        server.send_message(msg)


def render():
    default_rcv = ""
    try:
        default_rcv = st.secrets.get("CONTACT_RECEIVER_EMAIL", "")
    except Exception:
        pass
    default_rcv = default_rcv or os.getenv("CONTACT_RECEIVER_EMAIL", "")

    with st.form("contact_us_form", clear_on_submit=True):
        name = st.text_input("Name", placeholder="Your name or callsign")
        email = st.text_input("Your Email (Reply-To)", placeholder="researcher@agency.org")
        receiver = st.text_input(
            "Receiver Email (Optional — for inter-researcher communication)",
            placeholder="Leave blank to send directly to Orb.Ignite Team without disclosing mailbox",
        )
        message = st.text_area("Message", placeholder="Enter your scientific inquiry, observation, or telemetry request...")
        submitted = st.form_submit_button("Send Message")
        if submitted:
            email_clean = email.strip()
            if not name.strip() or not email_clean or not message.strip():
                st.error("Please fill in your name, email, and message.")
            elif not re.match(r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+$", email_clean):
                st.error("Please enter a valid reply-to email address.")
            else:
                raw_rcv = receiver.strip()
                if raw_rcv and not re.match(r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+$", raw_rcv):
                    st.error("Please enter a valid recipient email address or leave it blank.")
                else:
                    
                    safe_name = re.sub(r"[\r\n]+", " ", name.strip())[:120]
                    safe_email = re.sub(r"[\r\n]+", "", email_clean)[:180]
                    safe_rcv = re.sub(r"[\r\n]+", "", raw_rcv)[:180]
                    safe_msg = message.strip()[:5000]
                    target_receiver = safe_rcv if safe_rcv else (default_rcv or "admin@orbignite.org")
                    stored_receiver_label = safe_rcv if safe_rcv else "Orb.Ignite Project Mailbox (Direct)"
                    payload = {
                        "name": safe_name,
                        "email": safe_email,
                        "receiver": stored_receiver_label,
                        "message": safe_msg,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    _save_contact_message(payload)
                    try:
                        _send_email_if_configured(safe_name, safe_email, safe_msg, receiver_email=target_receiver)
                    except Exception:
                        pass
                    if safe_rcv:
                        st.success(f"Message forwarded successfully to {safe_rcv}.")
                    else:
                        st.success("Message sent securely to the Orb.Ignite Project Team.")
