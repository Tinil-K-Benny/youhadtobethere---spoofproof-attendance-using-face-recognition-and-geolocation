import os
import pymongo
from dotenv import load_dotenv
from datetime import datetime
import csv
import io

load_dotenv()
URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "facecheck")

client = pymongo.MongoClient(URI)
db = client[DB_NAME]

raw_csv = """Subject Name,Subject Code,Teacher Name,Day of Week,Start Time,End Time
Software Engineering / Pattern Recognition,PECST411 / PECST412,Ms. Anna Eldho / Ms. Sareena K K,Monday,8:45 AM,9:35 AM
Database Management Systems,PCCST402,Dr. Noora V T,Monday,9:35 AM,10:25 AM
Software Engineering / Pattern Recognition,PECST411 / PECST412,Ms. Anna Eldho / Ms. Sareena K K,Monday,10:35 AM,11:30 AM
Operating Systems (Remedial),PCCST403,Ms. Meera V M,Monday,12:15 PM,1:05 PM
Mathematics for Information Science,GAMAT401,Mr. Rahul Ravi,Monday,1:05 PM,2:55 PM
Youth to Power-Aptitude Training,Y2P-AT,Mr. Reshma R,Monday,2:55 PM,3:45 PM
Mathematics for Information Science,GAMAT401,Mr. Rahul Ravi,Tuesday,8:45 AM,9:35 AM
Computer Organization and Architecture,PBCST404,Ms. Anu S,Tuesday,9:35 AM,10:25 AM
Engineering Ethics and Sustainable Development,UCHUT34,Mr. Deepu R,Tuesday,10:35 AM,11:30 AM
Computer Organization and Architecture (R),PBCST404,Ms. Anu S,Tuesday,12:15 PM,1:05 PM
Operating Systems (Tutorial),PCCST403,Ms. Meera V M,Tuesday,1:05 PM,1:55 PM
Database Management Systems,PCCST402,Dr. Noora V T,Tuesday,2:05 PM,2:55 PM
Software Engineering / Pattern Recognition,PECST411 / PECST412,Ms. Anna Eldho / Ms. Sareena K K,Tuesday,2:55 PM,3:45 PM
Computer Organization and Architecture,PBCST404,Ms. Anu S,Wednesday,8:45 AM,10:25 AM
Engineering Ethics and Sustainable Development,UCHUT34,Mr. Deepu R,Wednesday,9:35 AM,10:25 AM
Computer Organization and Architecture,PBCST404,Ms. Anu S,Wednesday,10:35 AM,11:30 AM
Database Management Systems (Remedial),PCCST402,Dr. Noora V T,Wednesday,12:15 PM,1:05 PM
DBMS Lab / OS Lab,PCCSL408 / PCCSL407,Dr. Noora V T / Ms. Meera V M,Wednesday,1:05 PM,3:45 PM
Software Engineering / Pattern Recognition,PECST411 / PECST412,Ms. Anna Eldho / Ms. Sareena K K,Thursday,8:45 AM,9:35 AM
Database Management Systems,PCCST402,Dr. Noora V T,Thursday,9:35 AM,10:25 AM
Operating Systems,PCCST403,Ms. Meera V M,Thursday,10:35 AM,11:30 AM
Microcontrollers / Math (MIS-4),MNECT409 / GAMAT401,Ms. Amrutha Joshy / Mr. Rahul Ravi,Thursday,12:15 PM,1:05 PM
Operating Systems,PCCST403,Ms. Meera V M,Thursday,1:05 PM,1:55 PM
Mathematics for Information Science,GAMAT401,Mr. Rahul Ravi,Thursday,2:05 PM,2:55 PM
Database Management Systems (Tutorial),PCCST402,Dr. Noora V T,Thursday,2:55 PM,3:45 PM
Operating Systems,PCCST403,Ms. Meera V M,Friday,8:45 AM,9:35 AM
DBMS Lab / OS Lab,PCCSL408 / PCCSL407,Dr. Noora V T / Ms. Meera V M,Friday,9:35 AM,11:30 AM
Computer Organization and Architecture (P),PBCST404,Ms. Anu S,Friday,2:05 PM,2:55 PM
Engineering Ethics and Sustainable Development,UCHUT34,Mr. Deepu R,Friday,2:55 PM,3:45 PM"""

def parse_time(t_str):
    t = datetime.strptime(t_str.strip(), "%I:%M %p")
    return t.strftime("%H:%M")

reader = csv.DictReader(io.StringIO(raw_csv.strip()))
docs = []
for row in reader:
    doc = {
        "subject": row["Subject Name"].strip(),
        "subject_code": row["Subject Code"].strip(),
        "teacher": row["Teacher Name"].strip(),
        "schedule": {
            "day": row["Day of Week"].strip(),
            "start_time": parse_time(row["Start Time"]),
            "end_time": parse_time(row["End Time"])
        },
        "location_zone": {
            "lat": 10.269747442890257,
            "lng": 76.40036119740759,
            "radius_meters": 100
        },
        "created_at": datetime.utcnow()
    }
    docs.append(doc)

db.classes.insert_many(docs)
print(f"Successfully inserted {len(docs)} classes into MongoDB!")
