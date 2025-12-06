import smtplib
from email.mime.text import MIMEText
import streamlit as st

def send_email(to_email, subject, body):
    sender_email = st.secrets["EMAIL_USER"]
    app_password = st.secrets["EMAIL_PASS"]

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        st.success(f"📨 {to_email} adresine e-posta gönderildi.")
    except Exception as e:
        st.error(f"E-posta gönderimi başarısız: {e}")
