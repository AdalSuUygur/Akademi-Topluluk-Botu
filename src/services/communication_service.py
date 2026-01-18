"""
Topluluk iletişim servisi.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from src.core.logger import logger
from src.core.exceptions import CemilBotError
from src.commands import ChatManager, ConversationManager, UserManager
from src.repositories import CommunicationRepository, UserRepository
from src.clients import CronClient


class CommunicationService:
    """
    Topluluk iletişim isteklerini yöneten servis.
    """
    
    def __init__(
        self,
        chat_manager: ChatManager,
        conv_manager: ConversationManager,
        user_manager: UserManager,
        communication_repo: CommunicationRepository,
        user_repo: UserRepository,
        cron_client: Optional[CronClient] = None
    ):
        self.chat = chat_manager
        self.conv = conv_manager
        self.user_manager = user_manager
        self.repo = communication_repo
        self.user_repo = user_repo
        self.cron_client = cron_client
    
    def _get_workspace_owner(self) -> Optional[str]:
        """Workspace owner veya admin kullanıcıyı bulur."""
        try:
            # Tüm kullanıcıları listele
            response = self.user_manager.list_users(limit=1000)
            if response.get("ok"):
                members = response.get("members", [])
                # Önce owner'ı bul
                for member in members:
                    if member.get("is_owner", False):
                        owner_id = member.get("id")
                        logger.info(f"[i] Workspace owner bulundu: {owner_id}")
                        return owner_id
                # Owner yoksa admin'i bul
                for member in members:
                    if member.get("is_admin", False):
                        admin_id = member.get("id")
                        logger.info(f"[i] Workspace admin bulundu: {admin_id}")
                        return admin_id
            logger.warning("[!] Workspace owner/admin bulunamadı")
            return None
        except Exception as e:
            logger.error(f"[X] Workspace owner bulurken hata: {e}")
            return None
    
    async def create_communication_request(
        self,
        requester_id: str,
        channel_id: str,
        topic: str,
        description: str
    ) -> str:
        """
        İletişim isteği oluşturur ve kanala block mesajı gönderir.
        
        Returns:
            communication_id: Oluşturulan iletişim isteğinin ID'si
        """
        try:
            # 1. Veritabanına kaydet
            communication_id = self.repo.create({
                "requester_id": requester_id,
                "topic": topic,
                "description": description,
                "channel_id": channel_id,
                "status": "open"
            })
            
            # 2. Kullanıcı bilgisini al
            user_data = self.user_repo.get_by_slack_id(requester_id)
            requester_name = user_data.get('full_name', requester_id) if user_data else requester_id
            
            logger.info(f"[>] İletişim isteği oluşturuldu | Kullanıcı: {requester_name} ({requester_id}) | Konu: {topic}")
            
            # 3. Yeni iletişim kanalı oluştur
            channel_name = f"iletisim-{communication_id[:8]}"
            try:
                communication_channel = self.conv.create_channel(
                    name=channel_name,
                    is_private=False
                )
                communication_channel_id = communication_channel["id"]
                logger.info(f"[+] İletişim kanalı oluşturuldu: #{channel_name} (ID: {communication_channel_id})")
                
                # Akademi owner'ı bul
                owner_id = self._get_workspace_owner()
                
                # Kanalı davet et: owner + requester
                invite_users = [requester_id]
                if owner_id and owner_id != requester_id:
                    invite_users.append(owner_id)
                
                if invite_users:
                    try:
                        self.conv.invite_users(communication_channel_id, invite_users)
                        logger.info(f"[+] Kullanıcılar kanala davet edildi: {invite_users}")
                    except Exception as e:
                        logger.warning(f"[!] Kullanıcılar davet edilemedi: {e}")
                
                # Kanal açılış mesajı gönder
                welcome_blocks = [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"💬 İletişim İsteği: {topic}",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": (
                                f"*<@{requester_id}>* iletişim kurmak istiyor:\n\n"
                                f"*{description}*\n\n"
                                f"Bu kanal 30 dakika sonra otomatik olarak kapatılacak. "
                                f"İletişim kurmak isteyenler 'Kanala Katıl' butonuna tıklayarak bu kanala katılabilir."
                            )
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"🆔 İletişim ID: `{communication_id[:8]}...` | ⏰ Kanal 30 dakika sonra kapanacak"
                            }
                        ]
                    }
                ]
                
                self.chat.post_message(
                    channel=communication_channel_id,
                    text=f"💬 İletişim İsteği: {topic}",
                    blocks=welcome_blocks
                )
                
                # Veritabanına communication_channel_id kaydet
                self.repo.update(communication_id, {"communication_channel_id": communication_channel_id})
                
                # 30 dakika sonra kanalı kapatmak için scheduled task ekle
                if self.cron_client:
                    try:
                        job_id = f"close_communication_channel_{communication_id}"
                        self.cron_client.add_once_job(
                            func=self._close_communication_channel,
                            delay_minutes=30,
                            job_id=job_id,
                            args=[communication_id, communication_channel_id]
                        )
                        logger.info(f"[+] Kanal kapatma görevi planlandı: {job_id} (30 dakika sonra)")
                    except Exception as e:
                        logger.warning(f"[!] Kanal kapatma görevi planlanamadı: {e}")
                
            except Exception as e:
                logger.error(f"[X] İletişim kanalı oluşturulamadı: {e}")
                communication_channel_id = None
            
            # 4. Block mesajı oluştur (pop-up butonu ile)
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"💬 İletişim İsteği: {topic}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*<@{requester_id}>* iletişim kurmak istiyor:\n\n{description}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "💚 Kanala Katıl",
                                "emoji": True
                            },
                            "style": "primary",
                            "action_id": "communication_join_channel",
                            "value": communication_id
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📋 Detaylar",
                                "emoji": True
                            },
                            "action_id": "communication_details",
                            "value": communication_id
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"🆔 ID: `{communication_id[:8]}...` | 📅 {datetime.now().strftime('%d.%m.%Y %H:%M')} | ⏰ 30 dakika sonra kapanacak"
                        }
                    ]
                }
            ]
            
            # 5. Mesajı kanala gönder
            response = self.chat.post_message(
                channel=channel_id,
                text=f"💬 İletişim İsteği: {topic}",
                blocks=blocks
            )
            
            # 6. Message TS'yi kaydet (güncelleme için)
            if response.get("ok"):
                message_ts = response.get("ts")
                self.repo.update(communication_id, {"message_ts": message_ts})
                logger.info(f"[+] İletişim isteği mesajı gönderildi | Kanal: {channel_id} | TS: {message_ts}")
            
            return communication_id
            
        except Exception as e:
            logger.error(f"[X] CommunicationService.create_communication_request hatası: {e}", exc_info=True)
            raise CemilBotError(f"İletişim isteği oluşturulamadı: {e}")
    
    async def join_communication_channel(self, communication_id: str, user_id: str) -> Dict[str, Any]:
        """
        Birisi 'Kanala Katıl' butonuna tıkladığında çağrılır.
        Kullanıcıyı iletişim kanalına davet eder.
        
        Returns:
            Dict with success status and message
        """
        try:
            # 1. İletişim isteğini al
            communication_request = self.repo.get(communication_id)
            if not communication_request:
                return {"success": False, "message": "❌ İletişim isteği bulunamadı."}
            
            # 2. Durum kontrolü
            if communication_request["status"] == "closed":
                return {"success": False, "message": "❌ Bu iletişim kanalı kapatılmış."}
            
            # 3. İletişim kanalı kontrolü
            communication_channel_id = communication_request.get("communication_channel_id")
            if not communication_channel_id:
                return {"success": False, "message": "❌ İletişim kanalı bulunamadı."}
            
            # 4. Kullanıcı bilgisini al
            user_data = self.user_repo.get_by_slack_id(user_id)
            user_name = user_data.get('full_name', user_id) if user_data else user_id
            
            logger.info(f"[>] Kanala katılma isteği | Kullanıcı: {user_name} ({user_id}) | İletişim ID: {communication_id}")
            
            # 5. Kullanıcıyı kanala davet et
            try:
                self.conv.invite_users(communication_channel_id, [user_id])
                logger.info(f"[+] Kullanıcı kanala davet edildi: {user_id} | Kanal: {communication_channel_id}")
                
                # İletişim kanalına bilgilendirme mesajı gönder
                self.chat.post_message(
                    channel=communication_channel_id,
                    text=f"✅ <@{user_id}> kanala katıldı!",
                    blocks=[{
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"✅ *<@{user_id}>* kanala katıldı ve iletişim kurmak istiyor!"
                        }
                    }]
                )
                
                return {
                    "success": True,
                    "message": f"✅ Kanala katıldınız! <#{communication_channel_id}> kanalına gidebilirsiniz.",
                    "channel_id": communication_channel_id
                }
            except Exception as e:
                error_msg = str(e).lower()
                if "already_in_channel" in error_msg or "already_in team" in error_msg:
                    logger.info(f"[i] Kullanıcı zaten kanalda: {user_id}")
                    return {
                        "success": True,
                        "message": f"✅ Zaten kanaldasınız! <#{communication_channel_id}> kanalına gidebilirsiniz.",
                        "channel_id": communication_channel_id
                    }
                else:
                    logger.warning(f"[!] Kullanıcı kanala davet edilemedi: {e}")
                    return {"success": False, "message": "❌ Kanala katılamadınız. Lütfen tekrar deneyin."}
            
        except Exception as e:
            logger.error(f"[X] CommunicationService.join_communication_channel hatası: {e}", exc_info=True)
            return {"success": False, "message": "Kanala katılırken bir hata oluştu."}
    
    def _close_communication_channel(self, communication_id: str, communication_channel_id: str):
        """İletişim kanalını kapatır (30 dakika sonra otomatik çağrılır)."""
        try:
            logger.info(f"[>] İletişim kanalı kapatılıyor | Communication ID: {communication_id} | Kanal: {communication_channel_id}")
            
            # Kanalı arşivle
            success = self.conv.archive_channel(communication_channel_id)
            
            if success:
                # İletişim isteğini kapatılmış olarak işaretle
                self.repo.update(communication_id, {"status": "closed"})
                
                # Kanal kapatıldı mesajı gönder (eğer hala açıksa)
                try:
                    self.chat.post_message(
                        channel=communication_channel_id,
                        text="⏰ Bu iletişim kanalı 30 dakika sonra otomatik olarak kapatıldı.",
                        blocks=[{
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "⏰ *Kanal Kapatıldı*\n\nBu iletişim kanalı 30 dakika sonra otomatik olarak kapatıldı. "
                                        "İletişime devam etmek isterseniz, yeni bir iletişim isteği oluşturabilirsiniz."
                            }
                        }]
                    )
                except Exception as e:
                    logger.debug(f"[i] Kanal zaten kapatılmış, mesaj gönderilemedi: {e}")
                
                logger.info(f"[+] İletişim kanalı başarıyla kapatıldı | Communication ID: {communication_id}")
            else:
                logger.warning(f"[!] İletişim kanalı kapatılamadı | Communication ID: {communication_id}")
                
        except Exception as e:
            logger.error(f"[X] İletişim kanalı kapatılırken hata: {e}", exc_info=True)
    
    def get_communication_details(self, communication_id: str) -> Dict[str, Any]:
        """İletişim isteği detaylarını getirir."""
        communication_request = self.repo.get(communication_id)
        if not communication_request:
            return None
        
        return communication_request
