from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
# CORREÇÃO AQUI: Adicionado OneLineListItem na lista de imports
from kivymd.uix.list import MDList, OneLineAvatarIconListItem, IconLeftWidget, IconRightWidget, OneLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.card import MDCard
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp
from kivy.properties import StringProperty, BooleanProperty

from src.config import DIET_TYPES

# Item da lista de seleção de alimentos
class FoodSelectionItem(OneLineAvatarIconListItem):
    food_id = 0
    def __init__(self, food_id, name, category, is_selected=False, is_allergy=False, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.text = name
        self.food_id = food_id
        self.callback = callback
        self._no_ripple_effect = True

        # Checkbox "Tenho Acesso" (Esquerda)
        self.check = IconLeftWidget(icon="checkbox-marked" if is_selected else "checkbox-blank-outline")
        self.check.bind(on_release=self.toggle_selection)
        self.add_widget(self.check)

        # Botão Alergia (Direita)
        self.allergy_btn = IconRightWidget(
            icon="alert-circle" if is_allergy else "alert-circle-outline", 
            theme_text_color="Custom", 
            text_color=(1,0,0,1) if is_allergy else (0.5,0.5,0.5,1)
        )
        self.allergy_btn.bind(on_release=self.toggle_allergy)
        self.add_widget(self.allergy_btn)

    def toggle_selection(self, instance):
        is_active = self.check.icon == "checkbox-marked"
        self.check.icon = "checkbox-blank-outline" if is_active else "checkbox-marked"
        if self.callback: self.callback(self.food_id, "select", not is_active)

    def toggle_allergy(self, instance):
        is_allergy = self.allergy_btn.icon == "alert-circle"
        self.allergy_btn.icon = "alert-circle-outline" if is_allergy else "alert-circle"
        self.allergy_btn.text_color = (0.5,0.5,0.5,1) if is_allergy else (1,0,0,1)
        # Se tem alergia, desmarca o acesso
        if not is_allergy: 
            self.check.icon = "checkbox-blank-outline"
            if self.callback: self.callback(self.food_id, "select", False)
        
        if self.callback: self.callback(self.food_id, "allergy", not is_allergy)

class DietSetupScreen(MDScreen):
    def __init__(self, db, save_callback, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.save_callback = save_callback
        self.selected_diet_type = "Onívora (Padrão)"
        self.user_id = None
        self.selected_foods = set()
        self.excluded_foods = set()
        self.menu_diet = None
        self.build_ui()

    def build_ui(self):
        layout = MDBoxLayout(orientation="vertical", spacing=10, padding=10)
        
        # 1. Seletor de Tipo de Dieta
        card_type = MDCard(orientation="vertical", size_hint_y=None, height=dp(110), padding=10, radius=[10], elevation=1)
        card_type.add_widget(MDLabel(text="1. Escolha o Tipo de Dieta", font_style="Subtitle2", theme_text_color="Primary", size_hint_y=None, height=dp(25)))
        
        self.btn_diet_type = MDRaisedButton(text=self.selected_diet_type, size_hint_x=1, on_release=self.open_diet_menu)
        card_type.add_widget(self.btn_diet_type)
        
        self.lbl_diet_desc = MDLabel(text=DIET_TYPES[self.selected_diet_type], theme_text_color="Secondary", font_style="Caption", size_hint_y=None, height=dp(35))
        card_type.add_widget(self.lbl_diet_desc)
        layout.add_widget(card_type)

        # 2. Lista de Alimentos (Acervo)
        layout.add_widget(MDLabel(text="2. Selecione o que você come (e Alergias)", font_style="Subtitle2", size_hint_y=None, height=dp(30)))
        
        self.scroll = MDScrollView()
        self.food_list = MDList()
        self.scroll.add_widget(self.food_list)
        layout.add_widget(self.scroll)

        # 3. Botão Salvar
        btn_save = MDRaisedButton(text="SALVAR PREFERÊNCIAS", size_hint_x=1, height=dp(50), md_bg_color=(0, 0.7, 0, 1), on_release=self.save_preferences)
        layout.add_widget(btn_save)

        self.add_widget(layout)

    def load_data(self, user_id):
        self.user_id = user_id
        settings = self.db.get_user_diet_settings(user_id)
        all_foods = self.db.get_all_foods()
        
        if settings:
            self.selected_diet_type = settings['diet_type']
            self.selected_foods = set(settings['preferred'])
            self.excluded_foods = set(settings['excluded'])
        else:
            # Padrão: Seleciona tudo que não for alérgico
            self.selected_diet_type = "Onívora (Padrão)"
            self.selected_foods = set([f['id'] for f in all_foods])
            self.excluded_foods = set()

        self.update_diet_ui()
        self.populate_food_list(all_foods)

    def update_diet_ui(self):
        self.btn_diet_type.text = self.selected_diet_type
        self.lbl_diet_desc.text = DIET_TYPES.get(self.selected_diet_type, "")

    def open_diet_menu(self, instance):
        menu_items = [
            {"text": key, "viewclass": "OneLineListItem", "on_release": lambda x=key: self.set_diet_type(x)}
            for key in DIET_TYPES.keys()
        ]
        self.menu_diet = MDDropdownMenu(caller=instance, items=menu_items, width_mult=4)
        self.menu_diet.open()

    def set_diet_type(self, type_name):
        self.selected_diet_type = type_name
        self.update_diet_ui()
        self.menu_diet.dismiss()

    def populate_food_list(self, foods):
        self.food_list.clear_widgets()
        # Agrupa por categoria
        categories = {}
        for f in foods:
            cat = f['category']
            if cat not in categories: categories[cat] = []
            categories[cat].append(f)
        
        for cat, items in categories.items():
            self.food_list.add_widget(OneLineListItem(text=f"--- {cat.upper()} ---", theme_text_color="Primary", font_style="Subtitle2"))
            for f in items:
                is_sel = f['id'] in self.selected_foods
                is_exc = f['id'] in self.excluded_foods
                item = FoodSelectionItem(f['id'], f['name'], f['category'], is_sel, is_exc, callback=self.on_food_toggle)
                self.food_list.add_widget(item)

    def on_food_toggle(self, food_id, action, value):
        if action == "select":
            if value: self.selected_foods.add(food_id)
            else: self.selected_foods.discard(food_id)
        elif action == "allergy":
            if value: 
                self.excluded_foods.add(food_id)
                self.selected_foods.discard(food_id) # Remove da seleção se for alérgico
            else: self.excluded_foods.discard(food_id)

    def save_preferences(self, instance):
        if self.user_id:
            self.db.save_user_diet_preferences(
                self.user_id, 
                self.selected_diet_type, 
                list(self.selected_foods), 
                list(self.excluded_foods)
            )
            # Chama o callback para voltar ao app principal ou carregar a dieta
            if self.save_callback: self.save_callback(self.user_id)