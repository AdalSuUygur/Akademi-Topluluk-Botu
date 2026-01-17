import os
import asyncio
from typing import List, Dict, Any
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

    async def check_and_celebrate(self):
        """Bugün doğanları bulur ve kutlar."""
        try:
            logger.info("[>] Günlük doğum günü kontrolü yapılıyor...")
            users = self.user_repo.get_users_with_birthday_today()
            
            if not users:
                logger.info("[i] Bugün doğum günü olan kimse bulunamadı.")
                return

            logger.info(f"[!] Bugün {len(users)} kişinin doğum günü!")
            
            # Mentions listesi oluştur
            mentions = [f"<@{user['slack_id']}>" for user in users if user.get('slack_id')]
            mentions_str = ", ".join(mentions)

            # ASCII Süslemeli Mesaj
            message_text = (
                "*****************************************\n"
                "        [!] DOGUM GUNU KUTLAMASI [!]       \n"
                "*****************************************\n\n"
                f"Bugün çok özel bir gün! Sevgili {mentions_str} iyi ki doğdunuz! \n\n"
                "Yeni yaşınızda sağlık, mutluluk ve başarılar dileriz. \n"
                "Topluluğumuzun bir parçası olduğunuz için çok mutluyuz! \n\n"
                "== CEMIL v2.0 ==\n"
                "*****************************************"
            )

            if self.channel_id:
                self.chat.post_message(
                    channel=self.channel_id,
                    text="Mutlu Yıllar! 🎈",
                    blocks=[
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": f"```\n{message_text}\n```"}
                        }
                    ]
                )
                logger.info(f"[+] Doğum günü mesajı {self.channel_id} kanalına gönderildi.")
            else:
                logger.warning("[!] BIRTHDAY_CHANNEL_ID ayarlanmadığı için mesaj gönderilemedi.")

        except Exception as e:
            logger.error(f"[X] BirthdayService.check_and_celebrate hatası: {e}")

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
