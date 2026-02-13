from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm

class DietReportService:
    @staticmethod
    def generate_diet_pdf(filename, user_data, target_macros, diet_items):
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # --- PALETA DE CORES (MODERNA) ---
        BLUE_DARK = colors.HexColor("#1565C0")   # Azul Institucional
        BLUE_LIGHT = colors.HexColor("#E3F2FD")  # Azul Fundo Suave
        TEXT_DARK = colors.HexColor("#263238")   # Cinza Quase Preto
        TEXT_GREY = colors.HexColor("#546E7A")   # Cinza Médio
        ACCENT_GREEN = colors.HexColor("#2E7D32")
        ACCENT_ORANGE = colors.HexColor("#EF6C00")
        ACCENT_RED = colors.HexColor("#C62828")

        # --- 1. CABEÇALHO PREMIUM ---
        c.setFillColor(BLUE_DARK)
        c.rect(0, height - 3.5*cm, width, 3.5*cm, fill=1, stroke=0)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(1.5*cm, height - 1.8*cm, "Plano Alimentar")
        
        c.setFont("Helvetica", 14)
        c.drawString(1.5*cm, height - 2.6*cm, f"Cliente: {user_data['name']}")
        
        # --- 2. DASHBOARD DE METAS (CAIXA DE RESUMO) ---
        y = height - 5.0*cm
        
        # Fundo da caixa com borda suave
        c.setStrokeColor(colors.lightgrey)
        c.setFillColor(colors.white)
        c.roundRect(1.5*cm, y - 1.5*cm, width - 3*cm, 2*cm, 8, fill=1, stroke=1)
        
        # Colunas de Macros
        col_width = (width - 3*cm) / 4
        
        def draw_stat(label, value, x_pos, color):
            c.setFillColor(color)
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(x_pos, y - 0.7*cm, value)
            c.setFillColor(TEXT_GREY)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(x_pos, y - 1.2*cm, label.upper())

        # Busca valores seguros
        k = target_macros.get('target_kcal', 0)
        p = target_macros.get('target_prot', 0)
        carb = target_macros.get('target_carb', 0)
        f = target_macros.get('target_fat', 0)

        # Desenha os 4 indicadores
        start_x = 1.5*cm + col_width/2
        draw_stat("Calorias", f"{k:.0f}", start_x, BLUE_DARK)
        draw_stat("Proteína", f"{p:.0f}g", start_x + col_width, ACCENT_GREEN)
        draw_stat("Carboidrato", f"{carb:.0f}g", start_x + 2*col_width, ACCENT_ORANGE)
        draw_stat("Gordura", f"{f:.0f}g", start_x + 3*col_width, ACCENT_RED)

        # --- 3. LISTA DE REFEIÇÕES ---
        y -= 2.8*cm
        current_meal = ""
        
        for item in diet_items:
            # Verifica quebra de página
            if y < 3*cm:
                c.showPage()
                y = height - 2*cm

            # --- CABEÇALHO DA REFEIÇÃO (PILL AZUL) ---
            if item['meal'] != current_meal:
                current_meal = item['meal']
                y -= 0.5 * cm # Espaço extra antes do bloco
                
                # Barra de fundo suave
                c.setFillColor(BLUE_LIGHT)
                c.roundRect(1.5*cm, y - 0.1*cm, width - 3*cm, 0.8*cm, 4, fill=1, stroke=0)
                
                # Título da Refeição
                c.setFillColor(BLUE_DARK)
                c.setFont("Helvetica-Bold", 12)
                c.drawString(2*cm, y + 0.15*cm, current_meal.upper())
                
                y -= 1.0 * cm # Desce para os itens

            # --- ITEM ALIMENTAR ---
            # Nome do Alimento (Negrito suave)
            c.setFillColor(TEXT_DARK)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(2*cm, y, f"• {item['name']}")
            
            # Badge de Quantidade (Cinza claro)
            qty_text = f"{item['qty']}{item['unit']}"
            qty_width = c.stringWidth(qty_text, "Helvetica", 9) + 0.4*cm
            
            # Desenha o fundo da badge de quantidade
            c.setFillColor(colors.HexColor("#F5F5F5"))
            c.roundRect(12*cm, y - 0.1*cm, qty_width, 0.5*cm, 2, fill=1, stroke=0)
            
            # Texto da Quantidade
            c.setFillColor(TEXT_DARK)
            c.setFont("Helvetica", 9)
            c.drawCentredString(12*cm + qty_width/2, y + 0.05*cm, qty_text)
            
            # Macros (Alinhados à direita, fonte menor e discreta)
            c.setFillColor(TEXT_GREY)
            c.setFont("Helvetica", 8)
            macros_txt = f"P: {item['prot']:.0f}  C: {item['carb']:.0f}  G: {item['fat']:.0f}  |  {item['kcal']:.0f} kcal"
            c.drawRightString(width - 2*cm, y, macros_txt)
            
            # Linha divisória fina entre itens
            c.setStrokeColor(colors.HexColor("#EEEEEE"))
            c.setLineWidth(0.5)
            c.line(2*cm, y - 0.3*cm, width - 2*cm, y - 0.3*cm)
            
            y -= 0.7 * cm # Espaçamento confortável para o próximo item

        c.save()
        return filename