from kivy.core.window import Window

Window.size = (1280, 768)
Window.left = 50
Window.top = 50

from src.app import FitnessApp

if __name__ == "__main__":
    FitnessApp().run()