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

DIET_TYPES = {
    "Ovolactovegetariana": "Exclui carnes, mas inclui ovos, leite e laticínios.",
    "Lactovegetariana": "Exclui carnes e ovos. Inclui leite e laticínios.",
    "Ovovegetariana": "Exclui carnes e laticínios. Inclui ovos.",
    "Vegetariana Estrita": "Exclui todos alimentos de origem animal (carnes, ovos, leite, mel).",
    "Vegana": "Estilo de vida que exclui produtos animais (alimentação, vestuário, etc).",
    "Crudívora": "Apenas alimentos crus ou cozidos a baixa temperatura (geralmente vegetais).",
    "Frugívora": "Baseada apenas no consumo de frutos.",
    "Flexitariana": "Predominantemente vegetal, com consumo ocasional de carne.",
    "Pescetariana": "Exclui carnes vermelhas e aves, mas inclui peixes e frutos do mar.",
    "Plant-Based": "Foca em alimentos integrais de origem vegetal, minimamente processados.",
    "Carnívora": "Apenas alimentos de origem animal (carnes, ovos, miúdos).",
    "Paleolítica": "Carnes, peixes, ovos, frutas, vegetais e nozes. Exclui grãos e processados.",
    "Onívora (Padrão)": "Sem restrições específicas (inclui todos os grupos)."
}