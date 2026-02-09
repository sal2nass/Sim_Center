import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date
import calendar
import os

# =========================
# 0) Page Config + Styling
# =========================
st.set_page_config(page_title="SimCenter Pro OS", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
* { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
.stApp { background-color: #ffffff; }
.kpi-card { background:#fff; padding:18px; border-radius:14px; border:1px solid #e2e8f0; box-shadow:0 2px 6px rgba(0,0,0,0.04); }
.small { opacity:0.8; font-size:13px; }
hr { border:0; border-top:1px solid #e2e8f0; margin:14px 0; }
</style>
""", unsafe_allow_html=True)

# =========================
# 1) RBAC Users & Roles
# =========================
OWNER_EMAIL = "sal2nass@gmail.com"
LEADER_EMAILS = ["sal4nass@gmail.com"]
EMPLOYEE_EMAILS = ["sal_saleh@hotmail.com"]

def get_role(email: str) -> str:
    email = (email or "").strip().lower()
    if email == OWNER_EMAIL.lower():
        return "OWNER"
    if email in [e.lower() for e in LEADER_EMAILS]:
        return "LEADER"
    if email in [e.lower() for e in EMPLOYEE_EMAILS]:
        return "EMPLOYEE"
    return "DENY"

# =========================
# 2) Storage (CSV Files)
# =========================
SESSIONS_FILE = "sessions.csv"
COURSES_FILE = "courses.csv"
LEAVES_FILE = "leave_requests.csv"
MANNEQUINS_FILE = "mannequins.csv"
OUTGOING_FILE = "outgoing_requests.csv"

def ensure_files():
    if not os.path.exists(SESSIONS_FILE):
        pd.DataFrame(columns=["date","title","location","room","assigned_email","duration_hours"]).to_csv(SESSIONS_FILE, index=False)

    if not os.path.exists(COURSES_FILE):
        pd.DataFrame(columns=["employee_email","course","due_date"]).to_csv(COURSES_FILE, index=False)

    if not os.path.exists(LEAVES_FILE):
        pd.DataFrame(columns=["employee_email","start_date","end_date","reason","status",
                              "leader_email","owner_email","created_at","updated_at"]).to_csv(LEAVES_FILE, index=False)

    if not os.path.exists(MANNEQUINS_FILE):
        pd.DataFrame([{
            "total":0, "working":0, "maintenance":0,
            "updated_by":"", "updated_at":""
        }]).to_csv(MANNEQUINS_FILE, index=False)

    if not os.path.exists(OUTGOING_FILE):
        pd.DataFrame(columns=["title","target_entity","request_date","last_update","updated_by","updated_at"]).to_csv(OUTGOING_FILE, index=False)

def load_csv(path: str, cols: list[str]) -> pd.DataFrame:
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            for c in cols:
                if c not in df.columns:
                    df[c] = None
            return df[cols]
        except Exception:
            return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def save_csv(df: pd.DataFrame, path: str):
    df.to_csv(path, index=False)

ensure_files()

# =========================
# 3) Login (Streamlit)
# =========================
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "role" not in st.session_state:
    st.session_state.role = ""

st.sidebar.title("🔐 تسجيل الدخول")
email_in = st.sidebar.text_input("Email", value=st.session_state.user_email)

c1, c2 = st.sidebar.columns(2)
with c1:
    if st.button("Login"):
        role = get_role(email_in)
        if role == "DENY":
            st.sidebar.error("هذا الإيميل غير مصرح له")
        else:
            st.session_state.user_email = email_in.strip().lower()
            st.session_state.role = role
            st.sidebar.success(f"Logged in as: {role}")
            st.rerun()

with c2:
    if st.button("Logout"):
        st.session_state.user_email = ""
        st.session_state.role = ""
        st.sidebar.info("تم تسجيل الخروج")
        st.rerun()

if not st.session_state.role:
    st.info("فضلاً سجل دخولك من القائمة الجانبية.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.write("👤 المستخدم:", st.session_state.user_email)
st.sidebar.write("🛡️ الدور:", st.session_state.role)

role = st.session_state.role
me = st.session_state.user_email

# =========================
# 4) Common Helpers
# =========================
def parse_date_safe(x):
    try:
        return pd.to_datetime(x).date()
    except Exception:
        return None

def is_unavailable_on_day(employee_email: str, day: date, leaves_df: pd.DataFrame) -> bool:
    emp = (employee_email or "").strip().lower()
    approved = leaves_df[leaves_df["status"] == "APPROVED_OWNER"].copy()
    for _, r in approved.iterrows():
        if (str(r["employee_email"]).strip().lower() != emp):
            continue
        sd = parse_date_safe(r["start_date"])
        ed = parse_date_safe(r["end_date"])
        if sd and ed and sd <= day <= ed:
            return True
    return False

def month_range(year: int, month: int):
    first = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    last = date(year, month, last_day)
    return first, last

def sessions_for_day(day: date, sessions_df: pd.DataFrame) -> pd.DataFrame:
    if sessions_df.empty:
        return sessions_df
    s = sessions_df.copy()
    s["date_parsed"] = s["date"].apply(parse_date_safe)
    return s[s["date_parsed"] == day].drop(columns=["date_parsed"])

def unavailable_for_day(day: date, leaves_df: pd.DataFrame) -> list[str]:
    approved = leaves_df[leaves_df["status"] == "APPROVED_OWNER"].copy()
    unavail = []
    for _, r in approved.iterrows():
        sd = parse_date_safe(r["start_date"])
        ed = parse_date_safe(r["end_date"])
        if sd and ed and sd <= day <= ed:
            unavail.append(str(r["employee_email"]).strip().lower())
    return sorted(list(set(unavail)))

# =========================
# 5) Navigation by Role
# =========================
if role == "OWNER":
    pages = ["📊 Owner Dashboard", "🗓️ Calendar (View)", "✅ Leave Approvals (Final)"]
elif role == "LEADER":
    pages = ["🧭 Leader Dashboard", "⬆️ Upload Excel", "🗓️ Calendar", "✅ Leave Approvals (Leader)"]
else:
    pages = ["🗓️ My Calendar", "🎓 My Courses", "📝 Request Leave"]

page = st.sidebar.radio("القائمة", pages)

# Load data once per view
sessions = load_csv(SESSIONS_FILE, ["date","title","location","room","assigned_email","duration_hours"])
courses = load_csv(COURSES_FILE, ["employee_email","course","due_date"])
leaves = load_csv(LEAVES_FILE, ["employee_email","start_date","end_date","reason","status","leader_email","owner_email","created_at","updated_at"])
mannequins = load_csv(MANNEQUINS_FILE, ["total","working","maintenance","updated_by","updated_at"])
outgoing = load_csv(OUTGOING_FILE, ["title","target_entity","request_date","last_update","updated_by","updated_at"])

# =========================================
# 6) LEADER: Upload Excel (Sessions + Courses)
# =========================================
if role in ["LEADER","OWNER"] and page == "⬆️ Upload Excel":
    st.header("⬆️ رفع ملف Excel (Sessions + Courses)")

    st.info("صيغة ملف Excel:\n"
            "- Sheet اسمها Sessions بأعمدة: date, title, location, room, assigned_email, duration_hours\n"
            "- Sheet اسمها Courses بأعمدة: employee_email, course, due_date (اختياري)")

    uploaded = st.file_uploader("ارفع ملف Excel", type=["xlsx"])

    if uploaded:
        try:
            xls = pd.ExcelFile(uploaded)

            if "Sessions" in xls.sheet_names:
                s_df = xls.parse("Sessions")
                needed = ["date","title","location","room","assigned_email","duration_hours"]
                for c in needed:
                    if c not in s_df.columns:
                        s_df[c] = None

                sessions2 = pd.concat([sessions, s_df[needed]], ignore_index=True)
                save_csv(sessions2, SESSIONS_FILE)
                st.success("✅ تم تحديث Sessions")

            if "Courses" in xls.sheet_names:
                c_df = xls.parse("Courses")
                needed2 = ["employee_email","course","due_date"]
                for c in needed2:
                    if c not in c_df.columns:
                        c_df[c] = None

                courses2 = pd.concat([courses, c_df[needed2]], ignore_index=True)
                save_csv(courses2, COURSES_FILE)
                st.success("✅ تم تحديث Courses")

            st.warning("ملاحظة: إذا تبي تمنع التكرار مستقبلاً نضيف زر (Replace) بدل (Append).")

        except Exception as e:
            st.error(f"فشل قراءة الملف: {e}")

# =========================================
# 7) LEADER: Dashboard (Mannequins + Outgoing + Leave Leader approvals)
# =========================================
if role in ["LEADER","OWNER"] and page == "🧭 Leader Dashboard":
    st.header("🧭 Leader Dashboard")

    left, right = st.columns([1,1])

    with left:
        st.subheader("🧍‍♂️ تحديث المانيكان")
        cur = mannequins.iloc[0] if len(mannequins) else {"total":0,"working":0,"maintenance":0}
        total = st.number_input("Total", min_value=0, value=int(cur.get("total",0) or 0))
        working = st.number_input("Working", min_value=0, value=int(cur.get("working",0) or 0))
        maintenance = st.number_input("Maintenance", min_value=0, value=int(cur.get("maintenance",0) or 0))

        if st.button("💾 حفظ بيانات المانيكان"):
            df = pd.DataFrame([{
                "total": total,
                "working": working,
                "maintenance": maintenance,
                "updated_by": me,
                "updated_at": datetime.now().isoformat(timespec="seconds")
            }])
            save_csv(df, MANNEQUINS_FILE)
            st.success("✅ تم الحفظ")
            st.rerun()

    with right:
        st.subheader("📤 إضافة طلب خارج المركز")
        title = st.text_input("عنوان الطلب")
        target = st.text_input("الجهة")
        req_date = st.date_input("تاريخ الطلب", value=date.today())
        last_update = st.text_input("آخر تحديث / الحالة")

        if st.button("➕ إضافة الطلب"):
            if not title.strip() or not target.strip():
                st.error("الرجاء تعبئة العنوان والجهة")
            else:
                o2 = pd.concat([outgoing, pd.DataFrame([{
                    "title": title.strip(),
                    "target_entity": target.strip(),
                    "request_date": req_date.isoformat(),
                    "last_update": last_update.strip(),
                    "updated_by": me,
                    "updated_at": datetime.now().isoformat(timespec="seconds")
                }])], ignore_index=True)
                save_csv(o2, OUTGOING_FILE)
                st.success("✅ تمت الإضافة")
                st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    st.subheader("📤 الطلبات الخارجة (تعديل آخر تحديث)")
    outgoing_show = outgoing.copy()
    if outgoing_show.empty:
        st.info("لا توجد طلبات.")
    else:
        st.dataframe(outgoing_show, use_container_width=True)

        idxs = list(outgoing_show.index)
        pick = st.selectbox("اختر الطلب لتحديثه", idxs)
        new_update = st.text_input("آخر تحديث جديد", value=str(outgoing_show.loc[pick, "last_update"]))
        if st.button("🔄 تحديث"):
            outgoing.loc[pick, "last_update"] = new_update.strip()
            outgoing.loc[pick, "updated_by"] = me
            outgoing.loc[pick, "updated_at"] = datetime.now().isoformat(timespec="seconds")
            save_csv(outgoing, OUTGOING_FILE)
            st.success("✅ تم التحديث")
            st.rerun()

# =========================================
# 8) OWNER: Dashboard (Hours + Rooms + Utilization + Mannequins + Outgoing + Pending Owner Leaves)
# =========================================
if role == "OWNER" and page == "📊 Owner Dashboard":
    st.header("📊 Owner Dashboard")

    s = sessions.copy()
    if not s.empty:
        s["duration_hours"] = pd.to_numeric(s["duration_hours"], errors="coerce").fillna(0)
        actual_hours = float(s["duration_hours"].sum())
        rooms_used = s["room"].fillna("").astype(str).str.strip()
        rooms_used = rooms_used[rooms_used != ""].nunique()
    else:
        actual_hours = 0.0
        rooms_used = 0

    expected_hours = 1200.0
    utilization = (actual_hours / expected_hours * 100.0) if expected_hours else 0.0

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='kpi-card'><div class='small'>عدد الساعات الفعلية</div><h2>{actual_hours:.1f}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi-card'><div class='small'>عدد الغرف المستخدمة</div><h2>{rooms_used}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi-card'><div class='small'>معدل استخدام المركز (من {int(expected_hours)} ساعة)</div><h2>{utilization:.1f}%</h2></div>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    st.subheader("🧍‍♂️ المانيكان")
    st.dataframe(mannequins, use_container_width=True)

    st.subheader("📤 الطلبات الخارجة من المركز")
    st.dataframe(outgoing.sort_values("updated_at", ascending=False) if not outgoing.empty else outgoing, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    st.subheader("✅ طلبات الإجازة بانتظار موافقة نهائية (Owner)")
    pending_owner = leaves[leaves["status"] == "PENDING_OWNER"].copy()
    if pending_owner.empty:
        st.info("لا توجد طلبات بانتظار موافقتك.")
    else:
        st.dataframe(pending_owner, use_container_width=True)

# =========================================
# 9) Leave Approvals (Leader / Owner)
# =========================================
if (role == "LEADER" and page == "✅ Leave Approvals (Leader)") or (role == "OWNER" and page == "✅ Leave Approvals (Final)"):
    if role == "LEADER":
        st.header("✅ موافقات الإجازة (Leader - مبدئية)")
        view = leaves[leaves["status"] == "PENDING_LEADER"].copy()
    else:
        st.header("✅ موافقات الإجازة (Owner - نهائية)")
        view = leaves[leaves["status"] == "PENDING_OWNER"].copy()

    if view.empty:
        st.info("لا توجد طلبات حالياً.")
    else:
        st.dataframe(view, use_container_width=True)

        row_ids = list(view.index)
        pick = st.selectbox("اختر طلب (index) من الجدول", row_ids)
        action = st.selectbox("الإجراء", ["approve", "reject"])

        if st.button("تنفيذ القرار"):
            now = datetime.now().isoformat(timespec="seconds")

            if role == "LEADER":
                if action == "approve":
                    leaves.loc[pick, "status"] = "PENDING_OWNER"
                else:
                    leaves.loc[pick, "status"] = "REJECTED_LEADER"
                leaves.loc[pick, "leader_email"] = me

            if role == "OWNER":
                if action == "approve":
                    leaves.loc[pick, "status"] = "APPROVED_OWNER"
                else:
                    leaves.loc[pick, "status"] = "REJECTED_OWNER"
                leaves.loc[pick, "owner_email"] = me

            leaves.loc[pick, "updated_at"] = now
            save_csv(leaves, LEAVES_FILE)
            st.success("✅ تم تحديث الطلب")
            st.rerun()

# =========================================
# 10) EMPLOYEE: Request Leave
# =========================================
if role == "EMPLOYEE" and page == "📝 Request Leave":
    st.header("📝 طلب إجازة")

    start = st.date_input("من", value=date.today())
    end = st.date_input("إلى", value=date.today())
    reason = st.text_input("السبب (اختياري)")

    if st.button("Submit"):
        if end < start:
            st.error("تأكد أن تاريخ النهاية بعد البداية")
        else:
            now = datetime.now().isoformat(timespec="seconds")
            new_row = pd.DataFrame([{
                "employee_email": me,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "reason": reason.strip(),
                "status": "PENDING_LEADER",
                "leader_email": "",
                "owner_email": "",
                "created_at": now,
                "updated_at": now
            }])
            leaves2 = pd.concat([leaves, new_row], ignore_index=True)
            save_csv(leaves2, LEAVES_FILE)
            st.success("✅ تم إرسال الطلب للليدر")
            st.rerun()

# =========================================
# 11) EMPLOYEE: My Courses
# =========================================
if role == "EMPLOYEE" and page == "🎓 My Courses":
    st.header("🎓 الكورسات المطلوبة منك")
    my = courses.copy()
    if my.empty:
        st.info("لا توجد كورسات حتى الآن (بانتظار رفع الليدر للملف).")
    else:
        my["employee_email"] = my["employee_email"].fillna("").astype(str).str.strip().str.lower()
        my = my[my["employee_email"] == me].copy()
        if my.empty:
            st.info("لا توجد كورسات مسجلة لك حالياً.")
        else:
            st.dataframe(my, use_container_width=True)

# =========================================
# 12) Calendar (All roles) + Day Details
# =========================================
def calendar_view(read_only: bool):
    st.subheader("🗓️ التقويم الشهري")

    today = date.today()
    colA, colB = st.columns(2)
    with colA:
        year = st.number_input("السنة", min_value=2020, max_value=2100, value=today.year, step=1)
    with colB:
        month = st.number_input("الشهر", min_value=1, max_value=12, value=today.month, step=1)

    first, last = month_range(int(year), int(month))

    # Build month grid summary: sessions count + unavailable count per day
    days = [date(int(year), int(month), d) for d in range(1, calendar.monthrange(int(year), int(month))[1] + 1)]

    s = sessions.copy()
    if not s.empty:
        s["date_parsed"] = s["date"].apply(parse_date_safe)
    else:
        s["date_parsed"] = None

    summary = []
    for d in days:
        sess_count = int((s["date_parsed"] == d).sum()) if not s.empty else 0
        unavail = unavailable_for_day(d, leaves)
        summary.append({
            "اليوم": d.isoformat(),
            "عدد السيشنات": sess_count,
            "غير متواجد (إجازات معتمدة)": len(unavail)
        })
    sum_df = pd.DataFrame(summary)

    st.dataframe(sum_df, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    picked_day = st.date_input("اختر يوم لعرض التفاصيل", value=today)
    st.subheader(f"تفاصيل يوم: {picked_day.isoformat()}")

    day_sess = sessions_for_day(picked_day, sessions)
    if day_sess.empty:
        st.info("لا توجد سيشنات في هذا اليوم.")
    else:
        # For leaders/owners: show warning if assigned employee has approved leave
        if role in ["LEADER","OWNER"]:
            day_sess2 = day_sess.copy()
            day_sess2["assigned_email"] = day_sess2["assigned_email"].fillna("").astype(str).str.strip().str.lower()
            day_sess2["unavailable?"] = day_sess2["assigned_email"].apply(
                lambda e: "نعم" if (e and is_unavailable_on_day(e, picked_day, leaves)) else "لا"
            )
            st.dataframe(day_sess2, use_container_width=True)
        else:
            st.dataframe(day_sess, use_container_width=True)

    unavail_list = unavailable_for_day(picked_day, leaves)
    if unavail_list:
        st.warning("⚠️ موظفين غير متواجدين (إجازات معتمدة): " + " , ".join(unavail_list))
    else:
        st.success("✅ لا يوجد إجازات معتمدة تؤثر على هذا اليوم.")

    if read_only:
        st.caption("الوضع: عرض فقط (Read-only)")

# Owner Calendar View
if role == "OWNER" and page == "🗓️ Calendar (View)":
    st.header("🗓️ Calendar (Owner View)")
    calendar_view(read_only=True)

# Leader Calendar
if role == "LEADER" and page == "🗓️ Calendar":
    st.header("🗓️ Calendar (Leader)")
    calendar_view(read_only=False)

# Employee Calendar
if role == "EMPLOYEE" and page == "🗓️ My Calendar":
    st.header("🗓️ My Calendar (Employee)")
    calendar_view(read_only=True)

# =========================================
# 13) Footer / Notes
# =========================================
st.sidebar.markdown("---")
st.sidebar.caption("MVP v1 • التخزين حالياً CSV داخل الريبو (مناسب للتجربة).")

