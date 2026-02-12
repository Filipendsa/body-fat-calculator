import sqlite3
from src.config import DATABASE_NAME

class DatabaseHandler:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_NAME)
        self.create_tables()
        self.migrate_db()
        self.seed_food_database() # Popula alimentos e dieta de exemplo

    def create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, cpf TEXT, email TEXT)
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT,
                weight REAL, height REAL, sex TEXT, age INTEGER,
                chest REAL, axillary REAL, tricep REAL, subscapular REAL, abdominal REAL, suprailiac REAL, thigh REAL, biceps REAL, calf REAL,
                shoulder REAL, thorax REAL, waist REAL, abdomen_perim REAL, hips REAL, arm_r REAL, arm_l REAL, forearm_r REAL, forearm_l REAL, thigh_r REAL, thigh_l REAL, calf_r REAL, calf_l REAL,
                bf_percent REAL, fat_mass REAL, lean_mass REAL, bmi REAL,
                rcq REAL, ama REAL, ama_class TEXT, tma REAL, tma_class TEXT, bf_class TEXT,
                tmb REAL, tdee REAL, activity_level TEXT,
                diet_goal TEXT, target_bf REAL, diet_intensity REAL, prot_g_kg REAL,
                target_kcal REAL, target_prot REAL, target_carb REAL, target_fat REAL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        # --- TABELA DE ALIMENTOS (ACERVO) ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS foods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                category TEXT,
                unit TEXT,
                base_qty REAL,
                kcal REAL, prot REAL, carb REAL, fat REAL,
                tags TEXT 
            )
        """)

        # --- TABELA DE PREFERÊNCIAS DE DIETA DO USUÁRIO ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_diet_settings (
                user_id INTEGER PRIMARY KEY,
                diet_type TEXT,
                excluded_foods TEXT,
                preferred_foods TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        # --- FALTAVA ESTA TABELA: REFEIÇÕES DO DIA (DIET LOG) ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diet_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                meal_name TEXT, 
                food_id INTEGER,
                quantity REAL, 
                FOREIGN KEY(food_id) REFERENCES foods(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        self.conn.commit()

    def seed_food_database(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT count(*) FROM foods")
        
        # Popula apenas se o banco estiver vazio
        if cursor.fetchone()[0] < 10: 
            foods_data = [
                # PROTEÍNAS ANIMAIS
                ("Peito de Frango Grelhado", "Proteína", "g", 100, 159, 31, 0, 3.6, "carnivore,paleo,onivoro"),
                ("Patinho Moído (Carne Bovina)", "Proteína", "g", 100, 219, 35.9, 0, 7.3, "carnivore,paleo,onivoro"),
                ("Ovo de Galinha (Inteiro)", "Proteína", "un", 1, 72, 6, 0.6, 5, "carnivore,paleo,ovolacto,onivoro"),
                ("Tilápia Grelhada", "Proteína", "g", 100, 128, 26, 0, 2.6, "carnivore,paleo,pescetariano,onivoro"),
                ("Whey Protein Concentrado", "Proteína", "g", 30, 114, 24, 4.5, 0, "vegetariano,onivoro"), # Ajustado pro seu PDF
                
                # PROTEÍNAS VEGETAIS
                ("Lentilha Cozida", "Proteína", "g", 100, 116, 9, 20, 0.4, "vegan,vegetariano,flexitariano,plant-based"),
                ("Grão de Bico Cozido", "Proteína", "g", 100, 164, 8.9, 27, 2.6, "vegan,vegetariano,plant-based"),
                ("Tofu", "Proteína", "g", 100, 76, 8, 1.9, 4.8, "vegan,vegetariano,plant-based"),
                ("Proteína de Soja Texturizada", "Proteína", "g", 30, 100, 15, 9, 0.5, "vegan,vegetariano"),

                # CARBOIDRATOS
                ("Arroz Branco Cozido", "Carbo", "g", 110, 140.8, 2.75, 30.91, 0.22, "vegan,vegetariano,onivoro"), # Ajustado PDF
                ("Feijão Carioca Cozido", "Carbo", "g", 90, 68.4, 4.32, 12.24, 0.45, "vegan,vegetariano,onivoro"), # Ajustado PDF
                ("Batata Doce Cozida", "Carbo", "g", 100, 86, 1.6, 20, 0.1, "vegan,paleo,plant-based"),
                ("Aveia em Flocos", "Carbo", "g", 20, 78.8, 2.8, 13.4, 1.8, "vegan,vegetariano"), # Ajustado PDF
                ("Banana Nanica", "Fruta", "un", 1, 119, 1.8, 30.9, 0.1, "vegan,paleo,frugivoro"), # Ajustado PDF
                ("Macarrão Integral Cozido", "Carbo", "g", 100, 124, 5, 26, 0.5, "vegan,vegetariano"),
                ("Pão de Forma Integral", "Carbo", "un", 2, 118, 4.6, 20, 2.2, "vegan,vegetariano,onivoro"), # Ajustado PDF

                # GORDURAS
                ("Azeite de Oliva", "Gordura", "ml", 13, 119, 0, 0, 13.5, "vegan,paleo,plant-based"),
                ("Pasta de Amendoim", "Gordura", "g", 15, 84.3, 3.3, 3.75, 7.05, "vegan,paleo,plant-based"), # Ajustado PDF
                ("Abacate", "Gordura", "g", 100, 160, 2, 8.5, 14.6, "vegan,paleo,frugivoro"),

                # LATICÍNIOS / FRUTAS EXTRAS
                ("Laranja Pera", "Fruta", "un", 2, 133.2, 3.6, 32.04, 0.36, "vegan,frugivoro"), # Ajustado PDF
                ("Iogurte Natural Desnatado", "Proteína", "g", 170, 80, 8, 12, 0, "lactovegetariano,onivoro")
            ]
            cursor.executemany("INSERT INTO foods (name, category, unit, base_qty, kcal, prot, carb, fat, tags) VALUES (?,?,?,?,?,?,?,?,?)", foods_data)
            self.conn.commit()

            # --- CARREGA O EXEMPLO DA SUA DIETA PARA O USER_ID 1 ---
            # Verifica se existe pelo menos 1 usuário (se não, ignora)
            cursor.execute("SELECT id FROM users LIMIT 1")
            user = cursor.fetchone()
            if user:
                uid = user[0]
                ids = {}
                cursor.execute("SELECT name, id FROM foods")
                for row in cursor.fetchall(): ids[row[0]] = row[1]
                
                # Sua dieta do PDF
                sample_diet = [
                    (uid, "Desjejum", ids["Whey Protein Concentrado"], 30),
                    (uid, "Desjejum", ids["Aveia em Flocos"], 20),
                    (uid, "Desjejum", ids["Banana Nanica"], 1),
                    (uid, "Desjejum", ids["Pasta de Amendoim"], 15),
                    (uid, "Almoço", ids["Arroz Branco Cozido"], 110),
                    (uid, "Almoço", ids["Feijão Carioca Cozido"], 90),
                    (uid, "Almoço", ids["Peito de Frango Grelhado"], 130),
                    (uid, "Lanche", ids["Pão de Forma Integral"], 2),
                    (uid, "Lanche", ids["Ovo de Galinha (Inteiro)"], 2),
                    (uid, "Lanche", ids["Laranja Pera"], 2)
                ]
                cursor.executemany("INSERT INTO diet_log (user_id, meal_name, food_id, quantity) VALUES (?, ?, ?, ?)", sample_diet)
                
                # Salva você como Onívoro para pular a tela de Setup
                all_foods_ids = ",".join(map(str, ids.values()))
                cursor.execute("INSERT OR REPLACE INTO user_diet_settings (user_id, diet_type, preferred_foods, excluded_foods) VALUES (?, ?, ?, ?)", 
                               (uid, "Onívora (Padrão)", all_foods_ids, ""))
                
                self.conn.commit()

    # --- FALTAVA ESTA FUNÇÃO PARA LER AS REFEIÇÕES DO BANCO ---
    def get_diet_log(self, user_id):
        cursor = self.conn.cursor()
        query = """
            SELECT l.id, l.meal_name, l.quantity, f.name, f.unit, f.base_qty, f.kcal, f.prot, f.carb, f.fat
            FROM diet_log l
            JOIN foods f ON l.food_id = f.id
            WHERE l.user_id = ?
            ORDER BY 
                CASE l.meal_name 
                    WHEN 'Desjejum' THEN 1 
                    WHEN 'Almoço' THEN 2 
                    WHEN 'Lanche' THEN 3 
                    WHEN 'Jantar' THEN 4 
                    ELSE 5 
                END
        """
        cursor.execute(query, (user_id,))
        cols = ["log_id", "meal", "qty", "name", "unit", "base_qty", "kcal", "prot", "carb", "fat"]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def save_user_diet_preferences(self, user_id, diet_type, preferred_ids, excluded_ids):
        pref_str = ",".join(map(str, preferred_ids))
        excl_str = ",".join(map(str, excluded_ids))
        cursor = self.conn.cursor()
        cursor.execute("REPLACE INTO user_diet_settings (user_id, diet_type, preferred_foods, excluded_foods) VALUES (?, ?, ?, ?)", 
                       (user_id, diet_type, pref_str, excl_str))
        self.conn.commit()

    def get_user_diet_settings(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT diet_type, preferred_foods, excluded_foods FROM user_diet_settings WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            pref = [int(x) for x in row[1].split(",")] if row[1] else []
            excl = [int(x) for x in row[2].split(",")] if row[2] else []
            return {"diet_type": row[0], "preferred": pref, "excluded": excl}
        return None

    def get_all_foods(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, category, tags FROM foods ORDER BY category, name")
        return [dict(zip(["id", "name", "category", "tags"], row)) for row in cursor.fetchall()]

    def migrate_db(self):
        cursor = self.conn.cursor()
        cols_to_add = [
            ("rcq", "REAL DEFAULT 0"), ("ama", "REAL DEFAULT 0"), ("ama_class", "TEXT DEFAULT '-'"), ("tma", "REAL DEFAULT 0"), ("tma_class", "TEXT DEFAULT '-'"), ("bf_class", "TEXT DEFAULT '-'"),
            ("tmb", "REAL DEFAULT 0"), ("tdee", "REAL DEFAULT 0"), ("activity_level", "TEXT DEFAULT 'Sedentário'"),
            ("diet_goal", "TEXT DEFAULT 'Manter'"), ("target_bf", "REAL DEFAULT 0"), ("diet_intensity", "REAL DEFAULT 0"), ("prot_g_kg", "REAL DEFAULT 2.0"),
            ("target_kcal", "REAL DEFAULT 0"), ("target_prot", "REAL DEFAULT 0"), ("target_carb", "REAL DEFAULT 0"), ("target_fat", "REAL DEFAULT 0")
        ]
        for col_name, col_type in cols_to_add:
            try:
                cursor.execute(f"ALTER TABLE assessments ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError: pass 
        self.conn.commit()

    def add_user(self, name, cpf, email): self.conn.execute("INSERT INTO users (name, cpf, email) VALUES (?, ?, ?)", (name, cpf, email)); self.conn.commit()
    def get_users(self): cursor = self.conn.cursor(); cursor.execute("SELECT * FROM users ORDER BY name"); return [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
    def add_assessment(self, data):
        keys = ', '.join(data.keys()); placeholders = ', '.join(['?'] * len(data))
        cursor = self.conn.cursor(); cursor.execute(f"INSERT INTO assessments ({keys}) VALUES ({placeholders})", tuple(data.values())); self.conn.commit(); return cursor.lastrowid
    def get_history(self, user_id): cursor = self.conn.cursor(); cursor.execute("SELECT * FROM assessments WHERE user_id = ? ORDER BY date DESC", (user_id,)); return [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
    def delete_assessment(self, assessment_id): self.conn.execute("DELETE FROM assessments WHERE id = ?", (assessment_id,)); self.conn.commit()