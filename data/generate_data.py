"""
Campus Management Report — Sample Data Generator
Populates all 9 domains with realistic KU data using batch inserts.
"""

import os, sys, random, uuid
from datetime import date, timedelta
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import pandas as pd

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))
engine = create_engine(os.getenv('DATABASE_URL'))
CHUNK = 100

def w(df, table):
    for i in range(0, len(df), CHUNK):
        df.iloc[i:i+CHUNK].to_sql(table, engine, if_exists='append', index=False, method='multi')

COUNTIES = ["Nairobi","Kiambu","Nakuru","Mombasa","Kisumu","Meru","Uasin Gishu","Machakos","Nyeri","Kilifi",
            "Kakamega","Bungoma","Embu","Kitui","Siaya","Homa Bay","Bomet","Kericho","Nandi","Kajiado"]
MALE = ["James","John","Peter","David","Joseph","Daniel","Samuel","Michael","Brian","Kevin","George","Patrick","Collins","Dennis"]
FEMALE = ["Mary","Jane","Grace","Faith","Joy","Mercy","Esther","Ruth","Sarah","Gladys","Ann","Lucy","Wanjiku","Njeri"]
SURNAMES = ["Mwangi","Kamau","Ochieng","Kiplagat","Mutua","Wanyama","Njoroge","Otieno","Korir","Kiptoo",
            "Wafula","Kariuki","Kibet","Maina","Gitau","Mugo","Kimani","Ndirangu","Rotich","Omolo"]

KU = {
    "School of Computing & Informatics": {"code":"SCI","depts":{"Computer Science":{"code":"CS","progs":[("BSc Computer Science","Bachelors",4,72000),("MSc Computer Science","Masters",2,95000)]},"Information Technology":{"code":"IT","progs":[("BSc Information Technology","Bachelors",4,72000)]}}},
    "School of Business": {"code":"SOB","depts":{"Accounting & Finance":{"code":"AF","progs":[("BCom Accounting","Bachelors",4,68000),("MBA Finance","Masters",2,120000)]},"Business Administration":{"code":"BA","progs":[("BBA Management","Bachelors",4,65000)]}}},
    "School of Engineering & Technology": {"code":"SET","depts":{"Electrical Engineering":{"code":"EE","progs":[("BSc Electrical Engineering","Bachelors",5,95000)]},"Civil Engineering":{"code":"CE","progs":[("BSc Civil Engineering","Bachelors",5,95000)]}}},
    "School of Education": {"code":"SOE","depts":{"Educational Foundations":{"code":"EF","progs":[("BEd Arts","Bachelors",4,55000),("BEd Science","Bachelors",4,58000)]},"Educational Psychology":{"code":"EP","progs":[("MEd Educational Psychology","Masters",2,85000)]}}},
    "School of Medicine": {"code":"SOM","depts":{"Clinical Medicine":{"code":"CM","progs":[("MBChB Medicine","Bachelors",6,150000)]},"Nursing":{"code":"NR","progs":[("BSc Nursing","Bachelors",4,85000)]}}},
    "School of Law": {"code":"SOL","depts":{"Public Law":{"code":"PL","progs":[("LLB Law","Bachelors",4,95000)]}}},
    "School of Agriculture": {"code":"SOA","depts":{"Agricultural Economics":{"code":"AE","progs":[("BSc Agricultural Economics","Bachelors",4,60000)]}}},
    "School of Pure & Applied Sciences": {"code":"SPAS","depts":{"Mathematics":{"code":"MA","progs":[("BSc Mathematics","Bachelors",4,58000),("BSc Actuarial Science","Bachelors",4,75000)]},"Chemistry":{"code":"CH","progs":[("BSc Chemistry","Bachelors",4,62000)]}}},
}

COURSES_BY_DEPT = {
    "CS":["CSC101 Intro to Programming","CSC201 Data Structures","CSC301 Databases","CSC302 Networks","CSC401 Software Eng"],
    "IT":["CIT101 IT Fundamentals","CIT201 Web Development","CIT301 Systems Admin"],
    "AF":["ACC101 Financial Accounting","FIN201 Corporate Finance","ACC301 Auditing"],
    "BA":["BUS101 Business Management","BUS201 Marketing","BUS301 Strategy"],
    "EE":["EEE101 Circuit Analysis","EEE201 Electronics","EEE301 Power Systems"],
    "CE":["ECE101 Structural Mechanics","ECE201 Geotechnics","ECE301 Hydraulics"],
    "EF":["EDF101 Curriculum Dev","EDF201 Teaching Methods"],
    "EP":["EDP101 Child Psychology"],
    "CM":["MED101 Anatomy","MED201 Physiology","MED301 Pathology"],
    "NR":["NUR101 Nursing Practice","NUR201 Clinical Care"],
    "PL":["LAW101 Constitutional Law","LAW201 Criminal Law"],
    "AE":["AGE101 Farm Management","AGE201 Agri Economics"],
    "MA":["MAT101 Calculus","MAT201 Linear Algebra","MAT301 Statistics"],
    "CH":["CHE101 General Chemistry","CHE201 Organic Chemistry"],
}

def gen_name(g):
    f = random.choice(MALE if g=="Male" else FEMALE)
    return f, random.choice(SURNAMES)

def grade(score):
    if score>=70: return "A"
    elif score>=60: return "B"
    elif score>=50: return "C"
    elif score>=40: return "D"
    elif score>=30: return "E"
    return "F"

def run():
    print("="*50)
    print("CAMPUS MANAGEMENT REPORT — Data Generator")
    print("="*50)

    # 1. Academic structure
    print("\n[1/9] Academic structure...")
    sch_rows, dept_rows, prog_rows, course_rows, curric_rows = [],[],[],[],[]
    sch_ids, dept_ids, prog_list = {},{},[]

    for sname, sdata in KU.items():
        sid = str(uuid.uuid4())
        sch_ids[sname] = sid
        sch_rows.append({"school_id":sid,"school_code":sdata["code"],"school_name":sname,"dean_name":f"Prof. {random.choice(SURNAMES)}"})
        for dname, ddata in sdata["depts"].items():
            did = str(uuid.uuid4())
            dept_ids[dname] = did
            dept_rows.append({"dept_id":did,"dept_code":ddata["code"],"dept_name":dname,"school_id":sid,"hod_name":f"Dr. {random.choice(SURNAMES)}"})
            for pname,level,dur,fee in ddata["progs"]:
                pid = str(uuid.uuid4())
                prog_rows.append({"programme_id":pid,"programme_code":f"{sdata['code']}-{ddata['code']}-{random.randint(100,999)}",
                                  "programme_name":pname,"level":level,"dept_id":did,"duration_years":dur,"fee_per_semester":fee})
                prog_list.append({"id":pid,"dept":dname,"dept_code":ddata["code"],"school":sname,"fee":fee})
            for c in COURSES_BY_DEPT.get(ddata["code"],[]):
                cid = str(uuid.uuid4())
                code, name = c.split(" ",1)
                course_rows.append({"course_id":cid,"course_code":code,"course_name":name,"credit_hours":random.choice([2,3,3,4]),"dept_id":did})

    w(pd.DataFrame(sch_rows),"school")
    w(pd.DataFrame(dept_rows),"department")
    w(pd.DataFrame(prog_rows),"programme")
    w(pd.DataFrame(course_rows),"course_unit")
    print(f"   {len(sch_rows)} schools, {len(dept_rows)} depts, {len(prog_rows)} programmes, {len(course_rows)} courses")

    # 2. Semesters
    print("[2/9] Semesters...")
    sem_rows = []
    sem_ids = {}
    for y in [2024,2025]:
        for t in ["Semester 1","Semester 2","Semester 3"]:
            sid = str(uuid.uuid4())
            sem_ids[(y,t)] = sid
            sem_rows.append({"semester_id":sid,"year":y,"term":t,"is_current":(y==2025 and t=="Semester 1")})
    w(pd.DataFrame(sem_rows),"semester")

    # 3. Students
    print("[3/9] 500 students...")
    stu_rows, nok_rows = [],[]
    students = []
    for i in range(500):
        g = random.choice(["Male","Female"])
        fn, ln = gen_name(g)
        sid = str(uuid.uuid4())
        adm = f"KU/2025/{str(i+1).zfill(5)}"
        prog = random.choice(prog_list)
        stu_rows.append({"student_id":sid,"admission_no":adm,"first_name":fn,"last_name":ln,"gender":g,
                         "date_of_birth":str(date(random.randint(1998,2005),random.randint(1,12),random.randint(1,28))),
                         "nationality":"Kenyan","national_id":str(random.randint(10000000,99999999)),
                         "phone":f"07{random.randint(10000000,99999999)}","email":f"{fn.lower()}.{ln.lower()}@students.ku.ac.ke",
                         "county":random.choice(COUNTIES),"admission_type":random.choices(["Government","Self-Sponsored"],weights=[70,30])[0],
                         "programme_id":prog["id"],"entry_year":2025,"status":"Active"})
        nok_rows.append({"student_id":sid,"name":f"{random.choice(MALE)} {random.choice(SURNAMES)}",
                         "relationship":random.choice(["Father","Mother","Guardian"]),"phone":f"07{random.randint(10000000,99999999)}"})
        students.append({"id":sid,"dept_code":prog["dept_code"],"school":prog["school"],"fee":prog["fee"]})
    w(pd.DataFrame(stu_rows),"student")
    w(pd.DataFrame(nok_rows),"next_of_kin")
    print(f"   500 students, 500 next of kin")

    # 4. Staff + lecturers
    print("[4/9] Staff & lecturers...")
    staff_rows, lec_rows, pay_rows = [],[],[]
    dept_list = list(dept_ids.items())
    for i in range(120):
        g = random.choice(["Male","Female"])
        fn, ln = gen_name(g)
        sid = str(uuid.uuid4())
        role = "Academic" if i < 80 else random.choice(["Administrative","Technical","Support"])
        dn, did = random.choice(dept_list)
        salary = random.randint(60000,250000) if role=="Academic" else random.randint(30000,100000)
        staff_rows.append({"staff_id":sid,"staff_no":f"STF/{str(i+1).zfill(4)}","first_name":fn,"last_name":ln,
                           "gender":g,"role":role,"dept_id":did,"employment_date":str(date(random.randint(2010,2024),random.randint(1,12),1)),
                           "phone":f"07{random.randint(10000000,99999999)}","email":f"{fn.lower()}.{ln.lower()}@ku.ac.ke","is_active":True})
        if role == "Academic":
            lid = str(uuid.uuid4())
            lec_rows.append({"lecturer_id":lid,"staff_id":sid,"specialization":dn,"qualification":random.choice(["PhD","Masters","Professor"])})
        for m in range(1,7):
            allow = random.randint(5000,30000)
            deduct = random.randint(3000,15000)
            pay_rows.append({"staff_id":sid,"basic_salary":salary,"allowances":allow,"deductions":deduct,
                             "pay_date":str(date(2025,m,28)),"pay_month":m,"pay_year":2025})
    w(pd.DataFrame(staff_rows),"staff")
    w(pd.DataFrame(lec_rows),"lecturer")
    w(pd.DataFrame(pay_rows),"payroll")
    print(f"   {len(staff_rows)} staff, {len(lec_rows)} lecturers, {len(pay_rows)} payroll records")

    # 5. Course registration + results
    print("[5/9] Course registrations & results...")
    reg_rows, res_rows = [],[]
    sem_id = sem_ids.get((2025,"Semester 1"), list(sem_ids.values())[0])
    all_courses = {r["course_code"]: r["course_id"] for r in course_rows}
    
    for s in students:
        dept_courses = [c for c in course_rows if c["course_code"].startswith(s["dept_code"][:2].upper()) or random.random()<0.1]
        chosen = random.sample(dept_courses, min(5, len(dept_courses))) if dept_courses else []
        for c in chosen:
            rid = str(uuid.uuid4())
            reg_rows.append({"reg_id":rid,"student_id":s["id"],"course_id":c["course_id"],"semester_id":sem_id,"status":"Registered","registration_date":str(date(2025,1,random.randint(5,20)))})
            cat = round(random.uniform(5,30),1)
            exam = round(random.uniform(10,70),1)
            total = round(cat+exam,1)
            res_rows.append({"reg_id":rid,"cat_score":cat,"exam_score":exam,"grade":grade(total)})
    w(pd.DataFrame(reg_rows),"course_registration")
    w(pd.DataFrame(res_rows),"result")
    print(f"   {len(reg_rows)} registrations, {len(res_rows)} results")

    # 6. Payments
    print("[6/9] Fee payments...")
    pay_stu_rows = []
    for s in students:
        amt = round(s["fee"] * random.uniform(0.4,1.0), 2)
        pay_stu_rows.append({"student_id":s["id"],"amount":amt,"payment_date":str(date(2025,random.randint(1,3),random.randint(1,28))),
                             "method":random.choices(["M-Pesa","Bank Transfer","HELB","Cash","Cheque","Bursary"],weights=[35,25,20,10,5,5])[0],
                             "receipt_no":f"RCP/2025/{str(len(pay_stu_rows)+1).zfill(6)}","academic_year":"2024/2025"})
    w(pd.DataFrame(pay_stu_rows),"payment")
    print(f"   {len(pay_stu_rows)} payments")

    # 7. Accommodation
    print("[7/9] Accommodation...")
    hostels = [("Nyayo Hall",200,"Male"),("Uhuru Hall",180,"Female"),("Kenyatta Hall",220,"Male"),("Mama Ngina Hall",160,"Female")]
    hostel_rows, room_rows, alloc_rows = [],[],[]
    for hname, cap, gen in hostels:
        hid = str(uuid.uuid4())
        hostel_rows.append({"hostel_id":hid,"hostel_name":hname,"capacity":cap,"gender_restriction":gen})
        for r in range(1, cap//2 + 1):
            rid = str(uuid.uuid4())
            room_rows.append({"room_id":rid,"hostel_id":hid,"room_number":f"{hname[0]}{str(r).zfill(3)}","capacity":2,"is_available":True})
    w(pd.DataFrame(hostel_rows),"hostel")
    w(pd.DataFrame(room_rows),"room")
    # Allocate 60% of students
    available_rooms = room_rows.copy()
    random.shuffle(available_rooms)
    allocated = 0
    for s in students[:300]:
        if allocated >= len(available_rooms): break
        alloc_rows.append({"student_id":s["id"],"room_id":available_rooms[allocated]["room_id"],"semester_id":sem_id,"check_in_date":str(date(2025,1,10))})
        allocated += 1
    w(pd.DataFrame(alloc_rows),"room_allocation")
    print(f"   {len(hostel_rows)} hostels, {len(room_rows)} rooms, {len(alloc_rows)} allocations")

    # 8. Transport
    print("[8/9] Transport...")
    vehicles = [("KCB 100A","Bus",60),("KCB 200B","Van",14),("KCB 300C","Truck",0),("KCB 400D","SUV",7),("KCB 500E","Bus",45)]
    veh_rows, drv_rows, trip_rows = [],[],[]
    driver_staff = [s for s in staff_rows if s["role"]=="Support"][:5]
    for (reg,vtype,cap) in vehicles:
        vid = str(uuid.uuid4())
        veh_rows.append({"vehicle_id":vid,"registration_no":reg,"type":vtype,"capacity":cap,"is_active":True})
        for _ in range(random.randint(10,30)):
            trip_rows.append({"vehicle_id":vid,"driver_id":None,"trip_date":str(date(2025,random.randint(1,6),random.randint(1,28))),
                              "destination":random.choice(["Nairobi CBD","JKIA","Thika","Mombasa","Nakuru"]),
                              "purpose":random.choice(["Staff transport","Field trip","Goods delivery","Student trip","Administration"]),
                              "distance_km":round(random.uniform(5,500),1),"fuel_litres":round(random.uniform(5,200),1),
                              "cost":round(random.uniform(500,50000),2)})
    w(pd.DataFrame(veh_rows),"vehicle")
    # Create drivers from support staff
    for ds in driver_staff:
        did = str(uuid.uuid4())
        drv_rows.append({"driver_id":did,"staff_id":ds["staff_id"],"license_no":f"DL{random.randint(100000,999999)}"})
    if drv_rows:
        w(pd.DataFrame(drv_rows),"driver")
        for t in trip_rows:
            t["driver_id"] = random.choice(drv_rows)["driver_id"]
    w(pd.DataFrame(trip_rows),"trip")
    print(f"   {len(veh_rows)} vehicles, {len(drv_rows)} drivers, {len(trip_rows)} trips")

    # 9. Procurement
    print("[9/9] Procurement & inventory...")
    suppliers = ["Nairobi Office Supplies","KenTech Solutions","East Africa Paper","Medico Supplies","AgriChem Kenya"]
    sup_rows, item_rows, po_rows, stock_rows = [],[],[],[]
    sup_ids = {}
    for sn in suppliers:
        sid = str(uuid.uuid4())
        sup_ids[sn] = sid
        sup_rows.append({"supplier_id":sid,"name":sn,"contact_person":f"{random.choice(MALE)} {random.choice(SURNAMES)}",
                         "phone":f"07{random.randint(10000000,99999999)}","rating":round(random.uniform(2,5),2)})
    items = [("A4 Paper","Stationery",450),("Printer Toner","IT",3500),("Lab Chemicals","Science",12000),
             ("Projector","IT",45000),("Desk","Furniture",8000),("Textbooks","Library",2500),("Laptop","IT",65000),
             ("Cleaning Supplies","Maintenance",800),("First Aid Kit","Medical",3000),("Whiteboard Marker","Stationery",150)]
    item_ids = {}
    for iname,cat,price in items:
        iid = str(uuid.uuid4())
        item_ids[iname] = iid
        item_rows.append({"item_id":iid,"name":iname,"category":cat,"unit_of_measure":"piece","unit_price":price})
        stock_rows.append({"item_id":iid,"quantity_available":random.randint(5,200),"reorder_level":random.randint(10,50),
                           "last_restocked":str(date(2025,random.randint(1,3),random.randint(1,28)))})
    for _ in range(25):
        po_rows.append({"supplier_id":random.choice(list(sup_ids.values())),"order_date":str(date(2025,random.randint(1,6),random.randint(1,28))),
                        "total_amount":round(random.uniform(10000,500000),2),
                        "status":random.choice(["Draft","Submitted","Approved","Delivered","Cancelled"]),
                        "approved_by":f"Dr. {random.choice(SURNAMES)}"})

    w(pd.DataFrame(sup_rows),"supplier")
    w(pd.DataFrame(item_rows),"item")
    w(pd.DataFrame(po_rows),"purchase_order")
    w(pd.DataFrame(stock_rows),"stock")
    print(f"   {len(sup_rows)} suppliers, {len(item_rows)} items, {len(po_rows)} POs, {len(stock_rows)} stock records")

    # 10. Research & Publications
    print("[10/11] Research & publications...")
    rp_rows, pub_rows = [], []
    academic_staff = [s for s in staff_rows if s["role"]=="Academic"]
    journals = ["East African Journal of Sciences","African Journal of Education","Kenya Medical Journal",
                "Journal of Agricultural Research","African Business Review","International Journal of Computing",
                "Journal of Engineering & Technology","African Law Review"]
    project_titles = [
        "Impact of Climate Change on Smallholder Farming in Central Kenya",
        "Machine Learning Approaches for Early Disease Detection in Rural Clinics",
        "Blockchain-Based Land Registry System for Kenyan Counties",
        "Analysis of Student Retention Factors in Kenyan Public Universities",
        "Renewable Energy Adoption Patterns in Peri-Urban Kenya",
        "Antimicrobial Resistance Surveillance in Nairobi Hospitals",
        "Digital Financial Inclusion Among Women in Informal Settlements",
        "Constitutional Reform and Devolution: A Decade of Implementation",
        "Optimization of Water Distribution Networks in Arid Regions",
        "Impact of HELB Funding on Student Academic Performance",
        "Sustainable Urban Transport Planning for Kenyan Cities",
        "AI-Driven Crop Yield Prediction for Kenyan Agriculture",
        "Mental Health Support Systems in Kenyan Universities",
        "Cybersecurity Readiness of Kenyan Financial Institutions",
        "Effect of School Feeding Programmes on Learning Outcomes",
    ]
    funding_sources = ["NRF Kenya","DAAD","World Bank","USAID","Wellcome Trust","Bill & Melinda Gates Foundation","KU Internal","African Development Bank"]
    for i, title in enumerate(project_titles):
        pi = random.choice(academic_staff)
        rp_rows.append({
            "title": title,
            "principal_investigator": pi["staff_id"],
            "dept_id": pi["dept_id"],
            "funding_source": random.choice(funding_sources),
            "grant_amount": round(random.uniform(500000, 15000000), 2),
            "amount_utilized": round(random.uniform(100000, 10000000), 2),
            "start_date": str(date(random.randint(2022, 2025), random.randint(1, 12), 1)),
            "end_date": str(date(random.randint(2025, 2028), random.randint(1, 12), 28)),
            "status": random.choice(["Active", "Active", "Active", "Completed", "Proposal"])
        })

    for _ in range(40):
        auth = random.choice(academic_staff)
        co_authors = ", ".join([f"{random.choice(MALE)} {random.choice(SURNAMES)}" for _ in range(random.randint(1,4))])
        pub_rows.append({
            "title": f"{'A Study of' if random.random()>0.5 else 'Analysis of'} {random.choice(['Factors','Patterns','Trends','Effects','Outcomes'])} in {random.choice(['Kenya','East Africa','Sub-Saharan Africa','Nairobi','Rural Communities'])}",
            "authors": f"{auth['first_name']} {auth['last_name']}, {co_authors}",
            "dept_id": auth["dept_id"],
            "journal": random.choice(journals),
            "publication_date": str(date(random.randint(2023, 2025), random.randint(1, 12), random.randint(1, 28))),
        })

    w(pd.DataFrame(rp_rows), "research_project")
    w(pd.DataFrame(pub_rows), "publication")
    print(f"   {len(rp_rows)} projects, {len(pub_rows)} publications")

    # 11. Budgets & Fee Structure
    print("[11/11] Budgets & fee structure...")
    budget_rows, fee_rows = [], []
    for dn, did in dept_ids.items():
        budget_amt = round(random.uniform(2000000, 20000000), 2)
        budget_rows.append({
            "dept_id": did, "fiscal_year": "2024/2025",
            "budget_amount": budget_amt,
            "actual_spent": round(budget_amt * random.uniform(0.5, 0.95), 2)
        })
    w(pd.DataFrame(budget_rows), "budget")

    for p in prog_rows:
        for stype in ["Government", "Self-Sponsored"]:
            amt = p["fee_per_semester"] if stype == "Self-Sponsored" else p["fee_per_semester"] * 0.3
            fee_rows.append({
                "programme_id": p["programme_id"],
                "amount": round(amt, 2),
                "sponsor_type": stype
            })
    w(pd.DataFrame(fee_rows), "fee_structure")
    print(f"   {len(budget_rows)} budgets, {len(fee_rows)} fee structures")

    print(f"\n{'='*50}")
    print("COMPLETE. All domains populated.")
    print(f"{'='*50}")

if __name__ == "__main__":
    run()
