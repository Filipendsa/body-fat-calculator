import sqlite3
import math
import threading
import smtplib
import os
from datetime import datetime
from email.message import EmailMessage

# Carrega as variáveis do arquivo .env
from dotenv import load_dotenv
load_dotenv()

# Bibliotecas de PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton, MDRectangleFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDList, ThreeLineIconListItem, IconLeftWidget, OneLineAvatarIconListItem, OneLineListItem
from kivy.clock import Clock
from kivy.properties import StringProperty, DictProperty
from kivy.metrics import dp

# --- CONFIGURAÇÃO DE EMAIL (Lendo do .env) ---
SENDER_EMAIL = os.getenv("EMAIL_USER")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")
DATABASE_NAME = os.getenv("DB_NAME", "fitness_tracker_v5.db")

# --- SERVIÇO DE RELATÓRIO PDF ---
class ReportService:
    @staticmethod
    def generate_pdf(filename, user_data, assessment_data):
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # 1. Cabeçalho
        c.setFillColor(colors.HexColor("#1976D2"))
        c.rect(0, height - 3 * cm, width, 3 * cm, fill=1, stroke=0)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(2 * cm, height - 1.8 * cm, "BioTracker Pro")
        c.setFont("Helvetica", 12)
        c.drawString(2 * cm, height - 2.5 * cm, "Relatório de Avaliação Física & Metabólica")

        # 2. Dados
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 12)
        y = height - 4.5 * cm
        c.drawString(2 * cm, y, f"Cliente: {user_data['name']}")
        c.drawString(12 * cm, y, f"Data: {assessment_data['date']}")
        
        # 3. Resumo Principal
        y -= 2 * cm
        c.setStrokeColor(colors.HexColor("#E0E0E0"))
        c.setFillColor(colors.HexColor("#F5F5F5"))
        c.roundRect(1.5 * cm, y - 2*cm, width - 3*cm, 2.5*cm, 10, fill=1, stroke=1)
        
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width/2, y - 0.8*cm, f"Gordura Corporal: {assessment_data['bf_percent']:.2f}%")
        c.setFont("Helvetica", 10)
        c.drawCentredString(width/2, y - 1.5*cm, f"Classificação: {assessment_data.get('bf_class', '-')}")

        # 4. Metabolismo
        y -= 3.5 * cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Metabolismo Basal e Gasto Energético")
        c.line(2 * cm, y - 0.2*cm, width - 2*cm, y - 0.2*cm)
        
        y_met = y - 1 * cm
        c.setFont("Helvetica", 10)
        c.drawString(2 * cm, y_met, f"Taxa Metabólica Basal (TMB):")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(8 * cm, y_met, f"{assessment_data.get('tmb', 0):.0f} kcal/dia")
        
        c.setFont("Helvetica", 10)
        c.drawString(2 * cm, y_met - 0.6*cm, f"Nível de Atividade:")
        c.drawString(8 * cm, y_met - 0.6*cm, f"{assessment_data.get('activity_level', 'Não informado')}")

        c.setFont("Helvetica", 10)
        c.drawString(2 * cm, y_met - 1.2*cm, f"Gasto Energético Total (GET):")
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor("#D32F2F"))
        c.drawString(8 * cm, y_met - 1.2*cm, f"{assessment_data.get('tdee', 0):.0f} kcal/dia")
        c.setFillColor(colors.black)

        # 5. Mapa de Gordura
        y = y_met - 2.5 * cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Mapa de Distribuição (mm)")
        c.line(2 * cm, y - 0.2*cm, width - 2*cm, y - 0.2*cm)
        
        def draw_zone(x_pos, y_pos, label, value):
            val = float(value) if value else 0
            if val < 10: color = colors.green
            elif val < 20: color = colors.orange
            else: color = colors.red
            c.setFillColor(color)
            c.circle(x_pos, y_pos, 0.8 * cm, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(x_pos, y_pos - 3, f"{val:.0f}")
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 9)
            c.drawCentredString(x_pos, y_pos - 1.3 * cm, label)

        y_map = y - 2.5 * cm
        draw_zone(4 * cm, y_map, "Peitoral", assessment_data.get('chest', 0))
        draw_zone(7 * cm, y_map, "Axilar", assessment_data.get('axillary', 0))
        draw_zone(10 * cm, y_map, "Abdominal", assessment_data.get('abdominal', 0))
        draw_zone(13 * cm, y_map, "Supra-il.", assessment_data.get('suprailiac', 0))
        draw_zone(16 * cm, y_map, "Tríceps", assessment_data.get('tricep', 0))
        
        y_map_2 = y_map - 2.5 * cm
        draw_zone(8 * cm, y_map_2, "Coxa", assessment_data.get('thigh', 0))
        draw_zone(12 * cm, y_map_2, "Panturrilha", assessment_data.get('calf', 0))
        
        # 6. Tabelas Finais
        y = y_map_2 - 3.5 * cm
        c.setFont("Helvetica", 10)
        c.drawString(2 * cm, y, f"Massa Gorda: {assessment_data['fat_mass']:.2f} kg")
        c.drawString(2 * cm, y - 1*cm, f"Massa Magra: {assessment_data['lean_mass']:.2f} kg")
        c.drawString(10 * cm, y, f"RCQ: {assessment_data.get('rcq', 0):.2f}")
        c.drawString(10 * cm, y - 1*cm, f"IMC: {assessment_data['bmi']:.2f}")

        c.save()
        return filename

# --- SERVIÇO DE EMAIL (COM LIMPEZA AUTOMÁTICA) ---
class EmailService:
    @staticmethod
    def send_email_thread(user_email, user_name, pdf_path, callback_success, callback_error):
        def run():
            try:
                msg = EmailMessage()
                msg['Subject'] = f"Relatório BioTracker - {user_name}"
                msg['From'] = SENDER_EMAIL
                msg['To'] = user_email
                msg.set_content("Segue em anexo seu relatório de avaliação física e metabólica.")

                # Lê o arquivo para a memória
                with open(pdf_path, 'rb') as f:
                    file_data = f.read()
                    file_name = os.path.basename(pdf_path)
                    msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

                # Envia
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
                    smtp.send_message(msg)
                
                Clock.schedule_once(lambda dt: callback_success(), 0)

            except Exception as e:
                Clock.schedule_once(lambda dt: callback_error(str(e)), 0)
            
            finally:
                # --- LIMPEZA: APAGA O ARQUIVO PDF APÓS O ENVIO (OU ERRO) ---
                if os.path.exists(pdf_path):
                    try:
                        os.remove(pdf_path)
                        print(f"Arquivo temporário removido: {pdf_path}")
                    except Exception as cleanup_error:
                        print(f"Erro ao remover arquivo temporário: {cleanup_error}")

        threading.Thread(target=run).start()

# --- CAMADA DE DADOS (DATABASE) ---
class DatabaseHandler:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_NAME)
        self.create_tables()
        self.migrate_db()

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

# --- LÓGICA DE CÁLCULO ---
class CalculatorService:
    @staticmethod
    def calculate_bmr_tdee(sex, weight, height_m, age, activity_factor):
        height_cm = height_m * 100
        if sex == "Masculino":
            bmr = (10 * weight) + (6.25 * height_cm) - (5 * age) + 5
        else:
            bmr = (10 * weight) + (6.25 * height_cm) - (5 * age) - 161
        tdee = bmr * activity_factor
        return bmr, tdee

    @staticmethod
    def get_bf_classification(bf, sex, age):
        if not bf: return "-"
        if sex == "Masculino":
            if bf < 6: return "Risco"; 
            if bf < 14: return "Atleta"; 
            if bf < 25: return "Médio"; 
            return "Alto"
        else:
            if bf < 12: return "Risco"; 
            if bf < 20: return "Atleta"; 
            if bf < 32: return "Médio"; 
            return "Alto"

    @staticmethod
    def get_muscle_area_class(area, type_m):
        if not area: return "-"
        if type_m == "arm": return "Alta" if area > 75 else "Baixa" if area < 40 else "Média"
        return "Adequada" if area > 120 else "Baixa"

    @staticmethod
    def calculate_results(sex, age, weight, height, folds, perims, activity_factor=1.2):
        s7 = sum([folds[k] for k in ['chest','axillary','tricep','subscapular','abdominal','suprailiac','thigh']])
        s7_sq = s7 ** 2
        density = (1.112 - (0.00043499*s7) + (0.00000055*s7_sq) - (0.00028826*age)) if sex == "Masculino" else (1.097 - (0.00046971*s7) + (0.00000056*s7_sq) - (0.00012828*age))
        try: bf_percent = (495 / density) - 450
        except: bf_percent = 0.0
        
        fat_mass = weight * (bf_percent / 100); lean_mass = weight - fat_mass
        bmi = weight / (height * height) if height > 0 else 0
        rcq = perims.get('waist',0) / perims.get('hips',1) if perims.get('hips',0) > 0 else 0
        
        try: ama = ((perims.get('arm_r',0) - (math.pi * (folds['tricep']/10))) ** 2) / (4 * math.pi) - (10.0 if sex=="Masculino" else 6.5)
        except: ama = 0
        try: tma = ((perims.get('thigh_r',0) - (math.pi * (folds['thigh']/10))) ** 2) / (4 * math.pi)
        except: tma = 0
        
        tmb, tdee = CalculatorService.calculate_bmr_tdee(sex, weight, height, age, activity_factor)

        return {
            "bf_percent": bf_percent, "fat_mass": fat_mass, "lean_mass": lean_mass, "bmi": bmi,
            "rcq": rcq, "ama": ama, "tma": tma,
            "tmb": tmb, "tdee": tdee,
            "bf_class": CalculatorService.get_bf_classification(bf_percent, sex, age),
            "ama_class": CalculatorService.get_muscle_area_class(ama, "arm"),
            "tma_class": CalculatorService.get_muscle_area_class(tma, "thigh")
        }

# --- UI COMPONENTS ---
class SectionCard(MDCard):
    title = StringProperty("")
    def __init__(self, title, **kwargs):
        super().__init__(**kwargs); self.orientation = "vertical"; self.padding = "10dp"; self.size_hint_y = None; self.elevation = 2; self.radius = [10]; self.bind(minimum_height=self.setter('height'))
        self.add_widget(MDLabel(text=title, theme_text_color="Primary", font_style="H6", size_hint_y=None, height="30dp", bold=True))
        self.grid = MDGridLayout(cols=2, spacing="10dp", adaptive_height=True); self.add_widget(self.grid)
    def add_input(self, widget): self.grid.add_widget(widget)

class DetailRow(MDBoxLayout):
    def __init__(self, label, value, **kwargs):
        super().__init__(**kwargs); self.orientation = "horizontal"; self.size_hint_y = None; self.height = dp(24)
        self.add_widget(MDLabel(text=label, bold=True, size_hint_x=0.6, theme_text_color="Primary", font_style="Body2"))
        self.add_widget(MDLabel(text=str(value), halign="right", size_hint_x=0.4, theme_text_color="Secondary", font_style="Body2"))

class ComparisonRow(MDBoxLayout):
    def __init__(self, label, val_r, val_l, **kwargs):
        super().__init__(**kwargs); self.orientation = "horizontal"; self.size_hint_y = None; self.height = dp(24)
        diff = abs(val_r - val_l)
        self.add_widget(MDLabel(text=label, bold=True, size_hint_x=0.4, font_style="Body2"))
        self.add_widget(MDLabel(text=f"D: {val_r}", halign="center", size_hint_x=0.2, font_style="Caption"))
        self.add_widget(MDLabel(text=f"E: {val_l}", halign="center", size_hint_x=0.2, font_style="Caption"))
        self.add_widget(MDLabel(text=f"Δ: {diff:.1f}", halign="right", size_hint_x=0.2, font_style="Caption", markup=True))

class AssessmentItem(ThreeLineIconListItem): data = DictProperty({})

# --- APP PRINCIPAL ---
class FitnessApp(MDApp):
    current_user = DictProperty(None, allownone=True)
    activity_factor = 1.2
    activity_text = "Sedentário"

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.db = DatabaseHandler()
        self.inputs = {}
        self.dialog = None
        self.dialog_activity = None

        self.root_layout = MDBoxLayout(orientation='vertical')
        self.toolbar = MDTopAppBar(title="BioTracker Pro", elevation=4); self.root_layout.add_widget(self.toolbar)
        self.bottom_nav = MDBottomNavigation(selected_color_background="white", text_color_active="blue")

        # ABA 1: USUÁRIOS
        screen_users = MDBottomNavigationItem(name='screen_users', text='Usuários', icon='account-group')
        user_layout = MDBoxLayout(orientation='vertical', padding=20, spacing=10)
        self.input_name = MDTextField(hint_text="Nome Completo"); self.input_cpf = MDTextField(hint_text="CPF", input_filter="int"); self.input_email = MDTextField(hint_text="Email")
        user_layout.add_widget(MDLabel(text="Cadastrar / Selecionar", font_style="H6", size_hint_y=None, height=30))
        user_layout.add_widget(self.input_name); user_layout.add_widget(self.input_cpf); user_layout.add_widget(self.input_email)
        user_layout.add_widget(MDRaisedButton(text="CADASTRAR", on_release=self.register_user, size_hint_x=1))
        self.user_list = MDList(); user_scroll = MDScrollView(); user_scroll.add_widget(self.user_list); user_layout.add_widget(user_scroll)
        screen_users.add_widget(user_layout); self.bottom_nav.add_widget(screen_users)

        # ABA 2: AVALIAR
        screen_new = MDBottomNavigationItem(name='screen_new', text='Avaliar', icon='pencil-plus')
        scroll = MDScrollView(); form_layout = MDBoxLayout(orientation='vertical', padding="15dp", spacing="20dp", adaptive_height=True)
        config_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height="50dp", spacing="10dp")
        self.sex_switch = MDSwitch(); self.sex_switch.bind(active=self.on_sex_change); self.label_sex = MDLabel(text="Sexo: Feminino", halign="center")
        config_layout.add_widget(self.label_sex); config_layout.add_widget(self.sex_switch); config_layout.add_widget(MDLabel(size_hint_x=1)); config_layout.add_widget(MDIconButton(icon="eraser", on_release=self.clear_fields))
        form_layout.add_widget(config_layout)
        
        card_general = SectionCard("Dados Gerais"); self.create_field(card_general, "age", "Idade", "numeric"); self.create_field(card_general, "weight", "Peso (kg)", "numeric"); self.create_field(card_general, "height", "Altura (m)", "numeric"); form_layout.add_widget(card_general)
        
        self.btn_activity = MDRectangleFlatButton(text="Nível de Atividade: Sedentário", size_hint_x=1, on_release=self.open_activity_dialog)
        form_layout.add_widget(self.btn_activity)

        card_folds = SectionCard("Dobras (mm)"); folds = [("subscapular", "Subescapular"), ("tricep", "Tricipital"), ("biceps", "Bicipital"), ("chest", "Peitoral"), ("axillary", "Axilar Média"), ("suprailiac", "Supra-ilíaca"), ("abdominal", "Abdominal"), ("thigh", "Coxa"), ("calf", "Panturrilha")]
        for k, l in folds: self.create_field(card_folds, k, l, "numeric")
        form_layout.add_widget(card_folds)
        card_perims = SectionCard("Perímetros (cm)"); perims = [("shoulder", "Ombro"), ("thorax", "Tórax"), ("waist", "Cintura"), ("abdomen_perim", "Abdômen"), ("hips", "Quadril"), ("arm_r", "Braço D"), ("arm_l", "Braço E"), ("forearm_r", "Antebr. D"), ("forearm_l", "Antebr. E"), ("thigh_r", "Coxa D"), ("thigh_l", "Coxa E"), ("calf_r", "Pantur. D"), ("calf_l", "Pantur. E")]
        for k, l in perims: self.create_field(card_perims, k, l, "numeric")
        form_layout.add_widget(card_perims)
        form_layout.add_widget(MDRaisedButton(text="SALVAR AVALIAÇÃO", size_hint_x=1, height="50dp", md_bg_color=(0, 0.7, 0, 1), on_release=self.calculate_and_save))
        scroll.add_widget(form_layout); screen_new.add_widget(scroll); self.bottom_nav.add_widget(screen_new)

        # ABA 3: HISTÓRICO
        screen_history = MDBottomNavigationItem(name='screen_history', text='Histórico', icon='history', on_tab_press=self.load_history)
        self.history_list = MDList(); scroll_hist = MDScrollView(); scroll_hist.add_widget(self.history_list); screen_history.add_widget(scroll_hist); self.bottom_nav.add_widget(screen_history)
        self.root_layout.add_widget(self.bottom_nav); screen = MDScreen(); screen.add_widget(self.root_layout)
        Clock.schedule_once(self.set_default_sex, 0); Clock.schedule_once(lambda x: self.load_users(), 1)
        return screen

    # --- LÓGICA DE ATIVIDADE ---
    def open_activity_dialog(self, instance):
        if not self.dialog_activity:
            items = [("Sedentário (Pouco ou nenhum ex.)", 1.2), ("Leve (Ex. leve 1-3 dias/sem)", 1.375), ("Moderado (Ex. mod. 3-5 dias/sem)", 1.55), ("Alto (Ex. pesado 6-7 dias/sem)", 1.725), ("Extremo (Ex. muito pesado/físico)", 1.9)]
            list_items = MDList()
            for text, factor in items:
                list_items.add_widget(OneLineListItem(text=text, on_release=lambda x, f=factor, t=text: self.set_activity(f, t)))
            self.dialog_activity = MDDialog(title="Selecione o Nível de Atividade", type="confirmation", items=[list_items], buttons=[MDFlatButton(text="CANCELAR", on_release=lambda x: self.dialog_activity.dismiss())])
        self.dialog_activity.open()

    def set_activity(self, factor, text):
        self.activity_factor = factor; self.activity_text = text.split(" (")[0]
        self.btn_activity.text = f"Nível de Atividade: {self.activity_text}"; self.dialog_activity.dismiss()

    # --- ACTION METHODS ---
    def register_user(self, instance):
        name = self.input_name.text.strip(); cpf = self.input_cpf.text.strip(); email = self.input_email.text.strip()
        if not name: return
        self.db.add_user(name, cpf, email); self.input_name.text = ""; self.input_cpf.text = ""; self.load_users()

    def load_users(self):
        self.user_list.clear_widgets(); users = self.db.get_users()
        for u in users:
            item = OneLineAvatarIconListItem(text=f"{u['name']}", on_release=lambda x, user=u: self.select_user(user))
            item.add_widget(IconLeftWidget(icon="account-check"))
            self.user_list.add_widget(item)

    def select_user(self, user):
        self.current_user = user; self.toolbar.title = f"BioTracker - {user['name']}"; self.bottom_nav.switch_tab('screen_new')

    def set_default_sex(self, dt): self.sex_switch.active = True; self.label_sex.text = "Sexo: Masculino"
    def create_field(self, card, key, hint, mode): field = MDTextField(hint_text=hint, input_filter='float', mode="rectangle", size_hint_x=1); self.inputs[key] = field; card.add_input(field)
    def on_sex_change(self, instance, value): self.label_sex.text = "Sexo: Masculino" if value else "Sexo: Feminino"
    def clear_fields(self, instance):
        for field in self.inputs.values(): field.text = ""
        self.set_activity(1.2, "Sedentário")

    def calculate_and_save(self, instance):
        if not self.current_user: self.bottom_nav.switch_tab('screen_users'); return
        try:
            data = {}
            for key, field in self.inputs.items():
                val = field.text.strip(); data[key] = float(val.replace(',', '.')) if val else 0.0
            sex = "Masculino" if self.sex_switch.active else "Feminino"
            folds_calc = {k: data[k] for k in ["chest", "axillary", "tricep", "subscapular", "abdominal", "suprailiac", "thigh"]}
            perims_calc = {k: data.get(k, 0) for k in ["waist", "hips", "arm_r", "thigh_r"]}
            results = CalculatorService.calculate_results(sex, int(data.get('age',0)), data.get('weight',0), data.get('height',0), folds_calc, perims_calc, self.activity_factor)
            db_data = data.copy(); db_data['sex'] = sex; db_data['user_id'] = self.current_user['id']; db_data['date'] = datetime.now().strftime("%d/%m/%Y %H:%M"); db_data['activity_level'] = self.activity_text; db_data.update(results)
            self.db.add_assessment(db_data); self.clear_fields(None); self.show_detail_modal(data=db_data)
        except ValueError as e: self.show_dialog("Erro", str(e))

    def load_history(self, instance):
        self.history_list.clear_widgets()
        if not self.current_user: return
        records = self.db.get_history(self.current_user['id'])
        for rec in records:
            rcq_val = rec.get('rcq') or 0.0; bf_class = rec.get('bf_class') or "-"
            tdee_val = rec.get('tdee') or 0
            item = AssessmentItem(text=f"{rec['date']}", secondary_text=f"BF: {rec['bf_percent']:.1f}% | GET: {tdee_val:.0f}kcal", tertiary_text=f"Peso: {rec['weight']}kg | RCQ: {rcq_val:.2f}", data=rec, on_release=lambda x: self.show_detail_modal(item=x))
            item.add_widget(IconLeftWidget(icon="run" if rec['bf_percent'] < 20 else "human-handsup"))
            self.history_list.add_widget(item)

    # --- MODAL COMPLETO ---
    def show_detail_modal(self, item=None, data=None):
        record = item.data if item else data
        content = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing="5dp", padding="10dp")

        # Botão PDF
        btn_email = MDRaisedButton(text="ENVIAR RELATÓRIO PDF (EMAIL)", md_bg_color=(0.8, 0.2, 0.2, 1), size_hint_x=1, on_release=lambda x: self.action_send_email(record))
        content.add_widget(btn_email); content.add_widget(MDRectangleFlatButton(size_hint_y=None, height="1dp", size_hint_x=1, opacity=0))

        # Helpers
        def add_header(text): content.add_widget(MDLabel(text=text, font_style="Subtitle1", bold=True, size_hint_y=None, height=dp(30), theme_text_color="Primary")); content.add_widget(MDRectangleFlatButton(size_hint_y=None, height="1dp", size_hint_x=1, md_bg_color=(0.8,0.8,0.8,1)))
        def add_rows(fields_list):
            for label, key, unit in fields_list:
                val = record.get(key); val = val if val is not None else 0
                val_str = f"{val:.2f} {unit}" if isinstance(val, (int, float)) else str(val)
                content.add_widget(DetailRow(label, val_str))
            content.add_widget(MDLabel(size_hint_y=None, height=dp(10)))

        # 1. Metabolismo
        add_header("METABOLISMO")
        add_rows([("TMB (Basal)", "tmb", "kcal"), ("Atividade", "activity_level", ""), ("GET (Total)", "tdee", "kcal")])

        # 2. Composição
        add_header("COMPOSIÇÃO CORPORAL")
        add_rows([("Gordura Corporal", "bf_percent", "%"), ("Classificação BF", "bf_class", ""), ("Massa Gorda", "fat_mass", "kg"), ("Massa Magra", "lean_mass", "kg"), ("IMC", "bmi", "kg/m²")])
        
        # 3. Índices
        add_header("ÍNDICES E ÁREAS")
        add_rows([("RCQ (Cintura/Quadril)", "rcq", ""), ("Área Musc. Braço", "ama", "cm²"), ("Classif. AMA", "ama_class", ""), ("Área Musc. Coxa", "tma", "cm²"), ("Classif. TMA", "tma_class", "")])

        # 4. Assimetria
        add_header("ASSIMETRIA (D vs E)")
        segs = [("Braços", "arm_r", "arm_l"), ("Antebraços", "forearm_r", "forearm_l"), ("Coxas", "thigh_r", "thigh_l"), ("Panturrilhas", "calf_r", "calf_l")]
        for lbl, k1, k2 in segs:
            v1 = record.get(k1) or 0; v2 = record.get(k2) or 0
            content.add_widget(ComparisonRow(lbl, v1, v2))
        content.add_widget(MDLabel(size_hint_y=None, height=dp(10)))

        # 5. Dados Brutos
        add_header("DOBRAS E MEDIDAS")
        dobras = [("Subescapular", "subscapular", "mm"), ("Tricipital", "tricep", "mm"), ("Peitoral", "chest", "mm"), ("Abdominal", "abdominal", "mm"), ("Coxa", "thigh", "mm"), ("Cintura", "waist", "cm"), ("Quadril", "hips", "cm")]
        add_rows(dobras)

        scroll = MDScrollView(size_hint_y=None, height="500dp"); scroll.add_widget(content)
        self.dialog = MDDialog(title=f"Avaliação: {record['date']}", type="custom", content_cls=scroll, buttons=[MDFlatButton(text="FECHAR", on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()

    def action_send_email(self, record):
        if not self.current_user.get('email'): self.show_dialog("Erro", "Usuário sem email."); return
        pdf_name = f"relatorio_{self.current_user['id']}_{record['id']}.pdf"
        try:
            ReportService.generate_pdf(pdf_name, self.current_user, record)
            self.show_dialog("Enviando...", "Aguarde confirmação.")
            EmailService.send_email_thread(self.current_user['email'], self.current_user['name'], pdf_name, lambda: self.show_dialog("Sucesso", "Email enviado!"), lambda err: self.show_dialog("Erro", str(err)))
        except Exception as e: self.show_dialog("Erro", f"Falha PDF: {e}")

    def show_dialog(self, title, text):
        d = MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: d.dismiss())]); d.open()

if __name__ == "__main__":
    FitnessApp().run()