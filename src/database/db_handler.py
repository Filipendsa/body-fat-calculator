import sqlite3
from src.config import DATABASE_NAME

class DatabaseHandler:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_NAME)
        self.create_tables()
        self.migrate_db()
        self.seed_food_database() 

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_diet_settings (
                user_id INTEGER PRIMARY KEY,
                diet_type TEXT,
                excluded_foods TEXT,
                preferred_foods TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

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
        
        # Popula apenas se o banco estiver vazio ou com poucos itens
        if cursor.fetchone()[0] < 50: 
            foods_data = [
                # --- PROTEÍNAS ANIMAIS (LIMPAS - Levítico 11) ---
                ("Peito de Frango Grelhado", "Proteína", "g", 100, 159, 31, 0, 3.6, "carnivore,paleo,onivoro"),
                ("Patinho Moído (Carne Bovina)", "Proteína", "g", 100, 219, 35.9, 0, 7.3, "carnivore,paleo,onivoro"),
                ("Contra Filé Grelhado", "Proteína", "g", 100, 203, 37, 0, 4.7, "carnivore,paleo,onivoro"),
                ("Ovo de Galinha (Inteiro)", "Proteína", "un", 1, 72, 6, 0.6, 5, "carnivore,paleo,ovolacto,onivoro"),
                ("Clara de Ovo", "Proteína", "un", 1, 17, 3.6, 0.2, 0, "carnivore,paleo,ovolacto,onivoro"),
                ("Tilápia Grelhada", "Proteína", "g", 100, 128, 26, 0, 2.6, "carnivore,paleo,pescetariano,onivoro"),
                ("Atum em Água (Lata)", "Proteína", "g", 60, 60, 13, 0, 0.5, "carnivore,paleo,pescetariano,onivoro"),
                ("Whey Protein Concentrado", "Proteína", "g", 30, 114, 24, 4.5, 0, "vegetariano,onivoro"), 
                
                # --- PROTEÍNAS VEGETAIS ---
                ("Lentilha Cozida", "Proteína", "g", 100, 116, 9, 20, 0.4, "vegan,vegetariano,flexitariano,plant-based"),
                ("Grão de Bico Cozido", "Proteína", "g", 100, 164, 8.9, 27, 2.6, "vegan,vegetariano,plant-based"),
                ("Tofu", "Proteína", "g", 100, 76, 8, 1.9, 4.8, "vegan,vegetariano,plant-based"),
                ("Proteína de Soja Texturizada", "Proteína", "g", 30, 100, 15, 9, 0.5, "vegan,vegetariano"),

                # --- CARBOIDRATOS (Pães e Grãos) ---
                ("Arroz Branco Cozido", "Carbo", "g", 110, 140.8, 2.75, 30.91, 0.22, "vegan,vegetariano,onivoro"),
                ("Feijão Carioca Cozido", "Carbo", "g", 90, 68.4, 4.32, 12.24, 0.45, "vegan,vegetariano,onivoro"),
                ("Batata Doce Cozida", "Carbo", "g", 100, 86, 1.6, 20, 0.1, "vegan,paleo,plant-based"),
                ("Batata Inglesa Cozida", "Carbo", "g", 100, 52, 1.2, 12, 0, "vegan,plant-based"),
                ("Aveia em Flocos", "Carbo", "g", 20, 78.8, 2.8, 13.4, 1.8, "vegan,vegetariano"),
                ("Macarrão Integral Cozido", "Carbo", "g", 100, 124, 5, 26, 0.5, "vegan,vegetariano"),
                ("Pão de Forma Integral", "Carbo", "fat", 2, 118, 4.6, 20, 2.2, "vegan,vegetariano,onivoro"), # Unidade = fatia
                ("Pão Francês", "Carbo", "un", 1, 135, 4.5, 28, 0, "vegan,vegetariano,onivoro"),
                ("Tapioca (Goma)", "Carbo", "g", 100, 336, 0, 84, 0, "vegan,gluten-free"), 

                # --- FRUTAS (Variedade Completa) ---
                ("Banana Nanica", "Fruta", "un", 1, 119, 1.8, 30.9, 0.1, "vegan,paleo,frugivoro"),
                ("Banana Prata", "Fruta", "un", 1, 68, 0.9, 18, 0.1, "vegan,paleo,frugivoro"),
                ("Maçã", "Fruta", "un", 1, 52, 0.3, 14, 0.2, "vegan,frugivoro"),
                ("Laranja Pera", "Fruta", "un", 1, 65, 1.2, 16, 0.1, "vegan,frugivoro"), # Ajustado para 1 unidade média
                ("Mamão Papaia", "Fruta", "un", 0.5, 60, 0.8, 15, 0.2, "vegan,frugivoro"), # Meio mamão
                ("Abacaxi", "Fruta", "fat", 1, 50, 0.5, 13, 0.1, "vegan,frugivoro"), # Fatia
                ("Melão", "Fruta", "fat", 1, 30, 0.8, 8, 0, "vegan,frugivoro"),
                ("Melancia", "Fruta", "fat", 1, 30, 0.6, 8, 0, "vegan,frugivoro"),
                ("Morango", "Fruta", "un", 5, 20, 0.5, 5, 0, "vegan,frugivoro"), # 5 unidades
                ("Uva", "Fruta", "un", 10, 35, 0.4, 9, 0, "vegan,frugivoro"), # 10 unidades
                ("Manga", "Fruta", "un", 1, 135, 1, 35, 0.6, "vegan,frugivoro"),

                # --- GORDURAS ---
                ("Azeite de Oliva", "Gordura", "ml", 13, 119, 0, 0, 13.5, "vegan,paleo,plant-based"),
                ("Pasta de Amendoim", "Gordura", "g", 15, 84.3, 3.3, 3.75, 7.05, "vegan,paleo,plant-based"),
                ("Abacate", "Gordura", "g", 100, 160, 2, 8.5, 14.6, "vegan,paleo,frugivoro"),
                ("Castanha do Pará", "Gordura", "un", 1, 26, 0.5, 0.5, 2.5, "vegan,paleo"),

                # --- LATICÍNIOS (Variedade de Iogurtes e Requeijão) ---
                ("Leite Desnatado", "Carbo", "ml", 200, 70, 6, 10, 0, "lactovegetariano,onivoro"),
                ("Leite Integral", "Carbo", "ml", 200, 120, 6, 10, 6, "lactovegetariano,onivoro"),
                ("Iogurte Natural Desnatado", "Proteína", "g", 170, 80, 8, 12, 0, "lactovegetariano,onivoro"), # Copo padrão
                ("Iogurte Grego Zero", "Proteína", "g", 100, 56, 10, 4, 0, "lactovegetariano,onivoro"),
                ("Iogurte de Morango", "Carbo", "g", 170, 150, 5, 28, 2, "lactovegetariano,onivoro"),
                ("Requeijão Light", "Gordura", "g", 10, 18, 1.3, 0.3, 0.8, "lactovegetariano,onivoro"), # Colher de sopa rasa
                ("Queijo Minas Frescal", "Proteína", "fat", 30, 70, 5, 1, 5, "lactovegetariano,onivoro"),
                ("Mussarela", "Gordura", "fat", 20, 60, 5, 1, 5, "lactovegetariano,onivoro")
                # Adicione isso dentro da lista foods_data no seu método seed_food_database
                ("Mix de Legumes (Cozidos)", "Vegetais", "gramas", 100, 38, 2, 8, 0.2, "legumes,mix"),
                ("Mix de Salada (Folhosas)", "Vegetais", "gramas", 100, 15, 1.5, 3, 0.2, "salada,alface,folhas"),
            ]
            cursor.executemany("INSERT INTO foods (name, category, unit, base_qty, kcal, prot, carb, fat, tags) VALUES (?,?,?,?,?,?,?,?,?)", foods_data)
            self.conn.commit()

    def import_sample_diet(self, user_id):
        """Importa a dieta baseada no seu PDF apenas quando solicitado"""
        cursor = self.conn.cursor()
        ids = {}
        cursor.execute("SELECT name, id FROM foods")
        for row in cursor.fetchall(): ids[row[0]] = row[1]
        
        sample_diet = [
            (user_id, "Desjejum", ids.get("Whey Protein Concentrado"), 30),
            (user_id, "Desjejum", ids.get("Aveia em Flocos"), 20),
            (user_id, "Desjejum", ids.get("Banana Nanica"), 1),
            (user_id, "Desjejum", ids.get("Pasta de Amendoim"), 15),
            (user_id, "Almoço", ids.get("Arroz Branco Cozido"), 110),
            (user_id, "Almoço", ids.get("Feijão Carioca Cozido"), 90),
            (user_id, "Almoço", ids.get("Peito de Frango Grelhado"), 130),
            (user_id, "Almoço", ids.get("Mix de Legumes (Cozidos)"), 100),
            (user_id, "Almoço", ids.get("Mix de Salada (Folhosas)"), 100),
            (user_id, "Lanche", ids.get("Pão de Forma Integral"), 2),
            (user_id, "Lanche", ids.get("Ovo de Galinha (Inteiro)"), 2),
            (user_id, "Lanche", ids.get("Laranja Pera"), 2),
            (user_id, "Lanche", ids.get("Requeijão Light"), 10)
        ]
        
        # Filtra itens que por acaso não existam no banco
        valid_items = [x for x in sample_diet if x[2] is not None]
        cursor.executemany("INSERT INTO diet_log (user_id, meal_name, food_id, quantity) VALUES (?, ?, ?, ?)", valid_items)
        self.conn.commit()
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
    def search_foods(self, query):
        """Busca alimentos pelo nome sem limites baixos"""
        cursor = self.conn.cursor()
        
        # Aumentamos o limite para 100 para garantir que tudo apareça
        sql = """
            SELECT id, name, category, unit, base_qty, kcal, prot, carb, fat 
            FROM foods 
            WHERE name LIKE ? 
            ORDER BY name LIMIT 100
        """
        cursor.execute(sql, (f'%{query}%',))
        cols = ["id", "name", "category", "unit", "base_qty", "kcal", "prot", "carb", "fat"]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]
    def add_diet_item(self, user_id, meal_name, food_id, quantity):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO diet_log (user_id, meal_name, food_id, quantity) VALUES (?, ?, ?, ?)", 
                       (user_id, meal_name, food_id, quantity))
        self.conn.commit()

    def remove_diet_item(self, log_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM diet_log WHERE id = ?", (log_id,))
        self.conn.commit()
        
    def copy_meal_items(self, user_id, source_meal, target_meal):
        """Copia todos os alimentos de uma refeição para outra"""
        cursor = self.conn.cursor()
        
        # 1. Pega os itens da origem
        cursor.execute("SELECT food_id, quantity FROM diet_log WHERE user_id = ? AND meal_name = ?", (user_id, source_meal))
        items = cursor.fetchall()
        
        if not items: return False # Nada para copiar
        
        # 2. Insere na refeição destino
        new_items = [(user_id, target_meal, food_id, qty) for food_id, qty in items]
        cursor.executemany("INSERT INTO diet_log (user_id, meal_name, food_id, quantity) VALUES (?, ?, ?, ?)", new_items)
        
        self.conn.commit()
        return True
    
    def update_assessment_macros(self, assessment_id, tmb, tdee, target_kcal, target_prot, target_carb, target_fat):
        """Atualiza apenas os dados metabólicos e de dieta de uma avaliação existente"""
        cursor = self.conn.cursor()
        sql = """
            UPDATE assessments SET 
            tmb = ?, tdee = ?, 
            target_kcal = ?, target_prot = ?, target_carb = ?, target_fat = ?
            WHERE id = ?
        """
        cursor.execute(sql, (tmb, tdee, target_kcal, target_prot, target_carb, target_fat, assessment_id))
        self.conn.commit()
        
    def update_assessment_settings(self, assessment_id, activity_level, diet_goal, diet_intensity):
        """Atualiza as configurações de base da avaliação (para recalculo)"""
        cursor = self.conn.cursor()
        sql = """
            UPDATE assessments SET 
            activity_level = ?, 
            diet_goal = ?, 
            diet_intensity = ?
            WHERE id = ?
        """
        cursor.execute(sql, (activity_level, diet_goal, diet_intensity, assessment_id))
        self.conn.commit()