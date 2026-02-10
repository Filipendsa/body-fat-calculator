# ... (Imports)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm

class ReportService:
    @staticmethod
    def generate_pdf(filename, user_data, assessment_data):
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # ... (Partes 1, 2, 3 iguais ao anterior)
        # 1. Cabeçalho
        c.setFillColor(colors.HexColor("#1976D2")); c.rect(0, height - 3 * cm, width, 3 * cm, fill=1, stroke=0)
        c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 24); c.drawString(2 * cm, height - 1.8 * cm, "BioTracker Pro"); c.setFont("Helvetica", 12); c.drawString(2 * cm, height - 2.5 * cm, "Relatório de Avaliação Física & Metabólica")
        # 2. Dados
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 12); y = height - 4.5 * cm
        c.drawString(2 * cm, y, f"Cliente: {user_data['name']}"); c.drawString(12 * cm, y, f"Data: {assessment_data['date']}")
        # 3. Resumo
        y -= 2 * cm; c.setStrokeColor(colors.HexColor("#E0E0E0")); c.setFillColor(colors.HexColor("#F5F5F5")); c.roundRect(1.5 * cm, y - 2*cm, width - 3*cm, 2.5*cm, 10, fill=1, stroke=1)
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 14); c.drawCentredString(width/2, y - 0.8*cm, f"Gordura Corporal: {assessment_data['bf_percent']:.2f}%"); c.setFont("Helvetica", 10); c.drawCentredString(width/2, y - 1.5*cm, f"Classificação: {assessment_data.get('bf_class', '-')}")

        # 4. Metabolismo & Dieta (ATUALIZADO)
        y -= 3.5 * cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Metabolismo & Planejamento Alimentar")
        c.line(2 * cm, y - 0.2*cm, width - 2*cm, y - 0.2*cm)
        
        y_row = y - 1 * cm
        # Esquerda: Dados Metabólicos
        c.setFont("Helvetica-Bold", 10); c.drawString(2*cm, y_row, "Dados Atuais:")
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, y_row - 0.5*cm, f"TMB: {assessment_data.get('tmb',0):.0f} kcal")
        c.drawString(2*cm, y_row - 1.0*cm, f"GET: {assessment_data.get('tdee',0):.0f} kcal")
        
        # Direita: Sugestão Dieta
        diet_goal = assessment_data.get('diet_goal', 'Manter')
        kcal_target = assessment_data.get('target_kcal', 0)
        target_bf = assessment_data.get('target_bf', 0)
        
        c.setFont("Helvetica-Bold", 10); c.drawString(10*cm, y_row, f"Objetivo: {diet_goal}")
        c.setFont("Helvetica", 10)
        c.drawString(10*cm, y_row - 0.5*cm, f"Meta BF%: {target_bf:.1f}%")
        
        c.setFillColor(colors.HexColor("#D32F2F"))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(10*cm, y_row - 1.2*cm, f"Meta: {kcal_target:.0f} kcal/dia")
        c.setFillColor(colors.black)
        
        # Macros
        y_macros = y_row - 2.0 * cm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2*cm, y_macros, "Divisão de Macros Sugerida:")
        
        p = assessment_data.get('target_prot', 0)
        carb = assessment_data.get('target_carb', 0)
        f = assessment_data.get('target_fat', 0)
        
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, y_macros - 0.6*cm, f"Proteína: {p:.0f}g ({p*4:.0f} kcal)")
        c.drawString(7*cm, y_macros - 0.6*cm, f"Carboidratos: {carb:.0f}g ({carb*4:.0f} kcal)")
        c.drawString(14*cm, y_macros - 0.6*cm, f"Gorduras: {f:.0f}g ({f*9:.0f} kcal)")

        # ... (Restante: Mapa de Gordura e Tabelas Finais - Manter igual)
        # 5. Mapa de Gordura
        y = y_macros - 2.5 * cm
        c.setFont("Helvetica-Bold", 12); c.drawString(2 * cm, y, "Mapa de Distribuição (mm)"); c.line(2 * cm, y - 0.2*cm, width - 2*cm, y - 0.2*cm)
        def draw_zone(x_pos, y_pos, label, value):
            val = float(value) if value else 0
            if val < 10: color = colors.green
            elif val < 20: color = colors.orange
            else: color = colors.red
            c.setFillColor(color); c.circle(x_pos, y_pos, 0.8 * cm, fill=1, stroke=0)
            c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 10); c.drawCentredString(x_pos, y_pos - 3, f"{val:.0f}")
            c.setFillColor(colors.black); c.setFont("Helvetica", 9); c.drawCentredString(x_pos, y_pos - 1.3 * cm, label)

        y_map = y - 2.5 * cm
        draw_zone(4 * cm, y_map, "Peitoral", assessment_data.get('chest', 0)); draw_zone(7 * cm, y_map, "Axilar", assessment_data.get('axillary', 0)); draw_zone(10 * cm, y_map, "Abdominal", assessment_data.get('abdominal', 0)); draw_zone(13 * cm, y_map, "Supra-il.", assessment_data.get('suprailiac', 0)); draw_zone(16 * cm, y_map, "Tríceps", assessment_data.get('tricep', 0))
        y_map_2 = y_map - 2.5 * cm
        draw_zone(8 * cm, y_map_2, "Coxa", assessment_data.get('thigh', 0)); draw_zone(12 * cm, y_map_2, "Panturrilha", assessment_data.get('calf', 0))
        
        # 6. Tabelas Finais
        y = y_map_2 - 3.5 * cm
        c.setFont("Helvetica", 10)
        c.drawString(2 * cm, y, f"Massa Gorda: {assessment_data['fat_mass']:.2f} kg"); c.drawString(2 * cm, y - 1*cm, f"Massa Magra: {assessment_data['lean_mass']:.2f} kg")
        c.drawString(10 * cm, y, f"RCQ: {assessment_data.get('rcq', 0):.2f}"); c.drawString(10 * cm, y - 1*cm, f"IMC: {assessment_data['bmi']:.2f}")

        
        c.save()
        return filename