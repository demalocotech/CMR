"""Database connection and query helpers."""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv
import pandas as pd
import streamlit as st

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))
DATABASE_URL = os.getenv('DATABASE_URL', '')
_engine = None

KENYAN_COUNTIES = [
    "Baringo","Bomet","Bungoma","Busia","Elgeyo-Marakwet","Embu","Garissa","Homa Bay",
    "Isiolo","Kajiado","Kakamega","Kericho","Kiambu","Kilifi","Kirinyaga","Kisii","Kisumu",
    "Kitui","Kwale","Laikipia","Lamu","Machakos","Makueni","Mandera","Marsabit","Meru",
    "Migori","Mombasa","Murang'a","Nairobi","Nakuru","Nandi","Narok","Nyamira","Nyandarua",
    "Nyeri","Samburu","Siaya","Taita-Taveta","Tana River","Tharaka-Nithi","Trans-Nzoia",
    "Turkana","Uasin Gishu","Vihiga","Wajir","West Pokot"
]

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, poolclass=QueuePool, pool_size=5, pool_recycle=1800)
    return _engine

def query(sql, params=None):
    with get_engine().connect() as conn:
        r = conn.execute(text(sql), params or {})
        return pd.DataFrame(r.fetchall(), columns=r.keys())

def execute(sql, params=None):
    with get_engine().connect() as conn:
        r = conn.execute(text(sql), params or {})
        conn.commit()
        try:
            row = r.fetchone()
            return str(row[0]) if row else None
        except:
            return None

@st.cache_data(ttl=300)
def test_connection():
    try:
        with get_engine().connect() as c:
            c.execute(text("SELECT 1"))
        return True
    except:
        return False

@st.cache_data(ttl=120)
def get_schools():
    return query("SELECT school_id, school_code, school_name FROM school ORDER BY school_name")

@st.cache_data(ttl=120)
def get_departments(school_id=None):
    if school_id:
        return query("SELECT dept_id, dept_code, dept_name FROM department WHERE school_id=:s ORDER BY dept_name", {"s": school_id})
    return query("SELECT dept_id, dept_code, dept_name, school_id FROM department ORDER BY dept_name")

@st.cache_data(ttl=120)
def get_programmes(dept_id=None):
    if dept_id:
        return query("SELECT programme_id, programme_code, programme_name, level, fee_per_semester FROM programme WHERE dept_id=:d ORDER BY programme_name", {"d": dept_id})
    return query("SELECT programme_id, programme_code, programme_name, dept_id FROM programme ORDER BY programme_name")

@st.cache_data(ttl=60)
def get_semesters():
    return query("SELECT semester_id, year, term, is_current FROM semester ORDER BY year DESC, term")

@st.cache_data(ttl=30)
def get_students_lookup():
    return query("SELECT student_id, admission_no, first_name || ' ' || last_name as full_name FROM student WHERE status='Active' ORDER BY last_name LIMIT 500")

def next_admission_no(year=None):
    import datetime
    year = year or datetime.datetime.now().year
    r = query("SELECT admission_no FROM student WHERE admission_no LIKE :p ORDER BY admission_no DESC LIMIT 1", {"p": f"KU/{year}/%"})
    if r.empty:
        return f"KU/{year}/00001"
    n = int(r.iloc[0]['admission_no'].split('/')[-1])
    return f"KU/{year}/{str(n+1).zfill(5)}"

@st.cache_data(ttl=30)
def metric(sql, fmt="{:,}"):
    try:
        r = query(sql)
        v = r.iloc[0][0] if not r.empty and r.iloc[0][0] is not None else 0
        num = float(v)
        if fmt == "{:,}" and num == int(num):
            return fmt.format(int(num))
        return fmt.format(num)
    except:
        return "—"
