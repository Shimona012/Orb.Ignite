#Contact US corner, used SI for supabase integration
from datetime import datetime, timezone
from email.message import EmailMessage
import json
import os
import re
import smtplib
import streamlit as st
import Authentication

#To be tried after the whole mock is done
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
    msg["Subject"] = f"Orb.Ignite Contact: {name}"
    msg["From"] = smtp_email
    msg["To"] = receiver_email
    msg["Reply-To"] = email
    msg.set_content(f"From: {name} <{email}>\nTo: {receiver_email}\n\n{message}")
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
                    target_receiver = raw_rcv if raw_rcv else (default_rcv or "admin@orbignite.org")
                    stored_receiver_label = raw_rcv if raw_rcv else "Orb.Ignite Project Mailbox (Direct)"
                    payload = {
                        "name": name.strip(),
                        "email": email_clean,
                        "receiver": stored_receiver_label,
                        "message": message.strip(),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    _save_contact_message(payload)
                    try:
                        _send_email_if_configured(name.strip(), email_clean, message.strip(), receiver_email=target_receiver)
                    except Exception:
                        pass
                    if raw_rcv:
                        st.success(f"Message forwarded successfully to {raw_rcv}.")
                    else:
                        st.success("Message sent securely to the Orb.Ignite Project Team.")
