"""
İletişim istekleri için repository.
"""

from typing import List
from src.repositories.base_repository import BaseRepository
from src.core.logger import logger


class CommunicationRepository(BaseRepository):
    """
    İletişim istekleri için veritabanı işlemleri.
    """
    
    def __init__(self, db_client):
        super().__init__(db_client, "communication_requests")
    
    def get_open_requests(self, limit: int = 10) -> List[dict]:
        """Açık iletişim isteklerini getirir."""
        try:
            with self.db_client.get_connection() as conn:
                cursor = conn.cursor()
                sql = f"SELECT * FROM {self.table_name} WHERE status = 'open' ORDER BY created_at DESC LIMIT ?"
                cursor.execute(sql, (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"[X] {self.table_name}.get_open_requests hatası: {e}")
            return []
    
    def get_user_requests(self, user_id: str) -> List[dict]:
        """Kullanıcının iletişim isteklerini getirir."""
        return self.list(filters={"requester_id": user_id})
    
    def mark_closed(self, communication_id: str) -> bool:
        """İletişim isteğini kapatılmış olarak işaretle."""
        from datetime import datetime
        return self.update(communication_id, {
            "status": "closed",
            "closed_at": datetime.now().isoformat()
        })
