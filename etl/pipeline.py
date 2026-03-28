"""Campus Management Report — ETL Pipeline (Supabase-safe chunked inserts)."""

import os, sys, time
from datetime import datetime, date
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import pandas as pd

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))
engine = create_engine(os.getenv('DATABASE_URL'))
CHUNK = 100

def safe_write(df, table, schema='analytics'):
    if df.empty: return
    for i in range(0, len(df), CHUNK):
        df.iloc[i:i+CHUNK].to_sql(table, engine, schema=schema, if_exists='append', index=False, method='multi')

def trunc(table):
    with engine.connect() as c: c.execute(text(f"TRUNCATE analytics.{table} RESTART IDENTITY CASCADE")); c.commit()

def log_start():
    rid = f"ETL-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    with engine.connect() as c: c.execute(text("INSERT INTO etl_run_log (run_id,start_time,status) VALUES (:r,NOW(),'running')"),{"r":rid}); c.commit()
    return rid

def log_end(rid, status, records, errors=None):
    with engine.connect() as c: c.execute(text("UPDATE etl_run_log SET end_time=NOW(),status=:s,records_processed=:r,errors=:e WHERE run_id=:rid"),{"rid":rid,"s":status,"r":records,"e":errors}); c.commit()

def build_dim_date():
    print("  Building dim_date...")
    trunc('dim_date')
    dates = pd.date_range('2020-01-01','2030-12-31')
    records = []
    for d in dates:
        m = d.month
        sem = "Semester 1" if m<=4 else ("Semester 2" if m<=8 else "Semester 3")
        ay = f"{d.year}/{d.year+1}" if m>=9 else f"{d.year-1}/{d.year}"
        records.append({"date_key":int(d.strftime('%Y%m%d')),"full_date":d.date(),"year":d.year,"month":m,
                        "month_name":d.strftime('%B'),"week":d.isocalendar()[1],"day_of_week":d.weekday(),
                        "day_name":d.strftime('%A'),"quarter":(m-1)//3+1,"semester":sem,"academic_year":ay,
                        "is_exam_period":m in [3,4,7,8,11,12],"is_weekend":d.weekday()>=5})
    df = pd.DataFrame(records)
    safe_write(df,'dim_date')
    print(f"    {len(df)} rows"); return len(df)

def build_dim_hierarchy():
    print("  Building dim_academic_hierarchy...")
    trunc('dim_academic_hierarchy')
    df = pd.read_sql("""SELECT s.school_code,s.school_name,d.dept_code,d.dept_name,p.programme_code,p.programme_name,p.level::TEXT as programme_level
        FROM school s LEFT JOIN department d ON d.school_id=s.school_id LEFT JOIN programme p ON p.dept_id=d.dept_id ORDER BY s.school_name""", engine)
    safe_write(df,'dim_academic_hierarchy')
    print(f"    {len(df)} rows"); return len(df)

def build_fact_enrollment():
    print("  Building fact_enrollment...")
    trunc('fact_enrollment')
    df = pd.read_sql("""SELECT sc.school_name,d.dept_name,p.programme_name,s.entry_year,s.admission_type::TEXT,s.gender::TEXT,s.county,
        COUNT(*) as total_enrolled, COUNT(*) FILTER(WHERE s.status='Active') as active_count,
        COUNT(*) FILTER(WHERE s.status='Graduated') as graduated_count, COUNT(*) FILTER(WHERE s.status='Deferred') as deferred_count
        FROM student s JOIN programme p ON s.programme_id=p.programme_id JOIN department d ON p.dept_id=d.dept_id JOIN school sc ON d.school_id=sc.school_id
        GROUP BY sc.school_name,d.dept_name,p.programme_name,s.entry_year,s.admission_type,s.gender,s.county""", engine)
    df['snapshot_date']=date.today()
    safe_write(df,'fact_enrollment')
    print(f"    {len(df)} rows"); return len(df)

def build_fact_performance():
    print("  Building fact_academic_performance...")
    trunc('fact_academic_performance')
    df = pd.read_sql("""SELECT cu.course_code,cu.course_name,sc.school_name,d.dept_name,
        sem.year||'/'||(sem.year+1) as academic_year, sem.term::TEXT as semester,
        COUNT(*) as total_students, ROUND(AVG(r.total_score)::NUMERIC,2) as avg_total_score,
        ROUND((COUNT(*) FILTER(WHERE r.total_score>=40)::NUMERIC/NULLIF(COUNT(*),0)*100)::NUMERIC,2) as pass_rate_pct,
        COUNT(*) FILTER(WHERE r.grade='A') as grade_a, COUNT(*) FILTER(WHERE r.grade='B') as grade_b,
        COUNT(*) FILTER(WHERE r.grade='C') as grade_c, COUNT(*) FILTER(WHERE r.grade='D') as grade_d,
        COUNT(*) FILTER(WHERE r.grade='E') as grade_e, COUNT(*) FILTER(WHERE r.grade='F') as grade_f
        FROM result r JOIN course_registration cr ON r.reg_id=cr.reg_id JOIN course_unit cu ON cr.course_id=cu.course_id
        JOIN semester sem ON cr.semester_id=sem.semester_id JOIN department d ON cu.dept_id=d.dept_id JOIN school sc ON d.school_id=sc.school_id
        GROUP BY cu.course_code,cu.course_name,sc.school_name,d.dept_name,sem.year,sem.term""", engine)
    df['snapshot_date']=date.today()
    safe_write(df,'fact_academic_performance')
    print(f"    {len(df)} rows"); return len(df)

def build_fact_revenue():
    print("  Building fact_revenue...")
    trunc('fact_revenue')
    df = pd.read_sql("""SELECT sc.school_name,d.dept_name,p.programme_name,
        pay.academic_year, 'Semester 1' as semester,
        0 as total_billed, SUM(pay.amount) as total_collected, 0 as outstanding,
        0 as collection_rate_pct, COUNT(DISTINCT pay.student_id) as student_count,
        COUNT(*) FILTER(WHERE pay.method='M-Pesa') as method_mpesa,
        COUNT(*) FILTER(WHERE pay.method='Bank Transfer') as method_bank,
        COUNT(*) FILTER(WHERE pay.method='HELB') as method_helb,
        COUNT(*) FILTER(WHERE pay.method='Cash') as method_cash,
        COUNT(*) FILTER(WHERE pay.method='Cheque') as method_cheque,
        COUNT(*) FILTER(WHERE pay.method='Bursary') as method_bursary
        FROM payment pay JOIN student s ON pay.student_id=s.student_id
        JOIN programme p ON s.programme_id=p.programme_id JOIN department d ON p.dept_id=d.dept_id JOIN school sc ON d.school_id=sc.school_id
        GROUP BY sc.school_name,d.dept_name,p.programme_name,pay.academic_year""", engine)
    df['snapshot_date']=date.today()
    safe_write(df,'fact_revenue')
    print(f"    {len(df)} rows"); return len(df)

def build_fact_staff():
    print("  Building fact_staff_summary...")
    trunc('fact_staff_summary')
    df = pd.read_sql("""SELECT sc.school_name,d.dept_name,s.role::TEXT,COUNT(*) as total_staff,
        ROUND(AVG(p.basic_salary)::NUMERIC,2) as avg_salary,
        SUM(p.net_salary) as total_payroll,
        COUNT(*) FILTER(WHERE s.role='Academic') as academic_count,
        COUNT(*) FILTER(WHERE s.role!='Academic') as admin_count
        FROM staff s JOIN department d ON s.dept_id=d.dept_id JOIN school sc ON d.school_id=sc.school_id
        LEFT JOIN (SELECT DISTINCT ON(staff_id) staff_id,basic_salary,net_salary FROM payroll ORDER BY staff_id,pay_date DESC) p ON p.staff_id=s.staff_id
        WHERE s.is_active=TRUE GROUP BY sc.school_name,d.dept_name,s.role""", engine)
    df['snapshot_date']=date.today()
    safe_write(df,'fact_staff_summary')
    print(f"    {len(df)} rows"); return len(df)

def build_fact_accommodation():
    print("  Building fact_accommodation...")
    trunc('fact_accommodation')
    df = pd.read_sql("""SELECT h.hostel_name, h.capacity as total_capacity,
        COUNT(ra.allocation_id) as allocated, h.capacity-COUNT(ra.allocation_id) as available,
        ROUND((COUNT(ra.allocation_id)::NUMERIC/NULLIF(h.capacity,0)*100)::NUMERIC,1) as occupancy_rate_pct,
        'Semester 1' as semester, '2024/2025' as academic_year
        FROM hostel h LEFT JOIN room r ON r.hostel_id=h.hostel_id LEFT JOIN room_allocation ra ON ra.room_id=r.room_id
        GROUP BY h.hostel_id,h.hostel_name,h.capacity""", engine)
    df['snapshot_date']=date.today()
    safe_write(df,'fact_accommodation')
    print(f"    {len(df)} rows"); return len(df)

def build_fact_transport():
    print("  Building fact_transport...")
    trunc('fact_transport')
    df = pd.read_sql("""SELECT v.registration_no as vehicle_reg,v.type::TEXT as vehicle_type,
        COUNT(t.trip_id) as total_trips, COALESCE(SUM(t.distance_km),0) as total_distance_km,
        COALESCE(SUM(t.fuel_litres),0) as total_fuel_litres, COALESCE(SUM(t.cost),0) as total_cost,
        EXTRACT(MONTH FROM t.trip_date)::INT as period_month, EXTRACT(YEAR FROM t.trip_date)::INT as period_year
        FROM vehicle v LEFT JOIN trip t ON t.vehicle_id=v.vehicle_id WHERE t.trip_date IS NOT NULL
        GROUP BY v.registration_no,v.type,EXTRACT(MONTH FROM t.trip_date),EXTRACT(YEAR FROM t.trip_date)""", engine)
    df['snapshot_date']=date.today()
    safe_write(df,'fact_transport')
    print(f"    {len(df)} rows"); return len(df)

def build_fact_procurement():
    print("  Building fact_procurement...")
    trunc('fact_procurement')
    df = pd.read_sql("""SELECT s.name as supplier_name, COUNT(*) as total_orders, SUM(po.total_amount) as total_value,
        COUNT(*) FILTER(WHERE po.status='Delivered') as delivered, COUNT(*) FILTER(WHERE po.status IN('Draft','Submitted','Approved')) as pending,
        COUNT(*) FILTER(WHERE po.status='Cancelled') as cancelled, EXTRACT(YEAR FROM po.order_date)::INT as period_year
        FROM purchase_order po JOIN supplier s ON po.supplier_id=s.supplier_id
        GROUP BY s.name,EXTRACT(YEAR FROM po.order_date)""", engine)
    df['snapshot_date']=date.today()
    safe_write(df,'fact_procurement')
    print(f"    {len(df)} rows"); return len(df)

def build_fact_research():
    print("  Building fact_research...")
    trunc('fact_research')
    df = pd.read_sql("""SELECT d.dept_name,
        COUNT(*) FILTER(WHERE rp.status='Active') as active_projects,
        COALESCE(SUM(rp.grant_amount),0) as total_grants,
        COALESCE(SUM(rp.amount_utilized),0) as grants_utilized,
        CASE WHEN SUM(rp.grant_amount)>0 THEN ROUND((SUM(rp.amount_utilized)/SUM(rp.grant_amount)*100)::NUMERIC,2) ELSE 0 END as utilization_pct,
        (SELECT COUNT(*) FROM publication pub WHERE pub.dept_id=d.dept_id) as total_publications
        FROM research_project rp
        JOIN department d ON rp.dept_id=d.dept_id
        GROUP BY d.dept_id, d.dept_name""", engine)
    df['snapshot_date']=date.today()
    safe_write(df,'fact_research')
    print(f"    {len(df)} rows"); return len(df)

def run_pipeline():
    print("\nCAMPUS MANAGEMENT REPORT — ETL Pipeline")
    print("="*50)
    start = time.time()
    total = 0
    rid = log_start()
    try:
        total += build_dim_date()
        total += build_dim_hierarchy()
        total += build_fact_enrollment()
        total += build_fact_performance()
        total += build_fact_revenue()
        total += build_fact_staff()
        total += build_fact_accommodation()
        total += build_fact_transport()
        total += build_fact_procurement()
        total += build_fact_research()
        elapsed = round(time.time()-start,2)
        log_end(rid,'success',total)
        print(f"\n{'='*50}")
        print(f"COMPLETE: {total:,} records in {elapsed}s")
        print(f"{'='*50}")
    except Exception as e:
        log_end(rid,'failed',total,str(e))
        print(f"\nFAILED: {e}")
        raise

if __name__ == "__main__":
    run_pipeline()
