import os
import asyncio
from typing import List, Dict, Any
from datetime import datetime, date
from src.core.logger import logger
from src.core.exceptions import CemilBotError
from src.commands import ChatManager
from src.repositories import UserRepository
from src.clients import CronClient

class BirthdayService:
    """
    Doğum günlerini takip eden ve günlük kutlamalar yapan servis.
    """

    def __init__(
        self, 
        chat_manager: ChatManager, 
        user_repo: UserRepository, 
        cron_client: CronClient
    ):
        self.chat = chat_manager
        self.user_repo = user_repo
        self.cron = cron_client
        self.channel_id = os.environ.get("BIRTHDAY_CHANNEL_ID")

    def _calculate_age(self, birthday_str: str) -> int:
        """Doğum tarihinden yaşı hesaplar."""
        try:
            if not birthday_str:
                return None
            
            # YYYY-MM-DD formatından parse et
            birth_date = datetime.strptime(birthday_str, '%Y-%m-%d').date()
            today = date.today()
            
            # Yaş hesapla
            age = today.year - birth_date.year
            
            # Henüz doğum günü gelmediyse 1 yaş eksilt
            if (today.month, today.day) < (birth_date.month, birth_date.day):
                age -= 1
            
            return age
        except Exception as e:
            logger.warning(f"[!] Yaş hesaplanamadı: {birthday_str} | Hata: {e}")
            return None

    def _format_user_name(self, user: Dict[str, Any]) -> str:
        """Kullanıcı adını formatlar (orta isim dahil)."""
        first_name = user.get('first_name', '')
        middle_name = user.get('middle_name', '')
        surname = user.get('surname', '')
        
        if middle_name:
            return f"{first_name} {middle_name} {surname}".strip()
        else:
            return f"{first_name} {surname}".strip()

    async def check_and_celebrate(self):
        """Bugün doğanları bulur ve kutlar."""
        try:
            logger.info("[>] Günlük doğum günü kontrolü yapılıyor...")
            users = self.user_repo.get_users_with_birthday_today()
            
            if not users:
                logger.info("[i] Bugün doğum günü olan kimse bulunamadı.")
                return

            logger.info(f"[!] Bugün {len(users)} kişinin doğum günü!")
            
            # Kullanıcı bilgilerini hazırla
            birthday_users = []
            for user in users:
                slack_id = user.get('slack_id')
                if not slack_id:
                    logger.warning(f"[!] Slack ID bulunamadı: {user.get('full_name', 'Bilinmiyor')}")
                    continue
                
                user_name = self._format_user_name(user)
                if not user_name:
                    user_name = user.get('full_name', 'Bilinmiyor')
                
                age = self._calculate_age(user.get('birthday'))
                
                birthday_users.append({
                    'slack_id': slack_id,
                    'name': user_name,
                    'age': age
                })
            
            if not birthday_users:
                logger.warning("[!] Geçerli kullanıcı bulunamadı.")
                return

            # Mesaj blokları oluştur
            blocks = []
            
            # Başlık bloğu
            if len(birthday_users) == 1:
                user = birthday_users[0]
                age_text = f" {user['age']}. yaşını" if user['age'] else ""
                header_text = f"🎉 *Mutlu Yıllar!* 🎉\n\n🎂 Sevgili <@{user['slack_id']}> iyi ki doğdun{age_text}!"
            else:
                mentions = [f"<@{u['slack_id']}>" for u in birthday_users]
                mentions_str = ", ".join(mentions)
                header_text = f"🎉 *Mutlu Yıllar!* 🎉\n\n🎂 Bugün {len(birthday_users)} kişinin doğum günü!\n\n{mentions_str} iyi ki doğdunuz!"
            
            blocks.append({
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🎂 Doğum Günü Kutlaması 🎂",
                    "emoji": True
                }
            })
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": header_text
                }
            })
            
            # Her kullanıcı için detay bloğu
            for user in birthday_users:
                age_info = f" ({user['age']}. yaş)" if user['age'] else ""
                user_text = f"✨ <@{user['slack_id']}> - {user['name']}{age_info}"
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": user_text
                    }
                })
            
            # Alt mesaj bloğu
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🎁 Yeni yaşınızda sağlık, mutluluk ve başarılar dileriz!\n💝 Topluluğumuzun bir parçası olduğunuz için çok mutluyuz!"
                }
            })
            
            # Footer
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "🎈 Cemil Bot ile gönderildi"
                    }
                ]
            })

            if self.channel_id:
                self.chat.post_message(
                    channel=self.channel_id,
                    text="🎂 Doğum Günü Kutlaması! 🎂",
                    blocks=blocks
                )
                logger.info(f"[+] Doğum günü mesajı gönderildi | Kanal: {self.channel_id} | {len(birthday_users)} kişi")
            else:
                logger.warning("[!] BIRTHDAY_CHANNEL_ID ayarlanmadığı için mesaj gönderilemedi.")

        except Exception as e:
            logger.error(f"[X] BirthdayService.check_and_celebrate hatası: {e}", exc_info=True)

    def schedule_daily_check(self, hour: int = 9, minute: int = 0):
        """Günlük kontrolü belirtilen saate planlar."""
        try:
            self.cron.add_cron_job(
                func=self.check_and_celebrate,
                cron_expression={"hour": hour, "minute": minute},
                job_id="daily_birthday_check"
            )
            logger.info(f"[i] Günlük doğum günü kontrolü saat {hour:02d}:{minute:02d} için planlandı.")
        except Exception as e:
            logger.error(f"[X] Doğum günü planlama hatası: {e}")
