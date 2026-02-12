from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm

class ReportService:
    @staticmethod
    def generate_pdf(filename, user_data, assessment_data):
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # --- CORES E ESTILOS ---
        PRIMARY_COLOR = colors.HexColor("#1976D2") # Azul App
        BG_LIGHT = colors.HexColor("#F5F7FA")
        ACCENT_RED = colors.HexColor("#E53935")
        ACCENT_GREEN = colors.HexColor("#43A047")
        ACCENT_ORANGE = colors.HexColor("#FB8C00")
        TEXT_DARK = colors.HexColor("#263238")
        TEXT_LIGHT = colors.HexColor("#546E7A")

        # --- 1. CABEÇALHO MODERNO ---
        c.setFillColor(PRIMARY_COLOR)
        c.rect(0, height - 3.5 * cm, width, 3.5 * cm, fill=1, stroke=0)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 26)
        c.drawString(1.5 * cm, height - 1.8 * cm, "BioTracker Pro")
        c.setFont("Helvetica", 12)
        c.drawString(1.5 * cm, height - 2.6 * cm, "Relatório de Avaliação Física & Nutricional")
        
        # Data no canto direito
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(width - 1.5 * cm, height - 1.8 * cm, f"Data: {assessment_data['date']}")
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 1.5 * cm, height - 2.4 * cm, f"Cliente: {user_data['name']}")

        y = height - 5.0 * cm

        # --- 2. DESTAQUE PRINCIPAL (GORDURA) ---
        bf_pct = assessment_data['bf_percent']
        bf_class = assessment_data.get('bf_class', '-')
        
        c.setFillColor(TEXT_DARK)
        c.setFont("Helvetica-Bold", 40)
        c.drawCentredString(width/2, y, f"{bf_pct:.1f}%")
        
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(TEXT_LIGHT)
        c.drawCentredString(width/2, y - 0.7 * cm, "GORDURA CORPORAL")
        
        # Badge de classificação
        c.setFillColor(PRIMARY_COLOR)
        c.roundRect(width/2 - 2*cm, y - 1.8*cm, 4*cm, 0.8*cm, 4, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(width/2, y - 1.55*cm, bf_class.upper())

        y -= 3.5 * cm

        # --- 3. METABOLISMO E DIETA (LADO A LADO) ---
        c.setFillColor(TEXT_DARK)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1.5 * cm, y, "Metabolismo & Planejamento")
        c.setStrokeColor(colors.lightgrey)
        c.line(1.5 * cm, y - 0.3*cm, width - 1.5*cm, y - 0.3*cm)
        y -= 1.5 * cm

        # Coluna Esquerda: Dados Basais
        col1_x = 1.5 * cm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(col1_x, y, "Gasto Energético")
        
        c.setFont("Helvetica", 10)
        c.setFillColor(TEXT_LIGHT)
        c.drawString(col1_x, y - 0.8*cm, "Taxa Metabólica Basal (TMB)")
        c.drawString(col1_x, y - 1.6*cm, "Gasto Total Diário (GET)")
        
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(TEXT_DARK)
        c.drawRightString(col1_x + 7*cm, y - 0.8*cm, f"{assessment_data.get('tmb', 0):.0f} kcal")
        c.drawRightString(col1_x + 7*cm, y - 1.6*cm, f"{assessment_data.get('tdee', 0):.0f} kcal")

        # Coluna Direita: Meta da Dieta
        col2_x = 11 * cm
        diet_goal = assessment_data.get('diet_goal', 'Manter')
        target_kcal = assessment_data.get('target_kcal', 0)
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(col2_x, y, f"Objetivo: {diet_goal.upper()}")
        
        # Caixa de Destaque da Meta
        c.setFillColor(BG_LIGHT)
        c.roundRect(col2_x, y - 2*cm, 8*cm, 1.5*cm, 5, fill=1, stroke=0)
        
        c.setFillColor(TEXT_DARK)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(col2_x + 0.5*cm, y - 1.2*cm, "Meta Calórica:")
        c.setFillColor(ACCENT_RED if diet_goal != 'Manter' else PRIMARY_COLOR)
        c.setFont("Helvetica-Bold", 16)
        c.drawRightString(col2_x + 7.5*cm, y - 1.3*cm, f"{target_kcal:.0f} kcal")

        y -= 3.5 * cm

        # --- 4. MACRONUTRIENTES (BARRAS VISUAIS) ---
        c.setFillColor(TEXT_DARK)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1.5 * cm, y, "Distribuição de Macros")
        y -= 1.0 * cm

        p_g = assessment_data.get('target_prot', 0)
        c_g = assessment_data.get('target_carb', 0)
        f_g = assessment_data.get('target_fat', 0)
        
        def draw_macro_bar(label, grams, color, y_pos):
            kcal = grams * 9 if label == "Gorduras" else grams * 4
            c.setFillColor(colors.HexColor("#EEEEEE"))
            c.roundRect(1.5 * cm, y_pos, 10 * cm, 0.8 * cm, 4, fill=1, stroke=0)
            
            c.setFillColor(color)
            c.roundRect(1.5 * cm, y_pos, 0.2 * cm, 0.8 * cm, 2, fill=1, stroke=0) 
            
            c.setFillColor(TEXT_DARK)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(2.0 * cm, y_pos + 0.25*cm, label)
            
            c.setFillColor(TEXT_LIGHT)
            c.setFont("Helvetica", 10)
            c.drawRightString(11.0 * cm, y_pos + 0.25*cm, f"{grams:.0f}g  ({kcal:.0f} kcal)")

        draw_macro_bar("Proteínas", p_g, PRIMARY_COLOR, y)
        draw_macro_bar("Carboidratos", c_g, ACCENT_ORANGE, y - 1.2*cm)
        draw_macro_bar("Gorduras", f_g, ACCENT_RED, y - 2.4*cm)
        
        # Gráfico Pizza Simplificado (Texto visual)
        c.setFont("Helvetica", 9)
        c.setFillColor(PRIMARY_COLOR); c.circle(13.5*cm, y, 0.15*cm, fill=1, stroke=0); c.drawString(14*cm, y-0.1*cm, "Prot. (Construtor)")
        c.setFillColor(ACCENT_ORANGE); c.circle(13.5*cm, y-1.2*cm, 0.15*cm, fill=1, stroke=0); c.drawString(14*cm, y-1.3*cm, "Carb. (Energia)")
        c.setFillColor(ACCENT_RED); c.circle(13.5*cm, y-2.4*cm, 0.15*cm, fill=1, stroke=0); c.drawString(14*cm, y-2.5*cm, "Gord. (Hormônios)")

        y -= 4.0 * cm

        # --- 5. MAPA DE DISTRIBUIÇÃO DAS DOBRAS (9 DOBRAS) ---
        c.setFillColor(TEXT_DARK)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1.5 * cm, y, "Distribuição Localizada (Dobras em mm)")
        y -= 1.3 * cm

        def draw_zone(x_pos, y_pos, label, value):
            val = float(value) if value else 0
            if val < 10: color = ACCENT_GREEN
            elif val < 20: color = ACCENT_ORANGE
            else: color = ACCENT_RED
            
            c.setFillColor(color)
            c.circle(x_pos, y_pos, 0.75 * cm, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(x_pos, y_pos - 0.12 * cm, f"{val:.0f}")
            c.setFillColor(TEXT_DARK)
            c.setFont("Helvetica", 9)
            c.drawCentredString(x_pos, y_pos - 1.2 * cm, label)

        y_map = y
        # Linha superior (Membros Sup. / Costas / Peito - 5 dobras, espaçadas em 3.2cm)
        draw_zone(4.1 * cm, y_map, "Peitoral", assessment_data.get('chest', 0))
        draw_zone(7.3 * cm, y_map, "Axilar", assessment_data.get('axillary', 0))
        draw_zone(10.5 * cm, y_map, "Subescap.", assessment_data.get('subscapular', 0))
        draw_zone(13.7 * cm, y_map, "Bíceps", assessment_data.get('biceps', 0))
        draw_zone(16.9 * cm, y_map, "Tríceps", assessment_data.get('tricep', 0))
        
        # Linha inferior (Core / Pernas - 4 dobras, espaçadas em 3.2cm e centralizadas)
        y_map_2 = y_map - 2.2 * cm
        draw_zone(5.7 * cm, y_map_2, "Abdominal", assessment_data.get('abdominal', 0))
        draw_zone(8.9 * cm, y_map_2, "Supra-il.", assessment_data.get('suprailiac', 0))
        draw_zone(12.1 * cm, y_map_2, "Coxa", assessment_data.get('thigh', 0))
        draw_zone(15.3 * cm, y_map_2, "Panturrilha", assessment_data.get('calf', 0))

        # Legenda do mapa
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor(TEXT_LIGHT)
        c.drawCentredString(width/2, y_map_2 - 1.6 * cm, "* Verde: Baixo acúmulo | Laranja: Moderado | Vermelho: Alto acúmulo")

        y = y_map_2 - 3.2 * cm

        # --- 6. COMPOSIÇÃO CORPORAL (BARRA HORIZONTAL) ---
        c.setFillColor(TEXT_DARK)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1.5 * cm, y, "Composição Corporal")
        y -= 1.5 * cm

        fat_kg = assessment_data['fat_mass']
        lean_kg = assessment_data['lean_mass']
        total_weight = assessment_data['weight']
        
        # Barra Total
        bar_width = 18 * cm
        bar_height = 1.2 * cm
        fat_width = (fat_kg / total_weight) * bar_width if total_weight > 0 else 0
        
        # Desenha Massa Magra (Azul)
        c.setFillColor(PRIMARY_COLOR)
        c.rect(1.5 * cm, y, bar_width, bar_height, fill=1, stroke=0)
        # Desenha Massa Gorda (Laranja) por cima
        c.setFillColor(ACCENT_ORANGE)
        c.rect(1.5 * cm, y, fat_width, bar_height, fill=1, stroke=0)
        
        # Legendas da Barra
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        if fat_width > 2.5*cm: 
            c.drawString(2 * cm, y + 0.4*cm, f"Gordura: {fat_kg:.1f}kg")
        
        c.drawRightString(1.5*cm + bar_width - 0.5*cm, y + 0.4*cm, f"Massa Magra: {lean_kg:.1f}kg")

        # --- 7. RODAPÉ DE ÍNDICES ---
        y -= 2.0 * cm
        c.setStrokeColor(colors.lightgrey)
        c.line(1.5 * cm, y + 1*cm, width - 1.5*cm, y + 1*cm)
        
        c.setFillColor(TEXT_LIGHT)
        c.setFont("Helvetica", 10)
        c.drawString(1.5 * cm, y, f"IMC: {assessment_data['bmi']:.2f} kg/m²")
        c.drawCentredString(width/2, y, f"RCQ: {assessment_data.get('rcq', 0):.2f}")
        c.drawRightString(width - 1.5 * cm, y, "Gerado via BioTracker Pro")

        c.save()
        return filename