from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import ThreeLineIconListItem
from kivy.properties import StringProperty, DictProperty
from kivy.metrics import dp

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
    def __init__(self, label, value, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(24)
        self.add_widget(MDLabel(text=label, bold=True, size_hint_x=0.6, theme_text_color="Primary", font_style="Body2"))
        self.add_widget(MDLabel(text=str(value), halign="right", size_hint_x=0.4, theme_text_color="Secondary", font_style="Body2"))

class ComparisonRow(MDBoxLayout):
    def __init__(self, label, val_r, val_l, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(24)
        
        diff = abs(val_r - val_l)
        self.add_widget(MDLabel(text=label, bold=True, size_hint_x=0.4, font_style="Body2"))
        self.add_widget(MDLabel(text=f"D: {val_r}", halign="center", size_hint_x=0.2, font_style="Caption"))
        self.add_widget(MDLabel(text=f"E: {val_l}", halign="center", size_hint_x=0.2, font_style="Caption"))
        self.add_widget(MDLabel(text=f"Δ: {diff:.1f}", halign="right", size_hint_x=0.2, font_style="Caption", markup=True))

class AssessmentItem(ThreeLineIconListItem):
    data = DictProperty({})