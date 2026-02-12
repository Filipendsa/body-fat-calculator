import math

class CalculatorService:
    @staticmethod
    def calculate_bmr_tdee(sex, weight, height_m, age, activity_factor):
        """
        Calcula TMB (Taxa Metabólica Basal) e GET (Gasto Energético Total).
        Fórmula: Mifflin-St Jeor (1990) - Considerada a mais precisa atualmente.
        """
        # A fórmula exige altura em cm
        height_cm = height_m * 100
        
        # Base do cálculo: (10 x Peso) + (6.25 x Altura) - (5 x Idade)
        base_bmr = (10 * weight) + (6.25 * height_cm) - (5 * age)
        
        if sex == "Masculino":
            # Homens: Base + 5
            bmr = base_bmr + 5
        else:
            # Mulheres: Base - 161
            bmr = base_bmr - 161
            
        tdee = bmr * activity_factor
        return bmr, tdee

    @staticmethod
    def get_bf_classification(bf, sex, age):
        if not bf: return "-"
        if sex == "Masculino":
            return "Risco" if bf < 6 else "Atleta" if bf < 14 else "Médio" if bf < 25 else "Alto"
        else:
            return "Risco" if bf < 12 else "Atleta" if bf < 20 else "Médio" if bf < 32 else "Alto"

    @staticmethod
    def get_muscle_area_class(area, type_m):
        if not area: return "-"
        if type_m == "arm": return "Alta" if area > 75 else "Baixa" if area < 40 else "Média"
        return "Adequada" if area > 120 else "Baixa"

    @staticmethod
    def calculate_diet_macros(tdee, weight, goal, intensity_pct, protein_g_kg):
        """
        Calcula a dieta com base no TMB (Mifflin) e GET.
        Gordura fixa em 25% das calorias (equilíbrio hormonal).
        """
        # 1. Calorias Alvo (Déficit ou Superávit)
        if goal == "Cutting":
            target_kcal = tdee * (1 - (intensity_pct / 100))
        elif goal == "Bulking":
            target_kcal = tdee * (1 + (intensity_pct / 100))
        else: # Manter
            target_kcal = tdee

        # 2. Proteína (Definida pelo slider de g/kg)
        target_prot_g = weight * protein_g_kg
        kcal_prot = target_prot_g * 4

        # 3. Gordura (Fixa em 25% das Kcal - Padrão Saudável)
        kcal_fat = target_kcal * 0.25
        target_fat_g = kcal_fat / 9

        # 4. Carboidrato (O restante das calorias)
        kcal_remain = target_kcal - kcal_prot - kcal_fat
        target_carb_g = max(0, kcal_remain / 4)

        return target_kcal, target_prot_g, target_carb_g, target_fat_g

    @staticmethod
    def calculate_results(sex, age, weight, height, folds, perims, activity_factor=1.2, diet_config=None):
        # --- Composição Corporal (Pollock 7 Dobras) ---
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
        
        # Áreas Musculares
        try: ama = ((perims.get('arm_r',0) - (math.pi * (folds['tricep']/10))) ** 2) / (4 * math.pi) - (10.0 if sex=="Masculino" else 6.5)
        except: ama = 0
        try: tma = ((perims.get('thigh_r',0) - (math.pi * (folds['thigh']/10))) ** 2) / (4 * math.pi)
        except: tma = 0
        
        # --- Metabolismo (Mifflin-St Jeor) ---
        tmb, tdee = CalculatorService.calculate_bmr_tdee(sex, weight, height, age, activity_factor)

        # --- Dieta ---
        d_kcal = tdee; d_prot = 0; d_carb = 0; d_fat = 0
        if diet_config:
            d_kcal, d_prot, d_carb, d_fat = CalculatorService.calculate_diet_macros(
                tdee, weight, 
                diet_config['goal'], 
                diet_config['intensity'], 
                diet_config['prot_g_kg']
            )

        return {
            "bf_percent": bf_percent, "fat_mass": fat_mass, "lean_mass": lean_mass, "bmi": bmi,
            "rcq": rcq, "ama": ama, "tma": tma,
            "tmb": tmb, "tdee": tdee,
            "bf_class": CalculatorService.get_bf_classification(bf_percent, sex, age),
            "ama_class": CalculatorService.get_muscle_area_class(ama, "arm"),
            "tma_class": CalculatorService.get_muscle_area_class(tma, "thigh"),
            # Dados da Dieta
            "target_kcal": d_kcal, "target_prot": d_prot, "target_carb": d_carb, "target_fat": d_fat
        }