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
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.list import MDList, IconLeftWidget, OneLineAvatarIconListItem, OneLineListItem
from kivy.clock import Clock
from kivy.properties import DictProperty
from kivy.metrics import dp

# Importando os Módulos e Configurações
from src.config import ACTIVITY_LEVELS
from src.database.db_handler import DatabaseHandler
from src.modules.services.calculator import CalculatorService
from src.modules.services.report_service import ReportService
from src.modules.services.email_service import EmailService
from src.modules.ui.components import SectionCard, DetailRow, ComparisonRow, AssessmentItem

class FitnessApp(MDApp):
    current_user = DictProperty(None, allownone=True)
    
    # Variáveis de Estado para o Metabolismo
    activity_factor = 1.2 
    activity_text = "Sedentário (Pouco ou nenhum exercício)"

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.db = DatabaseHandler()
        self.inputs = {}
        self.dialog = None
        self.dialog_activity = None

        self.root_layout = MDBoxLayout(orientation='vertical')
        self.toolbar = MDTopAppBar(title="BioTracker Pro", elevation=4)
        self.root_layout.add_widget(self.toolbar)
        self.bottom_nav = MDBottomNavigation(selected_color_background="white", text_color_active="blue")

        # --- ABA 1: USUÁRIOS ---
        screen_users = MDBottomNavigationItem(name='screen_users', text='Usuários', icon='account-group')
        user_layout = MDBoxLayout(orientation='vertical', padding=20, spacing=10)
        
        self.input_name = MDTextField(hint_text="Nome Completo")
        self.input_cpf = MDTextField(hint_text="CPF", input_filter="int")
        self.input_email = MDTextField(hint_text="Email")
        
        user_layout.add_widget(MDLabel(text="Cadastrar / Selecionar", font_style="H6", size_hint_y=None, height=30))
        user_layout.add_widget(self.input_name)
        user_layout.add_widget(self.input_cpf)
        user_layout.add_widget(self.input_email)
        user_layout.add_widget(MDRaisedButton(text="CADASTRAR", on_release=self.register_user, size_hint_x=1))
        
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

        # Configurações Iniciais (Sexo / Limpar)
        config_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height="50dp", spacing="10dp")
        self.sex_switch = MDSwitch()
        self.sex_switch.bind(active=self.on_sex_change)
        self.label_sex = MDLabel(text="Sexo: Feminino", halign="center")
        
        config_layout.add_widget(self.label_sex)
        config_layout.add_widget(self.sex_switch)
        config_layout.add_widget(MDLabel(size_hint_x=1))
        config_layout.add_widget(MDIconButton(icon="eraser", on_release=self.clear_fields))
        form_layout.add_widget(config_layout)
        
        # Dados Gerais
        card_general = SectionCard("Dados Gerais")
        self.create_field(card_general, "age", "Idade", "numeric")
        self.create_field(card_general, "weight", "Peso (kg)", "numeric")
        self.create_field(card_general, "height", "Altura (m)", "numeric")
        form_layout.add_widget(card_general)
        
        # SELETOR DE ATIVIDADE (METABOLISMO)
        # Inicia com o valor padrão do Sedentário
        self.btn_activity = MDRectangleFlatButton(
            text="Nível de Atividade: Sedentário", 
            size_hint_x=1, 
            height="50dp",
            text_color="blue",
            line_color="blue",
            on_release=self.open_activity_dialog
        )
        form_layout.add_widget(self.btn_activity)

        # Dobras
        card_folds = SectionCard("Dobras (mm)")
        folds = [("subscapular", "Subescapular"), ("tricep", "Tricipital"), ("biceps", "Bicipital"),
                 ("chest", "Peitoral"), ("axillary", "Axilar Média"), ("suprailiac", "Supra-ilíaca"),
                 ("abdominal", "Abdominal"), ("thigh", "Coxa"), ("calf", "Panturrilha")]
        for k, l in folds: self.create_field(card_folds, k, l, "numeric")
        form_layout.add_widget(card_folds)

        # Perímetros
        card_perims = SectionCard("Perímetros (cm)")
        perims = [("shoulder", "Ombro"), ("thorax", "Tórax"), ("waist", "Cintura"), ("abdomen_perim", "Abdômen"),
                  ("hips", "Quadril"), ("arm_r", "Braço D"), ("arm_l", "Braço E"), ("forearm_r", "Antebr. D"),
                  ("forearm_l", "Antebr. E"), ("thigh_r", "Coxa D"), ("thigh_l", "Coxa E"), ("calf_r", "Pantur. D"),
                  ("calf_l", "Pantur. E")]
        for k, l in perims: self.create_field(card_perims, k, l, "numeric")
        form_layout.add_widget(card_perims)

        # Botão Salvar
        form_layout.add_widget(MDRaisedButton(text="SALVAR AVALIAÇÃO", size_hint_x=1, height="50dp", md_bg_color=(0, 0.7, 0, 1), on_release=self.calculate_and_save))
        
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

    # --- LÓGICA DO SELETOR DE ATIVIDADE ---
    def open_activity_dialog(self, instance):
        if not self.dialog_activity:
            # 1. Cria a lista de itens
            list_items = MDList()
            for text_label, factor in ACTIVITY_LEVELS.items():
                list_items.add_widget(
                    OneLineListItem(
                        text=text_label,
                        on_release=lambda x, f=factor, t=text_label: self.set_activity(f, t)
                    )
                )
            
            # 2. Envolve a lista em um ScrollView com altura definida
            # Isso garante que a lista apareça e seja rolável
            scroll = MDScrollView(
                size_hint_y=None,
                height="260dp"  # Altura fixa para o conteúdo do diálogo
            )
            scroll.add_widget(list_items)

            # 3. Cria o Dialog do tipo CUSTOM passando o scroll em content_cls
            self.dialog_activity = MDDialog(
                title="Selecione o Nível de Atividade",
                type="custom",
                content_cls=scroll,  # <--- AQUI ESTÁ A MÁGICA
                buttons=[
                    MDFlatButton(text="CANCELAR", on_release=lambda x: self.dialog_activity.dismiss())
                ]
            )
        self.dialog_activity.open()

    def set_activity(self, factor, text):
        """Atualiza o fator metabólico escolhido"""
        self.activity_factor = factor
        # Pega apenas a primeira parte do texto para o botão não ficar gigante
        short_text = text.split(" (")[0]
        self.activity_text = short_text
        self.btn_activity.text = f"Nível de Atividade: {short_text}"
        
        if self.dialog_activity:
            self.dialog_activity.dismiss()

    # --- MÉTODOS DE AÇÃO (USUÁRIOS/INTERFACE) ---
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
        self.current_user = user
        self.toolbar.title = f"BioTracker - {user['name']}"
        self.bottom_nav.switch_tab('screen_new')

    def set_default_sex(self, dt): 
        self.sex_switch.active = True; self.label_sex.text = "Sexo: Masculino"
    
    def create_field(self, card, key, hint, mode): 
        field = MDTextField(hint_text=hint, input_filter='float', mode="rectangle", size_hint_x=1)
        self.inputs[key] = field
        card.add_input(field)
    
    def on_sex_change(self, instance, value): 
        self.label_sex.text = "Sexo: Masculino" if value else "Sexo: Feminino"
    
    def clear_fields(self, instance):
        for field in self.inputs.values(): field.text = ""
        # Reseta para o padrão Sedentário
        default_text = "Sedentário (Pouco ou nenhum exercício)"
        self.set_activity(ACTIVITY_LEVELS[default_text], default_text)

    # --- CÁLCULO E SALVAMENTO ---
    def calculate_and_save(self, instance):
        if not self.current_user: 
            self.bottom_nav.switch_tab('screen_users')
            return
        try:
            data = {}
            for key, field in self.inputs.items():
                val = field.text.strip()
                data[key] = float(val.replace(',', '.')) if val else 0.0
            
            sex = "Masculino" if self.sex_switch.active else "Feminino"
            
            # Filtra dados para enviar ao serviço de cálculo
            folds_calc = {k: data[k] for k in ["chest", "axillary", "tricep", "subscapular", "abdominal", "suprailiac", "thigh"]}
            perims_calc = {k: data.get(k, 0) for k in ["waist", "hips", "arm_r", "thigh_r"]}
            
            # Executa cálculos (Incluindo o fator de atividade selecionado)
            results = CalculatorService.calculate_results(
                sex, 
                int(data.get('age',0)), 
                data.get('weight',0), 
                data.get('height',0), 
                folds_calc, 
                perims_calc, 
                self.activity_factor  # <--- Passa o fator escolhido na lista
            )

            # Prepara dados para o banco
            db_data = data.copy()
            db_data['sex'] = sex
            db_data['user_id'] = self.current_user['id']
            db_data['date'] = datetime.now().strftime("%d/%m/%Y %H:%M")
            db_data['activity_level'] = self.activity_text
            db_data.update(results)
            
            self.db.add_assessment(db_data)
            self.clear_fields(None)
            self.show_detail_modal(data=db_data)

        except ValueError as e: 
            self.show_dialog("Erro", str(e))

    # --- HISTÓRICO E MODAIS ---
    def load_history(self, instance):
        self.history_list.clear_widgets()
        if not self.current_user: return
        records = self.db.get_history(self.current_user['id'])
        for rec in records:
            rcq_val = rec.get('rcq') or 0.0
            bf_class = rec.get('bf_class') or "-"
            tdee_val = rec.get('tdee') or 0
            
            # Mostra GET no histórico
            item = AssessmentItem(
                text=f"{rec['date']}", 
                secondary_text=f"BF: {rec['bf_percent']:.1f}% | GET: {tdee_val:.0f}kcal", 
                tertiary_text=f"Peso: {rec['weight']}kg | RCQ: {rcq_val:.2f}", 
                data=rec, 
                on_release=lambda x: self.show_detail_modal(item=x)
            )
            item.add_widget(IconLeftWidget(icon="run" if rec['bf_percent'] < 20 else "human-handsup"))
            self.history_list.add_widget(item)

    def show_detail_modal(self, item=None, data=None):
        record = item.data if item else data
        content = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing="5dp", padding="10dp")

        # Botão PDF
        btn_email = MDRaisedButton(text="ENVIAR RELATÓRIO PDF (EMAIL)", md_bg_color=(0.8, 0.2, 0.2, 1), size_hint_x=1, on_release=lambda x: self.action_send_email(record))
        content.add_widget(btn_email); content.add_widget(MDRectangleFlatButton(size_hint_y=None, height="1dp", size_hint_x=1, opacity=0))

        # Funções Auxiliares de UI
        def add_header(text): 
            content.add_widget(MDLabel(text=text, font_style="Subtitle1", bold=True, size_hint_y=None, height=dp(30), theme_text_color="Primary"))
            content.add_widget(MDRectangleFlatButton(size_hint_y=None, height="1dp", size_hint_x=1, md_bg_color=(0.8,0.8,0.8,1)))
        
        def add_rows(fields_list):
            for label, key, unit in fields_list:
                val = record.get(key)
                val = val if val is not None else 0
                val_str = f"{val:.2f} {unit}" if isinstance(val, (int, float)) else str(val)
                content.add_widget(DetailRow(label, val_str))
            content.add_widget(MDLabel(size_hint_y=None, height=dp(10)))

        # Seções do Relatório
        add_header("METABOLISMO")
        add_rows([("TMB (Basal)", "tmb", "kcal"), ("Atividade", "activity_level", ""), ("GET (Total)", "tdee", "kcal")])

        add_header("COMPOSIÇÃO CORPORAL")
        add_rows([("Gordura Corporal", "bf_percent", "%"), ("Classificação BF", "bf_class", ""), ("Massa Gorda", "fat_mass", "kg"), ("Massa Magra", "lean_mass", "kg"), ("IMC", "bmi", "kg/m²")])
        
        add_header("ÍNDICES E ÁREAS")
        add_rows([("RCQ (Cintura/Quadril)", "rcq", ""), ("Área Musc. Braço", "ama", "cm²"), ("Classif. AMA", "ama_class", ""), ("Área Musc. Coxa", "tma", "cm²"), ("Classif. TMA", "tma_class", "")])

        add_header("ASSIMETRIA (D vs E)")
        segs = [("Braços", "arm_r", "arm_l"), ("Antebraços", "forearm_r", "forearm_l"), ("Coxas", "thigh_r", "thigh_l"), ("Panturrilhas", "calf_r", "calf_l")]
        for lbl, k1, k2 in segs:
            v1 = record.get(k1) or 0; v2 = record.get(k2) or 0
            content.add_widget(ComparisonRow(lbl, v1, v2))
        content.add_widget(MDLabel(size_hint_y=None, height=dp(10)))

        add_header("DOBRAS E MEDIDAS")
        dobras = [("Subescapular", "subscapular", "mm"), ("Tricipital", "tricep", "mm"), ("Peitoral", "chest", "mm"), ("Abdominal", "abdominal", "mm"), ("Coxa", "thigh", "mm"), ("Cintura", "waist", "cm"), ("Quadril", "hips", "cm")]
        add_rows(dobras)

        scroll = MDScrollView(size_hint_y=None, height="500dp")
        scroll.add_widget(content)
        
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