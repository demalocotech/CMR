# Campus Management Report

Kenyatta University — Integrated Data Management and Reporting Platform

## Domains

| Domain | Tables | Key Reports |
|--------|--------|-------------|
| Student | student, next_of_kin | Enrollment, demographics, retention |
| Academic | school, department, programme, course_unit, curriculum, course_registration, result, lecturer, teaching_allocation | Results, pass rates, workload |
| Finance | fee_structure, payment, budget | Collections, budget vs actual |
| HR | staff, payroll, staff_leave | Headcount, payroll, leave |
| Accommodation | hostel, room, room_allocation | Occupancy rates |
| Transport | vehicle, driver, trip | Fleet utilisation, fuel, cost |
| Procurement | supplier, item, purchase_order, po_line, stock | Orders, stock levels |
| Research | research_project, publication | Grants, publications |

## Setup

```bash
python -m venv venv
venv\Scripts\activate.bat          # Windows
pip install -r requirements.txt

# Deploy schema to Supabase SQL Editor (in order):
#   sql/00_drop_all.sql
#   sql/01_schema.sql
#   sql/02_analytics.sql
#   sql/03_indexes_triggers.sql

python data\generate_data.py
python etl\pipeline.py
cd app && streamlit run main.py
```
