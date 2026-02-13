from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.list import MDList, TwoLineAvatarIconListItem, IconRightWidget, IconLeftWidget, OneLineListItem
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.gridlayout import MDGridLayout
from kivy.metrics import dp
from kivy.properties import StringProperty

# Import para recalcular
from src.modules.services.calculator import CalculatorService
from src.config import ACTIVITY_LEVELS

# --- COMPONENTE: BARRA DE NUTRIENTES ---
class NutrientBar(MDBoxLayout):
    def __init__(self, label, current, target, color, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"; self.size_hint_y = None; self.height = dp(40); self.spacing = dp(5)
        
        header = MDBoxLayout(size_hint_y=None, height=dp(20))
        header.add_widget(MDLabel(text=f"{label}", bold=True, theme_text_color="Primary", font_style="Caption"))
        header.add_widget(MDLabel(text=f"{current:.0f} / {target:.0f}", halign="right", theme_text_color="Secondary", font_style="Caption"))
        self.add_widget(header)
        
        progress = (current / target * 100) if target > 0 else 0
        self.add_widget(MDProgressBar(value=progress, color=color, size_hint_y=None, height=dp(10)))

# --- COMPONENTE: DIÁLOGO DE ADICIONAR ALIMENTO ---
class FoodSearchContent(MDBoxLayout):
    def __init__(self, db, add_callback, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.add_callback = add_callback
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(400) 
        self.selected_food = None

        # 1. Campo de Busca
        self.search_field = MDTextField(hint_text="Buscar alimento (ex: Arroz)", mode="rectangle")
        self.search_field.bind(text=self.on_search_text)
        self.add_widget(self.search_field)

        # 2. Lista de Resultados
        self.results_scroll = MDScrollView(size_hint_y=1)
        self.results_list = MDList()
        self.results_scroll.add_widget(self.results_list)
        self.add_widget(self.results_scroll)

        # 3. Área de Quantidade
        self.qty_layout = MDBoxLayout(size_hint_y=None, height=dp(60), spacing=10)
        self.qty_field = MDTextField(hint_text="Qtd", input_filter="float", size_hint_x=0.4, disabled=True)
        self.unit_label = MDLabel(text="g/ml", size_hint_x=0.2, halign="center")
        self.btn_confirm = MDRaisedButton(text="ADICIONAR", size_hint_x=0.4, disabled=True, on_release=self.finish_add)
        
        self.qty_layout.add_widget(self.qty_field)
        self.qty_layout.add_widget(self.unit_label)
        self.qty_layout.add_widget(self.btn_confirm)
        self.add_widget(self.qty_layout)

        self.on_search_text(None, "")

    def on_search_text(self, instance, text):
        self.results_list.clear_widgets()
        results = self.db.search_foods(text)
        for food in results:
            item = OneLineListItem(text=f"{food['name']} ({food['kcal']:.0f}kcal/100{food['unit']})", on_release=lambda x, f=food: self.select_food(f))
            self.results_list.add_widget(item)

    def select_food(self, food):
        self.selected_food = food
        self.search_field.text = food['name']
        self.unit_label.text = food['unit']
        self.qty_field.disabled = False
        self.qty_field.text = str(food['base_qty'])
        self.btn_confirm.disabled = False
        self.qty_field.focus = True

    def finish_add(self, instance):
        if self.selected_food and self.qty_field.text:
            try:
                qty = float(self.qty_field.text)
                self.add_callback(self.selected_food['id'], qty)
            except ValueError: pass

# --- TELA PRINCIPAL DA DIETA ---
class DietScreen(MDScreen):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.current_user_id = None
        self.target_data = None
        self.dialog_add = None
        self.current_meal_adding = None
        self.clipboard_meal = None 
        self.build_ui()

    def build_ui(self):
        self.main_layout = MDBoxLayout(orientation="vertical", spacing=10, padding=10)
        
        # 1. Resumo do Dia (Card)
        self.summary_card = MDCard(orientation="vertical", size_hint_y=None, height=dp(160), padding=15, radius=[15], elevation=2)
        
        # --- HEADER DO CARD COM BOTÃO DE RECALCULAR ---
        header_layout = MDBoxLayout(size_hint_y=None, height=dp(30))
        header_layout.add_widget(MDLabel(text="Resumo Diário", font_style="H6", bold=True, valign="center"))
        
        # Botão Refresh (CORRIGIDO: icon_size em vez de user_font_size)
        btn_recalc = MDIconButton(icon="refresh", theme_text_color="Custom", text_color=(0, 0.5, 1, 1), icon_size="24sp")
        btn_recalc.bind(on_release=self.recalculate_macros)
        header_layout.add_widget(btn_recalc)
        
        self.summary_card.add_widget(header_layout)
        
        self.bars_layout = MDBoxLayout(orientation="vertical", spacing=10)
        self.summary_card.add_widget(self.bars_layout)
        self.main_layout.add_widget(self.summary_card)

        # 2. Lista de Refeições
        scroll = MDScrollView()
        self.content_list = MDList()
        self.content_list.padding = (0, 0, 0, 50)
        scroll.add_widget(self.content_list)
        self.main_layout.add_widget(scroll)
        
        self.add_widget(self.main_layout)

    def load_diet(self, user_id, target_data=None):
        self.current_user_id = user_id
        if target_data: self.target_data = target_data
        
        diet_log = self.db.get_diet_log(user_id)
        
        meal_order = ["Desjejum", "Almoço", "Lanche", "Jantar"]
        meals_data = {m: [] for m in meal_order}
        
        total_day = {"kcal":0, "prot":0, "carb":0, "fat":0}
        
        for item in diet_log:
            m = item['meal']
            if m not in meals_data: meals_data[m] = []
            
            ratio = item['qty'] / item['base_qty']
            k = item['kcal'] * ratio
            p = item['prot'] * ratio
            c = item['carb'] * ratio
            f = item['fat'] * ratio
            
            total_day['kcal'] += k; total_day['prot'] += p; total_day['carb'] += c; total_day['fat'] += f
            
            item_desc = {
                "id": item['log_id'],
                "name": item['name'],
                "qty_str": f"{item['qty']:.0f}{item['unit']}",
                "macros": f"P:{p:.1f} C:{c:.1f} G:{f:.1f} | {k:.0f}kcal"
            }
            meals_data[m].append(item_desc)

        self._update_bars(total_day)
        self._render_meal_list(meals_data)

    def recalculate_macros(self, instance):
        if not self.target_data: return
        td = self.target_data
        
        act_factor = 1.2
        for k, v in ACTIVITY_LEVELS.items():
            if td['activity_level'] in k:
                act_factor = v
                break

        tmb, tdee = CalculatorService.calculate_bmr_tdee(
            td['sex'], td['weight'], td['height'], td['age'], act_factor
        )

        target_kcal, target_prot, target_carb, target_fat = CalculatorService.calculate_diet_macros(
            tdee, td['weight'], 
            td['diet_goal'], 
            td['diet_intensity'], 
            td['prot_g_kg']
        )

        self.db.update_assessment_macros(
            td['id'], tmb, tdee, target_kcal, target_prot, target_carb, target_fat
        )
        
        self.target_data['tmb'] = tmb
        self.target_data['tdee'] = tdee
        self.target_data['target_kcal'] = target_kcal
        self.target_data['target_prot'] = target_prot
        self.target_data['target_carb'] = target_carb
        self.target_data['target_fat'] = target_fat
        
        self.load_diet(self.current_user_id, self.target_data)

    def _update_bars(self, totals):
        self.bars_layout.clear_widgets()
        t_kcal = self.target_data.get('target_kcal', 2000) if self.target_data else 2000
        t_prot = self.target_data.get('target_prot', 150) if self.target_data else 150
        t_carb = self.target_data.get('target_carb', 200) if self.target_data else 200
        t_fat = self.target_data.get('target_fat', 60) if self.target_data else 60

        self.bars_layout.add_widget(NutrientBar("Calorias", totals['kcal'], t_kcal, (0,0,1,1)))
        
        macros_grid = MDGridLayout(cols=3, spacing=10)
        macros_grid.add_widget(NutrientBar("Proteína", totals['prot'], t_prot, (0, 0.8, 0, 1)))
        macros_grid.add_widget(NutrientBar("Carbo", totals['carb'], t_carb, (1, 0.6, 0, 1)))
        macros_grid.add_widget(NutrientBar("Gordura", totals['fat'], t_fat, (1, 0, 0, 1)))
        self.bars_layout.add_widget(macros_grid)

    def _render_meal_list(self, meals_data):
        self.content_list.clear_widgets()
        
        for meal_name, items in meals_data.items():
            header_layout = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), padding=(10,0), spacing=10, md_bg_color=(0.95, 0.95, 0.95, 1))
            header_layout.add_widget(MDLabel(text=meal_name.upper(), theme_text_color="Primary", font_style="Subtitle2", bold=True, valign="center"))
            
            # Botão COPIAR (CORRIGIDO: icon_size em vez de user_font_size)
            if items:
                btn_copy = MDIconButton(icon="content-copy", theme_text_color="Custom", text_color=(0.5, 0.5, 0.5, 1), icon_size="20sp")
                btn_copy.bind(on_release=lambda x, m=meal_name: self.copy_meal(m))
                header_layout.add_widget(btn_copy)

            # Botão COLAR (CORRIGIDO: icon_size em vez de user_font_size)
            if self.clipboard_meal and self.clipboard_meal != meal_name:
                btn_paste = MDIconButton(icon="content-paste", theme_text_color="Custom", text_color=(0, 0.5, 1, 1), icon_size="20sp")
                btn_paste.bind(on_release=lambda x, m=meal_name: self.paste_meal(m))
                header_layout.add_widget(btn_paste)
            
            self.content_list.add_widget(header_layout)
            
            for food in items:
                item = TwoLineAvatarIconListItem(
                    text=f"{food['name']} ({food['qty_str']})",
                    secondary_text=food['macros'],
                    _no_ripple_effect=True
                )
                item.add_widget(IconLeftWidget(icon="food-variant"))
                trash = IconRightWidget(icon="trash-can-outline", theme_text_color="Error")
                trash.bind(on_release=lambda x, log_id=food['id']: self.delete_item(log_id))
                item.add_widget(trash)
                self.content_list.add_widget(item)
            
            btn_add = MDFlatButton(
                text=f"+ Adicionar em {meal_name}",
                theme_text_color="Custom", text_color=(0, 0.5, 1, 1),
                pos_hint={'center_x': 0.5},
                on_release=lambda x, m=meal_name: self.open_add_dialog(m)
            )
            self.content_list.add_widget(btn_add)

    def copy_meal(self, meal_name):
        self.clipboard_meal = meal_name
        self.load_diet(self.current_user_id, self.target_data)

    def paste_meal(self, target_meal):
        if self.clipboard_meal:
            success = self.db.copy_meal_items(self.current_user_id, self.clipboard_meal, target_meal)
            if success:
                self.clipboard_meal = None
                self.load_diet(self.current_user_id, self.target_data)

    def open_add_dialog(self, meal_name):
        self.current_meal_adding = meal_name
        content = FoodSearchContent(self.db, self.confirm_add)
        self.dialog_add = MDDialog(title=f"Adicionar ao {meal_name}", type="custom", content_cls=content, buttons=[MDFlatButton(text="CANCELAR", on_release=lambda x: self.dialog_add.dismiss())])
        self.dialog_add.open()

    def confirm_add(self, food_id, qty):
        if self.current_user_id and self.current_meal_adding:
            self.db.add_diet_item(self.current_user_id, self.current_meal_adding, food_id, qty)
            self.dialog_add.dismiss()
            self.load_diet(self.current_user_id, self.target_data)

    def delete_item(self, log_id):
        self.db.remove_diet_item(log_id)
        self.load_diet(self.current_user_id, self.target_data)