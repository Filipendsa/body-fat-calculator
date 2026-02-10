import sqlite3
import math
from src.config import DATABASE_NAME
from src.modules.services.calculator import CalculatorService

class DatabaseHandler:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_NAME)
        self.create_tables()
        self.migrate_db()
        self.recalculate_history()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, cpf TEXT, email TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, date TEXT,
                weight REAL, height REAL, sex TEXT, age INTEGER,
                chest REAL, axillary REAL, tricep REAL, subscapular REAL,
                abdominal REAL, suprailiac REAL, thigh REAL, biceps REAL, calf REAL,
                shoulder REAL, thorax REAL, waist REAL, abdomen_perim REAL, hips REAL,
                arm_r REAL, arm_l REAL, forearm_r REAL, forearm_l REAL,
                thigh_r REAL, thigh_l REAL, calf_r REAL, calf_l REAL,
                bf_percent REAL, fat_mass REAL, lean_mass REAL, bmi REAL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        self.conn.commit()

    def migrate_db(self):
        cursor = self.conn.cursor()
        cols_to_add = [
            ("rcq", "REAL DEFAULT 0"), ("ama", "REAL DEFAULT 0"), 
            ("ama_class", "TEXT DEFAULT '-'"), ("tma", "REAL DEFAULT 0"), 
            ("tma_class", "TEXT DEFAULT '-'"), ("bf_class", "TEXT DEFAULT '-'"),
            ("tmb", "REAL DEFAULT 0"), ("tdee", "REAL DEFAULT 0"),
            ("activity_level", "TEXT DEFAULT 'Sedentário'")
        ]
        for col_name, col_type in cols_to_add:
            try:
                cursor.execute(f"ALTER TABLE assessments ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError: pass 
        self.conn.commit()

    def recalculate_history(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, sex, age, bf_percent, waist, hips, arm_r, tricep, thigh_r, thigh FROM assessments WHERE rcq IS NULL OR rcq = 0")
        rows = cursor.fetchall()
        for row in rows:
            rec_id, sex, age, bf, waist, hips, arm_r, tricep, thigh_r, thigh_fold = row
            waist = waist or 0; hips = hips or 0; arm_r = arm_r or 0; tricep = tricep or 0; thigh_r = thigh_r or 0; thigh_fold = thigh_fold or 0
            
            rcq = waist / hips if hips > 0 else 0
            try: ama = ((arm_r - (math.pi * (tricep/10))) ** 2) / (4 * math.pi) - (10.0 if sex=="Masculino" else 6.5)
            except: ama = 0
            try: tma = ((thigh_r - (math.pi * (thigh_fold/10))) ** 2) / (4 * math.pi)
            except: tma = 0
            
            bf_cl = CalculatorService.get_bf_classification(bf, sex, age)
            ama_cl = CalculatorService.get_muscle_area_class(ama, "arm")
            tma_cl = CalculatorService.get_muscle_area_class(tma, "thigh")
            
            cursor.execute("UPDATE assessments SET rcq=?, ama=?, ama_class=?, tma=?, tma_class=?, bf_class=? WHERE id=?", (rcq, ama, ama_cl, tma, tma_cl, bf_cl, rec_id))
        self.conn.commit()

    def add_user(self, name, cpf, email):
        self.conn.execute("INSERT INTO users (name, cpf, email) VALUES (?, ?, ?)", (name, cpf, email)); self.conn.commit()

    def get_users(self):
        cursor = self.conn.cursor(); cursor.execute("SELECT * FROM users ORDER BY name")
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def add_assessment(self, data):
        keys = ', '.join(data.keys()); placeholders = ', '.join(['?'] * len(data))
        query = f"INSERT INTO assessments ({keys}) VALUES ({placeholders})"
        self.conn.execute(query, tuple(data.values())); self.conn.commit()

    def get_history(self, user_id):
        cursor = self.conn.cursor(); cursor.execute("SELECT * FROM assessments WHERE user_id = ? ORDER BY date DESC", (user_id,))
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]