import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة والهوية البصرية ---
st.set_page_config(page_title="SimCenter Pro OS v3", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #1e293b; color: white; }
    .calendar-day { border: 1px solid #e2e8f0; border-radius: 12px; padding: 10px; min-height: 150px; background: white; }
    .session-item { background: #eff6ff; color: #1e40af; padding: 6px; border-radius: 6px; margin-top: 5px; font-size: 11px; border-right: 4px solid #3b82f6; }
    .absent-item { background: #fef2f2; color: #991b1b; padding: 6px; border-radius: 6px; margin-top: 5px; font-size: 11px; border-right: 4px solid #ef4444; font-weight: bold; }
    .metric-box { background: white; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. تهيئة البيانات الدائمة ---
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
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>🛡️ SimCenter OS</h1>", unsafe_allow_html=True)
        email_in = st.text_input("البريد الإلكتروني").lower().strip()
        if st.button("دخول للنظام", use_container_width=True):
            if email_in in USERS:
                st.session_state.authenticated = True
                st.session_state.user = USERS[email_in]
                st.rerun()
            else: st.error("المستخدم غير مسجل")
else:
    user = st.session_state.user
    role = user['role']
    
    # --- 5. الشريط الجانبي والفلاتر ---
    with st.sidebar:
        st.write(f"### مرحباً، {user['name']}")
        st.divider()
        
        # فلتر التاريخ الموحد (يتحكم في كل النظام)
        st.write("📅 فترة عرض البيانات")
        start_f = st.date_input("من تاريخ", datetime.now().date() - timedelta(days=7))
        end_f = st.date_input("إلى تاريخ", datetime.now().date() + timedelta(days=30))
        
        st.divider()
        
        # القائمة بناءً على الصلاحية
        if role == "owner":
            menu = ["لوحة المؤشرات", "تقويم الفعاليات", "الاعتمادات النهائية", "الطلبات الخارجية", "التقارير"]
        elif role == "coordinator":
            menu = ["لوحة المؤشرات", "تقويم الفعاليات", "مراجعة الإجازات", "رفع جداول الإكسل"]
        else:
            menu = ["تقويمي الشخصي", "تقديم طلب إجازة"]
            
        choice = st.radio("القائمة الرئيسية", menu)
        
        if st.button("تسجيل الخروج"):
            st.session_state.authenticated = False
            st.rerun()

    # --- 6. تصفية البيانات المجدولة بناءً على الفلتر ---
    df_main = st.session_state.staff_schedules.copy()
    if not df_main.empty:
        df_main['التاريخ'] = pd.to_datetime(df_main['التاريخ']).dt.date
        df_main = df_main[(df_main['التاريخ'] >= start_f) & (df_main['التاريخ'] <= end_f)]

    # --- 7. منطق الصفحات ---

    # أ. لوحة المؤشرات الإجمالية
    if choice == "لوحة المؤشرات":
        st.header("📊 لوحة المؤشرات الإجمالية")
        
        c1, c2, c3, c4 = st.columns(4)
        total_hours = df_main['الساعات'].sum() if not df_main.empty else 0
        total_sessions = len(df_main)
        
        # احتساب الموظفين الغائبين خلال الفترة المختارة
        absent_count = len([r for r in st.session_state.leave_requests if r['الحالة'] == 'معتمد نهائياً' and r['من'] >= start_f])

        with c1: st.metric("إجمالي الساعات المنفذة", f"{total_hours} س")
        with c2: st.metric("إجمالي السيشنات", total_sessions)
        with c3: st.metric("طلبات الإجازة المعتمدة", absent_count)
        with c4: st.metric("الطلبات الخارجية", len(st.session_state.external_requests))

        st.divider()
        
        col_g1, col_g2 = st.columns(2)
        if not df_main.empty:
            with col_g1:
                fig1 = px.pie(df_main, names='الموظف', values='الساعات', title="توزيع مجهود الموظفين (ساعات)")
                st.plotly_chart(fig1, use_container_width=True)
            with col_g2:
                fig2 = px.bar(df_main, x='التاريخ', y='الساعات', color='الموظف', title="التسلسل الزمني للفعاليات")
                st.plotly_chart(fig2, use_container_width=True)
        else: st.info("لا توجد بيانات سيشنات في هذه الفترة")

    # ب. التقويم المطور
    elif "تقويم" in choice:
        st.header(f"📅 {choice}")
        # عرض أيام الشهر الحالية
        days_in_month = pd.date_range(start=start_f, end=end_f)
        
        for day in days_in_month:
            date_str = str(day.date())
            with st.expander(f"🗓️ {day.strftime('%A')} - {date_str}"):
                col_day1, col_day2 = st.columns([2, 1])
                
                with col_day1:
                    st.write("**📖 الحصص المجدولة:**")
                    tasks = df_main[df_main['التاريخ'] == day.date()]
                    if role == "employee": tasks = tasks[tasks['الموظف'] == user['name']]
                    
                    if not tasks.empty:
                        for _, row in tasks.iterrows():
                            st.markdown(f"<div class='session-item'><b>{row['المهمة']}</b><br>المدرب: {row['المدرب']} | المنسق: {row['المنسق']}</div>", unsafe_allow_html=True)
                    else: st.caption("لا يوجد حصص")

                with col_day2:
                    if role != "employee":
                        st.write("**🚫 غير متواجدين:**")
                        absents = [r['الموظف'] for r in st.session_state.leave_requests 
                                   if r['الحالة'] == 'معتمد نهائياً' and r['من'] <= day.date() <= r['إلى']]
                        if absents:
                            for a in absents: st.markdown(f"<div class='absent-item'>{a}</div>", unsafe_allow_html=True)
                        else: st.caption("الكل متواجد")

    # ج. مراجعة الإجازات (المنسق)
    elif choice == "مراجعة الإجازات":
        st.header("🔍 مراجعة طلبات الإجازة")
        pending = [r for r in st.session_state.leave_requests if r['الحالة'] == 'قيد الانتظار']
        if pending:
            df_pending = pd.DataFrame(pending)
            st.dataframe(df_pending, use_container_width=True)
            
            # اختيار الطلب بناءً على الاسم والتاريخ لضمان الدقة
            target = st.selectbox("اختر اسم الموظف للموافقة المبدئية", df_pending['الموظف'].unique())
            if st.button("موافقة مبدئية وتحويل للمدير"):
                for r in st.session_state.leave_requests:
                    if r['الموظف'] == target and r['الحالة'] == 'قيد الانتظار':
                        r['الحالة'] = 'موافق عليه من المنسق'
                st.success(f"تم تحويل طلبات {target} للمدير العام")
                st.rerun()
        else: st.info("لا توجد طلبات جديدة")

    # د. الاعتمادات النهائية (المدير فقط)
    elif choice == "الاعتمادات النهائية":
        st.header("⚖️ الاعتمادات النهائية (المدير العام)")
        to_approve = [r for r in st.session_state.leave_requests if r['الحالة'] == 'موافق عليه من المنسق']
        if to_approve:
            st.table(pd.DataFrame(to_approve))
            target_approve = st.selectbox("اختر الموظف للاعتماد النهائي", [r['الموظف'] for r in to_approve])
            if st.button("🚀 اعتماد نهائي ونشر في التقويم"):
                for r in st.session_state.leave_requests:
                    if r['الموظف'] == target_approve and r['الحالة'] == 'موافق عليه من المنسق':
                        r['الحالة'] = 'معتمد نهائياً'
                st.balloons()
                st.rerun()
        else: st.info("لا توجد طلبات بانتظار الاعتماد النهائي")

    # هـ. رفع جداول الإكسل (للمنسق فقط)
    elif choice == "رفع جداول الإكسل":
        st.header("📤 رفع السيشنات الأسبوعية")
        st.info("ارفع ملف الإكسل الذي يحتوي على الأعمدة: [الموظف، التاريخ، المهمة، المنسق، المدرب، الساعات، الإدارة]")
        up_file = st.file_uploader("اختر ملف الإكسل", type=["xlsx"])
        if up_file:
            new_df = pd.read_excel(up_file)
            new_df['التاريخ'] = pd.to_datetime(new_df['التاريخ']).dt.date
            
            # كاشف التعارض
            for _, row in new_df.iterrows():
                if any(r['الموظف'] == row['الموظف'] and r['الحالة'] == 'معتمد نهائياً' and r['من'] <= row['التاريخ'] <= r['إلى'] for r in st.session_state.leave_requests):
                    st.error(f"⚠️ تعارض: الموظف {row['الموظف']} لديه إجازة يوم {row['التاريخ']}")
            
            st.session_state.staff_schedules = new_df
            st.success("تم تحديث قاعدة البيانات بنجاح")

    # و. الطلبات الخارجية
    elif choice == "الطلبات الخارجية":
        st.header("🌐 الطلبات الخارجية")
        if st.session_state.external_requests:
            st.dataframe(pd.DataFrame(st.session_state.external_requests), use_container_width=True)
            
        with st.expander("➕ إضافة طلب جديد"):
            col_ext1, col_ext2 = st.columns(2)
            e_type = col_ext1.selectbox("نوع الملف", ["دورة", "ورشة", "اجتماع", "أخرى"])
            e_dept = col_ext2.text_input("الإدارة")
            e_date = st.date_input("التاريخ")
            if st.button("حفظ الطلب"):
                st.session_state.external_requests.append({
                    "نوع الملف": e_type, "الإدارة": e_dept, "التاريخ": str(e_date), "الحالة": "قيد المعالجة"
                })
                st.rerun()

    # ز. التقارير
    elif choice == "التقارير":
        st.header("📈 استخراج التقارير")
        if not df_main.empty:
            st.write(f"تقرير الفترة من {start_f} إلى {end_f}")
            st.dataframe(df_main)
            st.download_button("تحميل التقرير كـ CSV", df_main.to_csv(index=False), "SimCenter_Report.csv")
        else: st.warning("لا توجد بيانات ضمن هذه الفترة")

    # ح. طلب إجازة (الموظف)
    elif choice == "تقديم طلب إجازة":
        st.header("📝 طلب إجازة جديد")
        with st.form("leave_form"):
            d_start = st.date_input("من تاريخ")
            d_end = st.date_input("إلى تاريخ")
            reason = st.text_area("السبب")
            if st.form_submit_button("إرسال للمنسق"):
                st.session_state.leave_requests.append({
                    "الموظف": user['name'], "من": d_start, "إلى": d_end, "السبب": reason, "الحالة": "قيد الانتظار"
                })
                st.success("تم إرسال طلبك")
