"""
Database Models for Google Maps Scraper
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from dataclasses import dataclass
from database.connection import db
import logging

logger = logging.getLogger(__name__)

@dataclass
class Isletme:
    """İşletme model sınıfı"""
    id: Optional[int] = None
    google_id: str = ""
    isim: str = ""
    kategori: Optional[str] = None
    telefon: Optional[str] = None
    adres: Optional[str] = None
    website: Optional[str] = None
    calisma_saatleri: Optional[str] = None
    puan: Optional[float] = None
    yorum_sayisi: int = 0
    yogunluk_bilgisi: Optional[str] = None
    konum_linki: Optional[str] = None
    resim_url: Optional[str] = None
    il: Optional[str] = None
    ilce: Optional[str] = None
    durum: int = 0  # 0=potansiyel, 1=müşteri
    notlar: Optional[str] = None
    source_url: Optional[str] = None
    eklenme_tarihi: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Musteri:
    """Müşteri model sınıfı"""
    id: Optional[int] = None
    isletme_id: int = 0
    paket: Optional[str] = None
    odeme_durumu: str = "beklemede"  # beklemede, odendi, iptal
    iletisim_tarihi: Optional[date] = None
    notlar: Optional[str] = None
    kayit_tarihi: Optional[datetime] = None

@dataclass
class BlacklistItem:
    """Blacklist model sınıfı"""
    id: Optional[int] = None
    google_id: Optional[str] = None
    source_url: Optional[str] = None
    sebep: Optional[str] = None
    tarih: Optional[datetime] = None

class IsletmeManager:
    """İşletme veritabanı işlemleri"""
    
    @staticmethod
    def create(isletme: Isletme) -> Optional[int]:
        """Yeni işletme ekle"""
        query = """
        INSERT INTO isletmeler (
            google_id, isim, kategori, telefon, adres, website,
            calisma_saatleri, puan, yorum_sayisi, yogunluk_bilgisi,
            konum_linki, resim_url, il, ilce, durum, notlar, source_url
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        params = (
            isletme.google_id, isletme.isim, isletme.kategori, isletme.telefon,
            isletme.adres, isletme.website, isletme.calisma_saatleri, isletme.puan,
            isletme.yorum_sayisi, isletme.yogunluk_bilgisi, isletme.konum_linki,
            isletme.resim_url, isletme.il, isletme.ilce, isletme.durum,
            isletme.notlar, isletme.source_url
        )
        
        if db.execute_update(query, params):
            return db.get_last_insert_id()
        return None
    
    @staticmethod
    def update(isletme: Isletme) -> bool:
        """İşletme güncelle"""
        query = """
        UPDATE isletmeler SET
            isim=%s, kategori=%s, telefon=%s, adres=%s, website=%s,
            calisma_saatleri=%s, puan=%s, yorum_sayisi=%s, yogunluk_bilgisi=%s,
            konum_linki=%s, resim_url=%s, il=%s, ilce=%s, durum=%s, notlar=%s,
            source_url=%s, updated_at=CURRENT_TIMESTAMP
        WHERE google_id=%s
        """
        params = (
            isletme.isim, isletme.kategori, isletme.telefon, isletme.adres,
            isletme.website, isletme.calisma_saatleri, isletme.puan,
            isletme.yorum_sayisi, isletme.yogunluk_bilgisi, isletme.konum_linki,
            isletme.resim_url, isletme.il, isletme.ilce, isletme.durum,
            isletme.notlar, isletme.source_url, isletme.google_id
        )
        
        return db.execute_update(query, params)
    
    @staticmethod
    def upsert(isletme: Isletme) -> Optional[int]:
        """İşletme ekle veya güncelle"""
        existing = IsletmeManager.get_by_google_id(isletme.google_id)
        if existing:
            isletme.id = existing.id
            if IsletmeManager.update(isletme):
                return existing.id
            return None
        else:
            return IsletmeManager.create(isletme)
    
    @staticmethod
    def get_by_id(isletme_id: int) -> Optional[Isletme]:
        """ID ile işletme getir"""
        query = "SELECT * FROM isletmeler WHERE id = %s"
        result = db.execute_query(query, (isletme_id,))
        
        if result and len(result) > 0:
            return IsletmeManager._dict_to_isletme(result[0])
        return None
    
    @staticmethod
    def get_by_google_id(google_id: str) -> Optional[Isletme]:
        """Google ID ile işletme getir"""
        query = "SELECT * FROM isletmeler WHERE google_id = %s"
        result = db.execute_query(query, (google_id,))
        
        if result and len(result) > 0:
            return IsletmeManager._dict_to_isletme(result[0])
        return None
    
    @staticmethod
    def get_all(limit: int = None, offset: int = 0) -> List[Isletme]:
        """Tüm işletmeleri getir"""
        query = "SELECT * FROM isletmeler ORDER BY eklenme_tarihi DESC"
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        result = db.execute_query(query)
        if result:
            return [IsletmeManager._dict_to_isletme(row) for row in result]
        return []
    
    @staticmethod
    def search(filters: Dict[str, Any]) -> List[Isletme]:
        """Filtrelere göre işletme ara"""
        conditions = []
        params = []
        
        if filters.get('il'):
            conditions.append("il = %s")
            params.append(filters['il'])
        
        if filters.get('ilce'):
            conditions.append("ilce = %s")
            params.append(filters['ilce'])
        
        if filters.get('kategori'):
            conditions.append("kategori LIKE %s")
            params.append(f"%{filters['kategori']}%")
        
        if filters.get('isim'):
            conditions.append("isim LIKE %s")
            params.append(f"%{filters['isim']}%")
        
        if filters.get('telefon_var') is not None:
            if filters['telefon_var']:
                conditions.append("telefon IS NOT NULL AND telefon != ''")
            else:
                conditions.append("(telefon IS NULL OR telefon = '')")
        
        if filters.get('durum') is not None:
            conditions.append("durum = %s")
            params.append(filters['durum'])
        
        query = "SELECT * FROM isletmeler"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY eklenme_tarihi DESC"
        
        result = db.execute_query(query, tuple(params))
        if result:
            return [IsletmeManager._dict_to_isletme(row) for row in result]
        return []
    
    @staticmethod
    def delete(isletme_id: int) -> bool:
        """İşletme sil"""
        query = "DELETE FROM isletmeler WHERE id = %s"
        return db.execute_update(query, (isletme_id,))
    
    @staticmethod
    def make_customer(isletme_id: int) -> bool:
        """İşletmeyi müşteri yap"""
        try:
            logger.info(f"Müşteri yapma işlemi başlatılıyor: isletme_id={isletme_id}")
            
            # Önce işletmenin var olduğunu kontrol et
            isletme = IsletmeManager.get_by_id(isletme_id)
            if not isletme:
                logger.error(f"İşletme bulunamadı: id={isletme_id}")
                return False
            
            logger.info(f"İşletme bulundu: {isletme.isim}")
            
            # Zaten müşteri mi kontrol et
            if isletme.durum == 1:
                logger.warning(f"İşletme zaten müşteri: {isletme.isim}")
                return True
            
            # İşletme durumunu güncelle
            logger.info("İşletme durumu güncelleniyor...")
            query = "UPDATE isletmeler SET durum = 1, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
            if not db.execute_update(query, (isletme_id,)):
                logger.error("İşletme durumu güncellenemedi")
                return False
            
            logger.info("İşletme durumu başarıyla güncellendi")
            
            # Zaten müşteri kaydı var mı kontrol et
            existing_customer = MusteriManager.get_by_isletme_id(isletme_id)
            if existing_customer:
                logger.info("Müşteri kaydı zaten mevcut")
                return True
            
            # Müşteri kaydı oluştur
            logger.info("Müşteri kaydı oluşturuluyor...")
            from datetime import datetime
            musteri = Musteri(
                isletme_id=isletme_id,
                paket="Standart",
                odeme_durumu="beklemede",
                iletisim_tarihi=datetime.now().date(),
                notlar="Otomatik müşteri kaydı"
            )
            
            musteri_id = MusteriManager.create(musteri)
            if musteri_id:
                logger.info(f"Müşteri kaydı başarıyla oluşturuldu: musteri_id={musteri_id}")
                return True
            else:
                logger.error("Müşteri kaydı oluşturulamadı")
                return False
            
        except Exception as e:
            logger.error(f"Müşteri yapma hatası: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    @staticmethod
    def get_statistics() -> Dict[str, int]:
        """İstatistikleri getir"""
        stats = {}
        
        # Toplam işletme sayısı
        result = db.execute_query("SELECT COUNT(*) as count FROM isletmeler")
        stats['toplam_isletme'] = result[0]['count'] if result else 0
        
        # Müşteri sayısı
        result = db.execute_query("SELECT COUNT(*) as count FROM isletmeler WHERE durum = 1")
        stats['musteri_sayisi'] = result[0]['count'] if result else 0
        
        # Potansiyel müşteri sayısı
        result = db.execute_query("SELECT COUNT(*) as count FROM isletmeler WHERE durum = 0")
        stats['potansiyel_sayisi'] = result[0]['count'] if result else 0
        
        # Telefonu olan işletme sayısı
        result = db.execute_query("SELECT COUNT(*) as count FROM isletmeler WHERE telefon IS NOT NULL AND telefon != ''")
        stats['telefon_var'] = result[0]['count'] if result else 0
        
        return stats
    
    @staticmethod
    def _dict_to_isletme(data: Dict) -> Isletme:
        """Dict'i Isletme objesine çevir"""
        return Isletme(
            id=data.get('id'),
            google_id=data.get('google_id', ''),
            isim=data.get('isim', ''),
            kategori=data.get('kategori'),
            telefon=data.get('telefon'),
            adres=data.get('adres'),
            website=data.get('website'),
            calisma_saatleri=data.get('calisma_saatleri'),
            puan=data.get('puan'),
            yorum_sayisi=data.get('yorum_sayisi', 0),
            yogunluk_bilgisi=data.get('yogunluk_bilgisi'),
            konum_linki=data.get('konum_linki'),
            resim_url=data.get('resim_url'),
            il=data.get('il'),
            ilce=data.get('ilce'),
            durum=data.get('durum', 0),
            notlar=data.get('notlar'),
            source_url=data.get('source_url'),
            eklenme_tarihi=data.get('eklenme_tarihi'),
            updated_at=data.get('updated_at')
        )

class MusteriManager:
    """Müşteri veritabanı işlemleri"""
    
    @staticmethod
    def create(musteri: Musteri) -> Optional[int]:
        """Yeni müşteri ekle"""
        try:
            logger.info(f"🔍 DIAGNOSTIC: Müşteri oluşturma başlatılıyor: isletme_id={musteri.isletme_id}")
            
            # Veritabanı bağlantısını kontrol et
            if not db.initialized:
                logger.error("🚨 DIAGNOSTIC: Veritabanı havuzu başlatılmamış!")
                return None
            
            logger.info(f"✅ DIAGNOSTIC: Veritabanı havuzu aktif: {db.initialized}")
            
            query = """
            INSERT INTO musteriler (isletme_id, paket, odeme_durumu, iletisim_tarihi, notlar)
            VALUES (%s, %s, %s, %s, %s)
            """
            params = (
                musteri.isletme_id, musteri.paket, musteri.odeme_durumu,
                musteri.iletisim_tarihi, musteri.notlar
            )
            
            logger.info(f"🔍 DIAGNOSTIC: SQL Query: {query}")
            logger.info(f"🔍 DIAGNOSTIC: Parameters: {params}")
            logger.info(f"🔍 DIAGNOSTIC: Parameter types: {[type(p).__name__ for p in params]}")
            
            # Önce işletmenin var olduğunu kontrol et
            check_query = "SELECT id FROM isletmeler WHERE id = %s"
            check_result = db.execute_query(check_query, (musteri.isletme_id,))
            logger.info(f"🔍 DIAGNOSTIC: İşletme kontrolü sonucu: {check_result}")
            
            if not check_result:
                logger.error(f"🚨 DIAGNOSTIC: İşletme bulunamadı: id={musteri.isletme_id}")
                return None
            
            # Mevcut müşteri kaydı var mı kontrol et
            existing_query = "SELECT id FROM musteriler WHERE isletme_id = %s"
            existing_result = db.execute_query(existing_query, (musteri.isletme_id,))
            logger.info(f"🔍 DIAGNOSTIC: Mevcut müşteri kontrolü: {existing_result}")
            
            if existing_result:
                logger.warning(f"⚠️ DIAGNOSTIC: Müşteri kaydı zaten var: {existing_result[0]['id']}")
                return existing_result[0]['id']
            
            # Müşteri kaydını oluştur
            logger.info("🔍 DIAGNOSTIC: Müşteri kaydı oluşturuluyor...")
            result = db.execute_update(query, params)
            logger.info(f"🔍 DIAGNOSTIC: execute_update sonucu: {result}")
            
            if result:
                last_id = db.get_last_insert_id()
                logger.info(f"✅ DIAGNOSTIC: Müşteri başarıyla oluşturuldu: id={last_id}")
                return last_id
            else:
                logger.error("🚨 DIAGNOSTIC: db.execute_update() False döndü")
                
                # Hata detaylarını al
                if hasattr(db, 'last_error'):
                    logger.error(f"🚨 DIAGNOSTIC: Son hata: {db.last_error}")
                
                return None
                
        except Exception as e:
            logger.error(f"🚨 DIAGNOSTIC: Müşteri oluşturma hatası: {e}")
            import traceback
            logger.error(f"🚨 DIAGNOSTIC: Traceback: {traceback.format_exc()}")
            return None
    
    @staticmethod
    def update(musteri: Musteri) -> bool:
        """Müşteri güncelle"""
        query = """
        UPDATE musteriler SET
            paket=%s, odeme_durumu=%s, iletisim_tarihi=%s, notlar=%s
        WHERE id=%s
        """
        params = (
            musteri.paket, musteri.odeme_durumu, musteri.iletisim_tarihi,
            musteri.notlar, musteri.id
        )
        
        return db.execute_update(query, params)
    
    @staticmethod
    def get_by_isletme_id(isletme_id: int) -> Optional[Musteri]:
        """İşletme ID ile müşteri getir"""
        query = "SELECT * FROM musteriler WHERE isletme_id = %s"
        result = db.execute_query(query, (isletme_id,))
        
        if result and len(result) > 0:
            return MusteriManager._dict_to_musteri(result[0])
        return None
    
    @staticmethod
    def get_all_with_isletme() -> List[Dict]:
        """Tüm müşterileri işletme bilgileriyle getir"""
        query = """
        SELECT m.*, i.isim, i.telefon, i.adres, i.il, i.ilce, i.kategori
        FROM musteriler m
        JOIN isletmeler i ON m.isletme_id = i.id
        ORDER BY m.kayit_tarihi DESC
        """
        
        result = db.execute_query(query)
        return result if result else []
    
    @staticmethod
    def delete(musteri_id: int) -> bool:
        """Müşteri sil"""
        query = "DELETE FROM musteriler WHERE id = %s"
        return db.execute_update(query, (musteri_id,))
    
    @staticmethod
    def _dict_to_musteri(data: Dict) -> Musteri:
        """Dict'i Musteri objesine çevir"""
        return Musteri(
            id=data.get('id'),
            isletme_id=data.get('isletme_id', 0),
            paket=data.get('paket'),
            odeme_durumu=data.get('odeme_durumu', 'beklemede'),
            iletisim_tarihi=data.get('iletisim_tarihi'),
            notlar=data.get('notlar'),
            kayit_tarihi=data.get('kayit_tarihi')
        )

class BlacklistManager:
    """Blacklist veritabanı işlemleri"""
    
    @staticmethod
    def add(item: BlacklistItem) -> Optional[int]:
        """Blacklist'e ekle"""
        query = """
        INSERT INTO blacklist (google_id, source_url, sebep)
        VALUES (%s, %s, %s)
        """
        params = (item.google_id, item.source_url, item.sebep)
        
        if db.execute_update(query, params):
            return db.get_last_insert_id()
        return None
    
    @staticmethod
    def is_blacklisted(google_id: str = None, source_url: str = None) -> bool:
        """Blacklist'te var mı kontrol et"""
        if google_id:
            query = "SELECT COUNT(*) as count FROM blacklist WHERE google_id = %s"
            result = db.execute_query(query, (google_id,))
        elif source_url:
            query = "SELECT COUNT(*) as count FROM blacklist WHERE source_url = %s"
            result = db.execute_query(query, (source_url,))
        else:
            return False
        
        return result[0]['count'] > 0 if result else False
    
    @staticmethod
    def get_all() -> List[BlacklistItem]:
        """Tüm blacklist öğelerini getir"""
        query = "SELECT * FROM blacklist ORDER BY tarih DESC"
        result = db.execute_query(query)
        
        if result:
            return [BlacklistManager._dict_to_blacklist(row) for row in result]
        return []
    
    @staticmethod
    def remove(item_id: int) -> bool:
        """Blacklist'ten çıkar"""
        query = "DELETE FROM blacklist WHERE id = %s"
        return db.execute_update(query, (item_id,))
    
    @staticmethod
    def _dict_to_blacklist(data: Dict) -> BlacklistItem:
        """Dict'i BlacklistItem objesine çevir"""
        return BlacklistItem(
            id=data.get('id'),
            google_id=data.get('google_id'),
            source_url=data.get('source_url'),
            sebep=data.get('sebep'),
            tarih=data.get('tarih')
        )