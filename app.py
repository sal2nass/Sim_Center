import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة واللغة
st.set_page_config(page_title="Simulation Center System", layout="wide")

# قاموس المستخدمين والصلاحيات (تعدله لاحقاً بايميلاتك الحقيقية)
USERS = {
    "sal2nass@gmail.com": {"name": "المدير العام", "role": "owner"},
    "sal4nass@gmail.com": {"name": "منسق العمليات", "role": "coordinator"},
    "sal_saleh@hotmail.com": {"name": "أحمد محمد", "role": "employee"}
}

# 2. نظام الدخول البسيط
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 تسجيل الدخول | Login")
    email_input = st.text_input("أدخل البريد الإلكتروني المعتمد")
    if st.button("دخول"):
        if email_input in USERS:
            st.session_state.authenticated = True
            st.session_state.user_info = USERS[email_input]
            st.session_state.user_email = email_input
            st.rerun()
        else:
            st.error("البريد غير مسجل في النظام")
else:
    # --- بعد تسجيل الدخول بنجاح ---
    user = st.session_state.user_info
    
    # القائمة الجانبية حسب الصلاحية
    st.sidebar.write(f"مرحباً، {user['name']}")
    
    if user['role'] == "owner":
        menu = ["الداشبورد العام", "إدارة الإجازات", "رفع البيانات", "التقارير"]
    elif user['role'] == "coordinator":
        menu = ["الداشبورد العام", "مراجعة الإجازات"]
    else:
        menu = ["ملفي الشخصي", "طلب إجازة"]
    
    choice = st.sidebar.radio("القائمة", menu)

    # --- صفحة الداشبورد (للاونر والمنسق) ---
    if "الداشبورد العام" in choice:
        st.header("📊 لوحة المؤشرات الإجمالية")
        # هنا تضع كود المربعات (Metrics) الذي عملناه سابقاً
        st.success("هذه الصفحة تظهر فقط للمدراء والمنسقين")

    # --- صفحة رفع البيانات (للاونر فقط) ---
    if choice == "رفع البيانات":
        st.header("📤 تحديث بيانات النظام")
        uploaded_file = st.file_uploader("ارفع ملف data.xlsx لتحديث الساعات والأداء")
        if uploaded_file:
            st.success("تم تحديث البيانات بنجاح!")

    # زر الخروج
    if st.sidebar.button("تسجيل خروج"):
        st.session_state.authenticated = False
        st.rerun()
