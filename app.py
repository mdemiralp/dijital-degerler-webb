import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from backend.db import init_db, register_user, login_user, get_conn
from backend.email_utils import send_email

st.set_page_config(page_title="Dijital Değerler Takip", page_icon="🌿", layout="wide")
init_db()

def load_tasks(file="data/gorevler.xlsx"):
    conn = get_conn()
    c = conn.cursor()
    df = pd.read_excel(file, sheet_name="Görevler")
    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        week TEXT, value TEXT, text TEXT, points INTEGER
    )""")
    for _, row in df.iterrows():
        c.execute("SELECT COUNT(*) FROM tasks WHERE text=?", (row["Görev Metni"],))
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO tasks (week,value,text,points) VALUES (?,?,?,?)",
                      (row["Gün/Tarih"], row["Değer"], row["Görev Metni"], row["Puan Değeri"]))
    conn.commit()
    conn.close()

def complete_task(user_email, task_id, reflection):
    conn = get_conn()
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT * FROM records WHERE user_email=? AND task_id=?", (user_email, task_id))
    if c.fetchone():
        st.warning("Bu görevi zaten tamamladın!")
    else:
        c.execute("INSERT INTO records (user_email, task_id, completed, date, reflection) VALUES (?, ?, 1, ?, ?)",
                  (user_email, task_id, today, reflection))
        c.execute("UPDATE users SET points = points + 1 WHERE email=?", (user_email,))
        conn.commit()
        st.success("🎉 Görev tamamlandı! +1 puan kazandın.")
    conn.close()

def teacher_dashboard():
    st.header("📊 Öğretmen Paneli")
    conn = get_conn()
    users = pd.read_sql("SELECT name, email, points, medals FROM users WHERE role='student'", conn)
    conn.close()
    st.dataframe(users, use_container_width=True)

    st.subheader("🔔 Hatırlatma Gönder")
    if not users.empty:
        selected_email = st.selectbox("Öğrenci seç:", users["email"].tolist())
        if st.button("Hatırlatma Gönder"):
            body = "Merhaba 🌿\nBugünkü görevini tamamlamayı unutma!\nSevgiler, Dijital Değerler Ekibi"
            send_email(selected_email, "🌿 Dijital Değerler Hatırlatma", body)

    st.subheader("🏅 En Aktif Öğrenciler")
    if not users.empty:
        plt.figure()
        users_sorted = users.sort_values("points", ascending=False).head(5)
        plt.bar(users_sorted["name"], users_sorted["points"])
        plt.title("En Aktif 5 Öğrenci")
        st.pyplot(plt)

def student_view(user):
    st.header(f"👋 Hoş geldin, {user[1]}!")
    st.info(f"Puan: {user[5]} | Madalya: {user[6]} 🥇")

    load_tasks()
    conn = get_conn()
    tasks = pd.read_sql("SELECT * FROM tasks", conn)
    conn.close()

    for _, t in tasks.iterrows():
        with st.expander(f"{t['week']} — {t['value']}"):
            st.write(t["text"])
            reflection = st.text_input("Yansıtma notun:", key=f"r_{t['id']}")
            if st.button(f"Tamamla ✅ {t['id']}", key=f"b_{t['id']}"):
                complete_task(user[2], t["id"], reflection)

st.title("🌿 Dijital Değerler Takip Sistemi")
menu = ["Giriş Yap", "Kayıt Ol"]
choice = st.sidebar.selectbox("Menü", menu)

if choice == "Kayıt Ol":
    name = st.text_input("Ad Soyad")
    email = st.text_input("E-posta")
    password = st.text_input("Şifre", type="password")
    role = st.selectbox("Rol", ["student", "teacher"])
    if st.button("Kayıt Ol"):
        if register_user(name, email, password, role):
            st.success("Kayıt başarılı! Şimdi giriş yapabilirsiniz.")
        else:
            st.error("Bu e-posta zaten kayıtlı.")
else:
    email = st.text_input("E-posta")
    password = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        user = login_user(email, password)
        if user:
            st.session_state["user"] = user
        else:
            st.error("E-posta veya şifre hatalı.")

if "user" in st.session_state:
    user = st.session_state["user"]
    if user[4] == "teacher":
        teacher_dashboard()
    else:
        student_view(user)
