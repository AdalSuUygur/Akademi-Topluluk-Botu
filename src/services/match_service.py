import asyncio
from typing import List
from src.core.logger import logger
from src.core.exceptions import CemilBotError
from src.commands import ChatManager, ConversationManager
from src.clients import GroqClient, CronClient

class CoffeeMatchService:
    """
    Kullanıcılar arasında kahve eşleşmesi ve moderasyonunu yöneten servis.
    """

    def __init__(
        self, 
        chat_manager: ChatManager, 
        conv_manager: ConversationManager, 
        groq_client: GroqClient, 
        cron_client: CronClient
    ):
        self.chat = chat_manager
        self.conv = conv_manager
        self.groq = groq_client
        self.cron = cron_client

    async def start_match(self, user_id1: str, user_id2: str):
        """
        İki kullanıcıyı eşleştirir, grup açar ve buzları eritir.
        """
        try:
            logger.info(f"[>] Kahve eşleşmesi başlatılıyor: {user_id1} & {user_id2}")
            
            # 1. Grup konuşması aç
            channel = self.conv.open_conversation(users=[user_id1, user_id2])
            channel_id = channel["id"]
            logger.info(f"[+] Özel grup oluşturuldu: {channel_id}")

            # 2. Ice Breaker (Buzkıran) mesajı oluştur
            system_prompt = (
                "Sen Cemil'sin, bir topluluk asistanısın. Görevin birbiriyle eşleşen iki iş arkadaşı için "
                "kısa, eğlenceli ve samimi bir tanışma mesajı yazmak. Mesajda mutlaka kahve veya çay içmeye "
                "teşvik et ve ortak bir konu veya rastgele eğlenceli bir soru ortaya at."
            )
            user_prompt = f"Şu iki kullanıcı az önce kahve için eşleşti: <@{user_id1}> ve <@{user_id2}>. Onlara güzel bir selam ver."
            
            ice_breaker = await self.groq.quick_ask(system_prompt, user_prompt)

            # 3. Mesajı kanala gönder
            self.chat.post_message(
                channel=channel_id,
                text=ice_breaker,
                blocks=[
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"☕ *Kahve Eşleşmesi:* \n\n{ice_breaker}"}
                    },
                    {
                        "type": "context",
                        "elements": [{"type": "mrkdwn", "text": "ℹ️ Bu kanal 5 dakika sonra otomatik olarak kapatılacaktır."}]
                    }
                ]
            )

            # 4. 5 dakika sonra kapatma görevini planla
            self.cron.add_once_job(
                func=self.close_match,
                delay_minutes=5,
                job_id=f"close_match_{channel_id}",
                args=[channel_id]
            )
            logger.info(f"[i] 5 dakika sonra kapatma görevi planlandı: {channel_id}")

        except Exception as e:
            logger.error(f"[X] CoffeeMatchService.start_match hatası: {e}")
            raise CemilBotError(f"Eşleşme başlatılamadı: {e}")

    def close_match(self, channel_id: str):
        """
        Eşleşme grubunu kapatır ve bilgilendirir.
        """
        try:
            logger.info(f"[>] Eşleşme grubu kapatılıyor: {channel_id}")
            
            # 1. Kapanış mesajı gönder
            self.chat.post_message(
                channel=channel_id,
                text="👋 Süremiz doldu! Umarım güzel bir tanışma olmuştur. Görüşmek üzere!"
            )
            
            # 2. Grubu kapat (Slack Connect/DM'ler için close, kanallar için archive gerekebilir)
            # conversations.close sadece DM ve grup DM'ler için çalışır.
            self.conv.close_conversation(channel_id=channel_id)
            logger.info(f"[+] Grup başarıyla kapatıldı: {channel_id}")

        except Exception as e:
            logger.error(f"[X] CoffeeMatchService.close_match hatası: {e}")
            # Bu bir cron işi olduğu için hata fırlatmak yerine logluyoruz.
