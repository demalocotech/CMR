"""
Campus Management Report
Kenyatta University — Integrated Data Management and Reporting Platform
"""

import streamlit as st
import sys, os, io, datetime
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import (test_connection, query, execute, metric, get_schools, get_departments,
                      get_programmes, get_semesters, get_students_lookup,
                      next_admission_no, KENYAN_COUNTIES)
from dashboard import render_vc_dashboard

st.set_page_config(page_title="Campus Management Report — Kenyatta University", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

# ── KU Brand Colors ────────────────────────────────────────
# Navy #1b1464 | Maroon #800020 | Green #009e49 | Gold #d4a017 | White #ffffff
# ── Styles ──────────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;0,9..40,800;1,9..40,400&display=swap" rel="stylesheet">
<style>
    /* ── DIN-style Font (DM Sans — closest Google Fonts match) ── */
    html, body, [class*="css"], .stMarkdown, .stText,
    [data-testid="stSidebar"], [data-testid="stHeader"],
    .stSelectbox, .stMultiSelect, .stTextInput, .stNumberInput,
    .stDataFrame, button, input, select, textarea, th, td, label {
        font-family: 'DM Sans', 'DIN', 'DIN Alternate', 'DIN Condensed',
                     'Helvetica Neue', Arial, sans-serif !important;
    }

    /* ── Typography Scale ──
       Headings: 14px bold | Subheadings: 12px semibold | Body: 10px regular
       (using rem: 14px=0.875rem, 12px=0.75rem, 10px=0.625rem)
    ── */

    /* Global base — 10px body text */
    html, body, [class*="css"] { font-size: 10px; }
    .stMarkdown p, .stText, .stCaption, td, label,
    div[data-testid="stForm"] label { font-size: 0.625rem; line-height: 1.5; }

    /* Streamlit widget labels — 10px */
    .stSelectbox label, .stMultiSelect label, .stTextInput label,
    .stNumberInput label, .stDateInput label, .stRadio label,
    .stCheckbox label, .stSlider label {
        font-size: 0.625rem !important; font-weight: 500;
    }

    /* Streamlit default h1/h2/h3 overrides */
    h1, .stMarkdown h1 { font-size: 0.875rem !important; font-weight: 700 !important; }
    h2, .stMarkdown h2 { font-size: 0.875rem !important; font-weight: 700 !important; }
    h3, .stMarkdown h3 { font-size: 0.75rem !important; font-weight: 600 !important; }
    h4, .stMarkdown h4 { font-size: 0.75rem !important; font-weight: 600 !important; }

    /* Table header — 10px bold */
    th { font-size: 0.625rem !important; font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.3px; }
    td { font-size: 0.625rem !important; }

    /* Buttons — 10px */
    button, .stButton > button { font-size: 0.625rem !important; font-weight: 600; }

    /* Sidebar — KU Deep Navy */
    [data-testid="stSidebar"] { background: #1b1464; }
    [data-testid="stSidebar"] * { color: #d4d0f0 !important; }
    [data-testid="stSidebar"] .stButton > button {
        background: transparent; border: none; color: #d4d0f0 !important;
        text-align: left; font-size: 0.625rem !important; padding: 0.45rem 0.8rem;
        border-radius: 4px; width: 100%;
    }
    [data-testid="stSidebar"] .stButton > button:hover { background: #2a2180; }

    /* Header bar */
    .page-bar {
        border-bottom: 2px solid #009e49; padding: 0 0 0.6rem 0; margin-bottom: 1.5rem;
    }
    .page-bar h2 { font-size: 0.875rem !important; font-weight: 700 !important; color: #1b1464; margin: 0; }
    .page-bar p { font-size: 0.625rem; color: #6b7280; margin: 0.15rem 0 0 0; }

    /* KPI tiles */
    .kpi { background: #f8f7ff; border: 1px solid #e0dff0; border-radius: 4px; padding: 0.9rem 1rem; }
    .kpi .label { font-size: 0.5625rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.6px; font-weight: 600; }
    .kpi .value { font-size: 0.875rem; font-weight: 700; color: #1b1464; line-height: 1.3; }
    .kpi .note { font-size: 0.5625rem; color: #9ca3af; }

    /* Section headers — KU Green accent */
    .sec { font-size: 0.75rem; font-weight: 700; color: #1b1464;
           border-left: 3px solid #009e49; padding-left: 0.7rem;
           margin: 1.8rem 0 0.7rem 0; text-transform: uppercase; letter-spacing: 0.4px; }

    /* Forms */
    div[data-testid="stForm"] { border: 1px solid #e0dff0; border-radius: 4px; padding: 1rem; }

    /* Streamlit accent override */
    .stButton > button[kind="primary"] { background-color: #800020; border-color: #800020; }
    .stButton > button[kind="primary"]:hover { background-color: #5e0018; border-color: #5e0018; }

    /* Tabs — 10px */
    .stTabs [data-baseweb="tab"] { font-size: 0.625rem !important; font-weight: 600; }

    /* Dataframe — override Streamlit's internal font */
    [data-testid="stDataFrame"] { font-size: 0.625rem !important; }

    /* Hide defaults */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    header[data-testid="stHeader"] { background: transparent; }
</style>
""", unsafe_allow_html=True)

# ── State & Navigation ─────────────────────────────────────
if 'page' not in st.session_state:
    st.session_state.page = 'vc_dashboard'

def nav(p):
    st.session_state.page = p
    st.rerun()

# ── Sidebar ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p style="font-size:14px;font-weight:700;color:#d4a017 !important;margin-bottom:0;">KENYATTA UNIVERSITY</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:10px;color:#a09cc0 !important;margin-top:0;">Campus Management Report</p>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<p style="font-size:9px;letter-spacing:1.2px;color:#a09cc0 !important;margin-bottom:0.3rem;font-weight:700;">OPERATIONS</p>', unsafe_allow_html=True)
    if st.button("Data Entry", key="n10", use_container_width=True): nav('entry')
    if st.button("Export Centre", key="n11", use_container_width=True): nav('export')
    if st.button("ETL Pipeline", key="n12", use_container_width=True): nav('pipeline')

    st.markdown("---")
    st.markdown('<p style="font-size:9px;letter-spacing:1.2px;color:#a09cc0 !important;margin-bottom:0.3rem;font-weight:700;">REPORTS</p>', unsafe_allow_html=True)
    if st.button("VC Dashboard", key="n0", use_container_width=True): nav('vc_dashboard')
    if st.button("Student Records", key="n2", use_container_width=True): nav('students')
    if st.button("Academic Performance", key="n3", use_container_width=True): nav('academic')
    if st.button("Financial Reports", key="n4", use_container_width=True): nav('finance')
    if st.button("Human Resources", key="n5", use_container_width=True): nav('hr')
    if st.button("Accommodation", key="n6", use_container_width=True): nav('accommodation')
    if st.button("Transport", key="n7", use_container_width=True): nav('transport')
    if st.button("Procurement", key="n8", use_container_width=True): nav('procurement')
    if st.button("Research Output", key="n9", use_container_width=True): nav('research')
    
    st.markdown("---")
    connected = False
    try: connected = test_connection()
    except: pass
    status = "Connected" if connected else "Disconnected"
    color = "#009e49" if connected else "#dc2626"
    st.markdown(f'<p style="font-size:10px;">Database: <span style="color:{color};font-weight:600;">{status}</span></p>', unsafe_allow_html=True)
    st.caption("v1.0")


# ── Helpers ─────────────────────────────────────────────────
def header(title, subtitle=""):
    st.markdown(f'<div class="page-bar"><h2>{title}</h2><p>{subtitle}</p></div>', unsafe_allow_html=True)

def kpi(label, value, note=""):
    return f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div><div class="note">{note}</div></div>'

def section(title):
    st.markdown(f'<div class="sec">{title}</div>', unsafe_allow_html=True)

@st.cache_data(ttl=30)
def cached_query(sql):
    return query(sql)

def safe_table(sql, empty_msg="No data available."):
    try:
        df = cached_query(sql)
        if not df.empty:
            fmt = {}
            for col in df.columns:
                if df[col].dtype in ('int64', 'int32'):
                    fmt[col] = "{:,}"
                elif df[col].dtype in ('float64', 'float32'):
                    # Check if values look like money (large) or percentages (small)
                    col_lower = col.lower()
                    if any(k in col_lower for k in ['kes', 'salary', 'amount', 'cost', 'budget',
                           'spent', 'variance', 'payroll', 'grant', 'utilized', 'value', 'total']):
                        fmt[col] = "KES {:,.0f}"
                    elif any(k in col_lower for k in ['pct', 'rate', 'percent', '%']):
                        fmt[col] = "{:.1f}%"
                    else:
                        fmt[col] = "{:,.1f}"
            st.dataframe(df.style.format(fmt, na_rep="—"), use_container_width=True, hide_index=True)
        else:
            st.caption(empty_msg)
    except:
        st.caption("Database connection required.")


# ============================================================
# PAGES
# ============================================================

def page_students():
    header("Student Records", "Search and view student data")
    
    c1, c2, c3 = st.columns([3, 1, 1])
    search = c1.text_input("Search", placeholder="Name or admission number")
    status_f = c2.selectbox("Status", ["All","Active","Deferred","Graduated","Suspended","Withdrawn"])
    limit = c3.number_input("Rows", 25, 500, 50, 25)
    
    where = []
    if search: where.append(f"(s.first_name||' '||s.last_name ILIKE '%{search}%' OR s.admission_no ILIKE '%{search}%')")
    if status_f != "All": where.append(f"s.status='{status_f}'")
    clause = "WHERE "+" AND ".join(where) if where else ""
    
    safe_table(f"""SELECT s.admission_no, s.first_name||' '||s.last_name as name,
        s.gender::TEXT, s.admission_type::TEXT as admission, p.programme_name as programme,
        sc.school_name as school, s.county, s.status::TEXT, s.entry_year
        FROM student s LEFT JOIN programme p ON s.programme_id=p.programme_id
        LEFT JOIN department d ON p.dept_id=d.dept_id LEFT JOIN school sc ON d.school_id=sc.school_id
        {clause} ORDER BY s.last_name LIMIT {limit}""")


def page_academic():
    header("Academic Performance", "Course registrations, examination results, and teaching workload")
    
    tab1, tab2, tab3 = st.tabs(["Registrations", "Results", "Lecturer Workload"])
    
    with tab1:
        safe_table("""SELECT cu.course_code, cu.course_name, sem.year, sem.term::TEXT as semester, COUNT(*) as registrations
            FROM course_registration cr JOIN course_unit cu ON cr.course_id=cu.course_id
            JOIN semester sem ON cr.semester_id=sem.semester_id
            GROUP BY cu.course_code, cu.course_name, sem.year, sem.term ORDER BY registrations DESC LIMIT 30""")
    with tab2:
        safe_table("""SELECT cu.course_code, cu.course_name, COUNT(*) as students,
            ROUND(AVG(r.total_score)::NUMERIC,1) as avg_score,
            ROUND((COUNT(*) FILTER(WHERE r.total_score>=40)::NUMERIC/NULLIF(COUNT(*),0)*100)::NUMERIC,1) as pass_rate_pct
            FROM result r JOIN course_registration cr ON r.reg_id=cr.reg_id
            JOIN course_unit cu ON cr.course_id=cu.course_id
            GROUP BY cu.course_code, cu.course_name ORDER BY avg_score DESC LIMIT 30""")
    with tab3:
        safe_table("""SELECT st.first_name||' '||st.last_name as lecturer,
            COUNT(DISTINCT ta.course_id) as courses, SUM(cu.credit_hours) as total_hours
            FROM teaching_allocation ta JOIN lecturer l ON ta.lecturer_id=l.lecturer_id
            JOIN staff st ON l.staff_id=st.staff_id JOIN course_unit cu ON ta.course_id=cu.course_id
            GROUP BY st.first_name, st.last_name ORDER BY total_hours DESC""")


def page_finance():
    header("Financial Reports", "Fee collection, outstanding balances, and budget analysis")
    
    c1,c2,c3 = st.columns(3)
    c1.markdown(kpi("Total Collected", "KES "+metric("SELECT COALESCE(SUM(amount),0) FROM payment")), unsafe_allow_html=True)
    c2.markdown(kpi("Transactions", metric("SELECT COUNT(*) FROM payment")), unsafe_allow_html=True)
    c3.markdown(kpi("Avg Payment", "KES "+metric("SELECT COALESCE(ROUND(AVG(amount)::NUMERIC,0),0) FROM payment")), unsafe_allow_html=True)
    
    section("Payment Method Breakdown")
    safe_table("SELECT method::TEXT, COUNT(*) as transactions, ROUND(SUM(amount)::NUMERIC,0) as total_kes FROM payment GROUP BY method ORDER BY total_kes DESC")
    
    section("Budget vs Actual Expenditure")
    safe_table("""SELECT d.dept_name as department, b.fiscal_year, 
        ROUND(b.budget_amount::NUMERIC,0) as budget, ROUND(b.actual_spent::NUMERIC,0) as spent, 
        ROUND(b.variance::NUMERIC,0) as variance
        FROM budget b JOIN department d ON b.dept_id=d.dept_id ORDER BY d.dept_name""")


def page_hr():
    header("Human Resources", "Staff establishment, payroll, and leave")
    
    c1,c2,c3 = st.columns(3)
    c1.markdown(kpi("Total Staff", metric("SELECT COUNT(*) FROM staff WHERE is_active=TRUE")), unsafe_allow_html=True)
    c2.markdown(kpi("Academic", metric("SELECT COUNT(*) FROM staff WHERE role='Academic' AND is_active=TRUE")), unsafe_allow_html=True)
    c3.markdown(kpi("Latest Payroll", "KES "+metric("SELECT COALESCE(SUM(net_salary),0) FROM payroll WHERE pay_date=(SELECT MAX(pay_date) FROM payroll)")), unsafe_allow_html=True)
    
    section("Staff by Department and Role")
    safe_table("""SELECT d.dept_name as department, s.role::TEXT, COUNT(*) as headcount
        FROM staff s JOIN department d ON s.dept_id=d.dept_id WHERE s.is_active=TRUE
        GROUP BY d.dept_name, s.role ORDER BY headcount DESC""")
    
    section("Payroll Summary")
    safe_table("""SELECT s.staff_no, s.first_name||' '||s.last_name as name, s.role::TEXT,
        p.basic_salary as salary_basic, p.allowances as salary_allowances,
        p.deductions as salary_deductions, p.net_salary as salary_net, p.pay_date
        FROM payroll p JOIN staff s ON p.staff_id=s.staff_id
        ORDER BY p.pay_date DESC, s.last_name LIMIT 50""")


def page_accommodation():
    header("Accommodation", "Hostel occupancy and room allocation")
    
    safe_table("""SELECT h.hostel_name, h.capacity as total_beds,
        COUNT(ra.allocation_id) as allocated, h.capacity-COUNT(ra.allocation_id) as available,
        ROUND((COUNT(ra.allocation_id)::NUMERIC/NULLIF(h.capacity,0)*100)::NUMERIC,1) as occupancy_pct
        FROM hostel h LEFT JOIN room r ON r.hostel_id=h.hostel_id
        LEFT JOIN room_allocation ra ON ra.room_id=r.room_id
        GROUP BY h.hostel_id, h.hostel_name, h.capacity ORDER BY h.hostel_name""")


def page_transport():
    header("Transport", "Fleet utilisation, trip logs, and fuel consumption")
    
    safe_table("""SELECT v.registration_no, v.type::TEXT, v.capacity,
        COUNT(t.trip_id) as trips, COALESCE(ROUND(SUM(t.distance_km)::NUMERIC,0),0) as total_km,
        COALESCE(ROUND(SUM(t.fuel_litres)::NUMERIC,0),0) as fuel_litres,
        COALESCE(ROUND(SUM(t.cost)::NUMERIC,0),0) as cost_kes
        FROM vehicle v LEFT JOIN trip t ON t.vehicle_id=v.vehicle_id WHERE v.is_active=TRUE
        GROUP BY v.vehicle_id, v.registration_no, v.type, v.capacity ORDER BY trips DESC""")


def page_procurement():
    header("Procurement and Inventory", "Purchase orders, supplier performance, and stock levels")
    
    tab1, tab2, tab3 = st.tabs(["Purchase Orders", "Stock Levels", "Suppliers"])
    with tab1:
        safe_table("""SELECT s.name as supplier, po.order_date, ROUND(po.total_amount::NUMERIC,0) as amount, po.status::TEXT, po.approved_by
            FROM purchase_order po JOIN supplier s ON po.supplier_id=s.supplier_id ORDER BY po.order_date DESC LIMIT 50""")
    with tab2:
        safe_table("""SELECT i.name as item, i.category, st.quantity_available as qty, st.reorder_level,
            CASE WHEN st.quantity_available<=st.reorder_level THEN 'REORDER' ELSE 'OK' END as status
            FROM stock st JOIN item i ON st.item_id=i.item_id ORDER BY st.quantity_available""")
    with tab3:
        safe_table("SELECT name, contact_person, phone, email, rating FROM supplier ORDER BY rating DESC")


def page_research():
    header("Research Output", "Projects, grants, and publications")
    
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(kpi("Projects", metric("SELECT COUNT(*) FROM research_project")), unsafe_allow_html=True)
    c2.markdown(kpi("Active", metric("SELECT COUNT(*) FROM research_project WHERE status='Active'")), unsafe_allow_html=True)
    c3.markdown(kpi("Grants", "KES "+metric("SELECT COALESCE(SUM(grant_amount),0) FROM research_project")), unsafe_allow_html=True)
    c4.markdown(kpi("Publications", metric("SELECT COUNT(*) FROM publication")), unsafe_allow_html=True)
    
    section("Research Projects")
    safe_table("""SELECT rp.title, s.first_name||' '||s.last_name as principal_investigator,
        d.dept_name as department, rp.funding_source, ROUND(rp.grant_amount::NUMERIC,0) as grant_kes,
        ROUND(rp.amount_utilized::NUMERIC,0) as utilized_kes, rp.status::TEXT
        FROM research_project rp LEFT JOIN staff s ON rp.principal_investigator=s.staff_id
        LEFT JOIN department d ON rp.dept_id=d.dept_id ORDER BY rp.start_date DESC""")
    
    section("Publications")
    safe_table("""SELECT p.title, p.authors, d.dept_name as department, p.journal, p.publication_date
        FROM publication p LEFT JOIN department d ON p.dept_id=d.dept_id ORDER BY p.publication_date DESC LIMIT 30""")


# ============================================================
# DATA ENTRY
# ============================================================
def page_entry():
    header("Data Entry", "Create records across all operational modules")
    
    module = st.selectbox("Select module", [
        "Student Admission", "Course Registration", "Fee Payment", "Exam Results",
        "Staff Record", "Payroll Entry", "Room Allocation", "Trip Log", "Purchase Order"
    ])
    
    if module == "Student Admission":
        st.markdown("**New Student Admission**")

        # Cascading dropdowns OUTSIDE form so they rerun on change
        schools = get_schools()
        sch_map = dict(zip(schools['school_name'], schools['school_id']))
        sel_sch = st.selectbox("School", [""] + list(sch_map.keys()), key="adm_school")
        dept_map, prog_map = {}, {}
        if sel_sch:
            d = get_departments(str(sch_map[sel_sch]))
            dept_map = dict(zip(d['dept_name'], d['dept_id']))
        sel_dept = st.selectbox("Department", [""] + list(dept_map.keys()), key="adm_dept")
        if sel_dept:
            p = get_programmes(str(dept_map[sel_dept]))
            prog_map = dict(zip(p['programme_name'], p['programme_id']))
        sel_prog = st.selectbox("Programme", [""] + list(prog_map.keys()), key="adm_prog")

        with st.form("f_admission"):
            c1,c2,c3 = st.columns(3)
            adm_no = c1.text_input("Admission No", value=next_admission_no(), disabled=True)
            first_name = c1.text_input("First Name")
            last_name = c2.text_input("Last Name")
            gender = c2.selectbox("Gender", ["Male","Female","Other"])
            dob = c3.date_input("Date of Birth", value=datetime.date(2000,1,1))
            phone = c3.text_input("Phone")

            c1,c2 = st.columns(2)
            email = c1.text_input("Email")
            county = c1.selectbox("Home County", [""] + KENYAN_COUNTIES)
            admission_type = c2.selectbox("Admission Type", ["Government","Self-Sponsored"])
            national_id = c2.text_input("National ID")

            if st.form_submit_button("Submit", type="primary"):
                if not all([first_name, last_name, sel_sch, sel_dept, sel_prog, county]):
                    st.error("All required fields must be completed.")
                else:
                    try:
                        execute("""INSERT INTO student (admission_no,first_name,last_name,gender,date_of_birth,phone,email,county,national_id,admission_type,programme_id,entry_year)
                            VALUES (:a,:fn,:ln,:g,:d,:ph,:em,:co,:ni,:at,:pid,:ey)""",
                            {"a":adm_no,"fn":first_name,"ln":last_name,"g":gender,"d":str(dob),"ph":phone,"em":email,
                             "co":county,"ni":national_id,"at":admission_type,"pid":str(prog_map[sel_prog]),"ey":datetime.datetime.now().year})
                        st.success(f"Student {adm_no} admitted.")
                    except Exception as e: st.error(str(e))
    
    elif module == "Course Registration":
        with st.form("f_coursereg"):
            st.markdown("**Register Student for Course**")
            students = get_students_lookup()
            s_map = dict(zip(students.apply(lambda r: f"{r['admission_no']} - {r['full_name']}", axis=1), students['student_id']))
            sel_s = st.selectbox("Student", [""] + list(s_map.keys()))
            c1,c2 = st.columns(2)
            try:
                courses = query("SELECT course_id, course_code||' - '||course_name as lbl FROM course_unit ORDER BY course_code")
                c_map = dict(zip(courses['lbl'], courses['course_id']))
            except: c_map = {}
            sel_c = c1.selectbox("Course", [""] + list(c_map.keys()))
            try:
                sems = get_semesters()
                sem_map = dict(zip(sems.apply(lambda r: f"{r['year']} {r['term']}", axis=1), sems['semester_id']))
            except: sem_map = {}
            sel_sem = c2.selectbox("Semester", [""] + list(sem_map.keys()))
            if st.form_submit_button("Register", type="primary"):
                if not all([sel_s, sel_c, sel_sem]): st.error("All fields required.")
                else:
                    try:
                        sid = str(s_map[sel_s])
                        semid = str(sem_map[sel_sem])
                        # Check fee payment before allowing registration
                        fee_check = query("""
                            SELECT COALESCE(p.fee_per_semester, 0) AS required_fee,
                                   COALESCE((SELECT SUM(py.amount) FROM payment py
                                             WHERE py.student_id = s.student_id
                                             AND py.semester_id = :sem), 0) AS paid
                            FROM student s
                            LEFT JOIN programme p ON s.programme_id = p.programme_id
                            WHERE s.student_id = :s
                        """, {"s": sid, "sem": semid})
                        cid = str(c_map[sel_c])
                        if not fee_check.empty:
                            required = float(fee_check.iloc[0]['required_fee'])
                            paid = float(fee_check.iloc[0]['paid'])
                            if required > 0 and paid < required:
                                st.error(f"Registration blocked — student has paid KES {paid:,.0f} of KES {required:,.0f} required for this semester. Please clear fees before registering units.")
                            else:
                                # Check course belongs to student's programme department/school
                                dept_check = query("""
                                    SELECT p.dept_id AS student_dept, d.school_id AS student_school,
                                           d.dept_name, sc.school_name,
                                           cu.dept_id AS course_dept
                                    FROM student s
                                    JOIN programme p ON s.programme_id = p.programme_id
                                    JOIN department d ON p.dept_id = d.dept_id
                                    JOIN school sc ON d.school_id = sc.school_id
                                    JOIN course_unit cu ON cu.course_id = :c
                                    WHERE s.student_id = :s
                                """, {"s": sid, "c": cid})
                                if not dept_check.empty:
                                    row = dept_check.iloc[0]
                                    if str(row['course_dept']) != str(row['student_dept']):
                                        st.error(f"Registration blocked — this course does not belong to the student's department ({row['dept_name']}, {row['school_name']}). Students can only register units within their programme's department.")
                                    else:
                                        execute("INSERT INTO course_registration (student_id,course_id,semester_id) VALUES (:s,:c,:sem)",
                                            {"s": sid, "c": cid, "sem": semid})
                                        st.success("Course registered.")
                                else:
                                    st.error("Could not verify student programme or course department.")
                        else:
                            st.error("Student record not found.")
                    except Exception as e: st.error(str(e))
    
    elif module == "Fee Payment":
        with st.form("f_payment"):
            st.markdown("**Record Fee Payment**")
            students = get_students_lookup()
            s_map = dict(zip(students.apply(lambda r: f"{r['admission_no']} - {r['full_name']}", axis=1), students['student_id']))
            sel_s = st.selectbox("Student", [""] + list(s_map.keys()), key="fp_s")
            c1,c2 = st.columns(2)
            amount = c1.number_input("Amount (KES)", min_value=0.0, step=1000.0)
            method = c2.selectbox("Payment Method", ["M-Pesa","Bank Transfer","HELB","Cash","Cheque","Bursary"])
            try:
                sems = get_semesters()
                sem_map_pay = dict(zip(sems.apply(lambda r: f"{r['year']} {r['term']}", axis=1), sems['semester_id']))
            except: sem_map_pay = {}
            sel_sem_pay = c1.selectbox("Semester", [""] + list(sem_map_pay.keys()), key="fp_sem")
            pay_date = c2.date_input("Date", value=datetime.date.today())
            receipt = c1.text_input("Receipt No")
            if st.form_submit_button("Record Payment", type="primary"):
                if not sel_s or amount <= 0 or not sel_sem_pay: st.error("Select student, semester, and enter valid amount.")
                else:
                    try:
                        execute("INSERT INTO payment (student_id,amount,payment_date,method,receipt_no,semester_id) VALUES (:s,:a,:d,:m,:r,:sem)",
                            {"s":str(s_map[sel_s]),"a":amount,"d":str(pay_date),"m":method,"r":receipt,"sem":str(sem_map_pay[sel_sem_pay])})
                        st.success(f"Payment of KES {amount:,.0f} recorded.")
                    except Exception as e: st.error(str(e))
    
    elif module == "Exam Results":
        with st.form("f_result"):
            st.markdown("**Enter Examination Results**")
            st.caption("Only ungraded registrations are shown.")
            try:
                regs = query("""SELECT cr.reg_id, s.admission_no||' - '||cu.course_code||' '||cu.course_name as lbl
                    FROM course_registration cr JOIN student s ON cr.student_id=s.student_id
                    JOIN course_unit cu ON cr.course_id=cu.course_id
                    LEFT JOIN result r ON r.reg_id=cr.reg_id WHERE r.result_id IS NULL ORDER BY s.admission_no LIMIT 200""")
                r_map = dict(zip(regs['lbl'], regs['reg_id']))
            except: r_map = {}
            sel_r = st.selectbox("Registration", [""] + list(r_map.keys()))
            c1,c2 = st.columns(2)
            cat = c1.number_input("CAT Score (0-30)", 0.0, 30.0, 0.0, 0.5)
            exam = c2.number_input("Exam Score (0-70)", 0.0, 70.0, 0.0, 0.5)
            total = cat + exam
            gr = "A" if total>=70 else ("B" if total>=60 else ("C" if total>=50 else ("D" if total>=40 else ("E" if total>=30 else "F"))))
            st.caption(f"Total: {total:.1f}  |  Grade: {gr}")
            if st.form_submit_button("Submit Result", type="primary"):
                if not sel_r: st.error("Select a registration.")
                else:
                    try:
                        execute("INSERT INTO result (reg_id,cat_score,exam_score,grade) VALUES (:r,:c,:e,:g)",
                            {"r":str(r_map[sel_r]),"c":cat,"e":exam,"g":gr})
                        st.success(f"Result recorded: {total:.1f} ({gr})")
                    except Exception as e: st.error(str(e))
    
    elif module == "Staff Record":
        with st.form("f_staff"):
            st.markdown("**New Staff Record**")
            c1,c2,c3 = st.columns(3)
            staff_no = c1.text_input("Staff No", placeholder="STF/0001")
            fn = c1.text_input("First Name", key="sf_fn")
            ln = c2.text_input("Last Name", key="sf_ln")
            gender = c2.selectbox("Gender", ["Male","Female","Other"], key="sf_g")
            role = c3.selectbox("Role", ["Academic","Administrative","Technical","Support"])
            emp_date = c3.date_input("Employment Date", value=datetime.date.today())
            c1,c2 = st.columns(2)
            phone = c1.text_input("Phone", key="sf_ph")
            email = c2.text_input("Email", key="sf_em")
            depts = get_departments()
            d_map = dict(zip(depts['dept_name'], depts['dept_id']))
            sel_d = st.selectbox("Department", [""] + list(d_map.keys()), key="sf_d")
            if st.form_submit_button("Add Staff", type="primary"):
                if not all([staff_no, fn, ln, sel_d]): st.error("Staff No, Name, and Department are required.")
                else:
                    try:
                        execute("""INSERT INTO staff (staff_no,first_name,last_name,gender,role,dept_id,employment_date,phone,email)
                            VALUES (:sn,:fn,:ln,:g,:r,:d,:ed,:ph,:em)""",
                            {"sn":staff_no,"fn":fn,"ln":ln,"g":gender,"r":role,"d":str(d_map[sel_d]),"ed":str(emp_date),"ph":phone,"em":email})
                        st.success(f"Staff {staff_no} added.")
                    except Exception as e: st.error(str(e))
    
    elif module == "Payroll Entry":
        with st.form("f_payroll"):
            st.markdown("**Monthly Payroll Entry**")
            try:
                stf = query("SELECT staff_id, staff_no||' - '||first_name||' '||last_name as lbl FROM staff WHERE is_active=TRUE ORDER BY last_name")
                stf_map = dict(zip(stf['lbl'], stf['staff_id']))
            except: stf_map = {}
            sel_stf = st.selectbox("Staff", [""] + list(stf_map.keys()))
            c1,c2,c3 = st.columns(3)
            basic = c1.number_input("Basic Salary", 0.0, step=1000.0)
            allow = c2.number_input("Allowances", 0.0, step=500.0)
            deduct = c3.number_input("Deductions", 0.0, step=500.0)
            st.caption(f"Net salary: KES {basic+allow-deduct:,.2f}")
            pay_date = st.date_input("Pay Date", value=datetime.date.today(), key="pr_d")
            if st.form_submit_button("Submit Payroll", type="primary"):
                if not sel_stf or basic<=0: st.error("Select staff and enter valid salary.")
                else:
                    try:
                        execute("""INSERT INTO payroll (staff_id,basic_salary,allowances,deductions,pay_date,pay_month,pay_year)
                            VALUES (:s,:b,:a,:d,:pd,:pm,:py)""",
                            {"s":str(stf_map[sel_stf]),"b":basic,"a":allow,"d":deduct,"pd":str(pay_date),"pm":pay_date.month,"py":pay_date.year})
                        st.success(f"Payroll recorded. Net: KES {basic+allow-deduct:,.2f}")
                    except Exception as e: st.error(str(e))
    
    elif module == "Room Allocation":
        with st.form("f_room"):
            st.markdown("**Allocate Hostel Room**")
            students = get_students_lookup()
            s_map = dict(zip(students.apply(lambda r: f"{r['admission_no']} - {r['full_name']}", axis=1), students['student_id']))
            sel_s = st.selectbox("Student", [""] + list(s_map.keys()), key="ra_s")
            try:
                rooms = query("SELECT r.room_id, h.hostel_name||' - '||r.room_number as lbl FROM room r JOIN hostel h ON r.hostel_id=h.hostel_id WHERE r.is_available=TRUE ORDER BY h.hostel_name")
                rm_map = dict(zip(rooms['lbl'], rooms['room_id']))
            except: rm_map = {}
            sel_rm = st.selectbox("Room", [""] + list(rm_map.keys()))
            try:
                sems = get_semesters()
                sem_map = dict(zip(sems.apply(lambda r: f"{r['year']} {r['term']}", axis=1), sems['semester_id']))
            except: sem_map = {}
            sel_sem = st.selectbox("Semester", [""] + list(sem_map.keys()), key="ra_sem")
            checkin = st.date_input("Check-in Date", value=datetime.date.today())
            if st.form_submit_button("Allocate", type="primary"):
                if not all([sel_s, sel_rm, sel_sem]): st.error("All fields required.")
                else:
                    try:
                        execute("INSERT INTO room_allocation (student_id,room_id,semester_id,check_in_date) VALUES (:s,:r,:sem,:ci)",
                            {"s":str(s_map[sel_s]),"r":str(rm_map[sel_rm]),"sem":str(sem_map[sel_sem]),"ci":str(checkin)})
                        st.success("Room allocated.")
                    except Exception as e: st.error(str(e))
    
    elif module == "Trip Log":
        with st.form("f_trip"):
            st.markdown("**Log Vehicle Trip**")
            try:
                vehs = query("SELECT vehicle_id, registration_no||' ('||type::TEXT||')' as lbl FROM vehicle WHERE is_active=TRUE")
                v_map = dict(zip(vehs['lbl'], vehs['vehicle_id']))
            except: v_map = {}
            try:
                drvs = query("SELECT d.driver_id, s.first_name||' '||s.last_name as lbl FROM driver d JOIN staff s ON d.staff_id=s.staff_id")
                dr_map = dict(zip(drvs['lbl'], drvs['driver_id']))
            except: dr_map = {}
            c1,c2 = st.columns(2)
            sel_v = c1.selectbox("Vehicle", [""] + list(v_map.keys()))
            sel_dr = c2.selectbox("Driver", [""] + list(dr_map.keys()))
            trip_date = c1.date_input("Trip Date", value=datetime.date.today())
            destination = c2.text_input("Destination")
            purpose = st.text_input("Purpose")
            c1,c2,c3 = st.columns(3)
            dist = c1.number_input("Distance (km)", 0.0, step=10.0)
            fuel = c2.number_input("Fuel (litres)", 0.0, step=5.0)
            cost = c3.number_input("Cost (KES)", 0.0, step=500.0)
            if st.form_submit_button("Log Trip", type="primary"):
                if not all([sel_v, sel_dr, destination]): st.error("Vehicle, driver, and destination are required.")
                else:
                    try:
                        execute("""INSERT INTO trip (vehicle_id,driver_id,trip_date,destination,purpose,distance_km,fuel_litres,cost)
                            VALUES (:v,:d,:td,:dest,:p,:dist,:f,:c)""",
                            {"v":str(v_map[sel_v]),"d":str(dr_map[sel_dr]),"td":str(trip_date),"dest":destination,
                             "p":purpose,"dist":dist,"f":fuel,"c":cost})
                        st.success(f"Trip logged: {destination}")
                    except Exception as e: st.error(str(e))
    
    elif module == "Purchase Order":
        with st.form("f_po"):
            st.markdown("**Create Purchase Order**")
            try:
                sups = query("SELECT supplier_id, name FROM supplier ORDER BY name")
                sup_map = dict(zip(sups['name'], sups['supplier_id']))
            except: sup_map = {}
            sel_sup = st.selectbox("Supplier", [""] + list(sup_map.keys()))
            c1,c2 = st.columns(2)
            order_date = c1.date_input("Order Date", value=datetime.date.today())
            total_amt = c2.number_input("Total Amount (KES)", 0.0, step=5000.0)
            status = st.selectbox("Status", ["Draft","Submitted","Approved"])
            approved = st.text_input("Approved By")
            if st.form_submit_button("Create Order", type="primary"):
                if not sel_sup or total_amt<=0: st.error("Select supplier and enter valid amount.")
                else:
                    try:
                        execute("""INSERT INTO purchase_order (supplier_id,order_date,total_amount,status,approved_by) VALUES (:s,:od,:t,:st,:a)""",
                            {"s":str(sup_map[sel_sup]),"od":str(order_date),"t":total_amt,"st":status,"a":approved})
                        st.success(f"Purchase order created: KES {total_amt:,.0f}")
                    except Exception as e: st.error(str(e))


# ============================================================
# EXPORT CENTRE
# ============================================================
def page_export():
    header("Export Centre", "Download data as CSV or Excel")
    
    datasets = {
        "Students": "SELECT s.admission_no,s.first_name,s.last_name,s.gender::TEXT,s.admission_type::TEXT,s.county,s.status::TEXT,s.entry_year,p.programme_name FROM student s LEFT JOIN programme p ON s.programme_id=p.programme_id ORDER BY s.last_name",
        "Exam Results": "SELECT s.admission_no,s.first_name||' '||s.last_name as student,cu.course_code,cu.course_name,r.cat_score,r.exam_score,r.total_score,r.grade FROM result r JOIN course_registration cr ON r.reg_id=cr.reg_id JOIN student s ON cr.student_id=s.student_id JOIN course_unit cu ON cr.course_id=cu.course_id",
        "Fee Payments": "SELECT s.admission_no,s.first_name||' '||s.last_name as name,p.amount,p.payment_date,p.method::TEXT,p.receipt_no FROM payment p JOIN student s ON p.student_id=s.student_id ORDER BY p.payment_date DESC",
        "Staff": "SELECT s.staff_no,s.first_name,s.last_name,s.role::TEXT,d.dept_name,s.employment_date FROM staff s LEFT JOIN department d ON s.dept_id=d.dept_id ORDER BY s.last_name",
        "Payroll": "SELECT s.staff_no,s.first_name||' '||s.last_name as name,p.basic_salary,p.allowances,p.deductions,p.net_salary,p.pay_date FROM payroll p JOIN staff s ON p.staff_id=s.staff_id ORDER BY p.pay_date DESC",
        "Accommodation": "SELECT h.hostel_name,r.room_number,s.admission_no,s.first_name||' '||s.last_name as student FROM room_allocation ra JOIN room r ON ra.room_id=r.room_id JOIN hostel h ON r.hostel_id=h.hostel_id JOIN student s ON ra.student_id=s.student_id",
        "Trip Logs": "SELECT v.registration_no,v.type::TEXT,t.trip_date,t.destination,t.purpose,t.distance_km,t.fuel_litres,t.cost FROM trip t JOIN vehicle v ON t.vehicle_id=v.vehicle_id ORDER BY t.trip_date DESC",
        "Stock Levels": "SELECT i.name,i.category,st.quantity_available,st.reorder_level FROM stock st JOIN item i ON st.item_id=i.item_id",
        "Purchase Orders": "SELECT s.name as supplier,po.order_date,po.total_amount,po.status::TEXT FROM purchase_order po JOIN supplier s ON po.supplier_id=s.supplier_id ORDER BY po.order_date DESC",
        "Research Projects": "SELECT rp.title,s.first_name||' '||s.last_name as pi,rp.funding_source,rp.grant_amount,rp.status::TEXT FROM research_project rp LEFT JOIN staff s ON rp.principal_investigator=s.staff_id",
        "Publications": "SELECT p.title,p.authors,p.journal,p.publication_date FROM publication p ORDER BY p.publication_date DESC",
        "Budgets": "SELECT d.dept_name,b.fiscal_year,b.budget_amount,b.actual_spent,b.variance FROM budget b JOIN department d ON b.dept_id=d.dept_id",
    }
    
    sel = st.selectbox("Dataset", list(datasets.keys()))
    try:
        df = query(datasets[sel] + " LIMIT 5000")
        st.caption(f"{len(df)} records")
        st.dataframe(df.head(20), use_container_width=True, hide_index=True)
        c1,c2 = st.columns(2)
        c1.download_button("Download CSV", df.to_csv(index=False), f"{sel.lower().replace(' ','_')}.csv", "text/csv", use_container_width=True)
        buf = io.BytesIO(); df.to_excel(buf, index=False, engine='openpyxl')
        c2.download_button("Download Excel", buf.getvalue(), f"{sel.lower().replace(' ','_')}.xlsx", use_container_width=True)
    except Exception as e:
        st.caption(f"Error: {e}")


# ============================================================
# ETL PIPELINE MONITOR
# ============================================================
def page_pipeline():
    header("ETL Pipeline", "Run history and analytics table status")
    
    import subprocess
    if st.button("Run Pipeline", type="primary"):
        with st.spinner("Executing..."):
            try:
                r = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__),'..','etl','pipeline.py')],
                    capture_output=True, text=True, timeout=300, cwd=os.path.join(os.path.dirname(__file__),'..'))
                if r.returncode == 0: st.success("Pipeline completed."); st.code(r.stdout)
                else: st.error("Pipeline failed."); st.code(r.stderr or r.stdout)
            except Exception as e: st.error(str(e))
    
    section("Run History")
    safe_table("SELECT run_id, start_time, end_time, status, records_processed FROM etl_run_log ORDER BY start_time DESC LIMIT 10",
               "No runs recorded. Click Run Pipeline to start.")
    
    section("Analytics Tables")
    tables = ['dim_date','dim_academic_hierarchy','fact_enrollment','fact_academic_performance',
              'fact_revenue','fact_staff_summary','fact_accommodation','fact_transport','fact_procurement','fact_research']
    rows = []
    for t in tables:
        try:
            r = query(f"SELECT COUNT(*) as n FROM analytics.{t}")
            rows.append({"table": t, "rows": int(r.iloc[0]['n']), "status": "OK" if int(r.iloc[0]['n'])>0 else "EMPTY"})
        except:
            rows.append({"table": t, "rows": 0, "status": "NOT FOUND"})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ============================================================
# ROUTING
# ============================================================
PAGES = {
    'vc_dashboard': render_vc_dashboard,
    'students': page_students, 'academic': page_academic,
    'finance': page_finance, 'hr': page_hr, 'accommodation': page_accommodation,
    'transport': page_transport, 'procurement': page_procurement, 'research': page_research,
    'entry': page_entry, 'export': page_export, 'pipeline': page_pipeline,
}
PAGES.get(st.session_state.page, render_vc_dashboard)()
