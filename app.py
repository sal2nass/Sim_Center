import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. إعدادات الصفحة والتنسيق الجمالي ---
st.set_page_config(page_title="SimCenter OS", layout="wide", initial_sidebar_state="expanded")

# تصميم CSS لتحسين الواجهة
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    
    * { font-family: 'Cairo', sans-serif; }
    
    /* خلفية البطاقات */
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-right: 5px solid #4B90FF;
        margin-bottom: 20px;
    }
    
    .main { background-color: #f8f9fa; }
    
    /* تخصيص الأزرار */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #4B90FF;
        color: white;
        height: 3em;
    }
    
    [data-testid="stSidebar"] {
        background-color: #1E293B;
    }
    [data-testid="stSidebar"] * {
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة قاعدة البيانات البسيطة (Session State) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# بيانات المستخدمين (إيميلاتك الحقيقية)
USERS = {
    "sal2nass@gmail.com": {"name": "المدير العام", "role": "owner", "lang": "العربية"},
    "sal4nass@gmail.com": {"name": "منسق العمليات", "role": "coordinator", "lang": "العربية"},
    "sal_saleh@hotmail.com": {"name": "صالح (موظف)", "role": "employee", "lang": "العربية"}
}

# --- 3. نظام تسجيل الدخول ---
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/3064/3064155.png", width=100)
        st.title("Simulation Center OS")
        st.subheader("تسجيل الدخول | Login")
        email_input = st.text_input("البريد الإلكتروني", placeholder="example@center.com").lower().strip()
        login_btn = st.button("دخول إلى النظام")
        
        if login_btn:
            if email_input in USERS:
                st.session_state.authenticated = True
                st.session_state.user_info = USERS[email_input]
                st.session_state.user_email = email_input
                st.rerun()
            else:
                st.error("عذراً، هذا البريد غير مسجل لدينا.")

else:
    # --- 4. واجهة النظام بعد الدخول ---
    user = st.session_state.user_info
    role = user['role']
    
    # القائمة الجانبية الملونة
    with st.sidebar:
        st.markdown(f"### 👤 {user['name']}")
        st.markdown(f"**الدور:** {role.capitalize()}")
        st.divider()
        
        # اللغات (تبديل سريع)
        lang = st.radio("اللغة / Language", ["العربية", "English"], horizontal=True)
        
        st.divider()
        # القوائم بناءً على الصلاحية
        if role == "owner":
            menu = ["📊 الداشبورد", "📅 إدارة الإجازات", "🌐 طلبات خارجية", "📑 التقارير", "⚙️ الإعدادات"]
        elif role == "coordinator":
            menu = ["📊 الداشبورد", "📅 مراجعة الإجازات", "🌐 طلبات خارجية"]
        else:
            menu = ["👤 ملفي الشخصي", "📅 طلب إجازة"]
            
        choice = st.radio("القائمة الرئيسية", menu)
        
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 تسجيل الخروج"):
            st.session_state.authenticated = False
            st.rerun()

    # --- 5. محتوى الصفحات ---
    
    # صفحة الداشبورد (Owner & Coordinator)
    if choice == "📊 الداشبورد":
        st.title("📈 لوحة المؤشرات التشغيلية")
        
        # الصف الأول: الحضور والكوادر
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown('<div class="metric-card"><h4>👨‍🏫 مدربين اليوم</h4><h2>8</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="metric-card"><h4>🛠️ مشغلين اليوم</h4><h2>5</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown('<div class="metric-card"><h4>👥 إجمالي الكادر</h4><h2>25</h2></div>', unsafe_allow_html=True)
        with c4: st.markdown('<div class="metric-card"><h4>🎓 كورسات</h4><h2>30</h2></div>', unsafe_allow_html=True)

        # الصف الثاني: التشغيل والساعات
        st.divider()
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader("🎯 نسبة إشغال المركز (1200 ساعة مستهدفة)")
            progress = 850 / 1200
            st.progress(progress)
            st.write(f"تم إنجاز **850** ساعة تدريبية من أصل **1200**")
            
        with col_right:
            st.subheader("🤖 حالة الأصول")
            st.write(f"✅ تعمل: 32")
            st.write(f"🔧 صيانة: 8")
            st.write(f"📦 الإجمالي: 40")

    # صفحة الطلبات الخارجية (الجديدة)
    elif choice == "🌐 طلبات خارجية":
        st.title("🌍 متابعة الطلبات والفعاليات الخارجية")
        df_ext = pd.DataFrame({
            "الجهة": ["جامعة الملك سعود", "وزارة الصحة", "مستشفى الحرس"],
            "نوع الطلب": ["ورشة عمل", "استعارة دمى", "دورة ACLS"],
            "التاريخ": ["2026-03-10", "2026-03-25", "2026-04-05"],
            "الحالة": ["🟡 قيد الدراسة", "🟢 تم التعميد", "🔴 مرفوض"]
        })
        st.dataframe(df_ext, use_container_width=True)
        if role == "owner":
            st.button("+ إضافة طلب خارجي جديد")

    # صفحة الموظف (احمد محمد)
    elif choice == "👤 ملفي الشخصي":
        st.title(f"👋 أهلاً {user['name']}")
        cc1, cc2 = st.columns(2)
        with cc1:
            st.info("⏱️ ساعاتك المنفذة: **45 ساعة**")
            st.success("🌟 المساهمات: **12 عمل إبداعي**")
        with cc2:
            st.warning("💡 توصية الجودة: يرجى إتمام دورة المحاكاة المتقدمة")

    # صفحة الإجازات
    elif choice in ["📅 طلب إجازة", "📅 إدارة الإجازات"]:
        st.title("📅 نظام الإجازات والتقويم")
        if role == "employee":
            with st.form("leave_form"):
                st.date_input("من تاريخ")
                st.date_input("إلى تاريخ")
                st.selectbox("نوع الإجازة", ["اعتيادية", "اضطرارية", "مرضية"])
                st.form_submit_button("إرسال الطلب")
        else:
            st.subheader("الطلبات الواردة")
            st.write("لا توجد طلبات معلقة حالياً.")
            st.divider()
            st.subheader("🗓️ تقويم الموظفين (من الموجود؟)")
            # مثال لجدول الحضور
            st.table(pd.DataFrame({
                "السبت": ["✅", "✅", "✅"],
                "الأحد": ["✅", "❌", "✅"],
                "الاثنين": ["✅", "✅", "❌"]
            }, index=["أحمد", "سارة", "خالد"]))

    # صفحة التقارير
    elif choice == "📑 التقارير":
        st.title("📄 استخراج التقارير")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.date_input("تقرير من تاريخ")
        with col_r2:
            st.date_input("تقرير إلى تاريخ")
        
        st.selectbox("نوع التقرير", ["تقرير تشغيلي شامل", "تقرير أداء الموظفين", "تقرير صيانة الدمى"])
        if st.button("📥 تحميل التقرير (Excel)"):
            st.success("يتم الآن تجهيز التقرير...")
