import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Union
from src.core.logger import logger
from src.core.exceptions import SMTPClientError

class SMTPClient:
    """
    Google/Gmail üzerinden e-posta göndermek için merkezi istemci sınıfı.
    .env dosyasındaki kimlik bilgilerini kullanır.
    """

    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.environ.get("SMTP_EMAIL")
        self.sender_password = os.environ.get("SMTP_PASSWORD") # App Password kullanılmalıdır

        if not self.sender_email or not self.sender_password:
            logger.error("[X] SMTP_EMAIL veya SMTP_PASSWORD bulunamadı!")
            raise SMTPClientError("SMTP yapılandırması eksik (.env kontrol edin).")

    def send_email(self, 
                   to_emails: Union[str, List[str]], 
                   subject: str, 
                   body: str, 
                   is_html: bool = False) -> bool:
        """
        E-posta gönderir.
        to_emails: Tek bir string veya liste olarak alıcı adresleri.
        """
        if isinstance(to_emails, str):
            to_emails = [to_emails]

        # Mesajı hazırla
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = ", ".join(to_emails)
        msg['Subject'] = subject

        # İçeriği ekle (HTML veya Düz Metin)
        msg.attach(MIMEText(body, 'html' if is_html else 'plain'))

        try:
            logger.info(f"[>] E-posta gönderiliyor: {subject} -> {msg['To']}")
            
            # Bağlantıyı kur ve TLS başlat
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            
            # Giriş yap ve gönder
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"[+] E-posta başarıyla gönderildi: {subject}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("[X] SMTP Kimlik Doğrulama Hatası! Şifreyi veya 'Uygulama Şifresi'ni kontrol edin.")
            raise SMTPClientError("E-posta kimlik doğrulaması başarısız.")
            
        except Exception as e:
            logger.error(f"[X] E-posta gönderme hatası: {e}")
            raise SMTPClientError(f"E-posta gönderilemedi: {e}")

    def send_request_notification(self, requester_slack_id: str, request_content: str):
        """
        Kullanıcının Slack üzerinden yaptığı talebi yöneticiye e-posta ile bildirir.
        """
        admin_email = os.environ.get("ADMIN_EMAIL", self.sender_email)
        subject = "Cemil Bot - Yeni Kullanıcı Talebi"
        body = f"""
        <h3>Yeni Slack Talebi</h3>
        <p><b>Talep Eden Slack ID:</b> {requester_slack_id}</p>
        <p><b>Talep İçeriği:</b></p>
        <blockquote style="background: #f9f9f9; border-left: 5px solid #ccc; padding: 10px;">
            {request_content}
        </blockquote>
        <p><i>Bu e-posta Cemil Bot tarafından otomatik oluşturulmuştur.</i></p>
        """
        return self.send_email(admin_email, subject, body, is_html=True)
