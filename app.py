import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة والتنسيق الاحترافي ---
st.set_page_config(page_title="SimCenter Pro OS", layout="wide")

# CSS لتجميل الواجهة بشكل جذري
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    * { font-family: 'Cairo', sans-serif; }
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-top: 4px solid #4B90FF; }
    div[data-testid="stExpander"] { background-color: white; border-radius: 10px; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #4B90FF; color: white; font-weight: bold; }
    [data-testid="stSidebar"] { background-color: #0E1117; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. نظام اللغات والصلاحيات ---
TRANSLATIONS = {
    "العربية": {
        "dir": "rtl", "dash": "لوحة البيانات", "leaves": "إدارة الإجازات", "cal": "تقويم الحضور", 
        "ext": "الطلبات الخارجية", "rep": "التقارير", "update": "تحديث البيانات", "profile": "ملفي الشخصي",
        "apply": "طلب إجازة", "target": "الساعات المستهدفة", "executed": "الساعات المنفذة", "manikins": "حالة الدمى"
    },
    "English": {
        "dir": "ltr", "dash": "Dashboard", "leaves": "Leave Management", "cal": "Attendance Calendar", 
        "ext": "External Requests", "rep": "Reports", "update": "Update Data", "profile": "My Profile",
        "apply": "Apply for Leave", "target": "Target Hours", "executed": "Executed Hours", "manikins": "Manikins Status"
    }
}

lang_choice = st.sidebar.selectbox("Language / اللغة", ["العربية", "English"])
T = TRANSLATIONS[lang_choice]

USERS = {
    "sal2nass@gmail.com": {"name": "المدير العام", "role": "owner"},
    "sal4nass@gmail.com": {"name": "المنسق", "role": "coordinator"},
    "sal_saleh@hotmail.com": {"name": "صالح (موظف)", "role": "employee"}
}

if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'leave_db' not in st.session_state: st.session_state.leave_db = []

# --- 3. منطق الدخول ---
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.title("🛡️ SimCenter OS")
        email = st.text_input("البريد الإلكتروني | Email").lower().strip()
        if st.button("دخول | Login"):
            if email in USERS:
                st.session_state.authenticated = True
                st.session_state.user = USERS[email]
                st.rerun()
            else: st.error("Access Denied | غير مسجل")
else:
    user = st.session_state.user
    role = user['role']
    st.sidebar.markdown(f"### ✨ {user['name']}")
    
    # القوائم
    if role == "owner": menu = [T['dash'], T['leaves'], T['cal'], T['ext'], T['rep']]
    elif role == "coordinator": menu = [T['dash'], T['cal'], T['update']]
    else: menu = [T['profile'], T['apply']]
    choice = st.sidebar.radio("Main Menu", menu)

    # --- 4. محتوى الصفحات (مع الرسوم البيانية) ---
    if choice == T['dash']:
        st.header(f"📊 {T['dash']}")
        
        # البطاقات العلوية
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("مدربين اليوم", "8", "+2")
        m2.metric("مشغلين اليوم", "5", "-1")
        m3.metric("إجمالي الكادر", "25")
        m4.metric("كورسات مفعلة", "12")

        st.markdown("---")
        
        # الرسوم البيانية
        g1, g2 = st.columns([2, 1])
        
        with g1:
            st.subheader(f"📈 {T['executed']} vs {T['target']}")
            fig_hours = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = 850,
                delta = {'reference': 1200},
                gauge = {'axis': {'range': [None, 1200]},
                         'bar': {'color': "#4B90FF"},
                         'steps': [
                             {'range': [0, 600], 'color': "#FF4B4B"},
                             {'range': [600, 1200], 'color': "#E1E9F4"}]}))
            fig_hours.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_hours, use_container_width=True)

        with g2:
            st.subheader(f"🤖 {T['manikins']}")
            fig_pie = px.pie(values=[32, 8], names=["Working", "Maintenance"], 
                             color_discrete_sequence=["#00CC96", "#EF553B"], hole=0.5)
            fig_pie.update_layout(height=300, showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_pie, use_container_width=True)

    elif choice == T['cal']:
        st.header(T['cal'])
        st.info("جدول توزيع القوى البشرية للأسبوع الحالي")
        # تقويم تفاعلي بسيط
        dates = [(datetime.now() + timedelta(days=i)).strftime('%A %d/%m') for i in range(7)]
        df_cal = pd.DataFrame({
            "الموظف": ["صالح", "أحمد", "خالد", "فهد"],
            dates[0]: ["✅", "✅", "✅", "✅"],
            dates[1]: ["✅", "❌", "✅", "✅"],
            dates[2]: ["✅", "✅", "❌", "✅"],
            dates[3]: ["✅", "✅", "✅", "❌"]
        })
        st.dataframe(df_cal.set_index("الموظف"), use_container_width=True)
        st.write("✅: متواجد | ❌: إجازة")

    elif choice == T['apply']:
        st.subheader("📝 تقديم طلب إجازة")
        with st.container():
            start_date = st.date_input("تاريخ البدء")
            end_date = st.date_input("تاريخ الانتهاء")
            reason = st.text_area("السبب")
            if st.button(T['apply']):
                st.session_state.leave_db.append({
                    "Name": user['name'], "From": start_date, "To": end_date, "Reason": reason, "Status": "Pending"
                })
                st.balloons()
                st.success("تم إرسال الطلب بنجاح إلى المدير العام")

    elif choice == T['leaves'] and role == "owner":
        st.header("📥 الطلبات المعلقة")
        if st.session_state.leave_db:
            df_leaves = pd.DataFrame(st.session_state.leave_db)
            st.table(df_leaves)
            c_app, c_rej = st.columns(2)
            c_app.button("✅ اعتماد الكل")
            c_rej.button("❌ رفض")
        else:
            st.write("لا توجد طلبات حالياً")

    elif choice == T['update'] and role == "coordinator":
        st.header("🔄 تحديث بيانات المركز اليومية")
        with st.expander("إدخال البيانات التشغيلية"):
            st.number_input("المدربين اليوم", value=8)
            st.number_input("المشغلين اليوم", value=5)
            st.number_input("الساعات المنفذة الجديدة", value=10)
            st.button("حفظ وإرسال")

    if st.sidebar.button("🚪 Logout | خروج"):
        st.session_state.authenticated = False
        st.rerun()
