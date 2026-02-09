import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="SimCenter Pro OS", layout="wide")

# تصميم CSS لتحسين الواجهة والخطوط
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    * { font-family: 'Cairo', sans-serif; }
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-bottom: 4px solid #4B90FF; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. نظام الترجمة (عربي/انجليزي) ---
TRANSLATIONS = {
    "العربية": {
        "dir": "rtl", "dash": "لوحة المؤشرات", "leaves": "إدارة الإجازات", "cal": "تقويم الحضور والجدولة", 
        "ext": "الطلبات الخارجية", "rep": "التقارير", "update": "تحديث البيانات اليومية", "profile": "ملفي الشخصي",
        "apply": "تقديم طلب إجازة", "welcome": "مرحباً بك", "logout": "تسجيل خروج",
        "working": "تعمل", "maintenance": "صيانة", "hours_status": "حالة الساعات التشغيلية"
    },
    "English": {
        "dir": "ltr", "dash": "Dashboard", "leaves": "Leave Management", "cal": "Attendance & Scheduling", 
        "ext": "External Requests", "rep": "Reports", "update": "Daily Data Update", "profile": "My Profile",
        "apply": "Apply for Leave", "welcome": "Welcome", "logout": "Logout",
        "working": "Working", "maintenance": "Maintenance", "hours_status": "Operation Hours Status"
    }
}

# شريط اللغة الجانبي
if 'lang' not in st.session_state: st.session_state.lang = "العربية"
lang_choice = st.sidebar.selectbox("Language / اللغة", ["العربية", "English"])
T = TRANSLATIONS[lang_choice]

# --- 3. نظام الصلاحيات ---
USERS = {
    "sal2nass@gmail.com": {"name": "المدير العام", "role": "owner"},
    "sal4nass@gmail.com": {"name": "المنسق", "role": "coordinator"},
    "sal_saleh@hotmail.com": {"name": "صالح (موظف)", "role": "employee"}
}

if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'leave_db' not in st.session_state: st.session_state.leave_db = []

# --- 4. منطق تسجيل الدخول ---
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.title("🛡️ SimCenter OS")
        email_input = st.text_input("البريد الإلكتروني | Email").lower().strip()
        if st.button("دخول | Login"):
            if email_input in USERS:
                st.session_state.authenticated = True
                st.session_state.user = USERS[email_input]
                st.rerun()
            else: st.error("Access Denied | غير مسجل")
else:
    curr_user = st.session_state.user
    role = curr_user['role']
    st.sidebar.markdown(f"### ✨ {T['welcome']}, {curr_user['name']}")
    
    # تحديد القوائم بناءً على الصلاحيات
    if role == "owner": 
        menu = [T['dash'], T['leaves'], T['cal'], T['ext'], T['rep']]
    elif role == "coordinator": 
        menu = [T['dash'], T['cal'], T['update']]
    else: 
        menu = [T['profile'], T['apply']]
    
    choice = st.sidebar.radio("Main Menu", menu)

    # --- 5. محتوى الصفحات ---

    if choice == T['dash']:
        st.header(T['dash'])
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("مدربين اليوم", "8")
        m2.metric("مشغلين اليوم", "5")
        m3.metric("إجمالي الكادر", "25")
        m4.metric("كورسات المحاكاة", "24")
        st.markdown("---")
        
        c_chart1, c_chart2 = st.columns([2, 1])
        with c_chart1:
            st.subheader(T['hours_status'])
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = 850,
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {'axis': {'range': [None, 1200]}, 'bar': {'color': "#4B90FF"}}
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)

        with c_chart2:
            st.subheader("🤖 حالة الدمى")
            fig_pie = px.pie(values=[32, 8], names=[T['working'], T['maintenance']], 
                             color_discrete_sequence=["#28a745", "#dc3545"], hole=0.4)
            fig_pie.update_layout(height=300, showlegend=True)
            st.plotly_chart(fig_pie, use_container_width=True)

    elif choice == T['cal']:
        st.header(T['cal'])
        st.info("عرض التواجد اليومي والشهري للمساعدة في الجدولة")
        current_date = datetime.now()
        dates = [(current_date + timedelta(days=i)).strftime('%d/%m') for i in range(10)]
        data_cal = {"الموظف / Employee": ["صالح", "أحمد", "سارة", "خالد", "نورة"]}
        for d in dates: data_cal[d] = ["✅"] * 5
        data_cal[dates[1]][1] = "❌" # مثال لغياب
        st.dataframe(pd.DataFrame(data_cal).set_index("الموظف / Employee"), use_container_width=True)

    elif choice == T['apply']:
        st.subheader(T['apply'])
        with st.form("leave_request"):
            start = st.date_input("بداية الإجازة")
            end = st.date_input("نهاية الإجازة")
            reason = st.text_area("سبب الطلب")
            if st.form_submit_button(T['apply']):
                st.session_state.leave_db.append({"الموظف": curr_user['name'], "من": start, "إلى": end, "الحالة": "قيد الانتظار"})
                st.balloons()
                st.success("تم إرسال طلبك بنجاح")

    elif choice == T['leaves'] and role == "owner":
        st.header("📥 طلبات الإجازات الواردة")
        if st.session_state.leave_db:
            st.table(pd.DataFrame(st.session_state.leave_db))
        else: st.info("لا توجد طلبات معلقة")

    elif choice == T['update'] and role == "coordinator":
        st.header(T['update'])
        with st.form("update_form"):
            st.number_input("عدد المدربين", value=8)
            st.number_input("عدد المشغلين", value=5)
            st.number_input("عدد الدمى", value=32)
            if st.form_submit_button("حفظ التحديثات"):
                st.success("تم التحديث بنجاح")

    elif choice == T['ext'] and role == "owner":
        st.header(T['ext'])
        st.write("جدول متابعة الطلبات الخارجية...")

    if st.sidebar.button(T['logout']):
        st.session_state.authenticated = False
        st.rerun()
