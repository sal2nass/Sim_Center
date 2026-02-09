import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة والستايل (CSS) ---
st.set_page_config(page_title="SimCenter Pro OS", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background-color: #f8f9fa; }
    .calendar-day { border: 1px solid #dee2e6; border-radius: 12px; padding: 10px; min-height: 150px; background: white; transition: all 0.3s; }
    .calendar-day:hover { transform: translateY(-5px); box-shadow: 0 6px 12px rgba(0,0,0,0.1); }
    .session-item { background: #e7f3ff; color: #0061c1; padding: 5px 8px; border-radius: 6px; margin-top: 6px; font-size: 12px; border-right: 5px solid #007bff; cursor: pointer; }
    .absent-item { background: #fee2e2; color: #991b1b; padding: 5px 8px; border-radius: 6px; margin-top: 6px; font-size: 12px; border-right: 5px solid #ef4444; font-weight: bold; }
    .current-day { border: 2px solid #007bff !important; background: #f0f7ff; }
    .metric-card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. تهيئة مخزن البيانات (Session State) ---
if 'leave_requests' not in st.session_state:
    st.session_state.leave_requests = []
if 'staff_schedules' not in st.session_state:
    st.session_state.staff_schedules = pd.DataFrame(columns=["الموظف", "التاريخ", "المهمة", "المنسق", "المدرب", "الساعات"])
if 'external_requests' not in st.session_state:
    st.session_state.external_requests = []

# --- 3. نظام إدارة المستخدمين ---
USERS = {
    "sal2nass@gmail.com": {"name": "المدير العام", "role": "owner"},
    "sal4nass@gmail.com": {"name": "المنسق", "role": "coordinator"},
    "sal_saleh@hotmail.com": {"name": "صالح (موظف)", "role": "employee"}
}

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# --- 4. منطق تسجيل الدخول ---
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🛡️ نظام إدارة المركز")
        st.subheader("SimCenter Operation System")
        email_in = st.text_input("البريد الإلكتروني").lower().strip()
        if st.button("تسجيل الدخول", use_container_width=True):
            if email_in in USERS:
                st.session_state.authenticated = True
                st.session_state.user = USERS[email_in]
                st.rerun()
            else:
                st.error("عذراً، هذا البريد غير مسجل لدينا.")
else:
    user = st.session_state.user
    role = user['role']
    
    # القائمة الجانبية
    with st.sidebar:
        st.markdown(f"### 👤 {user['name']}")
        st.info(f"الصلاحية: {role}")
        st.divider()
        
        if role == "owner":
            menu = ["لوحة المؤشرات", "تقويم الفعاليات", "الاعتمادات النهائية", "الطلبات الخارجية", "التقارير"]
        elif role == "coordinator":
            menu = ["لوحة المؤشرات", "تقويم الفعاليات", "مراجعة الإجازات", "رفع جداول الإكسل"]
        else:
            menu = ["تقويمي الشخصي", "تقديم طلب إجازة"]
            
        choice = st.sidebar.radio("الانتقال إلى:", menu)
        st.divider()
        if st.button("تسجيل الخروج"):
            st.session_state.authenticated = False
            st.rerun()

    # --- 5. منطق الصفحات ---

    # أ. لوحة المؤشرات
    if choice == "لوحة المؤشرات":
        st.header("📊 حالة المركز اليوم")
        m1, m2, m3 = st.columns(3)
        
        today_str = datetime.now().date()
        absent_today = [r['الموظف'] for r in st.session_state.leave_requests 
                        if r['الحالة'] == 'معتمد نهائياً' and r['من'] <= today_str <= r['إلى']]
        
        m1.metric("المدربين المتواجدين", 15 - len(absent_today))
        m2.metric("إجمالي الساعات المنفذة", f"{st.session_state.staff_schedules['الساعات'].sum()} س")
        m3.metric("طلبات خارجية نشطة", len(st.session_state.external_requests))

    # ب. التقويم (العام والشخصي)
    elif "تقويم" in choice:
        st.header(f"📅 {choice} - فبراير 2026")
        
        # رؤوس أيام الأسبوع
        days_names = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
        cols = st.columns(7)
        for i, d_name in enumerate(days_names):
            cols[i].markdown(f"<div style='text-align:center; font-weight:bold; background:#eee; padding:5px; border-radius:5px;'>{d_name}</div>", unsafe_allow_html=True)

        start_date = datetime(2026, 2, 1)
        for week in range(4):
            week_cols = st.columns(7)
            for d in range(7):
                day_num = week * 7 + d + 1
                curr_date = start_date + timedelta(days=day_num-1)
                date_str = curr_date.strftime('%Y-%m-%d')
                
                with week_cols[d]:
                    is_today = "current-day" if curr_date.date() == datetime.now().date() else ""
                    st.markdown(f"<div class='calendar-day {is_today}'><b>{day_num}</b>", unsafe_allow_html=True)
                    
                    # 1. عرض السيشنات
                    sched = st.session_state.staff_schedules
                    day_tasks = sched[sched['التاريخ'].astype(str) == date_str]
                    if role == "employee": 
                        day_tasks = day_tasks[day_tasks['الموظف'] == user['name']]
                    
                    for _, row in day_tasks.iterrows():
                        if st.button(f"📖 {row['المهمة']}", key=f"btn_{day_num}_{row['المهمة']}"):
                            st.info(f"تفاصيل الحصة: {row['المهمة']}\n\nالمنسق: {row['المنسق']}\nالمدرب: {row['المدرب']}")

                    # 2. عرض الغائبين (للمدير والمنسق فقط)
                    if role != "employee":
                        absents = [r['الموظف'] for r in st.session_state.leave_requests 
                                   if r['الحالة'] == 'معتمد نهائياً' and r['من'] <= curr_date.date() <= r['إلى']]
                        for name in absents:
                            st.markdown(f"<div class='absent-item'>🚫 {name} (إجازة)</div>", unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)

    # ج. مراجعة الإجازات (المنسق)
    elif choice == "مراجعة الإجازات":
        st.header("🔍 طلبات بانتظار موافقة المنسق")
        pending = [r for r in st.session_state.leave_requests if r['الحالة'] == 'قيد الانتظار']
        if pending:
            df_p = pd.DataFrame(pending)
            st.dataframe(df_p, use_container_width=True)
            idx = st.selectbox("اختر رقم الطلب للموافقة المبدئية", range(len(st.session_state.leave_requests)))
            if st.button("موافقة وتحويل للمدير"):
                st.session_state.leave_requests[idx]['الحالة'] = 'موافق عليه من المنسق'
                st.success("تم التحويل")
                st.rerun()
        else:
            st.info("لا توجد طلبات جديدة حالياً.")

    # د. الاعتمادات النهائية (المدير)
    elif choice == "الاعتمادات النهائية":
        st.header("⚖️ قرارات المدير العام")
        to_approve = [r for r in st.session_state.leave_requests if r['الحالة'] == 'موافق عليه من المنسق']
        if to_approve:
            st.write("الطلبات المعتمدة من المنسقين:")
            st.table(pd.DataFrame(to_approve))
            idx = st.selectbox("اعتماد نهائي للطلب رقم", range(len(st.session_state.leave_requests)))
            if st.button("🚀 اعتماد نهائي (تحديث التقويم)"):
                st.session_state.leave_requests[idx]['الحالة'] = 'معتمد نهائياً'
                st.balloons()
                st.rerun()
        else:
            st.info("لا توجد طلبات بانتظار الاعتماد.")

    # هـ. رفع السيشنات (المنسق) مع كاشف التعارض
    elif choice == "رفع جداول الإكسل":
        st.header("📤 رفع السيشنات من Excel")
        st.markdown("""
        **ملاحظة:** يجب أن يحتوي ملف الإكسل على الأعمدة التالية: 
        `الموظف` ، `التاريخ` ، `المهمة` ، `المنسق` ، `المدرب` ، `الساعات`
        """)
        up = st.file_uploader("اختر ملف الإكسل", type=["xlsx"])
        if up:
            try:
                new_data = pd.read_excel(up)
                new_data['التاريخ'] = pd.to_datetime(new_data['التاريخ']).dt.date
                
                # فحص التعارض الذكي
                conflicts = []
                for _, row in new_data.iterrows():
                    is_absent = any(r['الموظف'] == row['الموظف'] and r['من'] <= row['التاريخ'] <= r['إلى'] and r['الحالة'] == 'معتمد نهائياً' 
                                   for r in st.session_state.leave_requests)
                    if is_absent:
                        conflicts.append(f"⚠️ تعارض: الموظف **{row['الموظف']}** لديه إجازة معتمدة يوم **{row['التاريخ']}** ولكن تم إسناد مهمة له!")
                
                if conflicts:
                    for c in conflicts: st.error(c)
                
                st.session_state.staff_schedules = new_data
                st.success("تم رفع البيانات وتحديث التقويم بنجاح!")
            except Exception as e:
                st.error(f"خطأ في قراءة الملف: {e}")

    # و. تقديم إجازة (الموظف)
    elif choice == "تقديم طلب إجازة":
        st.header("📝 تقديم طلب إجازة")
        with st.form("leave_form"):
            d1 = st.date_input("تاريخ البداية")
            d2 = st.date_input("تاريخ النهاية")
            reason = st.text_area("السبب")
            if st.form_submit_button("إرسال للمنسق"):
                st.session_state.leave_requests.append({
                    "الموظف": user['name'], "من": d1, "إلى": d2, "السبب": reason, "الحالة": "قيد الانتظار"
                })
                st.success("تم إرسال طلبك للمنسقين للمراجعة.")

    # ز. الطلبات الخارجية (المدير)
    elif choice == "الطلبات الخارجية":
        st.header("🌐 الطلبات الخارجية")
        if st.session_state.external_requests:
            st.table(pd.DataFrame(st.session_state.external_requests))
        with st.expander("إضافة طلب خارجي جديد"):
            org = st.text_input("جهة الطلب")
            evt = st.text_input("نوع الفعالية")
            if st.button("حفظ"):
                st.session_state.external_requests.append({"الجهة": org, "الفعالية": evt, "الحالة": "جديد"})
                st.rerun()

    # ح. التقارير (المدير)
    elif choice == "التقارير":
        st.header("📈 تقارير الأداء العام")
        if not st.session_state.staff_schedules.empty:
            st.write("إجمالي ساعات العمل لكل مدرب:")
            summary = st.session_state.staff_schedules.groupby("الموظف")["الساعات"].sum().reset_index()
            st.bar_chart(summary.set_index("الموظف"))
            st.download_button("تحميل التقرير الكامل CSV", st.session_state.staff_schedules.to_csv(), "report.csv")
        else:
            st.warning("لا توجد بيانات كافية لإصدار تقرير.")
