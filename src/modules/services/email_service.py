import smtplib
import os
import threading
from email.message import EmailMessage
from kivy.clock import Clock
from src.config import SENDER_EMAIL, SENDER_PASSWORD

class EmailService:
    @staticmethod
    def send_email_thread(user_email, user_name, pdf_path, callback_success, callback_error):
        def run():
            try:
                msg = EmailMessage()
                msg['Subject'] = f"Relatório BioTracker - {user_name}"
                msg['From'] = SENDER_EMAIL
                msg['To'] = user_email
                msg.set_content("Segue em anexo seu relatório de avaliação física e metabólica.")

                with open(pdf_path, 'rb') as f:
                    file_data = f.read()
                    file_name = os.path.basename(pdf_path)
                    msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
                    smtp.send_message(msg)
                
                Clock.schedule_once(lambda dt: callback_success(), 0)

            except Exception as e:
                Clock.schedule_once(lambda dt: callback_error(str(e)), 0)
            
            finally:
                if os.path.exists(pdf_path):
                    try:
                        os.remove(pdf_path)
                        print(f"Arquivo temporário removido: {pdf_path}")
                    except Exception as cleanup_error:
                        print(f"Erro ao limpar: {cleanup_error}")

        threading.Thread(target=run).start()