import math

class CalculatorService:
    @staticmethod
    def calculate_bmr_tdee(sex, weight, height_m, age, activity_factor):
        height_cm = height_m * 100
        if sex == "Masculino":
            bmr = (10 * weight) + (6.25 * height_cm) - (5 * age) + 5
        else:
            bmr = (10 * weight) + (6.25 * height_cm) - (5 * age) - 161
        tdee = bmr * activity_factor
        return bmr, tdee

    @staticmethod
    def get_bf_classification(bf, sex, age):
        if not bf: return "-"
        if sex == "Masculino":
            if bf < 6: return "Risco"
            if bf < 14: return "Atleta"
            if bf < 25: return "Médio"
            return "Alto"
        else:
            if bf < 12: return "Risco"
            if bf < 20: return "Atleta"
            if bf < 32: return "Médio"
            return "Alto"

    @staticmethod
    def get_muscle_area_class(area, type_m):
        if not area: return "-"
        if type_m == "arm": return "Alta" if area > 75 else "Baixa" if area < 40 else "Média"
        return "Adequada" if area > 120 else "Baixa"

    @staticmethod
    def calculate_results(sex, age, weight, height, folds, perims, activity_factor=1.2):
        s7 = sum([folds[k] for k in ['chest','axillary','tricep','subscapular','abdominal','suprailiac','thigh']])
        s7_sq = s7 ** 2
        
        if sex == "Masculino":
            density = 1.112 - (0.00043499*s7) + (0.00000055*s7_sq) - (0.00028826*age)
        else:
            density = 1.097 - (0.00046971*s7) + (0.00000056*s7_sq) - (0.00012828*age)
            
        try: bf_percent = (495 / density) - 450
        except: bf_percent = 0.0
        
        fat_mass = weight * (bf_percent / 100)
        lean_mass = weight - fat_mass
        bmi = weight / (height * height) if height > 0 else 0
        rcq = perims.get('waist',0) / perims.get('hips',1) if perims.get('hips',0) > 0 else 0
        
        try: ama = ((perims.get('arm_r',0) - (math.pi * (folds['tricep']/10))) ** 2) / (4 * math.pi) - (10.0 if sex=="Masculino" else 6.5)
        except: ama = 0
        try: tma = ((perims.get('thigh_r',0) - (math.pi * (folds['thigh']/10))) ** 2) / (4 * math.pi)
        except: tma = 0
        
        tmb, tdee = CalculatorService.calculate_bmr_tdee(sex, weight, height, age, activity_factor)

        return {
            "bf_percent": bf_percent, "fat_mass": fat_mass, "lean_mass": lean_mass, "bmi": bmi,
            "rcq": rcq, "ama": ama, "tma": tma,
            "tmb": tmb, "tdee": tdee,
            "bf_class": CalculatorService.get_bf_classification(bf_percent, sex, age),
            "ama_class": CalculatorService.get_muscle_area_class(ama, "arm"),
            "tma_class": CalculatorService.get_muscle_area_class(tma, "thigh")
        }