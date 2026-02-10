import sqlite3
from src.config import DATABASE_NAME

class DatabaseHandler:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_NAME)
        self.create_tables()
        self.migrate_db() # É aqui que ele cria as colunas novas

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
                
                -- Colunas V5
                rcq REAL, ama REAL, ama_class TEXT, tma REAL, tma_class TEXT, bf_class TEXT,
                tmb REAL, tdee REAL, activity_level TEXT,
                
                -- Colunas V6 (Onde estava dando erro)
                diet_goal TEXT, 
                target_bf REAL, 
                diet_intensity REAL, 
                prot_g_kg REAL,
                target_kcal REAL, 
                target_prot REAL, 
                target_carb REAL, 
                target_fat REAL,
                
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        self.conn.commit()

    def migrate_db(self):
        """
        Adiciona colunas novas em tabelas existentes sem perder dados.
        """
        cursor = self.conn.cursor()
        
        # Lista completa de colunas extras que foram adicionadas ao longo do tempo
        cols_to_add = [
            # V5
            ("rcq", "REAL DEFAULT 0"), 
            ("ama", "REAL DEFAULT 0"), 
            ("ama_class", "TEXT DEFAULT '-'"), 
            ("tma", "REAL DEFAULT 0"), 
            ("tma_class", "TEXT DEFAULT '-'"), 
            ("bf_class", "TEXT DEFAULT '-'"),
            ("tmb", "REAL DEFAULT 0"), 
            ("tdee", "REAL DEFAULT 0"),
            ("activity_level", "TEXT DEFAULT 'Sedentário'"),
            
            # V6 - Dieta (Aqui está a correção do seu erro)
            ("diet_goal", "TEXT DEFAULT 'Manter'"),
            ("target_bf", "REAL DEFAULT 0"),       # <--- O ERRO ESTAVA AQUI (Faltava essa coluna no banco)
            ("diet_intensity", "REAL DEFAULT 0"),
            ("prot_g_kg", "REAL DEFAULT 2.0"),
            ("target_kcal", "REAL DEFAULT 0"),
            ("target_prot", "REAL DEFAULT 0"),
            ("target_carb", "REAL DEFAULT 0"),
            ("target_fat", "REAL DEFAULT 0")
        ]
        
        for col_name, col_type in cols_to_add:
            try:
                # Tenta adicionar a coluna. Se ela já existir, o SQLite dá erro e o 'except' ignora.
                cursor.execute(f"ALTER TABLE assessments ADD COLUMN {col_name} {col_type}")
                print(f"Coluna adicionada com sucesso: {col_name}") # Log para debug
            except sqlite3.OperationalError:
                # Significa que a coluna já existe, segue o jogo.
                pass 
        
        self.conn.commit()

    def add_user(self, name, cpf, email):
        self.conn.execute("INSERT INTO users (name, cpf, email) VALUES (?, ?, ?)", (name, cpf, email))
        self.conn.commit()

    def get_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY name")
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def add_assessment(self, data):
        keys = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        query = f"INSERT INTO assessments ({keys}) VALUES ({placeholders})"
        
        cursor = self.conn.cursor()
        cursor.execute(query, tuple(data.values()))
        self.conn.commit()
        
        return cursor.lastrowid

    def get_history(self, user_id):
        cursor = self.conn.cursor(); cursor.execute("SELECT * FROM assessments WHERE user_id = ? ORDER BY date DESC", (user_id,))
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def delete_assessment(self, assessment_id):
        self.conn.execute("DELETE FROM assessments WHERE id = ?", (assessment_id,))
        self.conn.commit()