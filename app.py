import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة والتصميم ---
st.set_page_config(page_title="SimCenter Pro OS", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .calendar-card { background: #fdfdfd; border: 1px solid #ddd; padding: 10px; border-radius: 5px; margin-bottom: 5px; }
    .absent-label { color: #d9534f; font-weight: bold; }
    .session-label { color: #0275d8; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة البيانات الدائمة ---
if 'leave_requests' not in st.session_state:
    st.session_state.leave_requests = []
if 'external_requests' not in st.session_state:
    st.session_state.external_requests = []
if 'staff_schedules' not in st.session_state:
    # هيكل الجدول: [الموظف، التاريخ، المهمة، الساعات]
    st.session_state.staff_schedules = pd.DataFrame(columns=["الموظف", "التاريخ", "المهمة", "الساعات"])

# --- 3. نظام المستخدمين ---
USERS = {
    "sal2nass@gmail.com": {"name": "المدير العام", "role": "owner"},
    "sal4nass@gmail.com": {"name": "المنسق", "role": "coordinator"},
    "sal_saleh@hotmail.com": {"name": "صالح (موظف)", "role": "employee"}
}

if 'authenticated' not in st.session_state: st.session_state.authenticated = False

# --- 4. تسجيل الدخول ---
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.title("🛡️ SimCenter OS")
        email_in = st.text_input("البريد الإلكتروني").lower().strip()
        if st.button("دخول"):
            if email_in in USERS:
                st.session_state.authenticated = True
                st.session_state.user = USERS[email_in]
                st.rerun()
            else: st.error("المستخدم غير موجود")
else:
    user = st.session_state.user
    role = user['role']
    st.sidebar.subheader(f"👤 {user['name']}")

    # القوائم
    if role == "owner":
        menu = ["لوحة المؤشرات", "التقويم العام", "الاعتمادات النهائية", "الطلبات الخارجية", "التقارير"]
    elif role == "coordinator":
        menu = ["لوحة المؤشرات", "التقويم العام", "مراجعة الإجازات", "رفع جداول الإكسل"]
    else:
        menu = ["ملفي الشخصي", "تقويمي الشخصي", "تقديم طلب إجازة"]
    
    choice = st.sidebar.radio("القائمة", menu)

    # --- 5. منطق الصفحات ---

    # أ. لوحة المؤشرات
    if choice == "لوحة المؤشرات":
        st.header("📊 لوحة المؤشرات الإجمالية")
        m1, m2, m3 = st.columns(3)
        absent_today = [r['الموظف'] for r in st.session_state.leave_requests 
                        if r['الحالة'] == 'معتمد نهائياً' and r['من'] <= datetime.now().date() <= r['إلى']]
        m1.metric("المدربين المتواجدين", 15 - len(absent_today))
        m2.metric("إجمالي الساعات التشغيلية", f"{st.session_state.staff_schedules['الساعات'].sum()} ساعة")
        m3.metric("السيشنات المجدولة", len(st.session_state.staff_schedules))

    # ب. التقويم (العام للمدير والمنسق / الشخصي للموظف)
    elif choice in ["التقويم العام", "تقويمي الشخصي"]:
        st.header(f"📅 {choice}")
        
        # اختيار الشهر (افتراضياً الشهر الحالي)
        today = datetime.now()
        month_days = [today.replace(day=1) + timedelta(days=i) for i in range(30)]
        
        for day in month_days:
            date_str = day.strftime('%Y-%m-%d')
            with st.expander(f"📅 تاريخ: {day.strftime('%A %d/%m/%Y')}"):
                
                # 1. عرض الغيابات (للمدير والمنسق فقط)
                if role != "employee":
                    absents = [r['الموظف'] for r in st.session_state.leave_requests 
                               if r['الحالة'] == 'معتمد نهائياً' and r['من'] <= day.date() <= r['إلى']]
                    if absents:
                        st.markdown(f"🚫 **غير متواجدين:** {', '.join(absents)}", unsafe_allow_html=True)
                
                # 2. عرض الحصص (السيشنات) من الإكسل
                # تصفية الجدول بناءً على الموظف إذا كان هو المستخدم
                sched = st.session_state.staff_schedules
                if role == "employee":
                    day_tasks = sched[(sched['الموظف'] == user['name']) & (sched['التاريخ'].astype(str) == date_str)]
                else:
                    day_tasks = sched[sched['التاريخ'].astype(str) == date_str]
                
                if not day_tasks.empty:
                    st.write("📖 الحصص المجدولة:")
                    st.dataframe(day_tasks[["الموظف", "المهمة", "الساعات"]], hide_index=True)
                else:
                    st.caption("لا توجد حصص مجدولة")

    # ج. مراجعة الإجازات (المنسق)
    elif choice == "مراجعة الإجازات":
        st.header("🔍 مراجعة المنسق")
        pending = [r for r in st.session_state.leave_requests if r['الحالة'] == 'قيد الانتظار']
        if pending:
            df_p = pd.DataFrame(pending)
            st.table(df_p)
            req_idx = st.selectbox("اختر رقم الطلب للموافقة المبدئية", range(len(st.session_state.leave_requests)))
            if st.button("تحويل للمدير العام"):
                st.session_state.leave_requests[req_idx]['الحالة'] = 'موافق عليه من المنسق'
                st.rerun()
        else: st.info("لا توجد طلبات جديدة")

    # د. الاعتمادات النهائية (المدير)
    elif choice == "الاعتمادات النهائية":
        st.header("⚖️ قرار المدير العام")
        to_approve = [r for r in st.session_state.leave_requests if r['الحالة'] == 'موافق عليه من المنسق']
        if to_approve:
            st.table(pd.DataFrame(to_approve))
            req_idx = st.selectbox("اعتماد الطلب رقم", range(len(st.session_state.leave_requests)))
            if st.button("🚀 اعتماد نهائي (سيظهر في التقويم كغياب)"):
                st.session_state.leave_requests[req_idx]['الحالة'] = 'معتمد نهائياً'
                st.success("تم الاعتماد وتحديث التقويم")
                st.rerun()
        else: st.info("لا توجد طلبات تنتظر الاعتماد")

    # هـ. رفع جداول الإكسل (المنسق)
    elif choice == "رفع جداول الإكسل":
        st.header("📤 رفع السيشنات الأسبوعية")
        st.info("يجب أن يحتوي الإكسل على الأعمدة: [الموظف، التاريخ، المهمة، الساعات]")
        up = st.file_uploader("Upload Excel", type=["xlsx"])
        if up:
            try:
                df_up = pd.read_excel(up)
                df_up['التاريخ'] = pd.to_datetime(df_up['التاريخ']).dt.date
                st.session_state.staff_schedules = df_up
                st.success("تم تحديث الجدول بنجاح!")
                st.dataframe(df_up)
            except:
                st.error("تأكد من مطابقة أسماء الأعمدة في ملف الإكسل")

    # و. تقديم طلب إجازة (الموظف)
    elif choice == "تقديم طلب إجازة":
        st.header("📝 طلب إجازة")
        with st.form("l_form"):
            s_d = st.date_input("البداية")
            e_d = st.date_input("النهاية")
            rea = st.text_area("السبب")
            if st.form_submit_button("إرسال"):
                st.session_state.leave_requests.append({
                    "الموظف": user['name'], "من": s_d, "إلى": e_d, "السبب": rea, "الحالة": "قيد الانتظار"
                })
                st.success("تم الإرسال للمنسق")

    if st.sidebar.button("خروج"):
        st.session_state.authenticated = False
        st.rerun()
