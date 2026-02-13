from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm

class DietReportService:
    @staticmethod
    def generate_diet_pdf(filename, user_data, target_macros, diet_items):
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # Cabeçalho
        c.setFillColor(colors.HexColor("#1976D2"))
        c.rect(0, height - 3*cm, width, 3*cm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 22)
        c.drawString(1*cm, height - 1.5*cm, f"Plano Alimentar: {user_data['name']}")
        
        # Resumo de Macros Alvo
        y = height - 4*cm
        c.setFillColor(colors.HexColor("#F5F5F5"))
        c.rect(1*cm, y - 1.5*cm, width - 2*cm, 1.2*cm, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        macro_txt = f"META DIÁRIA: {target_macros['target_kcal']:.0f} kcal  |  P: {target_macros['target_prot']:.0f}g  |  C: {target_macros['target_carb']:.0f}g  |  G: {target_macros['target_fat']:.0f}g"
        c.drawCentredString(width/2, y - 0.8*cm, macro_txt)

        y -= 2.5*cm
        current_meal = ""
        
        for item in diet_items:
            if item['meal'] != current_meal:
                current_meal = item['meal']
                y -= 0.5*cm
                c.setFont("Helvetica-Bold", 12)
                c.setFillColor(colors.HexColor("#1976D2"))
                c.drawString(1*cm, y, current_meal.upper())
                y -= 0.6*cm
                c.line(1*cm, y + 0.1*cm, width - 1*cm, y + 0.1*cm)

            c.setFillColor(colors.black)
            c.setFont("Helvetica", 10)
            food_txt = f"• {item['name']} ({item['qty']}{item['unit']})"
            c.drawString(1.2*cm, y, food_txt)
            
            c.setFont("Helvetica-Oblique", 9)
            c.setFillColor(colors.grey)
            macros = f"P: {item['prot']:.1f}g | C: {item['carb']:.1f}g | G: {item['fat']:.1f}g | {item['kcal']:.0f} kcal"
            c.drawRightString(width - 1*cm, y, macros)
            y -= 0.5*cm
            
            if y < 2*cm: # Nova página se acabar o espaço
                c.showPage()
                y = height - 2*cm

        c.save()
        return filename