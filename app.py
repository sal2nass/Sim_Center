import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import calendar

# --- 1. الإعدادات الجمالية (ألوان SIMWorld) ---
st.set_page_config(page_title="SimCenter Pro OS", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background-color: #fcfcfc; }
    /* ستايل التقويم الشهري */
    .calendar-table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; }
    .calendar-table th { background: #f8f9fa; padding: 15px; border: 1px solid #eee; text-align: center; color: #333; }
    .calendar-table td { width: 14%; height: 120px; vertical-align: top; padding: 10px; border: 1px solid #eee; transition: 0.3s; }
    .calendar-table td:hover { background: #f0f7ff; }
    .day-num { font-weight: bold; color: #999; margin-bottom: 5px; display: block; }
    .session-card { background: #fff4e5; border-right: 4px solid #ffa000; padding: 4px 8px; border-radius: 4px; font-size: 11px; margin-bottom: 4px; color: #856404; cursor: pointer; }
    .absent-card { background: #fee2e2; border-right: 4px solid #ef4444; padding: 4px 8px; border-radius: 4px; font-size: 11px; color: #991b1b; }
    /* المربعات العلوية */
    .metric-container { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); text-align: center; border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة البيانات ---
if 'leave_requests' not in st.session_state: st.session_state.leave_requests = []
if 'staff_schedules' not in st.session_state:
    st.session_state.staff_schedules = pd.DataFrame(columns=["الموظف", "التاريخ", "المهمة", "المنسق", "المدرب", "الساعات", "الإدارة"])
if 'external_requests' not in st.session_state: st.session_state.external_requests = []

# --- 3. نظام الصلاحيات ---
USERS = {
    "sal2nass@gmail.com": {"name": "المدير العام", "role": "owner"},
    "sal4nass@gmail.com": {"name": "المنسق", "role": "coordinator"},
    "sal_saleh@hotmail.com": {"name": "صالح (موظف)", "role": "employee"}
}

if 'authenticated' not in st.session_state: st.session_state.authenticated = False

# --- 4. الدخول ---
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>🔐 تسجيل الدخول</h1>", unsafe_allow_html=True)
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
    
    # القائمة الجانبية
    with st.sidebar:
        st.write(f"### 👤 {user['name']}")
        st.divider()
        if role == "owner": menu = ["لوحة المؤشرات", "التقويم الشهري", "الاعتمادات النهائية", "الطلبات الخارجية", "التقارير"]
        elif role == "coordinator": menu = ["لوحة المؤشرات", "الالتقويم الشهري", "مراجعة الإجازات", "رفع جداول الإكسل"]
        else: menu = ["تقويمي الشخصي", "تقديم طلب إجازة"]
        choice = st.radio("القائمة الرئيسية", menu)
        
        st.divider()
        st.write("🗓️ **تصفية الفترة (للداشبورد)**")
        d_start = st.date_input("من تاريخ", datetime(2026, 2, 1))
        d_end = st.date_input("إلى تاريخ", datetime(2026, 3, 1))
        
        if st.button("تسجيل الخروج"):
            st.session_state.authenticated = False
            st.rerun()

    # --- 5. الصفحات ---

    # أ. لوحة المؤشرات (المقاييس التي طلبتها)
    if choice == "لوحة المؤشرات":
        st.header("📊 لوحة المؤشرات الإجمالية")
        df_view = st.session_state.staff_schedules.copy()
        if not df_view.empty:
            df_view['التاريخ'] = pd.to_datetime(df_view['التاريخ']).dt.date
            df_view = df_view[(df_view['التاريخ'] >= d_start) & (df_view['التاريخ'] <= d_end)]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("إجمالي الساعات", f"{df_view['الساعات'].sum() if not df_view.empty else 0} س")
        c2.metric("إجمالي السيشنات", len(df_view))
        c3.metric("طلبات الإجازة", len([r for r in st.session_state.leave_requests if r['الحالة'] == 'معتمد نهائياً']))
        c4.metric("الطلبات الخارجية", len(st.session_state.external_requests))

        st.divider()
        if not df_view.empty:
            fig = px.bar(df_view, x="الموظف", y="الساعات", color="الإدارة", title="تحليل الساعات حسب الإدارة والموظف")
            st.plotly_chart(fig, use_container_width=True)

    # ب. التقويم الشهري (مثل SIMWorld)
    elif "تقويم" in choice:
        st.header(f"📅 التقويم الشهري - فبراير 2026")
        
        # إنشاء مصفوفة الشهر
        cal = calendar.monthcalendar(2026, 2)
        days = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
        
        # بناء جدول HTML للتقويم
        html = "<table class='calendar-table'><thead><tr>"
        for d in days: html += f"<th>{d}</th>"
        html += "</tr></thead><tbody>"

        for week in cal:
            html += "<tr>"
            for day in week:
                if day == 0:
                    html += "<td></td>"
                else:
                    date_obj = datetime(2026, 2, day).date()
                    date_str = str(date_obj)
                    
                    cell_content = f"<span class='day-num'>{day}</span>"
                    
                    # 1. جلب السيشنات
                    day_tasks = st.session_state.staff_schedules[st.session_state.staff_schedules['التاريخ'].astype(str) == date_str]
                    if role == "employee": day_tasks = day_tasks[day_tasks['الموظف'] == user['name']]
                    
                    for _, row in day_tasks.iterrows():
                        cell_content += f"<div class='session-card' title='المدرب: {row['المدرب']}'>📖 {row['المهمة']}</div>"
                    
                    # 2. جلب الغائبين (للمدير والمنسق)
                    if role != "employee":
                        absents = [r['الموظف'] for r in st.session_state.leave_requests 
                                   if r['الحالة'] == 'معتمد نهائياً' and r['من'] <= date_obj <= r['إلى']]
                        for a in absents:
                            cell_content += f<div class='absent-card'>🚫 {a}</div>"
                    
                    html += f"<td>{cell_content}</td>"
            html += "</tr>"
        html += "</tbody></table>"
        st.markdown(html, unsafe_allow_html=True)

    # ج. رفع جداول الإكسل (للمنسق فقط)
    elif choice == "رفع جداول الإكسل":
        st.header("📤 رفع بيانات السيشنات")
        up = st.file_uploader("اختر ملف الإكسل", type=["xlsx"])
        if up:
            try:
                df = pd.read_excel(up)
                df['التاريخ'] = pd.to_datetime(df['التاريخ']).dt.date
                st.session_state.staff_schedules = df
                st.success("تم التحديث! اذهب للتقويم لمشاهدة النتائج")
            except Exception as e:
                st.error("تأكد من وجود الأعمدة: [الموظف، التاريخ، المهمة، المنسق، المدرب، الساعات، الإدارة]")

    # د. الاعتمادات النهائية (المدير)
    elif choice == "الاعتمادات النهائية":
        st.header("⚖️ اعتماد الإجازات")
        to_approve = [r for r in st.session_state.leave_requests if r['الحالة'] == 'موافق عليه من المنسق']
        if to_approve:
            st.table(pd.DataFrame(to_approve))
            emp_name = st.selectbox("اعتماد إجازة الموظف:", [r['الموظف'] for r in to_approve])
            if st.button("اعتماد نهائي"):
                for r in st.session_state.leave_requests:
                    if r['الموظف'] == emp_name and r['الحالة'] == 'موافق عليه من المنسق':
                        r['الحالة'] = 'معتمد نهائياً'
                st.rerun()
        else: st.info("لا توجد طلبات معتمدة من المنسقين حالياً")

    # هـ. الطلبات الخارجية
    elif choice == "الالطلبات الخارجية":
        st.header("🌐 الطلبات الخارجية")
        if st.session_state.external_requests:
            st.dataframe(pd.DataFrame(st.session_state.external_requests), use_container_width=True)
        with st.expander("إضافة طلب جديد"):
            col_ex1, col_ex2 = st.columns(2)
            t = col_ex1.selectbox("النوع", ["دورة", "ورشة", "اجتماع"])
            d = col_ex2.text_input("الإدارة الطالبة")
            dt = st.date_input("التاريخ")
            if st.button("حفظ"):
                st.session_state.external_requests.append({"نوع الملف": t, "الإدارة": d, "التاريخ": str(dt), "الحالة": "جديد"})
                st.rerun()

    # و. تقديم إجازة (الموظف)
    elif choice == "تقديم طلب إجازة":
        with st.form("l_form"):
            s = st.date_input("من")
            e = st.date_input("إلى")
            if st.form_submit_button("إرسال للمنسق"):
                st.session_state.leave_requests.append({"الموظف": user['name'], "من": s, "إلى": e, "الحالة": "قيد الانتظار"})
                st.success("تم الإرسال")

    # ز. مراجعة الإجازات (المنسق)
    elif choice == "مراجعة الإجازات":
        pending = [r for r in st.session_state.leave_requests if r['الحالة'] == 'قيد الانتظار']
        if pending:
            st.table(pd.DataFrame(pending))
            target = st.selectbox("مراجعة طلب:", [r['الموظف'] for r in pending])
            if st.button("موافقة مبدئية"):
                for r in st.session_state.leave_requests:
                    if r['الموظف'] == target and r['الحالة'] == 'قيد الانتظار':
                        r['الحالة'] = 'موافق عليه من المنسق'
                st.rerun()
