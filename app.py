import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. إعدادات اللغة والتنسيق ---
st.set_page_config(page_title="SimCenter OS", layout="wide")

# قاموس الترجمة
TRANSLATIONS = {
    "العربية": {
        "dir": "rtl",
        "dash": "الداشبورد",
        "leaves": "إدارة الإجازات",
        "ext_req": "الطلبات الخارجية",
        "reports": "التقارير",
        "update_data": "تحديث البيانات",
        "my_profile": "ملفي الشخصي",
        "apply_leave": "طلب إجازة",
        "calendar": "تقويم الحضور الشهري",
        "present": "متواجد",
        "absent": "إجازة",
        "send": "إرسال الطلب",
        "logout": "تسجيل خروج",
        "welcome": "مرحباً"
    },
    "English": {
        "dir": "ltr",
        "dash": "Dashboard",
        "leaves": "Leave Management",
        "ext_req": "External Requests",
        "reports": "Reports",
        "update_data": "Update Data",
        "my_profile": "My Profile",
        "apply_leave": "Apply for Leave",
        "calendar": "Monthly Attendance Calendar",
        "present": "Present",
        "absent": "On Leave",
        "send": "Submit Request",
        "logout": "Logout",
        "welcome": "Welcome"
    }
}

# اختيار اللغة في أعلى القائمة الجانبية
if 'lang' not in st.session_state: st.session_state.lang = "العربية"
lang_choice = st.sidebar.selectbox("Language / اللغة", ["العربية", "English"])
T = TRANSLATIONS[lang_choice]

# تطبيق التنسيق بناءً على اللغة
st.markdown(f"""<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * {{ font-family: 'Cairo', sans-serif; direction: {T['dir']}; text-align: {"right" if T['dir'] == 'rtl' else "left"}; }}
    .stMetric {{ background: white; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px #eee; }}
</style>""", unsafe_allow_html=True)

# --- 2. إدارة الدخول والصلاحيات ---
USERS = {
    "sal2nass@gmail.com": {"name": "المدير العام", "role": "owner"},
    "sal4nass@gmail.com": {"name": "المنسق", "role": "coordinator"},
    "sal_saleh@hotmail.com": {"name": "صالح (موظف)", "role": "employee"}
}

if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'leave_db' not in st.session_state: st.session_state.leave_db = []

if not st.session_state.authenticated:
    st.title("🔐 Login | دخول")
    email = st.text_input("Email").lower().strip()
    if st.button("Login"):
        if email in USERS:
            st.session_state.authenticated = True
            st.session_state.user = USERS[email]
            st.rerun()
else:
    user = st.session_state.user
    role = user['role']
    
    # القائمة الجانبية المخصصة
    st.sidebar.subheader(f"{T['welcome']}, {user['name']}")
    
    if role == "owner":
        menu = [T['dash'], T['leaves'], T['calendar'], T['ext_req'], T['reports']]
    elif role == "coordinator":
        menu = [T['dash'], T['calendar'], T['update_data']]
    else:
        menu = [T['my_profile'], T['apply_leave']]
        
    choice = st.sidebar.radio("Menu", menu)

    # --- 3. محتوى الصفحات بناءً على الملاحظات ---

    if choice == T['dash']:
        st.header(T['dash'])
        c1, c2, c3 = st.columns(3)
        c1.metric("Trainers", "8")
        c2.metric("Operators", "5")
        c3.metric("Operation %", "71%")

    elif choice == T['calendar']:
        st.header(T['calendar'])
        # بناء تقويم بسيط يعرض الموظفين
        days = [datetime.now() + timedelta(days=i) for i in range(7)]
        cal_data = {
            "Employee": ["صالح", "أحمد", "خالد"],
            days[0].strftime('%d/%m'): ["✅", "✅", "✅"],
            days[1].strftime('%d/%m'): ["✅", "❌", "✅"],
            days[2].strftime('%d/%m'): ["✅", "✅", "❌"],
        }
        st.table(pd.DataFrame(cal_data))
        st.caption("✅ = متواجد | ❌ = إجازة معتمدة")

    elif choice == T['apply_leave']:
        st.header(T['apply_leave'])
        with st.form("leave"):
            start = st.date_input("From")
            end = st.date_input("To")
            reason = st.text_area("Reason")
            if st.form_submit_button(T['send']):
                st.session_state.leave_db.append({"user": user['name'], "start": start, "end": end, "status": "Pending"})
                st.success("Sent to Owner!")

    elif choice == T['leaves'] and role == "owner":
        st.header(T['leaves'])
        if st.session_state.leave_db:
            st.write(pd.DataFrame(st.session_state.leave_db))
            if st.button("Approve All"): st.success("Approved!")
        else:
            st.info("No pending requests")

    elif choice == T['update_data'] and role == "coordinator":
        st.header(T['update_data'])
        st.number_input("Present Trainers Today", value=8)
        st.number_input("Active Manikins", value=32)
        if st.button("Save Changes"): st.success("Updated Successfully")

    if st.sidebar.button(T['logout']):
        st.session_state.authenticated = False
        st.rerun()
