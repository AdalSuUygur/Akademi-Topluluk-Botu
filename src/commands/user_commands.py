from typing import List, Optional, Dict, Any
from src.core.logger import logger
from src.core.exceptions import SlackClientError

class UserManager:
    """
    Slack Kullanıcı (Users) işlemlerini merkezi olarak yöneten sınıf.
    Dökümantasyon: https://api.slack.com/methods?filter=users
    """

    def __init__(self, client):
        self.client = client

    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Bir kullanıcı hakkında detaylı bilgi getirir (users.info).
        """
        try:
            response = self.client.users_info(user=user_id)
            if response["ok"]:
                user = response["user"]
                logger.info(f"[i] Kullanıcı bilgisi alındı: {user.get('real_name')} ({user_id})")
                return user
            else:
                raise SlackClientError(f"Kullanıcı bilgisi alınamadı: {response['error']}")
        except Exception as e:
            logger.error(f"[X] users.info hatası: {e}", exc_info=True)
            raise SlackClientError(str(e))

    def list_users(self, limit: int = 100, cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Workspace'teki tüm kullanıcıları listeler (users.list).
        """
        try:
            response = self.client.users_list(limit=limit, cursor=cursor)
            if response["ok"]:
                members = response.get("members", [])
                logger.info(f"[i] Kullanıcı listesi alındı: {len(members)} kişi")
                return response
            else:
                raise SlackClientError(f"Kullanıcılar listelenemedi: {response['error']}")
        except Exception as e:
            logger.error(f"[X] users.list hatası: {e}", exc_info=True)
            raise SlackClientError(str(e))

    def lookup_by_email(self, email: str) -> Dict[str, Any]:
        """
        Email adresi ile kullanıcı bulur (users.lookupByEmail).
        """
        try:
            response = self.client.users_lookupByEmail(email=email)
            if response["ok"]:
                user = response["user"]
                logger.info(f"[+] Email ile kullanıcı bulundu: {email} -> {user['id']}")
                return user
            else:
                raise SlackClientError(f"Email ile kullanıcı bulunamadı: {response['error']}")
        except Exception as e:
            logger.error(f"[X] users.lookupByEmail hatası: {e}")
            raise SlackClientError(str(e))

    def get_presence(self, user_id: str) -> str:
        """
        Kullanıcının online/offline durumunu getirir (users.getPresence).
        """
        try:
            response = self.client.users_getPresence(user=user_id)
            if response["ok"]:
                presence = response.get("presence", "unknown")
                logger.info(f"[i] Kullanıcı durumu ({user_id}): {presence}")
                return presence
            else:
                raise SlackClientError(f"Durum bilgisi alınamadı: {response['error']}")
        except Exception as e:
            logger.error(f"[X] users.getPresence hatası: {e}")
            raise SlackClientError(str(e))

    def set_presence(self, presence: str) -> bool:
        """
        Botun veya kullanıcının durumunu manuel ayarlar (users.setPresence).
        presence: 'auto' veya 'away'
        """
        try:
            response = self.client.users_setPresence(presence=presence)
            if response["ok"]:
                logger.info(f"[+] Durum manuel ayarlandı: {presence}")
                return True
            else:
                raise SlackClientError(f"Durum ayarlanamadı: {response['error']}")
        except Exception as e:
            logger.error(f"[X] users.setPresence hatası: {e}")
            raise SlackClientError(str(e))

    def get_profile(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Kullanıcı profil bilgilerini getirir (users.profile.get).
        """
        try:
            response = self.client.users_profile_get(user=user_id)
            if response["ok"]:
                profile = response.get("profile", {})
                logger.info(f"[i] Profil bilgisi alındı: {user_id or 'SELF'}")
                return profile
            else:
                raise SlackClientError(f"Profil alınamadı: {response['error']}")
        except Exception as e:
            logger.error(f"[X] users.profile.get hatası: {e}")
            raise SlackClientError(str(e))

    def set_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kullanıcı profil bilgilerini günceller (users.profile.set).
        """
        try:
            response = self.client.users_profile_set(profile=profile_data)
            if response["ok"]:
                logger.info("[+] Profil başarıyla güncellendi")
                return response.get("profile", {})
            else:
                raise SlackClientError(f"Profil güncellenemedi: {response['error']}")
        except Exception as e:
            logger.error(f"[X] users.profile.set hatası: {e}")
            raise SlackClientError(str(e))

    def get_identity(self) -> Dict[str, Any]:
        """
        Mevcut kullanıcının kimlik bilgilerini getirir (users.identity).
        """
        try:
            response = self.client.users_identity()
            if response["ok"]:
                identity = response.get("user", {})
                logger.info(f"[i] Kimlik bilgisi onaylandı: {identity.get('name')}")
                return identity
            else:
                raise SlackClientError(f"Kimlik doğrulanamadı: {response['error']}")
        except Exception as e:
            logger.error(f"[X] users.identity hatası: {e}")
            raise SlackClientError(str(e))

    def list_conversations(self, user_id: Optional[str] = None, types: str = "public_channel,private_channel") -> List[Dict[str, Any]]:
        """
        Kullanıcının dahil olduğu konuşmaları listeler (users.conversations).
        """
        try:
            response = self.client.users_conversations(user=user_id, types=types)
            if response["ok"]:
                channels = response.get("channels", [])
                logger.info(f"[i] Kullanıcı konuşmaları listelendi: {len(channels)} adet")
                return channels
            else:
                raise SlackClientError(f"Konuşmalar alınamadı: {response['error']}")
        except Exception as e:
            logger.error(f"[X] users.conversations hatası: {e}")
            raise SlackClientError(str(e))

    def set_photo(self, image_path: str) -> bool:
        """
        Kullanıcı profil fotoğrafını ayarlar (users.setPhoto).
        """
        try:
            with open(image_path, "rb") as image_file:
                response = self.client.users_setPhoto(image=image_file)
            if response["ok"]:
                logger.info(f"[+] Profil fotoğrafı güncellendi: {image_path}")
                return True
            else:
                raise SlackClientError(f"Fotoğraf ayarlanamadı: {response['error']}")
        except Exception as e:
            logger.error(f"[X] users.setPhoto hatası: {e}")
            raise SlackClientError(str(e))

    def delete_photo(self) -> bool:
        """
        Kullanıcı profil fotoğrafını siler (users.deletePhoto).
        """
        try:
            response = self.client.users_deletePhoto()
            if response["ok"]:
                logger.info("[+] Profil fotoğrafı silindi")
                return True
            else:
                raise SlackClientError(f"Fotoğraf silinemedi: {response['error']}")
        except Exception as e:
            logger.error(f"[X] users.deletePhoto hatası: {e}")
            raise SlackClientError(str(e))

    def lookup_discoverable_contact(self, email: str) -> Dict[str, Any]:
        """
        Email ile keşfedilebilir kişileri arar (users.discoverableContacts.lookup).
        """
        try:
            response = self.client.users_discoverableContacts_lookup(email=email)
            if response["ok"]:
                logger.info(f"[i] Keşfedilebilir kişi sorgusu başarılı: {email}")
                return response
            else:
                raise SlackClientError(f"Kişi sorgulanamadı: {response['error']}")
        except Exception as e:
            logger.error(f"[X] users.discoverableContacts.lookup hatası: {e}")
            raise SlackClientError(str(e))

    def set_active(self) -> bool:
        """
        Kullanıcıyı aktif olarak işaretler (users.setActive).
        Not: Bu metod bazı uygulama tiplerinde kısıtlanmış olabilir.
        """
        try:
            response = self.client.users_setActive()
            if response["ok"]:
                logger.info("[+] Kullanıcı aktif olarak işaretlendi")
                return True
            else:
                raise SlackClientError(f"Aktif işareti başarısız: {response['error']}")
        except Exception as e:
            logger.error(f"[X] users.setActive hatası: {e}")
            raise SlackClientError(str(e))
