from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.progressbar import MDProgressBar
# CORREÇÃO: Importando apenas TwoLineListItem
from kivymd.uix.list import MDList, TwoLineListItem
from kivymd.uix.gridlayout import MDGridLayout
from kivy.metrics import dp
from kivy.properties import StringProperty

class NutrientBar(MDBoxLayout):
    def __init__(self, label, current, target, color, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(40)
        self.spacing = dp(5)
        
        # Texto
        header = MDBoxLayout(size_hint_y=None, height=dp(20))
        header.add_widget(MDLabel(text=f"{label}", bold=True, theme_text_color="Primary", font_style="Caption"))
        header.add_widget(MDLabel(text=f"{current:.0f} / {target:.0f}", halign="right", theme_text_color="Secondary", font_style="Caption"))
        self.add_widget(header)
        
        # Barra
        progress = (current / target * 100) if target > 0 else 0
        self.add_widget(MDProgressBar(value=progress, color=color, size_hint_y=None, height=dp(10)))

class DietScreen(MDScreen):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.current_user_id = 1
        self.build_ui()

    def build_ui(self):
        self.main_layout = MDBoxLayout(orientation="vertical", spacing=10, padding=10)
        
        # 1. Resumo do Dia (Cabeçalho)
        self.summary_card = MDCard(orientation="vertical", size_hint_y=None, height=dp(160), padding=15, radius=[15], elevation=2)
        self.summary_card.add_widget(MDLabel(text="Resumo Diário", font_style="H6", bold=True, size_hint_y=None, height=dp(30)))
        
        self.bars_layout = MDBoxLayout(orientation="vertical", spacing=10)
        self.summary_card.add_widget(self.bars_layout)
        self.main_layout.add_widget(self.summary_card)

        # 2. Lista de Refeições
        scroll = MDScrollView()
        self.meal_list = MDList()
        scroll.add_widget(self.meal_list)
        self.main_layout.add_widget(scroll)
        
        self.add_widget(self.main_layout)

    def load_diet(self, user_id, target_data=None):
        self.current_user_id = user_id
        diet_log = self.db.get_diet_log(user_id)
        
        # Agrupa por Refeição
        meals = {}
        total_day = {"kcal":0, "prot":0, "carb":0, "fat":0}
        
        for item in diet_log:
            m = item['meal']
            if m not in meals: meals[m] = []
            
            # Calcula proporcional
            ratio = item['qty'] / item['base_qty']
            k = item['kcal'] * ratio
            p = item['prot'] * ratio
            c = item['carb'] * ratio
            f = item['fat'] * ratio
            
            # Soma totais
            total_day['kcal'] += k
            total_day['prot'] += p
            total_day['carb'] += c
            total_day['fat'] += f
            
            item_desc = {
                "name": item['name'],
                "qty_str": f"{item['qty']:.0f}{item['unit']}",
                "macros": f"P:{p:.1f}g C:{c:.1f}g G:{f:.1f}g | {k:.0f} kcal"
            }
            meals[m].append(item_desc)

        # Atualiza Barras de Progresso
        self.bars_layout.clear_widgets()
        t_kcal = target_data.get('target_kcal', 2000) if target_data else 2000
        t_prot = target_data.get('target_prot', 150) if target_data else 150
        t_carb = target_data.get('target_carb', 200) if target_data else 200
        t_fat = target_data.get('target_fat', 60) if target_data else 60

        self.bars_layout.add_widget(NutrientBar("Calorias", total_day['kcal'], t_kcal, (0,0,1,1)))
        
        macros_grid = MDGridLayout(cols=3, spacing=10)
        macros_grid.add_widget(NutrientBar("Proteína", total_day['prot'], t_prot, (0, 0.8, 0, 1)))
        macros_grid.add_widget(NutrientBar("Carbo", total_day['carb'], t_carb, (1, 0.6, 0, 1)))
        macros_grid.add_widget(NutrientBar("Gordura", total_day['fat'], t_fat, (1, 0, 0, 1)))
        self.bars_layout.add_widget(macros_grid)

        # Atualiza Lista Visual
        self.meal_list.clear_widgets()
        for meal_name, items in meals.items():
            # Cabeçalho da Refeição
            self.meal_list.add_widget(MDLabel(text=meal_name, bold=True, theme_text_color="Primary", size_hint_y=None, height=dp(40), padding=(20,0)))
            
            for food in items:
                # CORREÇÃO: Usando o TwoLineListItem padrão
                item = TwoLineListItem(
                    text=f"{food['name']} ({food['qty_str']})",
                    secondary_text=food['macros']
                )
                self.meal_list.add_widget(item)