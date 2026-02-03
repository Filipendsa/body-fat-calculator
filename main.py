import sqlite3
from datetime import datetime
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
from kivymd.uix.list import MDList, ThreeLineIconListItem, IconLeftWidget, OneLineAvatarIconListItem
from kivy.clock import Clock
from kivy.properties import StringProperty, DictProperty
from kivy.metrics import dp

# --- CAMADA DE DADOS (DATABASE) ---
class DatabaseHandler:
    def __init__(self, db_name="fitness_tracker_v3.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

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

    def add_user(self, name, cpf, email):
        self.conn.execute("INSERT INTO users (name, cpf, email) VALUES (?, ?, ?)", (name, cpf, email))
        self.conn.commit()

    def get_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY name")
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def add_assessment(self, data):
        keys = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        query = f"INSERT INTO assessments ({keys}) VALUES ({placeholders})"
        self.conn.execute(query, tuple(data.values()))
        self.conn.commit()

    def get_history(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM assessments WHERE user_id = ? ORDER BY date DESC", (user_id,))
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

# --- LÓGICA DE CÁLCULO ---
class CalculatorService:
    @staticmethod
    def calculate_results(sex, age, weight, height, folds):
        s7 = (folds['chest'] + folds['axillary'] + folds['tricep'] + 
              folds['subscapular'] + folds['abdominal'] + 
              folds['suprailiac'] + folds['thigh'])
        s7_sq = s7 ** 2

        if sex == "Masculino":
            density = 1.112 - (0.00043499 * s7) + (0.00000055 * s7_sq) - (0.00028826 * age)
        else:
            density = 1.097 - (0.00046971 * s7) + (0.00000056 * s7_sq) - (0.00012828 * age)

        try:
            bf_percent = (495 / density) - 450
        except ZeroDivisionError:
            bf_percent = 0.0

        fat_mass = weight * (bf_percent / 100)
        lean_mass = weight - fat_mass
        bmi = weight / (height * height) if height > 0 else 0

        return {
            "bf_percent": bf_percent, "fat_mass": fat_mass,
            "lean_mass": lean_mass, "bmi": bmi
        }

# --- UI COMPONENTS ---
class SectionCard(MDCard):
    title = StringProperty("")
    def __init__(self, title, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = "10dp"
        self.size_hint_y = None
        self.elevation = 2
        self.radius = [10]
        self.bind(minimum_height=self.setter('height'))
        self.add_widget(MDLabel(text=title, theme_text_color="Primary", font_style="H6", size_hint_y=None, height="30dp", bold=True))
        self.grid = MDGridLayout(cols=2, spacing="10dp", adaptive_height=True)
        self.add_widget(self.grid)

    def add_input(self, widget):
        self.grid.add_widget(widget)

class DetailRow(MDBoxLayout):
    """Linha customizada para o Modal de Detalhes (Evita sobreposição)"""
    def __init__(self, label, value, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(24) # Altura fixa para ficar organizado
        self.add_widget(MDLabel(text=label, bold=True, size_hint_x=0.6, theme_text_color="Primary", font_style="Body2"))
        self.add_widget(MDLabel(text=str(value), halign="right", size_hint_x=0.4, theme_text_color="Secondary", font_style="Body2"))

class AssessmentItem(ThreeLineIconListItem):
    data = DictProperty({})

# --- APP PRINCIPAL ---
class FitnessApp(MDApp):
    current_user = DictProperty(None, allownone=True)

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.db = DatabaseHandler()
        self.inputs = {}
        self.dialog = None
        
        self.root_layout = MDBoxLayout(orientation='vertical')
        self.toolbar = MDTopAppBar(title="BioTracker Pro", elevation=4)
        self.root_layout.add_widget(self.toolbar)

        # Guardamos referencia do bottom_nav para trocar abas via código
        self.bottom_nav = MDBottomNavigation(selected_color_background="white", text_color_active="blue")

        # --- ABA 1: USUÁRIOS ---
        screen_users = MDBottomNavigationItem(name='screen_users', text='Usuários', icon='account-group')
        user_layout = MDBoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Form Cadastro
        self.input_name = MDTextField(hint_text="Nome Completo")
        self.input_cpf = MDTextField(hint_text="CPF", input_filter="int")
        self.input_email = MDTextField(hint_text="Email")
        btn_add_user = MDRaisedButton(text="CADASTRAR", on_release=self.register_user, size_hint_x=1)
        
        user_layout.add_widget(MDLabel(text="Cadastrar / Selecionar", font_style="H6", size_hint_y=None, height=30))
        user_layout.add_widget(self.input_name)
        user_layout.add_widget(self.input_cpf)
        user_layout.add_widget(self.input_email)
        user_layout.add_widget(btn_add_user)
        
        # Lista Usuários
        self.user_list = MDList()
        user_scroll = MDScrollView()
        user_scroll.add_widget(self.user_list)
        user_layout.add_widget(user_scroll)
        
        screen_users.add_widget(user_layout)
        self.bottom_nav.add_widget(screen_users)

        # --- ABA 2: AVALIAR ---
        screen_new = MDBottomNavigationItem(name='screen_new', text='Avaliar', icon='pencil-plus')
        scroll = MDScrollView()
        form_layout = MDBoxLayout(orientation='vertical', padding="15dp", spacing="20dp", adaptive_height=True)

        config_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height="50dp", spacing="10dp")
        self.sex_switch = MDSwitch()
        self.sex_switch.bind(active=self.on_sex_change)
        self.label_sex = MDLabel(text="Sexo: Feminino", halign="center")
        btn_clear = MDIconButton(icon="eraser", on_release=self.clear_fields)
        
        config_layout.add_widget(self.label_sex)
        config_layout.add_widget(self.sex_switch)
        config_layout.add_widget(MDLabel(size_hint_x=1))
        config_layout.add_widget(btn_clear)
        form_layout.add_widget(config_layout)

        card_general = SectionCard("Dados Gerais")
        self.create_field(card_general, "age", "Idade", "numeric")
        self.create_field(card_general, "weight", "Peso (kg)", "numeric")
        self.create_field(card_general, "height", "Altura (m)", "numeric")
        form_layout.add_widget(card_general)

        card_folds = SectionCard("Dobras (mm)")
        folds = [("subscapular", "Subescapular"), ("tricep", "Tricipital"), ("biceps", "Bicipital"),
                 ("chest", "Peitoral"), ("axillary", "Axilar Média"), ("suprailiac", "Supra-ilíaca"),
                 ("abdominal", "Abdominal"), ("thigh", "Coxa"), ("calf", "Panturrilha")]
        for k, l in folds: self.create_field(card_folds, k, l, "numeric")
        form_layout.add_widget(card_folds)

        card_perims = SectionCard("Perímetros (cm)")
        perims = [("shoulder", "Ombro"), ("thorax", "Tórax"), ("waist", "Cintura"), ("abdomen_perim", "Abdômen"),
                  ("hips", "Quadril"), ("arm_r", "Braço D"), ("arm_l", "Braço E"), ("forearm_r", "Antebr. D"),
                  ("forearm_l", "Antebr. E"), ("thigh_r", "Coxa D"), ("thigh_l", "Coxa E"), ("calf_r", "Pantur. D"),
                  ("calf_l", "Pantur. E")]
        for k, l in perims: self.create_field(card_perims, k, l, "numeric")
        form_layout.add_widget(card_perims)

        btn_save = MDRaisedButton(text="SALVAR AVALIAÇÃO", size_hint_x=1, height="50dp", md_bg_color=(0, 0.7, 0, 1), on_release=self.calculate_and_save)
        form_layout.add_widget(btn_save)
        scroll.add_widget(form_layout)
        screen_new.add_widget(scroll)
        self.bottom_nav.add_widget(screen_new)

        # --- ABA 3: HISTÓRICO ---
        screen_history = MDBottomNavigationItem(name='screen_history', text='Histórico', icon='history', on_tab_press=self.load_history)
        self.history_list = MDList()
        scroll_hist = MDScrollView()
        scroll_hist.add_widget(self.history_list)
        screen_history.add_widget(scroll_hist)
        self.bottom_nav.add_widget(screen_history)

        self.root_layout.add_widget(self.bottom_nav)
        screen = MDScreen()
        screen.add_widget(self.root_layout)

        Clock.schedule_once(self.set_default_sex, 0)
        Clock.schedule_once(lambda x: self.load_users(), 1)

        return screen

    # --- USER MANAGEMENT ---
    def register_user(self, instance):
        name = self.input_name.text.strip()
        cpf = self.input_cpf.text.strip()
        email = self.input_email.text.strip()
        if not name:
            self.show_dialog("Erro", "Nome obrigatório.")
            return
        self.db.add_user(name, cpf, email)
        self.input_name.text = ""
        self.input_cpf.text = ""
        self.load_users()

    def load_users(self):
        self.user_list.clear_widgets()
        users = self.db.get_users()
        for u in users:
            item = OneLineAvatarIconListItem(text=f"{u['name']}", on_release=lambda x, user=u: self.select_user(user))
            item.add_widget(IconLeftWidget(icon="account-check"))
            self.user_list.add_widget(item)

    def select_user(self, user):
        self.current_user = user
        self.toolbar.title = f"BioTracker - {user['name']}"
        # FLUXO AUTOMÁTICO: Vai para a aba de avaliação
        self.bottom_nav.switch_tab('screen_new') 

    # --- CALCULATOR & LOGIC ---
    def set_default_sex(self, dt):
        self.sex_switch.active = True
        self.label_sex.text = "Sexo: Masculino"

    def create_field(self, card, key, hint, mode):
        field = MDTextField(hint_text=hint, input_filter='float', mode="rectangle", size_hint_x=1)
        self.inputs[key] = field
        card.add_input(field)

    def on_sex_change(self, instance, value):
        self.label_sex.text = "Sexo: Masculino" if value else "Sexo: Feminino"

    def clear_fields(self, instance):
        for field in self.inputs.values(): field.text = ""

    def calculate_and_save(self, instance):
        if not self.current_user:
            self.show_dialog("Atenção", "Selecione um usuário na aba 'Usuários' primeiro.")
            self.bottom_nav.switch_tab('screen_users')
            return

        try:
            data = {}
            required_calc = ["age", "weight", "height", "chest", "axillary", "tricep", "subscapular", "abdominal", "suprailiac", "thigh"]
            
            for key, field in self.inputs.items():
                val = field.text.strip()
                if not val:
                    if key in required_calc: raise ValueError(f"Campo '{key}' é obrigatório.")
                    data[key] = 0.0
                else:
                    data[key] = float(val.replace(',', '.'))

            sex = "Masculino" if self.sex_switch.active else "Feminino"
            folds_calc = {k: data[k] for k in ["chest", "axillary", "tricep", "subscapular", "abdominal", "suprailiac", "thigh"]}
            results = CalculatorService.calculate_results(sex, int(data['age']), data['weight'], data['height'], folds_calc)

            db_data = data.copy()
            db_data['sex'] = sex
            db_data['user_id'] = self.current_user['id']
            db_data['date'] = datetime.now().strftime("%d/%m/%Y %H:%M")
            db_data.update(results)
            
            self.db.add_assessment(db_data)
            self.clear_fields(None)
            
            # FLUXO AUTOMÁTICO: Mostra resultado imediatamente
            self.show_detail_modal(data=db_data)

        except ValueError as e:
            self.show_dialog("Erro", str(e))

    def load_history(self, instance):
        self.history_list.clear_widgets()
        if not self.current_user:
            self.history_list.add_widget(ThreeLineIconListItem(text="Selecione um usuário primeiro"))
            return

        records = self.db.get_history(self.current_user['id'])
        if not records:
            self.history_list.add_widget(ThreeLineIconListItem(text="Nenhuma avaliação encontrada."))
            return

        for rec in records:
            item = AssessmentItem(
                text=f"{rec['date']}",
                secondary_text=f"Gordura: {rec['bf_percent']:.1f}% | Peso: {rec['weight']}kg",
                tertiary_text="Toque para ver detalhes",
                data=rec,
                on_release=lambda x: self.show_detail_modal(item=x)
            )
            icon_name = "run" if rec['bf_percent'] < 20 else "human-handsup"
            item.add_widget(IconLeftWidget(icon=icon_name))
            self.history_list.add_widget(item)

    # --- NOVO MODAL (VISUAL CORRIGIDO) ---
    def show_detail_modal(self, item=None, data=None):
        # Aceita dados vindos do clique da lista (item) ou direto do cálculo (data)
        record = item.data if item else data
        
        # Container Principal Vertical
        content = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing="5dp", padding="10dp")

        # Função Helper para criar seções
        def add_header(text):
            content.add_widget(MDLabel(text=text, font_style="Subtitle1", bold=True, size_hint_y=None, height=dp(30), theme_text_color="Primary"))
            content.add_widget(MDRectangleFlatButton(size_hint_y=None, height="1dp", size_hint_x=1, md_bg_color=(0.8,0.8,0.8,1))) # Separator

        def add_rows(fields_list):
            for label, key, unit in fields_list:
                val = record.get(key, 0)
                # Formata valor
                val_str = f"{val:.2f} {unit}"
                row = DetailRow(label, val_str)
                content.add_widget(row)
            content.add_widget(MDLabel(size_hint_y=None, height=dp(10))) # Spacer

        # 1. Resultados Principais
        add_header("RESULTADOS")
        add_rows([
            ("Gordura Corporal", "bf_percent", "%"),
            ("Massa Gorda", "fat_mass", "kg"),
            ("Massa Magra", "lean_mass", "kg"),
            ("IMC", "bmi", "kg/m²")
        ])

        # 2. Dobras
        add_header("DOBRAS CUTÂNEAS")
        add_rows([
            ("Subescapular", "subscapular", "mm"), ("Tricipital", "tricep", "mm"),
            ("Bicipital", "biceps", "mm"), ("Peitoral", "chest", "mm"),
            ("Axilar Média", "axillary", "mm"), ("Supra-ilíaca", "suprailiac", "mm"),
            ("Abdominal", "abdominal", "mm"), ("Coxa", "thigh", "mm"),
            ("Panturrilha", "calf", "mm")
        ])

        # 3. Perímetros
        add_header("PERÍMETROS")
        add_rows([
            ("Ombro", "shoulder", "cm"), ("Toráx", "thorax", "cm"),
            ("Cintura", "waist", "cm"), ("Abdômen", "abdomen_perim", "cm"),
            ("Quadril", "hips", "cm"), 
            ("Braço (D)", "arm_r", "cm"), ("Braço (E)", "arm_l", "cm"),
            ("Coxa (D)", "thigh_r", "cm"), ("Coxa (E)", "thigh_l", "cm")
        ])

        # Scroll wrapper
        scroll = MDScrollView(size_hint_y=None, height="450dp")
        scroll.add_widget(content)

        self.dialog = MDDialog(
            title=f"Relatório: {record['date']}",
            type="custom",
            content_cls=scroll,
            buttons=[MDFlatButton(text="FECHAR", on_release=lambda x: self.dialog.dismiss())]
        )
        self.dialog.open()

    def show_dialog(self, title, text):
        d = MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: d.dismiss())])
        d.open()

if __name__ == "__main__":
    FitnessApp().run()