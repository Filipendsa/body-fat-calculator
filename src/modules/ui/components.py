from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import ThreeLineAvatarIconListItem
from kivymd.uix.slider import MDSlider
from kivy.properties import StringProperty, DictProperty, NumericProperty
from kivy.metrics import dp

class SectionCard(MDCard):
    title = StringProperty("")
    def __init__(self, title, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"; self.padding = "10dp"; self.size_hint_y = None; self.elevation = 2; self.radius = [10]
        self.bind(minimum_height=self.setter('height'))
        self.add_widget(MDLabel(text=title, theme_text_color="Primary", font_style="H6", size_hint_y=None, height="30dp", bold=True))
        self.grid = MDGridLayout(cols=2, spacing="10dp", adaptive_height=True); self.add_widget(self.grid)
    def add_input(self, widget): self.grid.add_widget(widget)

# --- CORREÇÃO DO SLIDER ---
class SmartSlider(MDSlider):
    """Slider que funciona dentro de ScrollView"""
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self) # Garante que o slider pegue o toque
            return super().on_touch_down(touch)
        return False

    def on_touch_move(self, touch):
        if touch.grab_current == self:
            return super().on_touch_move(touch) # Permite arrastar
        return False

    def on_touch_up(self, touch):
        if touch.grab_current == self:
            touch.ungrab(self)
            return super().on_touch_up(touch)
        return False

class LabelledSlider(MDBoxLayout):
    value = NumericProperty(0)
    def __init__(self, label_text, min_val, max_val, default_val, step=1, fmt="{:.0f}", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"; self.size_hint_y = None; self.height = dp(70); self.fmt = fmt
        
        header = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20))
        self.lbl_title = MDLabel(text=label_text, theme_text_color="Primary", bold=True, font_style="Body2")
        self.lbl_value = MDLabel(text=fmt.format(default_val), theme_text_color="Secondary", halign="right", font_style="Body2")
        header.add_widget(self.lbl_title); header.add_widget(self.lbl_value); self.add_widget(header)

        # Usa o SmartSlider agora
        self.slider = SmartSlider(min=min_val, max=max_val, value=default_val, step=step)
        self.slider.bind(value=self.on_slider_value)
        self.add_widget(self.slider)
        self.value = default_val

    def on_slider_value(self, instance, val):
        self.value = val
        self.lbl_value.text = self.fmt.format(val)

# ... (DetailRow, ComparisonRow, AssessmentItem permanecem iguais)
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

class AssessmentItem(ThreeLineAvatarIconListItem):
    data = DictProperty({})