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
from kivymd.uix.list import MDList, IconLeftWidget, IconRightWidget, OneLineAvatarIconListItem, OneLineListItem
from kivy.clock import Clock
from kivy.properties import DictProperty
from kivy.metrics import dp
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.slider import MDSlider
from kivymd.uix.card import MDCard  # <--- FALTAVA ESSE

from src.config import ACTIVITY_LEVELS
from src.database.db_handler import DatabaseHandler
from src.modules.services.calculator import CalculatorService
from src.modules.services.report_service import ReportService
from src.modules.services.email_service import EmailService
from src.modules.ui.components import SectionCard, AssessmentItem, LabelledSlider
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
        
        # 1. Verifica se a dieta já tem itens
        history = self.db.get_diet_log(user['id'])
        
        if not history:
            # Diálogo de confirmação
            self.dialog_import = MDDialog(
                title="Importar Dieta Padrão?",
                text="Deseja carregar a dieta baseada no plano de 2.600kcal (PDF Marcos Conti)?",
                buttons=[
                    MDFlatButton(text="NÃO", on_release=lambda x: self.finish_selection(user)),
                    MDRaisedButton(
                        text="IMPORTAR", 
                        md_bg_color=self.theme_cls.primary_color,
                        on_release=lambda x: self.execute_import(user)
                    )
                ]
            )
            self.dialog_import.open()
        else:
            self.finish_selection(user)

    def execute_import(self, user):
        self.db.import_sample_diet(user['id'])
        self.dialog_import.dismiss()
        self.finish_selection(user)
        self.show_dialog("Sucesso", "Dieta importada com sucesso!")

    def finish_selection(self, user):
        if hasattr(self, 'dialog_import'): self.dialog_import.dismiss()
        
        settings = self.db.get_user_diet_settings(user['id'])
        self.diet_container.clear_widgets()
        
        if settings:
            self.load_diet_dashboard(user['id'])
        else:
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
        self.current_view_record = item.data if item else data
        record = self.current_view_record
        
        # --- CORES DO TEMA ---
        C_PRIMARY = (0.1, 0.46, 0.82, 1) # Azul App
        C_BG_CARD = (0.97, 0.97, 0.97, 1) # Cinza muito leve
        
        # ScrollView Principal
        scroll = MDScrollView(size_hint_y=None, height=dp(550)) # Altura fixa grande
        
        # Container Principal
        main_content = MDBoxLayout(orientation="vertical", spacing=dp(15), padding=dp(25), size_hint_y=None)
        main_content.bind(minimum_height=main_content.setter('height'))

        # --- 1. CABEÇALHO (Data e Botões) ---
        header = MDBoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        # Data Grande
        date_txt = record['date'].split(' ')[0]
        header.add_widget(MDLabel(text=f"Avaliação: {date_txt}", font_style="H5", bold=True, theme_text_color="Primary", size_hint_x=0.6))
        
        # Botões de Ação
        btn_edit = MDIconButton(icon="pencil-outline", theme_text_color="Custom", text_color=C_PRIMARY, icon_size="28sp")
        btn_edit.bind(on_release=lambda x: self.open_edit_metabolism_dialog(record))
        
        btn_pdf = MDRaisedButton(text="GERAR PDF", md_bg_color=(0.8, 0.2, 0.2, 1), font_style="Button")
        btn_pdf.bind(on_release=lambda x: self.action_send_email(record))
        
        header.add_widget(btn_edit)
        header.add_widget(btn_pdf)
        main_content.add_widget(header)

        # --- 2. GRID DE 2 COLUNAS ---
        grid = MDGridLayout(cols=2, spacing=dp(30), size_hint_y=None, adaptive_height=True)

        # === COLUNA ESQUERDA: DIETA & MACROS ===
        col_diet = MDBoxLayout(orientation="vertical", spacing=dp(10), adaptive_height=True)
        
        # Título com Ícone
        title_box = MDBoxLayout(spacing=10, size_hint_y=None, height=dp(30))
        title_box.add_widget(MDIconButton(icon="silverware-fork-knife", icon_size="20sp", theme_text_color="Primary", disabled=True))
        title_box.add_widget(MDLabel(text="PLANEJAMENTO ALIMENTAR", font_style="H6", bold=True))
        col_diet.add_widget(title_box)

        # CARTÃO DE DESTAQUE (META CALÓRICA)
        target_kcal = record.get('target_kcal', 0)
        goal_text = record.get('diet_goal', '-').upper()
        
        hero_card = MDCard(orientation="vertical", size_hint_y=None, height=dp(90), padding=dp(15), radius=[10], md_bg_color=C_PRIMARY, elevation=2)
        hero_card.add_widget(MDLabel(text="META CALÓRICA DIÁRIA", theme_text_color="Custom", text_color=(1,1,1,0.8), font_style="Caption", halign="center"))
        hero_card.add_widget(MDLabel(text=f"{target_kcal:.0f} kcal", theme_text_color="Custom", text_color=(1,1,1,1), font_style="H4", bold=True, halign="center"))
        hero_card.add_widget(MDLabel(text=f"Objetivo: {goal_text}", theme_text_color="Custom", text_color=(1,1,1,0.8), font_style="Caption", halign="center"))
        col_diet.add_widget(hero_card)

        # Detalhes da Dieta
        col_diet.add_widget(MDLabel(text="", size_hint_y=None, height=dp(5)))
        tdee = record.get('tdee', 0)
        diff = target_kcal - tdee
        weekly = (diff * 7) / 7700
        change_txt = f"{'Ganhar' if weekly > 0 else 'Perder'} {abs(weekly):.2f} kg/sem"
        
        card_diet_details = MDCard(orientation="vertical", padding=dp(15), radius=[10], md_bg_color=C_BG_CARD, adaptive_height=True, elevation=0)
        self.add_detail_row(card_diet_details, "Intensidade", f"{record.get('diet_intensity',0):.0f}%")
        self.add_detail_row(card_diet_details, "Estimativa", change_txt)
        card_diet_details.add_widget(MDRectangleFlatButton(size_hint_y=None, height="1dp", size_hint_x=1, md_bg_color=(0.9,0.9,0.9,1))) # Separator
        self.add_detail_row(card_diet_details, "", "") # Espaço
        
        # Macros Coloridos
        self.create_macro_row(card_diet_details, "Proteína", f"{record.get('target_prot',0):.0f}g", (0, 0.7, 0, 1)) # Verde
        self.create_macro_row(card_diet_details, "Carboidrato", f"{record.get('target_carb',0):.0f}g", (1, 0.6, 0, 1)) # Laranja
        self.create_macro_row(card_diet_details, "Gordura", f"{record.get('target_fat',0):.0f}g", (1, 0.2, 0.2, 1)) # Vermelho
        
        col_diet.add_widget(card_diet_details)
        grid.add_widget(col_diet)

        # === COLUNA DIREITA: CORPO & METABOLISMO ===
        col_body = MDBoxLayout(orientation="vertical", spacing=dp(10), adaptive_height=True)
        
        # Título
        title_box2 = MDBoxLayout(spacing=10, size_hint_y=None, height=dp(30))
        title_box2.add_widget(MDIconButton(icon="human-male-height", icon_size="20sp", theme_text_color="Primary", disabled=True))
        title_box2.add_widget(MDLabel(text="CORPO & METABOLISMO", font_style="H6", bold=True))
        col_body.add_widget(title_box2)

        card_body = MDCard(orientation="vertical", padding=dp(15), radius=[10], md_bg_color=C_BG_CARD, adaptive_height=True, elevation=0)
        
        # Metabolismo
        card_body.add_widget(MDLabel(text="Energia", font_style="Subtitle2", theme_text_color="Primary"))
        self.add_detail_row(card_body, "Atividade", record.get('activity_level','-').split('(')[0])
        self.add_detail_row(card_body, "Basal (TMB)", f"{record.get('tmb',0):.0f} kcal")
        self.add_detail_row(card_body, "Gasto Total (GET)", f"{record.get('tdee',0):.0f} kcal", is_bold=True)
        
        # Divisor
        card_body.add_widget(MDLabel(text="", size_hint_y=None, height=dp(10)))
        card_body.add_widget(MDRectangleFlatButton(size_hint_y=None, height="1dp", size_hint_x=1, md_bg_color=(0.85,0.85,0.85,1)))
        card_body.add_widget(MDLabel(text="", size_hint_y=None, height=dp(10)))

        # Composição
        card_body.add_widget(MDLabel(text="Composição", font_style="Subtitle2", theme_text_color="Primary"))
        self.add_detail_row(card_body, "Peso Atual", f"{record.get('weight',0)} kg")
        
        # BF com cor de alerta
        bf = record.get('bf_percent', 0)
        bf_color = (0.8, 0, 0, 1) if bf > 25 else (0, 0.6, 0, 1) if bf < 15 else (0.3, 0.3, 0.3, 1)
        
        row_bf = MDBoxLayout(size_hint_y=None, height=dp(30))
        row_bf.add_widget(MDLabel(text="Gordura Corporal", font_style="Body2", theme_text_color="Secondary"))
        row_bf.add_widget(MDLabel(text=f"{bf:.1f}%", font_style="H6", bold=True, theme_text_color="Custom", text_color=bf_color, halign="right"))
        card_body.add_widget(row_bf)
        
        self.add_detail_row(card_body, "Massa Magra", f"{record.get('lean_mass',0):.1f} kg")
        self.add_detail_row(card_body, "Massa Gorda", f"{record.get('fat_mass',0):.1f} kg")
        
        col_body.add_widget(card_body)
        grid.add_widget(col_body)

        main_content.add_widget(grid)
        scroll.add_widget(main_content)

        self.dialog = MDDialog(
            type="custom",
            content_cls=scroll,
            size_hint_x=0.9, # Largo
            size_hint_y=0.9, # Alto
            buttons=[MDFlatButton(text="FECHAR", theme_text_color="Primary", on_release=lambda x: self.dialog.dismiss())]
        )
        self.dialog.open()

    def add_detail_row(self, layout, label, value, is_bold=False):
        row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(28))
        row.add_widget(MDLabel(text=label, font_style="Body2", theme_text_color="Secondary", size_hint_x=0.6))
        row.add_widget(MDLabel(text=str(value), font_style="Body1", bold=is_bold, halign="right", theme_text_color="Primary", size_hint_x=0.4))
        layout.add_widget(row)

    def create_macro_row(self, layout, label, value, color):
        row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(30), spacing=5)
        # Bolinha colorida
        dot = MDIconButton(icon="circle", icon_size="10sp", theme_text_color="Custom", text_color=color, size_hint=(None, None), size=(dp(20), dp(30)))
        row.add_widget(dot)
        row.add_widget(MDLabel(text=label, font_style="Body2", bold=True, size_hint_x=0.5))
        row.add_widget(MDLabel(text=value, font_style="Body1", halign="right", size_hint_x=0.4))
        layout.add_widget(row)

    def open_edit_metabolism_dialog(self, record):
        """Abre um diálogo para editar Atividade e Intensidade"""
        content = MDBoxLayout(orientation="vertical", size_hint_y=None, height=dp(280), spacing=dp(15), padding=dp(10))
        
        # 1. Seletor de Atividade
        content.add_widget(MDLabel(text="Nível de Atividade", font_style="Subtitle2"))
        
        from kivymd.uix.menu import MDDropdownMenu
        self.btn_act_select = MDRectangleFlatButton(text=record['activity_level'], size_hint_x=1)
        
        menu_items = [{"text": k, "viewclass": "OneLineListItem", "on_release": lambda x=k: self.set_edit_activity(x)} for k in ACTIVITY_LEVELS.keys()]
        self.menu_activity = MDDropdownMenu(caller=self.btn_act_select, items=menu_items, width_mult=4)
        self.btn_act_select.bind(on_release=lambda x: self.menu_activity.open())
        content.add_widget(self.btn_act_select)

        # 2. Seletor de Objetivo (REMOVIDO MDSwitch para evitar erro 'thumb')
        content.add_widget(MDLabel(text="Objetivo da Dieta", font_style="Subtitle2"))
        
        goals_box = MDBoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(45))
        self.btn_edit_cut = MDRaisedButton(text="Cutting", elevation=0, size_hint_x=0.5)
        self.btn_edit_cut.bind(on_release=lambda x: self.set_edit_goal("Cutting"))
        
        self.btn_edit_bulk = MDRaisedButton(text="Bulking", elevation=0, size_hint_x=0.5)
        self.btn_edit_bulk.bind(on_release=lambda x: self.set_edit_goal("Bulking"))
        
        goals_box.add_widget(self.btn_edit_cut)
        goals_box.add_widget(self.btn_edit_bulk)
        content.add_widget(goals_box)
        
        # 3. Slider de Intensidade
        content.add_widget(MDLabel(text="Intensidade do Superávit/Déficit", font_style="Subtitle2"))
        self.slider_edit_int = MDSlider(min=0, max=30, value=record.get('diet_intensity', 10), step=1)
        self.lbl_edit_int = MDLabel(text=f"{self.slider_edit_int.value:.0f}%", halign="center", font_style="H6", theme_text_color="Primary")
        
        # Atualiza o label quando o slider move
        self.slider_edit_int.bind(value=lambda instance, val: setattr(self.lbl_edit_int, 'text', f"{val:.0f}%"))
        
        content.add_widget(self.slider_edit_int)
        content.add_widget(self.lbl_edit_int)

        # Inicialização
        self.temp_edit_goal = record['diet_goal']
        self.update_edit_goal_buttons()

        self.dialog_edit = MDDialog(
            title="Editar Perfil Metabólico",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="CANCELAR", on_release=lambda x: self.dialog_edit.dismiss()),
                MDRaisedButton(text="SALVAR & RECALCULAR", md_bg_color=(0,0.7,0,1), on_release=lambda x: self.save_edited_metabolism(record))
            ]
        )
        self.dialog_edit.open()

    def set_edit_activity(self, text):
        self.btn_act_select.text = text
        self.menu_activity.dismiss()

    def set_edit_goal(self, goal):
        self.temp_edit_goal = goal
        self.update_edit_goal_buttons()

    def update_edit_goal_buttons(self):
        # Atualiza visualmente qual botão está selecionado
        active = self.theme_cls.primary_color
        inactive = (0.9, 0.9, 0.9, 1)
        self.btn_edit_cut.md_bg_color = active if self.temp_edit_goal == "Cutting" else inactive
        self.btn_edit_cut.text_color = (1,1,1,1) if self.temp_edit_goal == "Cutting" else (0,0,0,1)
        self.btn_edit_bulk.md_bg_color = active if self.temp_edit_goal == "Bulking" else inactive
        self.btn_edit_bulk.text_color = (1,1,1,1) if self.temp_edit_goal == "Bulking" else (0,0,0,1)

    def save_edited_metabolism(self, record):
        # 1. Coleta os novos dados do diálogo de edição
        new_activity_text = self.btn_act_select.text
        new_activity_factor = ACTIVITY_LEVELS.get(new_activity_text, 1.2)
        new_goal = self.temp_edit_goal
        new_intensity = self.slider_edit_int.value
        
        # 2. Salva as novas configurações de entrada (Atividade/Meta) no banco
        self.db.update_assessment_settings(record['id'], new_activity_text, new_goal, new_intensity)
        
        # 3. RECALCULA TUDO USANDO A FÓRMULA DE MIFFLIN COM OS NOVOS DADOS
        # Precisamos garantir que o peso, altura e idade usados aqui sejam os da avaliação original
        tmb, tdee = CalculatorService.calculate_bmr_tdee(
            record['sex'], record['weight'], record['height'], record['age'], new_activity_factor
        )
        
        # Recalcula as metas de calorias e macros
        tk, tp, tc, tf = CalculatorService.calculate_diet_macros(
            tdee, record['weight'], new_goal, new_intensity, record['prot_g_kg']
        )
        
        # 4. ATUALIZA OS RESULTADOS NO BANCO DE DADOS (Essa parte é vital!)
        self.db.update_assessment_macros(record['id'], tmb, tdee, tk, tp, tc, tf)
        
        # 5. Atualiza o dicionário local 'record' para que a UI mostre os dados novos ao reabrir
        record.update({
            'activity_level': new_activity_text, 
            'diet_goal': new_goal, 
            'diet_intensity': new_intensity,
            'tmb': tmb, 
            'tdee': tdee, 
            'target_kcal': tk, 
            'target_prot': tp, 
            'target_carb': tc, 
            'target_fat': tf
        })
        
        # 6. Fecha os diálogos e atualiza a tela de nutrição caso ela esteja aberta
        self.dialog_edit.dismiss()
        if hasattr(self, 'dialog'): self.dialog.dismiss()
        
        # Recarrega a tela de Nutrição com os novos macros alvo
        self.load_diet_dashboard(self.current_user['id'])
        
        # Reabre o modal de detalhes para confirmar que mudou
        self.show_detail_modal(data=record)
        self.show_dialog("Sucesso", f"Metas atualizadas! Nova meta: {tk:.0f} kcal")
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