"""
Topluluk iletişim komut handler'ları.
"""

import asyncio
from slack_bolt import App
from src.core.logger import logger
from src.core.settings import get_settings
from src.core.rate_limiter import get_rate_limiter
from src.core.validators import CommunicationRequest
from src.commands import ChatManager
from src.services import CommunicationService
from src.repositories import UserRepository


def setup_communication_handlers(
    app: App,
    communication_service: CommunicationService,
    chat_manager: ChatManager,
    user_repo: UserRepository
):
    """İletişim handler'larını kaydeder."""
    settings = get_settings()
    rate_limiter = get_rate_limiter(
        max_requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window
    )
    
    @app.command("/iletisim-kur")
    def handle_communication_request(ack, body):
        """İletişim isteği oluşturur."""
        ack()
        user_id = body["user_id"]
        channel_id = body["channel_id"]
        text = body.get("text", "").strip()
        
        # Rate limiting kontrolü
        allowed, error_msg = rate_limiter.is_allowed(user_id)
        if not allowed:
            chat_manager.post_ephemeral(channel=channel_id, user=user_id, text=error_msg)
            return
        
        # Kullanıcı bilgisini al
        try:
            user_data = user_repo.get_by_slack_id(user_id)
            user_name = user_data.get('full_name', user_id) if user_data else user_id
        except Exception:
            user_name = user_id
        
        logger.info(f"[>] /iletisim-kur komutu geldi | Kullanıcı: {user_name} ({user_id}) | Kanal: {channel_id}")
        
        # Input validation
        if not text:
            chat_manager.post_ephemeral(
                channel=channel_id,
                user=user_id,
                text="🤔 İletişim isteği için en azından konu gerekli.\nÖrnek: `/iletisim-kur Proje hakkında konuşmak istiyorum`"
            )
            return
        
        try:
            communication_request = CommunicationRequest.parse_from_text(text)
        except ValueError as ve:
            chat_manager.post_ephemeral(
                channel=channel_id,
                user=user_id,
                text=f"İletişim isteği formatı hatalı. Lütfen tekrar deneyin.\n\nHata: {str(ve)}"
            )
            return
        
        # Async işlemi sync wrapper ile çalıştır
        async def process_communication_request():
            try:
                communication_id = await communication_service.create_communication_request(
                    requester_id=user_id,
                    channel_id=channel_id,
                    topic=communication_request.topic,
                    description=communication_request.description
                )
                
                chat_manager.post_ephemeral(
                    channel=channel_id,
                    user=user_id,
                    text="✅ İletişim isteğiniz paylaşıldı! Topluluk üyeleri sizinle iletişim kurabilir."
                )
                
                logger.info(f"[+] İletişim isteği oluşturuldu | Kullanıcı: {user_name} ({user_id}) | ID: {communication_id}")
                
            except Exception as e:
                logger.error(f"[X] İletişim isteği hatası: {e}", exc_info=True)
                chat_manager.post_ephemeral(
                    channel=channel_id,
                    user=user_id,
                    text="İletişim isteği oluşturulurken bir hata oluştu. Lütfen tekrar deneyin."
                )
        
        asyncio.run(process_communication_request())
    
    @app.action("communication_join_channel")
    def handle_communication_join_channel(ack, body):
        """'Kanala Katıl' butonuna tıklama (pop-up)."""
        ack()
        user_id = body["user"]["id"]
        channel_id = body["channel"]["id"]
        communication_id = body["actions"][0]["value"]
        
        # Kullanıcı bilgisini al
        try:
            user_data = user_repo.get_by_slack_id(user_id)
            user_name = user_data.get('full_name', user_id) if user_data else user_id
        except Exception:
            user_name = user_id
        
        logger.info(f"[>] Kanala katılma isteği | Kullanıcı: {user_name} ({user_id}) | İletişim ID: {communication_id}")
        
        # Async işlemi sync wrapper ile çalıştır
        async def process_join_channel():
            try:
                result = await communication_service.join_communication_channel(communication_id, user_id)
                
                if result["success"]:
                    # Ephemeral mesaj (pop-up - sadece tıklayan görür)
                    chat_manager.post_ephemeral(
                        channel=channel_id,
                        user=user_id,
                        text=result["message"]
                    )
                    logger.info(f"[+] Kanala katılma başarılı | Kullanıcı: {user_name} ({user_id}) | İletişim ID: {communication_id}")
                else:
                    chat_manager.post_ephemeral(
                        channel=channel_id,
                        user=user_id,
                        text=result["message"]
                    )
                    logger.warning(f"[!] Kanala katılma başarısız | Kullanıcı: {user_name} ({user_id}) | Sebep: {result.get('message')}")
                    
            except Exception as e:
                logger.error(f"[X] Kanala katılma hatası: {e}", exc_info=True)
                chat_manager.post_ephemeral(
                    channel=channel_id,
                    user=user_id,
                    text="Kanala katılırken bir hata oluştu. Lütfen tekrar deneyin."
                )
        
        asyncio.run(process_join_channel())
    
    @app.action("communication_details")
    def handle_communication_details(ack, body):
        """'Detaylar' butonuna tıklama."""
        ack()
        user_id = body["user"]["id"]
        channel_id = body["channel"]["id"]
        communication_id = body["actions"][0]["value"]
        
        communication_request = communication_service.get_communication_details(communication_id)
        if not communication_request:
            chat_manager.post_ephemeral(
                channel=channel_id,
                user=user_id,
                text="❌ İletişim isteği bulunamadı."
            )
            return
        
        # Durum metni
        status_text = {
            "open": "🟢 Açık",
            "closed": "🔴 Kapatıldı"
        }.get(communication_request.get("status", "open"), "❓ Bilinmiyor")
        
        # Detaylı bilgi göster
        details_text = (
            f"*📋 İletişim İsteği Detayları*\n\n"
            f"*Konu:* {communication_request['topic']}\n"
            f"*Açıklama:* {communication_request['description']}\n"
            f"*Durum:* {status_text}\n"
            f"*Oluşturulma:* {communication_request.get('created_at', 'Bilinmiyor')}\n"
        )
        
        if communication_request.get('closed_at'):
            details_text += f"*Kapanma:* {communication_request['closed_at']}\n"
        
        chat_manager.post_ephemeral(
            channel=channel_id,
            user=user_id,
            text=details_text
        )
        
        logger.info(f"[i] İletişim detayları görüntülendi | Kullanıcı: {user_id} | İletişim ID: {communication_id}")
