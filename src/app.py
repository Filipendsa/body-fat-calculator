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
# ADICIONADO: IconRightWidget
from kivymd.uix.list import MDList, IconLeftWidget, IconRightWidget, OneLineAvatarIconListItem, OneLineListItem
from kivy.clock import Clock
from kivy.properties import DictProperty
from kivy.metrics import dp
from kivymd.uix.gridlayout import MDGridLayout

# Importando Módulos
from src.config import ACTIVITY_LEVELS
from src.database.db_handler import DatabaseHandler
from src.modules.services.calculator import CalculatorService
from src.modules.services.report_service import ReportService
from src.modules.services.email_service import EmailService
from src.modules.ui.components import SectionCard, DetailRow, ComparisonRow, AssessmentItem, LabelledSlider
from src.modules.ui.diet_screen import DietScreen
from src.modules.ui.diet_setup_screen import DietSetupScreen

class FitnessApp(MDApp):
    current_user = DictProperty(None, allownone=True)
    activity_factor = 1.2 
    activity_text = "Sedentário"
    diet_goal = "Manter"

    def build(self):
        # ... (Todo o método build permanece IGUAL) ...
        self.theme_cls.primary_palette = "Blue"
        self.db = DatabaseHandler()
        self.inputs = {}
        self.dialog = None
        self.dialog_activity = None
        self.dialog_delete = None # Novo dialog para confirmação

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
        user_layout.add_widget(self.input_name); user_layout.add_widget(self.input_cpf); user_layout.add_widget(self.input_email)
        user_layout.add_widget(MDRaisedButton(text="CADASTRAR", on_release=self.register_user, size_hint_x=1))
        self.user_list = MDList(); user_scroll = MDScrollView(); user_scroll.add_widget(self.user_list); user_layout.add_widget(user_scroll)
        screen_users.add_widget(user_layout); self.bottom_nav.add_widget(screen_users)

        # --- ABA 2: AVALIAR ---
        screen_new = MDBottomNavigationItem(name='screen_new', text='Avaliar', icon='pencil-plus')
        scroll = MDScrollView()
        form_layout = MDBoxLayout(orientation='vertical', padding="15dp", spacing="20dp", adaptive_height=True)

        # Configurações Iniciais
        config_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height="50dp", spacing="10dp")
        self.sex_switch = MDSwitch(); self.sex_switch.bind(active=self.on_sex_change); self.label_sex = MDLabel(text="Sexo: Feminino", halign="center")
        config_layout.add_widget(self.label_sex); config_layout.add_widget(self.sex_switch); config_layout.add_widget(MDLabel(size_hint_x=1)); config_layout.add_widget(MDIconButton(icon="eraser", on_release=self.clear_fields))
        form_layout.add_widget(config_layout)
        
        # Dados Gerais
        card_general = SectionCard("Dados Gerais"); self.create_field(card_general, "age", "Idade", "numeric"); self.create_field(card_general, "weight", "Peso (kg)", "numeric"); self.create_field(card_general, "height", "Altura (m)", "numeric"); form_layout.add_widget(card_general)
        
        # Metabolismo
        self.btn_activity = MDRectangleFlatButton(text="Nível de Atividade: Sedentário", size_hint_x=1, height="50dp", text_color="blue", line_color="blue", on_release=self.open_activity_dialog)
        form_layout.add_widget(self.btn_activity)

        # Dobras
        card_folds = SectionCard("Dobras (mm)"); folds = [("subscapular", "Subescapular"), ("tricep", "Tricipital"), ("biceps", "Bicipital"), ("chest", "Peitoral"), ("axillary", "Axilar Média"), ("suprailiac", "Supra-ilíaca"), ("abdominal", "Abdominal"), ("thigh", "Coxa"), ("calf", "Panturrilha")]
        for k, l in folds: self.create_field(card_folds, k, l, "numeric")
        form_layout.add_widget(card_folds)

        # Perímetros
        card_perims = SectionCard("Perímetros (cm)"); perims = [("shoulder", "Ombro"), ("thorax", "Tórax"), ("waist", "Cintura"), ("abdomen_perim", "Abdômen"), ("hips", "Quadril"), ("arm_r", "Braço D"), ("arm_l", "Braço E"), ("forearm_r", "Antebr. D"), ("forearm_l", "Antebr. E"), ("thigh_r", "Coxa D"), ("thigh_l", "Coxa E"), ("calf_r", "Pantur. D"), ("calf_l", "Pantur. E")]
        for k, l in perims: self.create_field(card_perims, k, l, "numeric")
        form_layout.add_widget(card_perims)

        # === SEÇÃO DIETA ===
        card_diet = SectionCard("Planejamento da Dieta")
        lbl_goal = MDLabel(text="Objetivo:", theme_text_color="Secondary", size_hint_y=None, height=30)
        card_diet.add_widget(lbl_goal)
        
        grid_buttons = MDGridLayout(cols=3, size_hint_y=None, height=50, spacing=10)
        self.btn_cut = MDRaisedButton(text="Cutting", size_hint_x=1, elevation=0, on_release=lambda x: self.set_diet_goal("Cutting"))
        self.btn_maintain = MDRaisedButton(text="Manter", size_hint_x=1, elevation=1, on_release=lambda x: self.set_diet_goal("Manter"))
        self.btn_bulk = MDRaisedButton(text="Bulking", size_hint_x=1, elevation=0, on_release=lambda x: self.set_diet_goal("Bulking"))
        
        grid_buttons.add_widget(self.btn_cut)
        grid_buttons.add_widget(self.btn_maintain)
        grid_buttons.add_widget(self.btn_bulk)
        card_diet.add_widget(grid_buttons)

        self.slider_intensity = LabelledSlider("Déficit/Superávit Calórico (%)", 0, 30, 20, fmt="{:.0f}%")
        card_diet.add_widget(self.slider_intensity)
        self.slider_target_bf = LabelledSlider("Meta de Gordura Corporal (%)", 4, 35, 12, fmt="{:.1f}%")
        card_diet.add_widget(self.slider_target_bf)
        self.slider_protein = LabelledSlider("Proteína (g/kg de peso)", 1.2, 3.5, 2.0, step=0.1, fmt="{:.1f} g/kg")
        card_diet.add_widget(self.slider_protein)
        form_layout.add_widget(card_diet)

        form_layout.add_widget(MDRaisedButton(text="SALVAR AVALIAÇÃO", size_hint_x=1, height="50dp", md_bg_color=(0, 0.7, 0, 1), on_release=self.calculate_and_save))
        scroll.add_widget(form_layout); screen_new.add_widget(scroll); self.bottom_nav.add_widget(screen_new)

        # ABA 3: NUTRIÇÃO (Lógica dinâmica)
        self.screen_diet_nav = MDBottomNavigationItem(name='screen_diet', text='Nutrição', icon='food-apple')
        self.diet_container = MDBoxLayout() # Container vazio para trocar telas
        self.screen_diet_nav.add_widget(self.diet_container)
        self.bottom_nav.add_widget(self.screen_diet_nav)
        
        self.diet_view = DietScreen(self.db)
        self.diet_setup_view = DietSetupScreen(self.db, save_callback=self.on_diet_setup_complete)
        
        # --- ABA 4: HISTÓRICO ---
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

    def set_diet_goal(self, goal):
        self.diet_goal = goal
        
        # Cores
        active_color = self.theme_cls.primary_color  # Azul
        inactive_color = (0.9, 0.9, 0.9, 1)          # Cinza Claro
        text_active = (1, 1, 1, 1)                   # Branco
        text_inactive = (0, 0, 0, 1)                 # Preto

        # Reseta todos para inativo
        self.btn_cut.md_bg_color = inactive_color
        self.btn_cut.text_color = text_inactive
        self.btn_cut.elevation = 0
        
        self.btn_maintain.md_bg_color = inactive_color
        self.btn_maintain.text_color = text_inactive
        self.btn_maintain.elevation = 0
        
        self.btn_bulk.md_bg_color = inactive_color
        self.btn_bulk.text_color = text_inactive
        self.btn_bulk.elevation = 0
        
        # Ativa o selecionado
        if goal == "Cutting": 
            self.btn_cut.md_bg_color = active_color
            self.btn_cut.text_color = text_active
            self.btn_cut.elevation = 4
        elif goal == "Manter": 
            self.btn_maintain.md_bg_color = active_color
            self.btn_maintain.text_color = text_active
            self.btn_maintain.elevation = 4
        elif goal == "Bulking": 
            self.btn_bulk.md_bg_color = active_color
            self.btn_bulk.text_color = text_active
            self.btn_bulk.elevation = 4

    def open_activity_dialog(self, instance):
        if not self.dialog_activity:
            list_items = MDList()
            for text_label, factor in ACTIVITY_LEVELS.items():
                list_items.add_widget(OneLineListItem(text=text_label, on_release=lambda x, f=factor, t=text_label: self.set_activity(f, t)))
            scroll = MDScrollView(size_hint_y=None, height="260dp"); scroll.add_widget(list_items)
            self.dialog_activity = MDDialog(title="Selecione o Nível de Atividade", type="custom", content_cls=scroll, buttons=[MDFlatButton(text="CANCELAR", on_release=lambda x: self.dialog_activity.dismiss())])
        self.dialog_activity.open()

    def set_activity(self, factor, text):
        self.activity_factor = factor; self.activity_text = text.split(" (")[0]
        self.btn_activity.text = f"Nível de Atividade: {self.activity_text}"
        if self.dialog_activity: self.dialog_activity.dismiss()

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
        
        # Verifica se o usuário já tem preferências de dieta salvas
        settings = self.db.get_user_diet_settings(user['id'])
        
        self.diet_container.clear_widgets()
        if settings:
            # Se tem config, mostra a DIETA (Dashboard)
            self.load_diet_dashboard(user['id'])
        else:
            # Se não tem, mostra o SETUP
            self.diet_setup_view.load_data(user['id'])
            self.diet_container.add_widget(self.diet_setup_view)
        
        self.bottom_nav.switch_tab('screen_new')
        
    def set_default_sex(self, dt): self.sex_switch.active = True; self.label_sex.text = "Sexo: Masculino"
    def create_field(self, card, key, hint, mode): field = MDTextField(hint_text=hint, input_filter='float', mode="rectangle", size_hint_x=1); self.inputs[key] = field; card.add_input(field)
    def on_sex_change(self, instance, value): self.label_sex.text = "Sexo: Masculino" if value else "Sexo: Feminino"
    
    def clear_fields(self, instance):
        for field in self.inputs.values(): field.text = ""
        self.set_activity(1.2, "Sedentário"); self.set_diet_goal("Manter")

    def on_diet_setup_complete(self, user_id):
        """Chamado quando o usuário termina de configurar a dieta"""
        self.show_dialog("Sucesso", "Preferências alimentares salvas!")
        self.diet_container.clear_widgets()
        self.load_diet_dashboard(user_id)

    def load_diet_dashboard(self, user_id):
        # Pega a última avaliação para saber as calorias alvo
        last_assessment = self.db.get_history(user_id)
        target_data = last_assessment[0] if last_assessment else None
        
        self.diet_view.load_diet(user_id, target_data)
        self.diet_container.add_widget(self.diet_view)
        
    def calculate_and_save(self, instance):
        if not self.current_user: self.bottom_nav.switch_tab('screen_users'); return
        try:
            data = {}
            for key, field in self.inputs.items():
                val = field.text.strip(); data[key] = float(val.replace(',', '.')) if val else 0.0
            sex = "Masculino" if self.sex_switch.active else "Feminino"
            folds_calc = {k: data[k] for k in ["chest", "axillary", "tricep", "subscapular", "abdominal", "suprailiac", "thigh"]}
            perims_calc = {k: data.get(k, 0) for k in ["waist", "hips", "arm_r", "thigh_r"]}
            diet_config = {'goal': self.diet_goal, 'intensity': self.slider_intensity.value, 'prot_g_kg': self.slider_protein.value}
            results = CalculatorService.calculate_results(sex, int(data.get('age',0)), data.get('weight',0), data.get('height',0), folds_calc, perims_calc, self.activity_factor, diet_config=diet_config)
            db_data = data.copy(); db_data['sex'] = sex; db_data['user_id'] = self.current_user['id']; db_data['date'] = datetime.now().strftime("%d/%m/%Y %H:%M"); db_data['activity_level'] = self.activity_text
            db_data['diet_goal'] = self.diet_goal; db_data['target_bf'] = self.slider_target_bf.value; db_data['diet_intensity'] = self.slider_intensity.value; db_data['prot_g_kg'] = self.slider_protein.value
            db_data.update(results)
            new_id = self.db.add_assessment(db_data)
            db_data['id'] = new_id 
            self.clear_fields(None)
            self.show_detail_modal(data=db_data)
        except ValueError as e: self.show_dialog("Erro", str(e))

    # --- ATUALIZADO: HISTÓRICO COM BOTÃO DE DELETAR ---
    def load_history(self, instance):
        self.history_list.clear_widgets()
        if not self.current_user: return
        records = self.db.get_history(self.current_user['id'])
        for rec in records:
            rcq_val = rec.get('rcq') or 0.0; bf_class = rec.get('bf_class') or "-"; tdee_val = rec.get('tdee') or 0
            
            # Item da lista
            item = AssessmentItem(
                text=f"{rec['date']} | {rec.get('diet_goal', 'Manter')}", 
                secondary_text=f"BF: {rec['bf_percent']:.1f}% | Meta Dieta: {rec.get('target_kcal', 0):.0f}kcal", 
                tertiary_text=f"Peso: {rec['weight']}kg | GET: {tdee_val:.0f}kcal", 
                data=rec, 
                on_release=lambda x: self.show_detail_modal(item=x)
            )
            
            # Ícone Esquerdo (Tipo de atividade/status)
            item.add_widget(IconLeftWidget(icon="run" if rec['bf_percent'] < 20 else "human-handsup"))
            
            # NOVO: Ícone Direito (Lixeira para deletar)
            # Usamos lambda x, id=rec['id']: ... para capturar o ID correto no loop
            trash_btn = IconRightWidget(
                icon="trash-can",
                on_release=lambda x, i=rec['id']: self.confirm_delete_dialog(i)
            )
            item.add_widget(trash_btn)
            
            self.history_list.add_widget(item)

    # --- LÓGICA DE DELETAR ---
    def confirm_delete_dialog(self, assessment_id):
        if not self.dialog_delete:
            self.dialog_delete = MDDialog(
                title="Excluir Avaliação?",
                text="Esta ação não pode ser desfeita.",
                type="alert",
                buttons=[
                    MDFlatButton(text="CANCELAR", on_release=lambda x: self.dialog_delete.dismiss()),
                    MDRaisedButton(
                        text="EXCLUIR", 
                        md_bg_color=(1, 0, 0, 1), # Vermelho
                        on_release=lambda x: self.execute_delete(assessment_id)
                    )
                ],
            )
        # Atualiza o comando do botão de excluir para o ID atual
        # Acessa o segundo botão (MDRaisedButton) da lista de botões
        self.dialog_delete.buttons[1].bind(on_release=lambda x: self.execute_delete(assessment_id))
        self.dialog_delete.open()

    def execute_delete(self, assessment_id):
        self.db.delete_assessment(assessment_id)
        self.dialog_delete.dismiss()
        self.load_history(None)
        self.show_dialog("Sucesso", "Registro excluído.")

    def show_detail_modal(self, item=None, data=None):
        record = item.data if item else data
        
        # Aumentamos o spacing e padding para não ficar exprimido
        content = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(12), padding=dp(15))
        
        btn_email = MDRaisedButton(
            text="ENVIAR RELATÓRIO PDF (EMAIL)", 
            md_bg_color=(0.8, 0.2, 0.2, 1), 
            font_style="Subtitle2", # Fonte do botão mais encorpada
            size_hint_x=1, 
            height=dp(50), # Botão um pouco mais alto
            on_release=lambda x: self.action_send_email(record)
        )
        content.add_widget(btn_email)
        content.add_widget(MDBoxLayout(size_hint_y=None, height=dp(10))) # Espaço extra abaixo do botão

        # --- A MÁGICA VISUAL ACONTECE AQUI ---
        def add_header(text): 
            # Título maior (H6) e usando a cor azul padrão do App
            content.add_widget(MDLabel(text=text, font_style="H6", bold=True, size_hint_y=None, height=dp(40), theme_text_color="Primary"))
            
            # CORREÇÃO: Linha fina de 1 pixel elegante, em vez do botão quadrado cinza
            content.add_widget(MDBoxLayout(size_hint_y=None, height=dp(1), md_bg_color=(0.8, 0.8, 0.8, 1)))
            
            # Espacinho abaixo da linha
            content.add_widget(MDBoxLayout(size_hint_y=None, height=dp(5)))
        
        def add_rows(fields_list):
            for label, key, unit in fields_list:
                val = record.get(key)
                val = val if val is not None else 0
                val_str = f"{val:.2f} {unit}" if isinstance(val, (int, float)) else str(val)
                content.add_widget(DetailRow(label, val_str))
            
            # Espaço generoso entre o fim de um bloco e o próximo título
            content.add_widget(MDBoxLayout(size_hint_y=None, height=dp(15)))

        # --- CONTEÚDO ---
        add_header("DIETA & METAS")
        
        target_bf = record.get('target_bf', 0)
        tdee = record.get('tdee', 0)
        target_kcal = record.get('target_kcal', 0)
        
        if tdee > 0 and target_kcal > 0:
            daily_diff = target_kcal - tdee 
            weekly_weight_change = (daily_diff * 7) / 7700
            
            if weekly_weight_change > 0:
                previsao_texto = f"Ganhar {weekly_weight_change:.2f} kg/sem"
            elif weekly_weight_change < 0:
                previsao_texto = f"Perder {abs(weekly_weight_change):.2f} kg/sem"
            else:
                previsao_texto = "Manter Peso"
        else:
            previsao_texto = "-"

        content.add_widget(DetailRow("Objetivo", record.get('diet_goal', '-')))
        content.add_widget(DetailRow("Estimativa", previsao_texto))
        content.add_widget(DetailRow("Meta BF%", f"{target_bf:.1f}%"))
        
        add_rows([
            ("Calorias Dieta", "target_kcal", "kcal"), 
            ("Proteína", "target_prot", "g"), 
            ("Carbo", "target_carb", "g"), 
            ("Gordura", "target_fat", "g")
        ])

        add_header("METABOLISMO")
        add_rows([
            ("TMB (Basal)", "tmb", "kcal"), 
            ("Atividade", "activity_level", ""), 
            ("GET (Total)", "tdee", "kcal")
        ])
        
        add_header("COMPOSIÇÃO CORPORAL")
        add_rows([
            ("Gordura Corporal", "bf_percent", "%"), 
            ("Classif. BF", "bf_class", ""), 
            ("Massa Gorda", "fat_mass", "kg"), 
            ("Massa Magra", "lean_mass", "kg"), 
            ("IMC", "bmi", "kg/m²")
        ])
        
        # ScrollView mais alto para acompanhar o novo tamanho do conteúdo
        scroll = MDScrollView(size_hint_y=None, height="600dp") 
        scroll.add_widget(content)
        
        self.dialog = MDDialog(
            title=f"Avaliação de {record['date'].split(' ')[0]}", # Simplifica o título para só a data
            type="custom", 
            content_cls=scroll, 
            buttons=[
                MDFlatButton(
                    text="FECHAR", 
                    theme_text_color="Custom", 
                    text_color=self.theme_cls.primary_color, 
                    font_style="Button",
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
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