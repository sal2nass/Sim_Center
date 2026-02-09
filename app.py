import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import calendar

# --- 1. الإعدادات البصرية (ستايل SIMWorld) ---
st.set_page_config(page_title="SimCenter Pro OS", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background-color: #ffffff; }
    
    /* تصميم التقويم الشهري */
    .cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; background-color: #e2e8f0; border: 1px solid #e2e8f0; }
    .cal-head { background-color: #f8fafc; padding: 10px; text-align: center; font-weight: bold; color: #475569; border: 1px solid #e2e8f0; }
    .cal-day { background-color: white; min-height: 120px; padding: 8px; border: 1px solid #e2e8f0; position: relative; }
    .cal-day:hover { background-color: #f1f5f9; }
    .day-number { font-size: 14px; font-weight: 700; color: #94a3b8; margin-bottom: 8px; display: block; }
    
    /* بطاقات المهام والإجازات */
    .task-card { background-color: #dbeafe; color: #1e40af; padding: 4px 8px; border-radius: 4px; font-size: 11px; margin-bottom: 4px; border-right: 4px solid #3b82f6; font-weight: 600; }
    .leave-card { background-color: #fee2e2; color: #991b1b; padding: 4px 8px; border-radius: 4px; font-size: 11px; margin-bottom: 4px; border-right: 4px solid #ef4444; font-weight: 600; }
    
    /* إحصائيات الداشبورد */
    .kpi-card { background: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة مخزن البيانات ---
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

# --- 4. تسجيل الدخول ---
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<h2 style='text-align:center;'>SimCenter Pro OS</h2>", unsafe_allow_html=True)
        email = st.text_input("البريد الإلكتروني").lower().strip()
        if st.button("تسجيل الدخول", use_container_width=True):
            if email in USERS:
                st.session_state.authenticated = True
                st.session_state.user = USERS[email]
                st.rerun()
            else: st.error("عذراً، البريد غير مسجل")
else:
    user = st.session_state.user
    role = user['role']

    # --- القائمة الجانبية ---
    with st.sidebar:
        st.markdown(f"### مرحباً، {user['name']}")
        st.info(f"صلاحية: {role}")
        st.divider()
        
        if role == "owner":
            menu = ["لوحة المؤشرات", "تقويم الفعاليات", "الاعتمادات النهائية", "الطلبات الخارجية", "التقارير"]
        elif role == "coordinator":
            menu = ["لوحة المؤشرات", "تقويم الفعاليات", "مراجعة الإجازات", "رفع جداول الإكسل"]
        else:
            menu = ["تقويمي الشخصي", "تقديم طلب إجازة"]
        
        choice = st.radio("القائمة الرئيسية", menu)
        
        st.divider()
        st.write("🗓️ فلتر الفترة (للمؤشرات)")
        d1 = st.date_input("من", datetime(2026, 2, 1))
        d2 = st.date_input("إلى", datetime(2026, 3, 31))
        
        if st.button("تسجيل الخروج"):
            st.session_state.authenticated = False
            st.rerun()

    # --- 5. منطق الصفحات ---

    if choice == "لوحة المؤشرات":
        st.header("📊 لوحة المؤشرات الإجمالية")
        df = st.session_state.staff_schedules.copy()
        if not df.empty:
            df['التاريخ'] = pd.to_datetime(df['التاريخ']).dt.date
            df = df[(df['التاريخ'] >= d1) & (df['التاريخ'] <= d2)]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("إجمالي الساعات", f"{df['الساعات'].sum() if not df.empty else 0} س")
        c2.metric("عدد الفعاليات", len(df))
        c3.metric("إجازات معتمدة", len([r for r in st.session_state.leave_requests if r['الحالة'] == 'معتمد نهائياً']))
        c4.metric("طلبات خارجية", len(st.session_state.external_requests))

        if not df.empty:
            st.divider()
            fig = px.bar(df, x="الموظف", y="الساعات", color="الإدارة", barmode="group", title="توزيع مجهود الموظفين")
            st.plotly_chart(fig, use_container_width=True)

    elif "تقويم" in choice:
        st.header(f"📅 تقويم شهر فبراير 2026")
        
        # أيام الأسبوع
        days_header = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
        cols = st.columns(7)
        for i, day_name in enumerate(days_header):
            cols[i].markdown(f"<div class='cal-head'>{day_name}</div>", unsafe_allow_html=True)
        
        # مصفوفة الشهر
        cal = calendar.monthcalendar(2026, 2)
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                with cols[i]:
                    if day == 0:
                        st.markdown("<div class='cal-day' style='background:#f9fafb;'></div>", unsafe_allow_html=True)
                    else:
                        current_date = datetime(2026, 2, day).date()
                        date_str = str(current_date)
                        
                        # تجميع المحتوى للخلية
                        tasks_html = ""
                        # 1. المهام
                        day_tasks = st.session_state.staff_schedules[st.session_state.staff_schedules['التاريخ'].astype(str) == date_str]
                        if role == "employee": day_tasks = day_tasks[day_tasks['الموظف'] == user['name']]
                        for _, row in day_tasks.iterrows():
                            tasks_html += f"<div class='task-card'>WORK: {row['المهمة']}</div>"
                        
                        # 2. الإجازات
                        if role != "employee":
                            absents = [r['الموظف'] for r in st.session_state.leave_requests 
                                       if r['الحالة'] == 'معتمد نهائياً' and r['من'] <= current_date <= r['إلى']]
                            for a in absents:
                                tasks_html += f"<div class='leave-card'>OFF: {a}</div>"
                        
                        st.markdown(f"""
                            <div class='cal-day'>
                                <span class='day-number'>{day}</span>
                                {tasks_html}
                            </div>
                        """, unsafe_allow_html=True)

    elif choice == "رفع جداول الإكسل":
        st.header("📤 رفع السيشنات الأسبوعية")
        uploaded_file = st.file_uploader("اختر ملف الإكسل (XLSX)", type="xlsx")
        if uploaded_file:
            try:
                new_df = pd.read_excel(uploaded_file)
                new_df['التاريخ'] = pd.to_datetime(new_df['التاريخ']).dt.date
                st.session_state.staff_schedules = new_df
                st.success("تم تحديث البيانات! اذهب للتقويم للمعاينة.")
            except Exception as e:
                st.error(f"خطأ في الملف: تأكد من تطابق الأعمدة المطلوبة.")

    elif choice == "تقديم طلب إجازة":
        st.header("📝 طلب إجازة")
        with st.form("leave_f"):
            s_date = st.date_input("بداية الإجازة")
            e_date = st.date_input("نهاية الإجازة")
            note = st.text_area("السبب")
            if st.form_submit_button("إرسال للمنسق"):
                st.session_state.leave_requests.append({
                    "الموظف": user['name'], "من": s_date, "إلى": e_date, "السبب": note, "الحالة": "قيد الانتظار"
                })
                st.success("تم الإرسال بنجاح")

    elif choice == "الاعتمادات النهائية":
        st.header("⚖️ اعتماد الإجازات النهائية")
        to_approve = [r for r in st.session_state.leave_requests if r['الحالة'] == 'موافق عليه من المنسق']
        if to_approve:
            st.table(pd.DataFrame(to_approve))
            emp = st.selectbox("اختر الموظف للاعتماد", [r['الموظف'] for r in to_approve])
            if st.button("اعتماد نهائي"):
                for r in st.session_state.leave_requests:
                    if r['الموظف'] == emp and r['الحالة'] == 'موافق عليه من المنسق':
                        r['الحالة'] = 'معتمد نهائياً'
                st.rerun()
        else: st.info("لا توجد طلبات معلقة من المنسقين")

    elif choice == "الطلبات الخارجية":
        st.header("🌐 الطلبات الخارجية")
        if st.session_state.external_requests:
            st.dataframe(pd.DataFrame(st.session_state.external_requests), use_container_width=True)
        with st.expander("إضافة طلب جديد"):
            col_a, col_b = st.columns(2)
            tp = col_a.selectbox("نوع الملف", ["ورشة", "دورة", "زيارة"])
            dp = col_b.text_input("الإدارة")
            dt = st.date_input("التاريخ المتوقع")
            if st.button("إضافة"):
                st.session_state.external_requests.append({"النوع": tp, "الإدارة": dp, "التاريخ": str(dt), "الحالة": "جديد"})
                st.rerun()
