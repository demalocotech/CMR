"""
VC Executive Dashboard — Real-Time Monitoring
Campus Management Report · Kenyatta University

Aggregated institutional metrics — no individual student data.
The VC monitors the university heartbeat here; drill-downs live
in the dedicated menu pages (Students, Academic, Finance, etc.).
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from database import query, metric

# ── KU Brand Color Palette ─────────────────────────────────
COLORS = {
    "navy": "#1b1464",
    "navy_light": "#2a2180",
    "maroon": "#800020",
    "green": "#009e49",
    "gold": "#d4a017",
    "danger": "#dc2626",
    "warning": "#d97706",
    "muted": "#6b7280",
    "bg": "#f8f7ff",
    "white": "#ffffff",
    "border": "#e0dff0",
}
# Ordered palette for multi-series charts
CHART_SEQ = ["#1b1464", "#009e49", "#d4a017", "#800020", "#2a2180",
             "#0891b2", "#7c3aed", "#d97706", "#dc2626", "#065f46"]

_FONT = "DM Sans, DIN, Helvetica Neue, Arial, sans-serif"

# ── Modern Plotly Defaults ─────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=10, t=36, b=0),
    font=dict(family=_FONT, size=10, color="#374151"),
    title_font=dict(size=11, color="#1b1464", family=_FONT),
    hoverlabel=dict(bgcolor="#1b1464", font_color="#fff", font_size=10,
                    bordercolor="rgba(0,0,0,0)"),
    xaxis=dict(showgrid=False, zeroline=False, linecolor="#e5e7eb", linewidth=0.5,
               tickfont=dict(size=9, color="#6b7280")),
    yaxis=dict(showgrid=True, gridcolor="#f3f4f6", gridwidth=0.5, zeroline=False,
               linecolor="#e5e7eb", linewidth=0.5,
               tickfont=dict(size=9, color="#6b7280"),
               tickformat=","),
    legend=dict(font=dict(size=9), bgcolor="rgba(0,0,0,0)", borderwidth=0),
    bargap=0.35,
    separators=",.",
)
PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}


# ── Cached Query Helpers ───────────────────────────────────

@st.cache_data(ttl=25)
def _q(sql):
    return query(sql)

@st.cache_data(ttl=25)
def _m(sql, fmt="{:,}"):
    return metric(sql, fmt)

def _safe_int(val):
    try:
        return int(float(str(val).replace(",", "").replace("—", "0")))
    except (ValueError, TypeError):
        return 0

def _safe_float(val):
    try:
        return float(str(val).replace(",", "").replace("—", "0").replace("%", ""))
    except (ValueError, TypeError):
        return 0.0


# ── Plotly Helpers ─────────────────────────────────────────

def _fig(height=320, **kw):
    """Create a pre-configured Figure with clean layout."""
    fig = go.Figure()
    fig.update_layout(**PLOTLY_LAYOUT, height=height, **kw)
    return fig

def _show(fig, key=None):
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key=key)


# ── Dashboard Styles ───────────────────────────────────────

DASHBOARD_CSS = """
<style>
    .dash-header {
        background: linear-gradient(135deg, #1b1464 0%, #2a2180 50%, #800020 100%);
        color: white; padding: 1.2rem 1.5rem; border-radius: 10px;
        margin-bottom: 1.5rem; border-bottom: 3px solid #d4a017;
    }
    .dash-header h1 { font-size: 14px; font-weight: 700; margin: 0; color: #d4a017; }
    .dash-header p { font-size: 10px; color: #c4c0e0; margin: 0.25rem 0 0 0; }
    .dash-header .live-dot {
        display: inline-block; width: 8px; height: 8px; border-radius: 50%;
        background: #009e49; margin-right: 6px; animation: pulse 2s infinite;
    }
    @keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.4;} }

    .kpi-card {
        background: #ffffff; border: 1px solid #e0dff0; border-radius: 10px;
        padding: 0.9rem 1rem; box-shadow: 0 1px 4px rgba(27,20,100,0.05);
        transition: all 0.2s ease; border-left: 3px solid #1b1464;
    }
    .kpi-card:hover { box-shadow: 0 6px 16px rgba(27,20,100,0.10); transform: translateY(-1px); }
    .kpi-card .kpi-label {
        font-size: 9px; color: #6b7280; text-transform: uppercase;
        letter-spacing: 0.8px; font-weight: 700; margin-bottom: 0.25rem;
    }
    .kpi-card .kpi-value { font-size: 14px; font-weight: 800; color: #1b1464; line-height: 1.2; }
    .kpi-card .kpi-delta { font-size: 10px; font-weight: 600; margin-top: 0.15rem; }
    .kpi-card .kpi-delta.up { color: #009e49; }
    .kpi-card .kpi-delta.down { color: #800020; }
    .kpi-card .kpi-note { font-size: 9px; color: #9ca3af; margin-top: 0.1rem; }

    .dash-section {
        font-size: 11px; font-weight: 700; color: #1b1464;
        border-left: 3px solid #009e49; padding-left: 0.7rem;
        margin: 1.8rem 0 0.7rem 0; text-transform: uppercase; letter-spacing: 0.5px;
    }

    .summary-counter {
        text-align: center; padding: 0.55rem 0.4rem;
        background: #f8f7ff; border-radius: 8px; border: 1px solid #e0dff0;
        border-left: 3px solid #d4a017;
    }
    .summary-counter .count-val { font-size: 14px; font-weight: 800; color: #1b1464; }
    .summary-counter .count-label { font-size: 9px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; }
</style>
"""


# ── KPI Card Builder ───────────────────────────────────────

def kpi_card(label, value, delta=None, delta_label="", note="", invert=False):
    delta_html = ""
    if delta is not None:
        try:
            d = float(str(delta).replace(",", "").replace("%", "").replace("+", ""))
            if d > 0:
                cls = "down" if invert else "up"
                arrow = "&#9650;" if not invert else "&#9660;"
                delta_html = f'<div class="kpi-delta {cls}">{arrow} +{delta} {delta_label}</div>'
            elif d < 0:
                cls = "up" if invert else "down"
                arrow = "&#9660;" if not invert else "&#9650;"
                delta_html = f'<div class="kpi-delta {cls}">{arrow} {delta} {delta_label}</div>'
            else:
                delta_html = '<div class="kpi-delta" style="color:#6b7280;">— No change</div>'
        except (ValueError, TypeError):
            delta_html = ""
    note_html = f'<div class="kpi-note">{note}</div>' if note else ""
    return f"""<div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}{note_html}
    </div>"""


# ════════════════════════════════════════════════════════════
# SECTION RENDERERS
# ════════════════════════════════════════════════════════════

def _render_kpis():
    c1, c2, c3, c4, c5 = st.columns(5)

    rev_total = _m("SELECT COALESCE(ROUND(SUM(amount)),0) FROM payment")
    c1.markdown(kpi_card("Total Revenue", f"KES {rev_total}", note="All collections"), unsafe_allow_html=True)

    payroll_cost = _m("SELECT COALESCE(ROUND(SUM(net_salary)),0) FROM payroll")
    transport_cost = _m("SELECT COALESCE(ROUND(SUM(cost)),0) FROM trip")
    procurement_cost = _m("SELECT COALESCE(ROUND(SUM(total_amount)),0) FROM purchase_order WHERE status='Delivered'")
    total_cost = _safe_int(payroll_cost) + _safe_int(transport_cost) + _safe_int(procurement_cost)
    c2.markdown(kpi_card("Total Expenditure", f"KES {total_cost:,}", note="Payroll + Transport + Procurement"), unsafe_allow_html=True)

    net = _safe_int(rev_total) - total_cost
    c3.markdown(kpi_card("Net Position", f"KES {net:,}", note="Revenue minus Expenditure"), unsafe_allow_html=True)

    students = _m("SELECT COUNT(*) FROM student WHERE status='Active'")
    total_students = _m("SELECT COUNT(*) FROM student")
    c4.markdown(kpi_card("Active Students", students, note=f"{total_students} total enrolled"), unsafe_allow_html=True)

    staff = _m("SELECT COUNT(*) FROM staff WHERE is_active=TRUE")
    schools_count = _m("SELECT COUNT(*) FROM school")
    depts_count = _m("SELECT COUNT(*) FROM department")
    programmes_count = _m("SELECT COUNT(*) FROM programme")
    c5.markdown(kpi_card("Staff", staff, note=f"{schools_count} Schools · {depts_count} Depts · {programmes_count} Programmes"), unsafe_allow_html=True)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)

    monthly_payroll = _m("""
        SELECT COALESCE(ROUND(SUM(net_salary)),0) FROM payroll
        WHERE pay_month=EXTRACT(MONTH FROM CURRENT_DATE)
        AND pay_year=EXTRACT(YEAR FROM CURRENT_DATE)
    """)
    c1.markdown(kpi_card("Monthly Payroll", f"KES {monthly_payroll}", note="Current month"), unsafe_allow_html=True)

    pass_rate = _m("SELECT COALESCE(ROUND(AVG(pass_rate_pct),1),0) FROM analytics.fact_academic_performance", fmt="{:.1f}")
    c2.markdown(kpi_card("Avg Pass Rate", f"{pass_rate}%", note="Across all schools"), unsafe_allow_html=True)

    occ = _m("SELECT COALESCE(ROUND(AVG(occupancy_rate_pct),1),0) FROM analytics.fact_accommodation", fmt="{:.1f}")
    hostel_beds = _m("SELECT COALESCE(SUM(capacity),0) FROM hostel")
    c3.markdown(kpi_card("Hostel Occupancy", f"{occ}%", note=f"{hostel_beds} total bed capacity"), unsafe_allow_html=True)

    trips_month = _m("""
        SELECT COUNT(*) FROM trip
        WHERE EXTRACT(MONTH FROM trip_date)=EXTRACT(MONTH FROM CURRENT_DATE)
        AND EXTRACT(YEAR FROM trip_date)=EXTRACT(YEAR FROM CURRENT_DATE)
    """)
    fleet_cost_month = _m("""
        SELECT COALESCE(ROUND(SUM(cost)),0) FROM trip
        WHERE EXTRACT(MONTH FROM trip_date)=EXTRACT(MONTH FROM CURRENT_DATE)
        AND EXTRACT(YEAR FROM trip_date)=EXTRACT(YEAR FROM CURRENT_DATE)
    """)
    c4.markdown(kpi_card("Fleet Trips", trips_month, note=f"KES {fleet_cost_month} cost this month"), unsafe_allow_html=True)

    research = _m("SELECT COUNT(*) FROM research_project WHERE status='Active'")
    grants = _m("SELECT COALESCE(ROUND(SUM(grant_amount)),0) FROM research_project WHERE status='Active'")
    c5.markdown(kpi_card("Research Projects", research, note=f"KES {grants} in grants"), unsafe_allow_html=True)


def _render_live_counters():
    st.markdown('<div class="dash-section">Live Pulse — Today\'s Activity</div>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    today_admissions = _m("SELECT COUNT(*) FROM student WHERE created_at::DATE = CURRENT_DATE")
    today_payments = _m("SELECT COUNT(*) FROM payment WHERE created_at::DATE = CURRENT_DATE")
    today_revenue = _m("SELECT COALESCE(ROUND(SUM(amount)),0) FROM payment WHERE created_at::DATE = CURRENT_DATE")
    today_results = _m("SELECT COUNT(*) FROM result WHERE created_at::DATE = CURRENT_DATE")
    today_pos = _m("SELECT COUNT(*) FROM purchase_order WHERE created_at::DATE = CURRENT_DATE")

    for col, val, label in [
        (c1, today_admissions, "New Admissions Today"),
        (c2, today_payments, "Payments Today"),
        (c3, f"KES {today_revenue}", "Revenue Today"),
        (c4, today_results, "Results Posted Today"),
        (c5, today_pos, "Purchase Orders Today"),
    ]:
        col.markdown(f"""<div class="summary-counter">
            <div class="count-val">{val}</div>
            <div class="count-label">{label}</div>
        </div>""", unsafe_allow_html=True)


def _render_revenue_vs_cost():
    st.markdown('<div class="dash-section">Financial Overview — Revenue vs Expenditure</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([3, 2])

    with c1:
        df = _q("""
            SELECT EXTRACT(YEAR FROM payment_date)::INT as year,
                   EXTRACT(MONTH FROM payment_date)::INT as month,
                   SUM(amount) as revenue
            FROM payment GROUP BY year, month ORDER BY year, month
        """)
        if not df.empty:
            fig = _fig(350, title="Monthly Revenue vs Payroll Cost")
            for i, yr in enumerate(sorted(df["year"].unique())):
                sub = df[df["year"] == yr]
                fig.add_trace(go.Scatter(
                    x=sub["month"], y=sub["revenue"],
                    mode="lines+markers", name=f"Revenue {int(yr)}",
                    line=dict(width=2.5, color=CHART_SEQ[i % len(CHART_SEQ)],
                              shape="spline", smoothing=1.2),
                    marker=dict(size=5, symbol="circle"),
                    fill="tozeroy" if i == 0 else None,
                    fillcolor=f"rgba(27,20,100,0.06)" if i == 0 else None,
                ))
            df_pay = _q("""
                SELECT pay_year as year, pay_month as month, SUM(net_salary) as cost
                FROM payroll WHERE pay_year IS NOT NULL AND pay_month IS NOT NULL
                GROUP BY pay_year, pay_month ORDER BY pay_year, pay_month
            """)
            if not df_pay.empty:
                for i, yr in enumerate(sorted(df_pay["year"].unique())):
                    sub = df_pay[df_pay["year"] == yr]
                    fig.add_trace(go.Scatter(
                        x=sub["month"], y=sub["cost"],
                        mode="lines+markers", name=f"Payroll {int(yr)}",
                        line=dict(width=2, dash="dot", color=COLORS["maroon"],
                                  shape="spline", smoothing=1.2),
                        marker=dict(size=4, symbol="diamond"),
                    ))
            fig.update_layout(
                xaxis=dict(title="Month", dtick=1, tickmode="linear",
                           showgrid=False, linecolor="#e5e7eb"),
                yaxis=dict(title="KES", showgrid=True, gridcolor="#f3f4f6"),
                legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
            )
            _show(fig)
        else:
            st.caption("No payment data available.")

    with c2:
        payroll_val = _safe_int(_m("SELECT COALESCE(SUM(net_salary),0) FROM payroll"))
        transport_val = _safe_int(_m("SELECT COALESCE(SUM(cost),0) FROM trip"))
        procurement_val = _safe_int(_m("SELECT COALESCE(SUM(total_amount),0) FROM purchase_order WHERE status='Delivered'"))
        budget_spent = _safe_int(_m("SELECT COALESCE(SUM(actual_spent),0) FROM budget"))

        labels, values, colors = [], [], []
        for lbl, val, clr in [
            ("Payroll", payroll_val, COLORS["maroon"]),
            ("Transport", transport_val, COLORS["gold"]),
            ("Procurement", procurement_val, COLORS["navy"]),
            ("Dept Budgets", budget_spent, COLORS["green"]),
        ]:
            if val > 0:
                labels.append(lbl); values.append(val); colors.append(clr)

        if values:
            fig = _fig(350, title="Expenditure Breakdown")
            fig.add_trace(go.Pie(
                labels=labels, values=values, hole=0.6,
                textinfo="label+percent", textposition="outside",
                textfont=dict(size=9),
                marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
                pull=[0.03] * len(values),
            ))
            fig.update_layout(showlegend=False)
            _show(fig)
        else:
            st.caption("No expenditure data available.")

    # Revenue by school + payment method
    df = _q("""
        SELECT sc.school_name as school, SUM(p.amount) as revenue
        FROM payment p
        JOIN student s ON p.student_id=s.student_id
        JOIN programme pr ON s.programme_id=pr.programme_id
        JOIN department d ON pr.dept_id=d.dept_id
        JOIN school sc ON d.school_id=sc.school_id
        GROUP BY sc.school_name ORDER BY revenue DESC
    """)
    if not df.empty:
        c1, c2 = st.columns([3, 2])
        with c1:
            fig = _fig(max(240, len(df) * 42), title="Revenue by School")
            fig.add_trace(go.Bar(
                y=df["school"], x=df["revenue"], orientation="h",
                marker=dict(color=COLORS["navy"], cornerradius=4),
                text=df["revenue"].apply(lambda v: f"KES {v:,.0f}"),
                textposition="outside", textfont=dict(size=9),
            ))
            fig.update_layout(
                yaxis=dict(autorange="reversed", showgrid=False),
                xaxis=dict(title="KES", showgrid=True, gridcolor="#f3f4f6"),
            )
            _show(fig)

        with c2:
            df_method = _q("""
                SELECT method::TEXT as method, SUM(amount) as total
                FROM payment GROUP BY method ORDER BY total DESC
            """)
            if not df_method.empty:
                fig = _fig(max(240, len(df) * 42), title="Revenue by Payment Method")
                fig.add_trace(go.Pie(
                    labels=df_method["method"], values=df_method["total"],
                    hole=0.6, textinfo="label+percent", textposition="outside",
                    textfont=dict(size=9),
                    marker=dict(colors=CHART_SEQ[:len(df_method)],
                                line=dict(color="#ffffff", width=2)),
                ))
                fig.update_layout(showlegend=False)
                _show(fig)


def _render_enrollment():
    st.markdown('<div class="dash-section">Enrollment Analytics</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        df = _q("""
            SELECT entry_year as year, COUNT(*) as students,
                   SUM(CASE WHEN status='Active' THEN 1 ELSE 0 END) as active,
                   SUM(CASE WHEN status='Graduated' THEN 1 ELSE 0 END) as graduated
            FROM student WHERE entry_year IS NOT NULL
            GROUP BY entry_year ORDER BY entry_year
        """)
        if not df.empty:
            fig = _fig(340, title="Enrollment Trend by Year")
            fig.add_trace(go.Bar(
                x=df["year"], y=df["students"], name="Total",
                marker=dict(color="rgba(27,20,100,0.15)", cornerradius=4),
            ))
            fig.add_trace(go.Scatter(
                x=df["year"], y=df["active"], name="Active",
                mode="lines+markers",
                line=dict(color=COLORS["green"], width=2.5, shape="spline", smoothing=1.2),
                marker=dict(size=6, color=COLORS["green"]),
            ))
            fig.add_trace(go.Scatter(
                x=df["year"], y=df["graduated"], name="Graduated",
                mode="lines+markers",
                line=dict(color=COLORS["gold"], width=2, dash="dot", shape="spline", smoothing=1.2),
                marker=dict(size=5, symbol="diamond", color=COLORS["gold"]),
            ))
            fig.update_layout(
                barmode="overlay",
                xaxis=dict(title="Entry Year", dtick=1),
                yaxis=dict(title="Students"),
                legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
            )
            _show(fig)

    with c2:
        df = _q("""
            SELECT sc.school_name as school, d.dept_name as department, COUNT(*) as students
            FROM student s
            JOIN programme p ON s.programme_id=p.programme_id
            JOIN department d ON p.dept_id=d.dept_id
            JOIN school sc ON d.school_id=sc.school_id
            WHERE s.status='Active'
            GROUP BY sc.school_name, d.dept_name
        """)
        if not df.empty:
            fig = px.treemap(
                df, path=["school", "department"], values="students",
                color="students",
                color_continuous_scale=[[0, "rgba(27,20,100,0.08)"], [1, "#1b1464"]],
                title="Active Students — School / Department",
            )
            fig.update_layout(**PLOTLY_LAYOUT, height=340, coloraxis_showscale=False)
            fig.update_traces(
                textinfo="label+value", textfont=dict(size=10),
                marker=dict(cornerradius=4),
            )
            _show(fig)

    c1, c2 = st.columns(2)
    with c1:
        df = _q("SELECT gender::TEXT as gender, COUNT(*) as count FROM student WHERE status='Active' GROUP BY gender")
        if not df.empty:
            fig = _fig(270, title="Gender Distribution")
            fig.add_trace(go.Pie(
                labels=df["gender"], values=df["count"], hole=0.6,
                marker=dict(colors=[COLORS["navy"], COLORS["maroon"], COLORS["muted"]],
                            line=dict(color="#ffffff", width=2)),
                textinfo="label+percent+value", textfont=dict(size=9),
            ))
            fig.update_layout(showlegend=False)
            _show(fig)

    with c2:
        df = _q("SELECT admission_type::TEXT as type, COUNT(*) as count FROM student WHERE status='Active' GROUP BY admission_type")
        if not df.empty:
            fig = _fig(270, title="Admission Type")
            fig.add_trace(go.Pie(
                labels=df["type"], values=df["count"], hole=0.6,
                marker=dict(colors=[COLORS["green"], COLORS["gold"]],
                            line=dict(color="#ffffff", width=2)),
                textinfo="label+percent+value", textfont=dict(size=9),
            ))
            fig.update_layout(showlegend=False)
            _show(fig)

    # Programme Performance Table
    st.markdown('<div class="dash-section">Programme Performance by Enrollment</div>', unsafe_allow_html=True)

    df = _q("""
        SELECT sc.school_name as "School",
               p.programme_name as "Programme",
               p.level::TEXT as "Level",
               COUNT(*) as "Total Enrolled",
               SUM(CASE WHEN s.status='Active' THEN 1 ELSE 0 END) as "Active",
               SUM(CASE WHEN s.status='Graduated' THEN 1 ELSE 0 END) as "Graduated",
               SUM(CASE WHEN s.status='Deferred' THEN 1 ELSE 0 END) as "Deferred",
               SUM(CASE WHEN s.status IN ('Suspended','Withdrawn') THEN 1 ELSE 0 END) as "Attrition"
        FROM student s
        JOIN programme p ON s.programme_id=p.programme_id
        JOIN department d ON p.dept_id=d.dept_id
        JOIN school sc ON d.school_id=sc.school_id
        GROUP BY sc.school_name, p.programme_name, p.level
        ORDER BY "Total Enrolled" DESC
    """)
    if not df.empty:
        schools = ["All Schools"] + sorted(df["School"].unique().tolist())
        sel_school_prog = st.selectbox("Filter by School", schools, key="prog_school_filter")
        if sel_school_prog != "All Schools":
            df = df[df["School"] == sel_school_prog]

        df["Retention %"] = ((df["Active"] + df["Graduated"]) / df["Total Enrolled"] * 100).round(1)
        st.dataframe(
            df.style.format({
                "Total Enrolled": "{:,}", "Active": "{:,}", "Graduated": "{:,}",
                "Deferred": "{:,}", "Attrition": "{:,}", "Retention %": "{:.1f}%",
            }, na_rep="—"),
            use_container_width=True, hide_index=True, height=400,
        )
    else:
        st.caption("No enrollment data available.")


def _render_academic():
    st.markdown('<div class="dash-section">Academic Performance by School</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    schools_list = _q("SELECT DISTINCT school_name FROM analytics.fact_academic_performance ORDER BY school_name")
    school_options = ["All Schools"] + (schools_list["school_name"].tolist() if not schools_list.empty else [])
    sel_school = c1.selectbox("School", school_options, key="acad_school_filter")

    courses_q = "SELECT DISTINCT course_name FROM analytics.fact_academic_performance"
    if sel_school != "All Schools":
        courses_q += f" WHERE school_name='{sel_school}'"
    courses_q += " ORDER BY course_name"
    courses_list = _q(courses_q)
    course_options = ["All Courses"] + (courses_list["course_name"].tolist() if not courses_list.empty else [])
    sel_course = c2.selectbox("Course", course_options, key="acad_course_filter")

    where_clauses = []
    if sel_school != "All Schools":
        where_clauses.append(f"school_name='{sel_school}'")
    if sel_course != "All Courses":
        where_clauses.append(f"course_name='{sel_course}'")
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    df = _q(f"""
        SELECT school_name as "School",
               COUNT(DISTINCT course_code) as "Courses",
               SUM(total_students) as "Students Examined",
               ROUND(AVG(avg_total_score),1) as "Avg Score",
               ROUND(AVG(pass_rate_pct),1) as "Pass Rate %",
               SUM(grade_a) as "A", SUM(grade_b) as "B", SUM(grade_c) as "C",
               SUM(grade_d) as "D", SUM(grade_e) as "E", SUM(grade_f) as "F"
        FROM analytics.fact_academic_performance
        {where_sql}
        GROUP BY school_name ORDER BY "Pass Rate %" DESC
    """)

    if not df.empty:
        def pass_rate_indicator(val):
            if val >= 70: return f"🟢 {val}%"
            elif val >= 50: return f"🟡 {val}%"
            else: return f"🔴 {val}%"

        df["Status"] = df["Pass Rate %"].apply(pass_rate_indicator)
        display_cols = ["School", "Status", "Courses", "Students Examined", "Avg Score",
                        "A", "B", "C", "D", "E", "F"]
        st.dataframe(
            df[display_cols].style.format({
                "Courses": "{:,}", "Students Examined": "{:,}", "Avg Score": "{:.1f}",
                "A": "{:,}", "B": "{:,}", "C": "{:,}", "D": "{:,}", "E": "{:,}", "F": "{:,}",
            }, na_rep="—"),
            use_container_width=True, hide_index=True,
            height=min(400, 50 + len(df) * 40),
        )

        c1, c2 = st.columns(2)
        with c1:
            colors = df["Pass Rate %"].apply(
                lambda v: COLORS["green"] if v >= 70 else (COLORS["gold"] if v >= 50 else COLORS["maroon"])
            ).tolist()
            fig = _fig(max(240, len(df) * 46), title="Pass Rate by School")
            fig.add_trace(go.Bar(
                y=df["School"], x=df["Pass Rate %"], orientation="h",
                marker=dict(color=colors, cornerradius=4,
                            line=dict(color="#ffffff", width=0.5)),
                text=df["Pass Rate %"].apply(lambda v: f"{v}%"),
                textposition="outside", textfont=dict(size=9),
            ))
            fig.update_layout(
                yaxis=dict(autorange="reversed", showgrid=False),
                xaxis=dict(range=[0, 105], title="%", showgrid=True, gridcolor="#f3f4f6"),
            )
            _show(fig)

        with c2:
            grade_colors = {"A": "#009e49", "B": "#34d399", "C": "#d4a017",
                            "D": "#d97706", "E": "#800020", "F": "#dc2626"}
            fig = _fig(max(240, len(df) * 46), title="Grade Distribution by School")
            for grade in ["A", "B", "C", "D", "E", "F"]:
                fig.add_trace(go.Bar(
                    y=df["School"], x=df[grade], name=grade, orientation="h",
                    marker=dict(color=grade_colors[grade], cornerradius=2),
                ))
            fig.update_layout(
                barmode="stack", bargap=0.25,
                yaxis=dict(autorange="reversed", showgrid=False),
                xaxis=dict(title="Students", showgrid=True, gridcolor="#f3f4f6"),
                legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
            )
            _show(fig)
    else:
        st.caption("Run ETL pipeline to generate academic analytics.")


def _render_operations():
    st.markdown('<div class="dash-section">Operational Health</div>', unsafe_allow_html=True)

    # Hostel occupancy — modern semi-circle gauges
    df = _q("""
        SELECT hostel_name, total_capacity, allocated, occupancy_rate_pct
        FROM analytics.fact_accommodation ORDER BY hostel_name
    """)
    if not df.empty:
        cols_per_row = min(len(df), 4)
        cols = st.columns(cols_per_row)
        for i, row in df.iterrows():
            with cols[i % cols_per_row]:
                rate = float(row["occupancy_rate_pct"]) if row["occupancy_rate_pct"] else 0
                bar_color = COLORS["green"] if rate < 80 else (COLORS["gold"] if rate < 95 else COLORS["maroon"])
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=rate,
                    number={"suffix": "%", "font": {"size": 22, "color": COLORS["navy"]}},
                    title={"text": row["hostel_name"], "font": {"size": 10, "color": COLORS["muted"]}},
                    gauge=dict(
                        axis=dict(range=[0, 100], tickfont=dict(size=8, color="#9ca3af"),
                                  tickcolor="#e5e7eb"),
                        bar=dict(color=bar_color, thickness=0.7),
                        bgcolor="#f8f7ff",
                        borderwidth=0,
                        steps=[
                            dict(range=[0, 70], color="rgba(0,158,73,0.06)"),
                            dict(range=[70, 90], color="rgba(212,160,23,0.08)"),
                            dict(range=[90, 100], color="rgba(128,0,32,0.08)"),
                        ],
                    ),
                ))
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    height=170, margin=dict(l=15, r=15, t=40, b=5),
                    font=dict(family=_FONT),
                )
                _show(fig)
    else:
        st.caption("Run ETL pipeline to generate accommodation analytics.")

    c1, c2 = st.columns(2)

    with c1:
        df = _q("""
            SELECT v.type::TEXT as vehicle_type, COUNT(t.trip_id) as trips,
                   COALESCE(SUM(t.distance_km),0) as distance_km,
                   COALESCE(SUM(t.fuel_litres),0) as fuel_litres,
                   COALESCE(SUM(t.cost),0) as total_cost
            FROM trip t JOIN vehicle v ON t.vehicle_id=v.vehicle_id
            GROUP BY v.type ORDER BY total_cost DESC
        """)
        if not df.empty:
            fig = _fig(290, title="Fleet: Cost & Trips by Type")
            fig.add_trace(go.Bar(
                x=df["vehicle_type"], y=df["total_cost"], name="Cost (KES)",
                marker=dict(color=COLORS["maroon"], cornerradius=4),
                text=df["total_cost"].apply(lambda v: f"{v:,.0f}"),
                textposition="outside", textfont=dict(size=8),
            ))
            fig.add_trace(go.Scatter(
                x=df["vehicle_type"], y=df["trips"], name="Trips", yaxis="y2",
                mode="lines+markers",
                line=dict(color=COLORS["navy"], width=2.5),
                marker=dict(size=7, color=COLORS["navy"]),
            ))
            fig.update_layout(
                yaxis=dict(title="KES", showgrid=True, gridcolor="#f3f4f6"),
                yaxis2=dict(title="Trips", overlaying="y", side="right",
                            showgrid=False, tickfont=dict(size=9, color="#6b7280")),
                legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
                bargap=0.4,
            )
            _show(fig)

    with c2:
        df = _q("""
            SELECT status::TEXT as status, COUNT(*) as count,
                   COALESCE(SUM(total_amount),0) as value
            FROM purchase_order GROUP BY status ORDER BY count DESC
        """)
        if not df.empty:
            status_colors = {
                "Draft": "#9ca3af", "Submitted": COLORS["navy"],
                "Approved": COLORS["gold"], "Delivered": COLORS["green"],
                "Cancelled": COLORS["maroon"],
            }
            colors = [status_colors.get(s, "#6b7280") for s in df["status"]]
            fig = _fig(290, title="Procurement by Status (Value)")
            fig.add_trace(go.Bar(
                x=df["status"], y=df["value"],
                marker=dict(color=colors, cornerradius=4),
                text=df["value"].apply(lambda v: f"KES {v:,.0f}"),
                textposition="outside", textfont=dict(size=8),
            ))
            fig.update_layout(
                xaxis=dict(title="Status"), yaxis=dict(title="KES"),
                bargap=0.4,
            )
            _show(fig)


# ════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ════════════════════════════════════════════════════════════

@st.fragment(run_every=timedelta(seconds=30))
def _live_dashboard():
    now = datetime.now().strftime("%H:%M:%S")

    st.markdown(f"""<div class="dash-header">
        <h1>Vice-Chancellor's Dashboard</h1>
        <p><span class="live-dot"></span>LIVE &nbsp;&middot;&nbsp; Kenyatta University &nbsp;&middot;&nbsp;
        Last updated: {now}</p>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("Refresh Now", key="dash_refresh", use_container_width=True):
            st.cache_data.clear()

    for section_fn, label in [
        (_render_kpis, "KPI"),
        (_render_live_counters, "Live counters"),
        (_render_revenue_vs_cost, "Financial"),
        (_render_enrollment, "Enrollment"),
        (_render_academic, "Academic"),
        (_render_operations, "Operations"),
    ]:
        try:
            section_fn()
        except Exception as e:
            st.warning(f"{label} section unavailable: {e}")


def render_vc_dashboard():
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)
    _live_dashboard()
