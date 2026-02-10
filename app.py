import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import calendar
import os

# =========================
# 0) Page Config + Global Styling
# =========================
st.set_page_config(page_title="SimCenter Pro OS", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
* { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }

.stApp { background: #f6f7fb; }
.block-container { padding-top: 1.2rem; }

.card {
  background:#fff; border:1px solid #e8eaf2; border-radius:16px;
  box-shadow:0 6px 18px rgba(17,24,39,0.05);
  padding:16px;
}
.kpi {
  background:#fff; border:1px solid #e8eaf2; border-radius:16px;
  box-shadow:0 6px 18px rgba(17,24,39,0.05);
  padding:18px;
}
.kpi .label { font-size: 13px; opacity: .75; }
.kpi .value { font-size: 30px; font-weight: 800; margin-top: 2px; }
.kpi .sub { font-size: 12px; opacity: .65; margin-top: 4px; }

.small { font-size: 12px; opacity: .75; }
hr { border:0; border-top:1px solid #e8eaf2; margin:16px 0; }

/* ===== Calendar (modern) ===== */
.cal-wrap {
  background:#fff; border:1px solid #e8eaf2; border-radius:18px;
  box-shadow:0 6px 18px rgba(17,24,39,0.05);
  padding:14px;
}
.cal-head {
  display:flex; align-items:center; justify-content:space-between;
  margin-bottom:10px;
}
.cal-title {
  font-weight:800; font-size:18px;
}
.cal-grid {
  display:grid;
  grid-template-columns: repeat(7, 1fr);
  gap:10px;
}
.cal-dow {
  background:#f3f4f8; border:1px solid #eceef6; border-radius:12px;
  padding:10px; text-align:center; font-weight:700; color:#374151;
}
.cal-cell {
  background:#fbfcff; border:1px solid #eceef6; border-radius:14px;
  padding:10px; min-height:110px; position:relative;
}
.cal-cell.muted { opacity:.45; background:#f8f9fd; }
.cal-num {
  position:absolute; top:10px; left:12px;
  width:28px; height:28px; display:flex; align-items:center; justify-content:center;
  border-radius:999px; font-weight:800; font-size:12px;
  background:#eef2ff; color:#1f3a8a;
}
.cal-num.today { background:#2563eb; color:#fff; }
.cal-events { margin-top:36px; display:flex; flex-direction:column; gap:6px; }
.pill {
  display:inline-block; padding:6px 10px; border-radius:999px;
  background:#fff7ed; border:1px solid #fed7aa;
  font-size:11.5px; font-weight:700; color:#92400e;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}
.pill.leave {
  background:#fef2f2; border:1px solid #fecaca; color:#991b1b;
}
.pill.gray {
  background:#f3f4f6; border:1px solid #e5e7eb; color:#374151;
}
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
# 3) Language Toggle (AR/EN)
# =========================
if "lang" not in st.session_state:
    st.session_state.lang = "AR"

lang_choice = st.sidebar.selectbox("Language / اللغة", ["AR", "EN"], index=0 if st.session_state.lang == "AR" else 1)
st.session_state.lang = lang_choice

T = {
    "AR": {
        "login_title": "🔐 تسجيل الدخول",
        "email": "Email",
        "login": "Login",
        "logout": "Logout",
        "user": "👤 المستخدم:",
        "role": "🛡️ الدور:",
        "menu": "القائمة",
        "please_login": "فضلاً سجل دخولك من القائمة الجانبية.",
        "not_allowed": "هذا الإيميل غير مصرح له",
        "logged_out": "تم تسجيل الخروج",
        "upload_excel": "⬆️ رفع ملف Excel",
        "leader_dash": "🧭 لوحة الليدر",
        "calendar": "🗓️ التقويم",
        "leave_approvals_leader": "✅ موافقات الإجازات (ليدر)",
        "leave_approvals_owner": "✅ موافقات الإجازات (مدير)",
        "owner_dash": "📊 لوحة المدير",
        "my_calendar": "🗓️ تقويمي",
        "my_courses": "🎓 كورساتي",
        "request_leave": "📝 طلب إجازة",
        "from": "من",
        "to": "إلى",
        "reason": "السبب",
        "submit": "Submit",
        "dup_leave": "⚠️ سبق رفعت طلب إجازة بنفس التاريخ (من/إلى). اختر تاريخ مختلف.",
        "sent_ok": "✅ تم رفع الطلب بنجاح وإرساله للّيدر.",
        "no_requests": "لا توجد طلبات حالياً.",
        "pending": "طلبات بانتظار قرارك",
        "employee": "الموظف",
        "approve": "اعتماد",
        "reject": "رفض",
        "done": "✅ تم تحديث الطلب",
        "sessions_period": "Sessions (الفترة)",
        "report_download": "⬇️ تنزيل تقرير HTML (جاهز للطباعة)",
        "csv_download": "⬇️ تنزيل Sessions للفترة (CSV)",
        "print_hint": "بعد تنزيل ملف HTML افتحه بالمتصفح واطبع مباشرة.",
    },
    "EN": {
        "login_title": "🔐 Login",
        "email": "Email",
        "login": "Login",
        "logout": "Logout",
        "user": "👤 User:",
        "role": "🛡️ Role:",
        "menu": "Menu",
        "please_login": "Please login from the sidebar.",
        "not_allowed": "Email not allowed",
        "logged_out": "Logged out",
        "upload_excel": "⬆️ Upload Excel",
        "leader_dash": "🧭 Leader Dashboard",
        "calendar": "🗓️ Calendar",
        "leave_approvals_leader": "✅ Leave Approvals (Leader)",
        "leave_approvals_owner": "✅ Leave Approvals (Owner)",
        "owner_dash": "📊 Owner Dashboard",
        "my_calendar": "🗓️ My Calendar",
        "my_courses": "🎓 My Courses",
        "request_leave": "📝 Request Leave",
        "from": "From",
        "to": "To",
        "reason": "Reason",
        "submit": "Submit",
        "dup_leave": "⚠️ You already submitted the same leave dates. Choose different dates.",
        "sent_ok": "✅ Request submitted and sent to the leader.",
        "no_requests": "No requests right now.",
        "pending": "Requests awaiting your decision",
        "employee": "Employee",
        "approve": "Approve",
        "reject": "Reject",
        "done": "✅ Request updated",
        "sessions_period": "Sessions (Period)",
        "report_download": "⬇️ Download HTML Report (Printable)",
        "csv_download": "⬇️ Download Sessions CSV (Period)",
        "print_hint": "Open the downloaded HTML in your browser and print it.",
    }
}
tr = T[st.session_state.lang]

# =========================
# 4) Login (Streamlit) - Clean Buttons
# =========================
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "role" not in st.session_state:
    st.session_state.role = ""

st.sidebar.title(tr["login_title"])
email_in = st.sidebar.text_input(tr["email"], value=st.session_state.user_email)

# Only one button: Login OR Logout
if not st.session_state.role:
    if st.sidebar.button(tr["login"]):
        role_ = get_role(email_in)
        if role_ == "DENY":
            st.sidebar.error(tr["not_allowed"])
        else:
            st.session_state.user_email = email_in.strip().lower()
            st.session_state.role = role_
            st.sidebar.success(f"Logged in as: {role_}")
            st.rerun()
else:
    if st.sidebar.button(tr["logout"]):
        st.session_state.user_email = ""
        st.session_state.role = ""
        st.sidebar.info(tr["logged_out"])
        st.rerun()

if not st.session_state.role:
    st.info(tr["please_login"])
    st.stop()

st.sidebar.markdown("---")
st.sidebar.write(tr["user"], st.session_state.user_email)
st.sidebar.write(tr["role"], st.session_state.role)

role = st.session_state.role
me = st.session_state.user_email

# =========================
# 5) Helpers
# =========================
def parse_date_safe(x):
    try:
        return pd.to_datetime(x).date()
    except Exception:
        return None

def month_name_ar(m: int) -> str:
    names = {
        1:"يناير",2:"فبراير",3:"مارس",4:"أبريل",5:"مايو",6:"يونيو",
        7:"يوليو",8:"أغسطس",9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر"
    }
    return names.get(m, str(m))

def month_name(m: int) -> str:
    if st.session_state.lang == "AR":
        return month_name_ar(m)
    return calendar.month_name[m]

def filter_sessions_by_range(sessions_df: pd.DataFrame, d_from: date, d_to: date) -> pd.DataFrame:
    if sessions_df.empty:
        return sessions_df
    s = sessions_df.copy()
    s["date_parsed"] = s["date"].apply(parse_date_safe)
    s = s[(s["date_parsed"].notna()) & (s["date_parsed"] >= d_from) & (s["date_parsed"] <= d_to)].copy()
    return s.drop(columns=["date_parsed"])

def unavailable_for_day(day: date, leaves_df: pd.DataFrame) -> list[str]:
    if leaves_df.empty:
        return []
    approved = leaves_df[leaves_df["status"] == "APPROVED_OWNER"].copy()
    unavail = []
    for _, r in approved.iterrows():
        sd = parse_date_safe(r["start_date"])
        ed = parse_date_safe(r["end_date"])
        if sd and ed and sd <= day <= ed:
            unavail.append(str(r["employee_email"]).strip().lower())
    return sorted(list(set(unavail)))

def employee_has_same_leave_request(leaves_df: pd.DataFrame, employee_email: str, start_d: date, end_d: date) -> bool:
    if leaves_df.empty:
        return False
    emp = (employee_email or "").strip().lower()
    sd = start_d.isoformat()
    ed = end_d.isoformat()
    m = leaves_df.copy()
    m["employee_email"] = m["employee_email"].fillna("").astype(str).str.strip().str.lower()
    m["start_date"] = m["start_date"].fillna("").astype(str).str.strip()
    m["end_date"] = m["end_date"].fillna("").astype(str).str.strip()
    return ((m["employee_email"] == emp) & (m["start_date"] == sd) & (m["end_date"] == ed)).any()

def make_html_report(title: str, kpis: dict, tables: dict) -> str:
    rows_kpi = "".join([f"""
      <div style="flex:1;background:#fff;border:1px solid #e8eaf2;border-radius:14px;padding:14px;box-shadow:0 6px 18px rgba(17,24,39,0.05);">
        <div style="opacity:.7;font-size:12px;">{k}</div>
        <div style="font-size:26px;font-weight:800;margin-top:4px;">{v}</div>
      </div>
    """ for k, v in kpis.items()])

    tables_html = ""
    for tname, df in tables.items():
        tables_html += f"<h3 style='margin-top:18px;'>{tname}</h3>"
        tables_html += df.to_html(index=False)

    return f"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8" />
<title>{title}</title>
<style>
body {{ font-family: Cairo, system-ui; background:#f6f7fb; padding:18px; }}
h1 {{ margin:0 0 10px; }}
.card {{ background:#fff;border:1px solid #e8eaf2;border-radius:16px;padding:16px;box-shadow:0 6px 18px rgba(17,24,39,0.05); }}
.kpi-row {{ display:flex; gap:12px; }}
table {{ width:100%; border-collapse:collapse; margin-top:10px; }}
th, td {{ border:1px solid #e8eaf2; padding:8px; font-size:13px; }}
th {{ background:#f3f4f8; }}
.small {{ opacity:.75; font-size:12px; }}
@media print {{
  body {{ background:#fff; }}
  .card {{ box-shadow:none; }}
}}
</style>
</head>
<body>
  <div class="card">
    <h1>{title}</h1>
    <div class="small">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
    <hr style="border:0;border-top:1px solid #e8eaf2;margin:14px 0;" />
    <div class="kpi-row">{rows_kpi}</div>
    {tables_html}
    <hr style="border:0;border-top:1px solid #e8eaf2;margin:14px 0;" />
    <div class="small">Print: File → Print</div>
  </div>
</body>
</html>
"""

# =========================
# 6) Navigation by Role (Translated titles)
# =========================
if role == "OWNER":
    pages = [tr["owner_dash"], tr["calendar"], tr["leave_approvals_owner"]]
elif role == "LEADER":
    pages = [tr["leader_dash"], tr["upload_excel"], tr["calendar"], tr["leave_approvals_leader"]]
else:
    pages = [tr["my_calendar"], tr["my_courses"], tr["request_leave"]]

page = st.sidebar.radio(tr["menu"], pages)

# Load data
sessions = load_csv(SESSIONS_FILE, ["date","title","location","room","assigned_email","duration_hours"])
courses = load_csv(COURSES_FILE, ["employee_email","course","due_date"])
leaves = load_csv(LEAVES_FILE, ["employee_email","start_date","end_date","reason","status","leader_email","owner_email","created_at","updated_at"])
mannequins = load_csv(MANNEQUINS_FILE, ["total","working","maintenance","updated_by","updated_at"])
outgoing = load_csv(OUTGOING_FILE, ["title","target_entity","request_date","last_update","updated_by","updated_at"])

# =========================
# 7) LEADER: Upload Excel
# =========================
if role in ["LEADER","OWNER"] and page == tr["upload_excel"]:
    st.title(tr["upload_excel"])
    st.markdown("""
<div class="card">
<b>Sessions</b>: date, title, location, room, assigned_email, duration_hours<br/>
<b>Courses</b>: employee_email, course, due_date
</div>
""", unsafe_allow_html=True)

    uploaded = st.file_uploader("Excel (.xlsx)", type=["xlsx"])
    if uploaded:
        try:
            xls = pd.ExcelFile(uploaded)

            if "Sessions" in xls.sheet_names:
                s_df = xls.parse("Sessions")
                needed = ["date","title","location","room","assigned_email","duration_hours"]
                for c in needed:
                    if c not in s_df.columns:
                        s_df[c] = None
                s_df = s_df[needed]
                sessions2 = pd.concat([sessions, s_df], ignore_index=True)
                save_csv(sessions2, SESSIONS_FILE)
                st.success("✅ Sessions updated")

            if "Courses" in xls.sheet_names:
                c_df = xls.parse("Courses")
                needed2 = ["employee_email","course","due_date"]
                for c in needed2:
                    if c not in c_df.columns:
                        c_df[c] = None
                c_df = c_df[needed2]
                courses2 = pd.concat([courses, c_df], ignore_index=True)
                save_csv(courses2, COURSES_FILE)
                st.success("✅ Courses updated")

            st.info("Current mode: Append (adds new rows).")
        except Exception as e:
            st.error(f"Excel read failed: {e}")

# =========================
# 8) LEADER: Dashboard (Mannequins + Outgoing)
# =========================
def leader_mannequin_section():
    st.subheader("🧍‍♂️ Mannequins")
    cur = mannequins.iloc[0] if len(mannequins) else {"total":0,"working":0,"maintenance":0}
    col1, col2, col3 = st.columns(3)
    total = col1.number_input("Total", min_value=0, value=int(cur.get("total",0) or 0))
    working = col2.number_input("Working", min_value=0, value=int(cur.get("working",0) or 0))
    maintenance = col3.number_input("Maintenance", min_value=0, value=int(cur.get("maintenance",0) or 0))

    if st.button("💾 Save Mannequins", use_container_width=True):
        df = pd.DataFrame([{
            "total": total,
            "working": working,
            "maintenance": maintenance,
            "updated_by": me,
            "updated_at": datetime.now().isoformat(timespec="seconds")
        }])
        save_csv(df, MANNEQUINS_FILE)
        st.success("✅ Saved")
        st.rerun()

def leader_outgoing_section():
    st.subheader("📤 Outgoing Requests")
    with st.expander("➕ Add New Request", expanded=True):
        c1, c2 = st.columns(2)
        title = c1.text_input("Title")
        target = c2.text_input("Target Entity")
        c3, c4 = st.columns(2)
        req_date = c3.date_input("Request Date", value=date.today())
        last_update = c4.text_input("Last Update / Status")

        if st.button("Add", use_container_width=True):
            if not title.strip() or not target.strip():
                st.error("Fill title + target")
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
                st.success("✅ Added")
                st.rerun()

    if outgoing.empty:
        st.info("No outgoing requests.")
        return

    show = outgoing.copy().sort_values("updated_at", ascending=False)
    st.dataframe(show, use_container_width=True)

    with st.expander("✏️ Update Status", expanded=False):
        idxs = list(show.index)
        pick = st.selectbox("Pick index", idxs)
        new_update = st.text_input("New Last Update", value=str(show.loc[pick, "last_update"]))
        if st.button("Update", use_container_width=True):
            outgoing.loc[pick, "last_update"] = new_update.strip()
            outgoing.loc[pick, "updated_by"] = me
            outgoing.loc[pick, "updated_at"] = datetime.now().isoformat(timespec="seconds")
            save_csv(outgoing, OUTGOING_FILE)
            st.success("✅ Updated")
            st.rerun()

if role in ["LEADER","OWNER"] and page == tr["leader_dash"]:
    st.title(tr["leader_dash"])
    a, b = st.columns([1,1])
    with a:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        leader_mannequin_section()
        st.markdown("</div>", unsafe_allow_html=True)
    with b:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        leader_outgoing_section()
        st.markdown("</div>", unsafe_allow_html=True)

# =========================
# 9) OWNER: Dashboard (Filters + Charts + Export + Report)
# =========================
if role == "OWNER" and page == tr["owner_dash"]:
    st.title(tr["owner_dash"])

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,1])
    today = date.today()
    default_from = date(today.year, today.month, 1)
    d_from = c1.date_input(tr["from"], value=default_from)
    d_to = c2.date_input(tr["to"], value=today)
    expected_hours = c3.number_input("Baseline Hours", min_value=0, value=1200, step=50)
    st.markdown("</div>", unsafe_allow_html=True)

    if d_to < d_from:
        st.error("Invalid range")
        st.stop()

    s_range = filter_sessions_by_range(sessions, d_from, d_to)
    if not s_range.empty:
        s_range["duration_hours"] = pd.to_numeric(s_range["duration_hours"], errors="coerce").fillna(0)
        actual_hours = float(s_range["duration_hours"].sum())
        rooms_used = s_range["room"].fillna("").astype(str).str.strip()
        rooms_used = rooms_used[rooms_used != ""].nunique()
        sessions_count = len(s_range)
    else:
        actual_hours = 0.0
        rooms_used = 0
        sessions_count = 0

    utilization = (actual_hours / float(expected_hours) * 100.0) if expected_hours else 0.0

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f"<div class='kpi'><div class='label'>Sessions</div><div class='value'>{sessions_count}</div><div class='sub'>Period</div></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='kpi'><div class='label'>Actual Hours</div><div class='value'>{actual_hours:.1f}</div><div class='sub'>Period</div></div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='kpi'><div class='label'>Rooms Used</div><div class='value'>{rooms_used}</div><div class='sub'>Based on room</div></div>", unsafe_allow_html=True)
    k4.markdown(f"<div class='kpi'><div class='label'>Utilization</div><div class='value'>{utilization:.1f}%</div><div class='sub'>Baseline: {int(expected_hours)}</div></div>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    left, right = st.columns([1.3, 1])
    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📈 Hours by Room")
        if not s_range.empty:
            tmp = s_range.copy()
            tmp["room"] = tmp["room"].fillna("Unspecified").astype(str)
            g = tmp.groupby("room", as_index=False)["duration_hours"].sum().sort_values("duration_hours", ascending=False)
            fig = px.bar(g, x="room", y="duration_hours")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sessions in this period.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🧍‍♂️ Mannequins")
        st.dataframe(mannequins, use_container_width=True)
        st.subheader("📤 Outgoing")
        st.dataframe(outgoing.sort_values("updated_at", ascending=False) if not outgoing.empty else outgoing, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🧾 Export / Printable Report")

    export_df = s_range.copy()
    if export_df.empty:
        export_df = pd.DataFrame(columns=["date","title","location","room","assigned_email","duration_hours"])

    csv_bytes = export_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label=tr["csv_download"],
        data=csv_bytes,
        file_name=f"sessions_{d_from}_{d_to}.csv",
        mime="text/csv",
        use_container_width=True
    )

    report_kpis = {
        "Sessions": sessions_count,
        "Hours": f"{actual_hours:.1f}",
        "Rooms": rooms_used,
        "Utilization": f"{utilization:.1f}%"
    }
    tables = {
        tr["sessions_period"]: export_df.head(500),
        "Outgoing Requests": outgoing.sort_values("updated_at", ascending=False).head(200) if not outgoing.empty else outgoing,
        "Mannequins": mannequins
    }
    html = make_html_report(
        title=f"SimCenter Report | {d_from} → {d_to}",
        kpis=report_kpis,
        tables=tables
    )
    st.download_button(
        label=tr["report_download"],
        data=html.encode("utf-8"),
        file_name=f"simcenter_report_{d_from}_{d_to}.html",
        mime="text/html",
        use_container_width=True
    )
    st.caption(tr["print_hint"])
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# 10) Leave Approvals (Leader / Owner) - Clean Card UI
# =========================
def render_leave_card(row, idx, is_leader: bool, leaves_df: pd.DataFrame):
    emp = str(row.get("employee_email","")).strip()
    sd = str(row.get("start_date","")).strip()
    ed = str(row.get("end_date","")).strip()
    rs = str(row.get("reason","")).strip()

    st.markdown(f"""
    <div class="card" style="margin-bottom:12px;">
      <div style="display:flex; justify-content:space-between; gap:10px; align-items:center;">
        <div>
          <div style="font-weight:800; font-size:16px;">{tr["employee"]}: {emp}</div>
          <div class="small">{tr["from"]}: <b>{sd}</b> &nbsp; | &nbsp; {tr["to"]}: <b>{ed}</b></div>
          <div class="small">{tr["reason"]}: {rs if rs else "-"}</div>
        </div>
        <div style="text-align:left;">
          <span class="pill gray">{row.get("status","")}</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    cA, cB = st.columns(2)
    with cA:
        if st.button(f"✅ {tr['approve']} #{idx}", use_container_width=True):
            now = datetime.now().isoformat(timespec="seconds")
            if is_leader:
                leaves_df.loc[idx, "status"] = "PENDING_OWNER"
                leaves_df.loc[idx, "leader_email"] = me
            else:
                leaves_df.loc[idx, "status"] = "APPROVED_OWNER"
                leaves_df.loc[idx, "owner_email"] = me
            leaves_df.loc[idx, "updated_at"] = now
            save_csv(leaves_df, LEAVES_FILE)
            st.success(tr["done"])
            st.rerun()

    with cB:
        if st.button(f"❌ {tr['reject']} #{idx}", use_container_width=True):
            now = datetime.now().isoformat(timespec="seconds")
            if is_leader:
                leaves_df.loc[idx, "status"] = "REJECTED_LEADER"
                leaves_df.loc[idx, "leader_email"] = me
            else:
                leaves_df.loc[idx, "status"] = "REJECTED_OWNER"
                leaves_df.loc[idx, "owner_email"] = me
            leaves_df.loc[idx, "updated_at"] = now
            save_csv(leaves_df, LEAVES_FILE)
            st.success(tr["done"])
            st.rerun()

if (role == "LEADER" and page == tr["leave_approvals_leader"]) or (role == "OWNER" and page == tr["leave_approvals_owner"]):
    is_leader = (role == "LEADER")
    st.title(tr["leave_approvals_leader"] if is_leader else tr["leave_approvals_owner"])

    if is_leader:
        view = leaves[leaves["status"] == "PENDING_LEADER"].copy()
    else:
        view = leaves[leaves["status"] == "PENDING_OWNER"].copy()

    st.markdown(f"<div class='card'><b>{tr['pending']}</b></div>", unsafe_allow_html=True)

    if view.empty:
        st.info(tr["no_requests"])
    else:
        view = view.sort_values("created_at", ascending=False)
        for idx, row in view.iterrows():
            label = f"{row.get('employee_email','')} | {row.get('start_date','')} → {row.get('end_date','')}"
            with st.expander(label, expanded=False):
                render_leave_card(row, idx, is_leader=is_leader, leaves_df=leaves)

# =========================
# 11) EMPLOYEE: Request Leave (Prevent duplicates)
# =========================
if role == "EMPLOYEE" and page == tr["request_leave"]:
    st.title(tr["request_leave"])
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    start = c1.date_input(tr["from"], value=date.today())
    end = c2.date_input(tr["to"], value=date.today())
    reason = st.text_input(tr["reason"] + " (optional)")

    if st.button(tr["submit"], use_container_width=True):
        if end < start:
            st.error("Invalid range")
        else:
            if employee_has_same_leave_request(leaves, me, start, end):
                st.warning(tr["dup_leave"])
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
                st.success(tr["sent_ok"])
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# 12) EMPLOYEE: My Courses
# =========================
if role == "EMPLOYEE" and page == tr["my_courses"]:
    st.title(tr["my_courses"])
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    if courses.empty:
        st.info("No courses yet." if st.session_state.lang == "EN" else "لا توجد كورسات حتى الآن.")
    else:
        my = courses.copy()
        my["employee_email"] = my["employee_email"].fillna("").astype(str).str.strip().str.lower()
        my = my[my["employee_email"] == me].copy()
        if my.empty:
            st.info("No assigned courses." if st.session_state.lang == "EN" else "لا توجد كورسات مسجلة لك حالياً.")
        else:
            st.dataframe(my.sort_values("due_date", na_position="last") if "due_date" in my.columns else my,
                         use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# 13) Calendar (Modern)
# =========================
def render_calendar_html(year: int, month: int, sessions_df: pd.DataFrame, leaves_df: pd.DataFrame) -> str:
    s = sessions_df.copy()
    if not s.empty:
        s["date_parsed"] = s["date"].apply(parse_date_safe)
    else:
        s["date_parsed"] = None

    month_cal = calendar.Calendar(firstweekday=6).monthdatescalendar(year, month)  # Sunday
    dow_ar = ["الأحد","الإثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت"]
    dow_en = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
    dow = dow_ar if st.session_state.lang == "AR" else dow_en

    today = date.today()

    html = "<div class='cal-wrap'>"
    html += "<div class='cal-head'>"
    html += f"<div class='cal-title'>{month_name(month)} {year}</div>"
    html += "<div class='small'>Pick a day below to see details</div>" if st.session_state.lang == "EN" else "<div class='small'>اختر يوم للتفاصيل بالأسفل</div>"
    html += "</div>"

    html += "<div class='cal-grid'>"
    for d in dow:
        html += f"<div class='cal-dow'>{d}</div>"

    for week in month_cal:
        for day in week:
            in_month = (day.month == month)
            muted = "" if in_month else " muted"
            num_class = "cal-num today" if day == today else "cal-num"

            day_sessions = s[s["date_parsed"] == day] if not s.empty else pd.DataFrame()
            unavail = unavailable_for_day(day, leaves_df)

            html += f"<div class='cal-cell{muted}'>"
            html += f"<div class='{num_class}'>{day.day}</div>"
            html += "<div class='cal-events'>"

            if not day_sessions.empty:
                for _, row in day_sessions.head(2).iterrows():
                    title = str(row.get("title","")).strip() or "Session"
                    html += f"<span class='pill' title='{title}'>{title}</span>"
                if len(day_sessions) > 2:
                    html += f"<span class='pill gray'>+{len(day_sessions)-2}</span>"

            if len(unavail) > 0:
                if len(unavail) == 1:
                    html += f"<span class='pill leave' title='Unavailable'>{unavail[0]}</span>"
                else:
                    label = f"{len(unavail)} Unavailable" if st.session_state.lang == "EN" else f"{len(unavail)} غير متواجد"
                    html += f"<span class='pill leave'>{label}</span>"

            if day_sessions.empty and len(unavail) == 0:
                html += f"<span class='pill gray'>{'None' if st.session_state.lang == 'EN' else 'لا يوجد'}</span>"

            html += "</div></div>"

    html += "</div></div>"
    return html

def calendar_page(title: str):
    st.title(title)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    colA, colB, colC = st.columns([1,1,1])
    today = date.today()
    year = colA.number_input("Year" if st.session_state.lang == "EN" else "السنة", min_value=2020, max_value=2100, value=today.year, step=1)
    month = colB.number_input("Month" if st.session_state.lang == "EN" else "الشهر", min_value=1, max_value=12, value=today.month, step=1)

    st.markdown(render_calendar_html(int(year), int(month), sessions, leaves), unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    picked_day = colC.date_input("Pick day" if st.session_state.lang == "EN" else "اختر يوم", value=today)
    st.subheader(("Details: " if st.session_state.lang == "EN" else "تفاصيل يوم: ") + picked_day.isoformat())

    day_sess = sessions.copy()
    if not day_sess.empty:
        day_sess["date_parsed"] = day_sess["date"].apply(parse_date_safe)
        day_sess = day_sess[day_sess["date_parsed"] == picked_day].drop(columns=["date_parsed"])
    else:
        day_sess = pd.DataFrame(columns=["date","title","location","room","assigned_email","duration_hours"])

    if day_sess.empty:
        st.info("No sessions." if st.session_state.lang == "EN" else "لا توجد سيشنات في هذا اليوم.")
    else:
        if role in ["LEADER","OWNER"]:
            tmp = day_sess.copy()
            tmp["assigned_email"] = tmp["assigned_email"].fillna("").astype(str).str.strip().str.lower()
            tmp["unavailable?"] = tmp["assigned_email"].apply(
                lambda e: "Yes" if (e and (e in unavailable_for_day(picked_day, leaves))) else ("No" if st.session_state.lang == "EN" else "لا")
            )
            if st.session_state.lang == "AR":
                tmp["unavailable?"] = tmp["assigned_email"].apply(lambda e: "نعم" if (e and (e in unavailable_for_day(picked_day, leaves))) else "لا")
            st.dataframe(tmp, use_container_width=True)
        else:
            st.dataframe(day_sess, use_container_width=True)

    unavail_list = unavailable_for_day(picked_day, leaves)
    if unavail_list:
        msg = ("Unavailable employees: " if st.session_state.lang == "EN" else "موظفين غير متواجدين: ") + " , ".join(unavail_list)
        st.warning(msg)
    else:
        st.success("No approved leaves affect this day." if st.session_state.lang == "EN" else "لا يوجد إجازات معتمدة تؤثر على هذا اليوم.")

    st.markdown("</div>", unsafe_allow_html=True)

# Calendar routing
if page == tr["calendar"] and role in ["OWNER","LEADER"]:
    calendar_page(tr["calendar"])
if page == tr["my_calendar"] and role == "EMPLOYEE":
    calendar_page(tr["my_calendar"])

# =========================
# Sidebar Footer
# =========================
st.sidebar.markdown("---")
st.sidebar.caption("MVP v3 • AR/EN + Clean approvals + Login/Logout toggle")

