import os
from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL = os.getenv("EMAIL_USER")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")
DATABASE_NAME = os.getenv("DB_NAME", "fitness_tracker_v5.db")

ACTIVITY_LEVELS = {
    "Sedentário (Pouco ou nenhum exercício)": 1.2,
    "Levemente Ativo (Exercício 1-3 dias/sem)": 1.375,
    "Moderadamente Ativo (Exercício 3-5 dias/sem)": 1.55,
    "Muito Ativo (Exercício 6-7 dias/sem)": 1.725,
    "Extremamente Ativo (Exercício físico pesado)": 1.9
}