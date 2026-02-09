import streamlit as st
import pandas as pd

# 1. قاموس اللغات
languages = {
    "العربية": {
        "dir": "rtl",
        "title": "نظام إدارة مركز المحاكاة",
        "dash": "لوحة المؤشرات",
        "emp_page": "صفحة الموظف",
        "admin": "الإدارة",
        "trainers": "المدربين الحاضرين",
        "operators": "المشغلين الحاضرين",
        "total_trainers": "إجمالي المدربين",
        "total_operators": "إجمالي المشغلين",
        "hours": "الساعات التدريبية",
        "courses": "كورس محاكاة",
        "ratio": "نسبة التشغيل",
        "manikins": "إجمالي الدمى",
        "working": "تعمل",
        "maintenance": "تحت الصيانة",
        "apply_vacation": "طلب إجازة",
        "recommendations": "توصيات التطوير"
    },
    "English": {
        "dir": "ltr",
        "title": "Simulation Center Management",
        "dash": "Dashboard",
        "emp_page": "Employee Page",
        "admin": "Management",
        "trainers": "Present Trainers",
        "operators": "Present Operators",
        "total_trainers": "Total Trainers",
        "total_operators": "Total Operators",
        "hours": "Training Hours",
        "courses": "Sim Courses",
        "ratio": "Operation Ratio",
        "manikins": "Total Manikins",
        "working": "Working",
        "maintenance": "Maintenance",
        "apply_vacation": "Apply for Vacation",
        "recommendations": "Development Recommendations"
    }
}

# 2. اختيار اللغة
st.sidebar.title("Language / اللغة")
lang_choice = st.sidebar.selectbox("", ["العربية", "English"])
lang = languages[lang_choice]

# 3. إعدادات الصفحة والتنسيق بناءً على اللغة المختارة
st.set_page_config(page_title=lang["title"], layout="wide")

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] {{
        font-family: 'Cairo', sans-serif;
        direction: {lang['dir']};
        text-align: {"right" if lang['dir'] == "rtl" else "left"};
    }}
    </style>
    """, unsafe_allow_html=True)

# 4. القائمة الجانبية
menu = [lang["dash"], lang["emp_page"], lang["admin"]]
choice = st.sidebar.radio(lang["title"], menu)

if choice == lang["dash"]:
    st.header(f"📊 {lang['dash']}")
    
    # شبكة البيانات (Metrics Grid)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(lang["trainers"], "8")
    col2.metric(lang["operators"], "5")
    col3.metric(lang["total_trainers"], "15")
    col4.metric(lang["total_operators"], "10")

    st.divider()
    
    col5, col6, col7 = st.columns(3)
    col5.metric(lang["hours"], "850 / 1200")
    col6.metric(lang["courses"], "24")
    col7.metric(lang["ratio"], "70.8%")

    st.divider()
    
    st.subheader(f"🤖 {lang['manikins']}")
    c1, c2, c3 = st.columns(3)
    c1.metric(lang["manikins"], "40")
    c2.metric(lang["working"], "32")
    c3.metric(lang["maintenance"], "8")

# ... باقي الصفحات تتبع نفس النمط باستخدام متغير lang ...
