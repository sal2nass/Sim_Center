import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة والستايل ---
st.set_page_config(page_title="SimCenter Pro OS v2", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background-color: #f4f7f9; }
    .calendar-day { border: 1px solid #dee2e6; border-radius: 12px; padding: 10px; min-height: 140px; background: white; }
    .absent-item { background: #fee2e2; color: #991b1b; padding: 4px; border-radius: 4px; margin-top: 4px; font-size: 11px; border-right: 4px solid #ef4444; }
    .session-item { background: #e7f3ff; color: #0061c1; padding: 4px; border-radius: 4px; margin-top: 4px; font-size: 11px; border-right: 4px solid #007bff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. تهيئة البيانات ---
if 'leave_requests' not in st.session_state: st.session_state.leave_requests = []
if 'staff_schedules' not in st.session_state:
    st.session_state.staff_schedules = pd.DataFrame(columns=["الموظف", "التاريخ", "المهمة", "المنسق", "المدرب", "الساعات", "الإدارة"])
if 'external_requests' not in st.session_state: st.session_state.external_requests = []

# --- 3. المستخدمين ---
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
        if st.button("دخول", use_container_width=True):
            if email_in in USERS:
                st.session_state.authenticated = True
                st.session_state.user = USERS[email_in]
                st.rerun()
            else: st.error("المستخدم غير مسجل")
else:
    user = st.session_state.user
    role = user['role']
    st.sidebar.markdown(f"### 👤 {user['name']}")
    
    if role == "owner": menu = ["لوحة المؤشرات", "تقويم الفعاليات", "الاعتمادات النهائية", "الطلبات الخارجية", "التقارير"]
    elif role == "coordinator": menu = ["لوحة المؤشرات", "تقويم الفعاليات", "مراجعة الإجازات", "رفع جداول الإكسل"]
    else: menu = ["تقويمي الشخصي", "تقديم طلب إجازة"]
    
    choice = st.sidebar.radio("القائمة", menu)

    # --- 5. منطق الصفحات ---

    # أ. لوحة المؤشرات (مع ميزة الفلترة التاريخية)
    if choice == "لوحة المؤشرات":
        st.header("📊 تحليلات الأداء")
        
        # فلتر التاريخ في الأعلى
        st.markdown("##### 🗓️ تصفية البيانات حسب الفترة الزمنية")
        c_f1, c_f2 = st.columns(2)
        start_f = c_f1.date_input("من تاريخ", datetime.now().date() - timedelta(days=30))
        end_f = c_f2.date_input("إلى تاريخ", datetime.now().date() + timedelta(days=30))

        # تصفية البيانات
        df_filtered = st.session_state.staff_schedules.copy()
        if not df_filtered.empty:
            df_filtered['التاريخ'] = pd.to_datetime(df_filtered['التاريخ']).dt.date
            mask = (df_filtered['التاريخ'] >= start_f) & (df_filtered['التاريخ'] <= end_f)
            df_filtered = df_filtered.loc[mask]

        # العدادات
        m1, m2, m3 = st.columns(3)
        total_hours = df_filtered['الساعات'].sum() if not df_filtered.empty else 0
        total_sessions = len(df_filtered)
        m1.metric("الساعات في الفترة المختارة", f"{total_hours} ساعة")
        m2.metric("عدد السيشنات", total_sessions)
        m3.metric("معدل الإنجاز", f"{min(100, int(total_hours/10))}%")

        st.divider()
        if not df_filtered.empty:
            fig = px.bar(df_filtered, x="الموظف", y="الساعات", color="المهمة", title="توزيع الساعات خلال الفترة")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("لا توجد بيانات سيشنات في هذه الفترة.")

    # ب. التقويم (العام والشخصي)
    elif "تقويم" in choice:
        st.header(f"📅 {choice}")
        # عرض تقويم فبراير 2026 كمثال
        start_cal = datetime(2026, 2, 1)
        for week in range(4):
            cols = st.columns(7)
            for d in range(7):
                curr = start_cal + timedelta(days=week*7 + d)
                with cols[d]:
                    st.markdown(f"<div class='calendar-day'><b>{curr.day}</b>", unsafe_allow_html=True)
                    # غيابات
                    absents = [r['الموظف'] for r in st.session_state.leave_requests if r['الحالة'] == 'معتمد نهائياً' and r['من'] <= curr.date() <= r['إلى']]
                    for a in absents: st.markdown(f"<div class='absent-item'>🚫 {a}</div>", unsafe_allow_html=True)
                    # سيشنات
                    day_tasks = st.session_state.staff_schedules[st.session_state.staff_schedules['التاريخ'].astype(str) == str(curr.date())]
                    if role == "employee": day_tasks = day_tasks[day_tasks['الموظف'] == user['name']]
                    for _, row in day_tasks.iterrows():
                        if st.button(f"📖 {row['المهمة']}", key=f"t_{curr.day}_{row['المهمة']}"):
                            st.info(f"المنسق: {row['المنسق']} | المدرب: {row['المدرب']}")
                    st.markdown("</div>", unsafe_allow_html=True)

    # ج. مراجعة الإجازات (المنسق)
    elif choice == "مراجعة الإجازات":
        st.header("🔍 مراجعة المنسق")
        pending = [r for r in st.session_state.leave_requests if r['الحالة'] == 'قيد الانتظار']
        if pending:
            st.table(pd.DataFrame(pending))
            idx = st.number_input("رقم الطلب للموافقة المبدئية", 0, len(st.session_state.leave_requests)-1)
            if st.button("موافقة (إرسال للمدير)"):
                st.session_state.leave_requests[idx]['الحالة'] = 'موافق عليه من المنسق'
                st.success("تم التحويل للمدير")
        else: st.info("لا توجد طلبات معلقة")

    # د. الاعتمادات النهائية (المدير فقط)
    elif choice == "الاعتمادات النهائية":
        st.header("⚖️ الاعتمادات النهائية")
        to_approve = [r for r in st.session_state.leave_requests if r['الحالة'] == 'موافق عليه من المنسق']
        if to_approve:
            st.table(pd.DataFrame(to_approve))
            idx = st.number_input("رقم الطلب للاعتماد النهائي", 0, len(st.session_state.leave_requests)-1)
            if st.button("🚀 اعتماد نهائي"):
                st.session_state.leave_requests[idx]['الحالة'] = 'معتمد نهائياً'
                st.balloons()
        else: st.info("لا توجد طلبات بانتظار قرارك")

    # هـ. الطلبات الخارجية (تعديل الهيكل)
    elif choice == "الطلبات الخارجية":
        st.header("🌐 الطلبات الخارجية")
        if st.session_state.external_requests:
            st.dataframe(pd.DataFrame(st.session_state.external_requests), use_container_width=True)
        
        with st.expander("إضافة طلب خارجي جديد"):
            col_e1, col_e2 = st.columns(2)
            e_type = col_e1.selectbox("نوع الملف", ["دورة تدريبية", "ورشة عمل", "زيارة ميدانية"])
            e_dept = col_e2.text_input("الإدارة الطالبة")
            e_date = st.date_input("التاريخ")
            if st.button("حفظ الطلب"):
                st.session_state.external_requests.append({
                    "نوع الملف": e_type, "الإدارة": e_dept, "التاريخ": str(e_date), "الحالة": "جديد"
                })
                st.rerun()

    # و. التقارير
    elif choice == "التقارير":
        st.header("📈 استخراج التقارير")
        st.write("استخدم الفلاتر في لوحة المؤشرات لتحديد البيانات المراد تصديرها.")
        if not st.session_state.staff_schedules.empty:
            st.download_button("تحميل كافة السيشنات (CSV)", st.session_state.staff_schedules.to_csv(index=False), "Full_Report.csv")
            st.dataframe(st.session_state.staff_schedules)
        else: st.warning("لا توجد بيانات")

    # ز. تقديم إجازة (الموظف)
    elif choice == "تقديم طلب إجازة":
        with st.form("l_form"):
            s_d = st.date_input("من")
            e_d = st.date_input("إلى")
            if st.form_submit_button("إرسال"):
                st.session_state.leave_requests.append({"الموظف": user['name'], "من": s_d, "إلى": e_d, "الحالة": "قيد الانتظار"})
                st.success("تم الإرسال للمنسق")

    if st.sidebar.button("خروج"):
        st.session_state.authenticated = False
        st.rerun()
