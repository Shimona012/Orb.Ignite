#Contact US corner, used SI for supabase integration
from datetime import datetime, timezone
from email.message import EmailMessage
import json
import os
import re
import smtplib
import socket
import uuid
import streamlit as st
import Authentication


def _get_messages_file_path():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Data")
    return os.path.join(data_dir, "contact_messages.json")


def load_contact_messages():
    msg_path = _get_messages_file_path()
    if os.path.exists(msg_path):
        try:
            with open(msg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []
    return []


def delete_contact_message(idx):
    msg_path = _get_messages_file_path()
    messages = load_contact_messages()
    if 0 <= idx < len(messages):
        messages.pop(idx)
        with open(msg_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2)
        return True
    return False


def clear_all_contact_messages():
    msg_path = _get_messages_file_path()
    with open(msg_path, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)


def validate_email_address(email_str):
    if not email_str:
        return False, "Email address cannot be empty."
    clean = email_str.strip().lower()
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, clean):
        return False, "Please enter a valid email format (e.g. name@domain.com)."
    parts = clean.split("@")
    if len(parts) != 2:
        return False, "Email must contain exactly one '@' symbol."
    user_part, domain_part = parts
    if not user_part or not domain_part:
        return False, "Email username and domain cannot be empty."
    if ".." in domain_part or domain_part.startswith(".") or domain_part.endswith("."):
        return False, "Invalid email domain structure."
    tld = domain_part.split(".")[-1]
    if len(tld) < 2 or not tld.isalpha():
        return False, f"Email domain extension '.{tld}' is invalid."
    try:
        socket.setdefaulttimeout(3.0)
        socket.gethostbyname(domain_part)
    except socket.gaierror:
        return False, f"The email domain '@{domain_part}' does not exist or has no active DNS records."
    except Exception:
        pass
    return True, ""


def _save_contact_message(payload):
    client = Authentication._get_supabase_client()
    if client is not None:
        try:
            client.table("contact_messages").insert(payload).execute()
        except Exception:
            pass

    msg_path = _get_messages_file_path()
    existing = load_contact_messages()
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
    smtp_email = None
    try:
        smtp_email = st.secrets.get("SMTP_EMAIL")
        default_rcv = st.secrets.get("CONTACT_RECEIVER_EMAIL", "")
    except Exception:
        pass
    smtp_email = smtp_email or os.getenv("SMTP_EMAIL")
    default_rcv = default_rcv or os.getenv("CONTACT_RECEIVER_EMAIL", "")

    st.write("Send a message, research query, or feedback to the Orb.Ignite team.")

    with st.form("contact_us_form", clear_on_submit=True):
        name = st.text_input("Your Name", placeholder="Your name or callsign")
        email = st.text_input("Your Email Address (Reply-To)", placeholder="researcher@agency.org")
        
        st.markdown("**Send Message To:**")
        c_rcv1, c_rcv2 = st.columns(2)
        with c_rcv1:
            send_to_admin = st.checkbox(
                "Administrator (Orb.Ignite Admin Inbox)",
                value=True,
                help="Saved directly to the Admin Inbox in the Orb.Ignite portal for project administrators.",
            )
        with c_rcv2:
            send_to_developer = st.checkbox(
                "Developer (Direct Technical Support)",
                value=False,
                help="Emailed directly to shimona.n.bakshi@gmail.com for technical inquiries.",
            )

        message = st.text_area(
            "Message",
            placeholder="Enter your scientific inquiry, observation, bug report, or telemetry request...",
            height=130,
        )
        submitted = st.form_submit_button("Send Message", use_container_width=True)
        if submitted:
            email_clean = email.strip()
            is_valid_em, em_err = validate_email_address(email_clean)
            if not name.strip() or not message.strip():
                st.error("Please fill in your name and message.")
            elif not is_valid_em:
                st.error(em_err)
            elif not send_to_admin and not send_to_developer:
                st.error("Please select at least one recipient (Admin, Developer, or both).")
            else:
                safe_name = re.sub(r"[\r\n]+", " ", name.strip())[:120]
                safe_email = re.sub(r"[\r\n]+", "", email_clean)[:180]
                safe_msg = message.strip()[:5000]

                target_labels = []
                if send_to_admin:
                    target_labels.append("Administrator (Admin Inbox)")
                if send_to_developer:
                    target_labels.append("Developer (shimona.n.bakshi@gmail.com)")

                stored_receiver_label = " & ".join(target_labels)
                payload = {
                    "id": uuid.uuid4().hex[:8],
                    "name": safe_name,
                    "email": safe_email,
                    "receiver": stored_receiver_label,
                    "to_admin": bool(send_to_admin),
                    "to_developer": bool(send_to_developer),
                    "message": safe_msg,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                _save_contact_message(payload)

                dev_email = "shimona.n.bakshi@gmail.com"
                if send_to_developer:
                    try:
                        _send_email_if_configured(safe_name, safe_email, safe_msg, receiver_email=dev_email)
                    except Exception:
                        pass

                if send_to_admin:
                    admin_rcv = default_rcv or smtp_email or "admin@orbignite.earth"
                    try:
                        _send_email_if_configured(safe_name, safe_email, safe_msg, receiver_email=admin_rcv)
                    except Exception:
                        pass

                if send_to_admin and send_to_developer:
                    st.success("Message recorded in the Admin Inbox and forwarded to Developer (shimona.n.bakshi@gmail.com).")
                elif send_to_developer:
                    st.success("Message forwarded to Developer (shimona.n.bakshi@gmail.com).")
                else:
                    st.success("Message recorded securely in the Orb.Ignite Admin Inbox.")
