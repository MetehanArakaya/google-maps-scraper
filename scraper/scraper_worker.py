"""
QThread-based Scraper Worker for Google Maps Scraper
"""
from PySide6.QtCore import QThread, Signal, QObject, QMutex, QMutexLocker
from typing import List, Dict, Any
import logging
import time
from scraper.google_maps_scraper import GoogleMapsScraper
from database.models import Isletme, IsletmeManager
from utils.excel_export import ExcelExporter

logger = logging.getLogger(__name__)

class ScraperWorker(QThread):
    """Thread-safe QThread tabanlı scraper worker sınıfı"""
    
    # Signals
    progress_updated = Signal(int)  # Progress percentage
    status_updated = Signal(str)    # Status message
    log_message = Signal(str)       # Log message
    business_scraped = Signal(dict) # Business data scraped
    scraping_finished = Signal(dict) # Scraping completed with stats
    error_occurred = Signal(str)    # Error message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scraper = None
        self.config = {}
        self.search_params = {}
        self.should_stop = False
        self.scraped_businesses = []
        
        # Thread safety
        self.mutex = QMutex()
        self.is_running = False
        
    def setup_scraper(self, config: Dict[str, Any]):
        """Scraper ayarlarını yap"""
        self.config = config
        self.scraper = GoogleMapsScraper(config)
        
    def set_search_params(self, il: str, ilce: str = "", sektor: str = "", limit: int = 50):
        """Arama parametrelerini ayarla"""
        self.search_params = {
            'il': il,
            'ilce': ilce,
            'sektor': sektor,
            'limit': limit
        }
        
    def run(self):
        """Thread-safe ana scraping işlemi"""
        with QMutexLocker(self.mutex):
            if self.is_running:
                self.error_occurred.emit("Scraping zaten çalışıyor")
                return
            self.is_running = True
        
        try:
            self.should_stop = False
            self.scraped_businesses = []
            
            # Parametreleri kontrol et
            if not self.search_params:
                self.error_occurred.emit("Arama parametreleri ayarlanmamış")
                return
            
            # Scraper'ı başlat
            if not self.scraper:
                self.error_occurred.emit("Scraper ayarlanmamış")
                return
            
            # Başlangıç mesajı
            search_query = self._build_search_description()
            self.status_updated.emit(f"Scraping başlatılıyor: {search_query}")
            self.log_message.emit(f"Arama başlatıldı: {search_query}")
            
            # Progress başlat
            self.progress_updated.emit(0)
            
            # Scraping işlemini başlat
            businesses = self.scraper.search_businesses(
                il=self.search_params['il'],
                ilce=self.search_params['ilce'],
                sektor=self.search_params['sektor'],
                limit=self.search_params['limit']
            )
            
            if self.should_stop:
                self.status_updated.emit("Scraping durduruldu")
                self.log_message.emit("Kullanıcı tarafından durduruldu")
                return
            
            # Veritabanına kaydet (thread-safe)
            self.status_updated.emit("Veritabanına kaydediliyor...")
            self.progress_updated.emit(80)
            
            saved_count = 0
            updated_count = 0
            error_count = 0
            
            # Batch processing için businesses'ları grupla
            batch_size = 10
            total_businesses = len(businesses)
            
            for batch_start in range(0, total_businesses, batch_size):
                if self.should_stop:
                    break
                
                batch_end = min(batch_start + batch_size, total_businesses)
                batch = businesses[batch_start:batch_end]
                
                # Her batch'i thread-safe şekilde işle
                batch_saved, batch_updated, batch_errors = self._process_business_batch(batch)
                saved_count += batch_saved
                updated_count += batch_updated
                error_count += batch_errors
                
                # Progress güncelle
                progress = 80 + int((batch_end) / total_businesses * 15)
                self.progress_updated.emit(progress)
                
                # CPU'ya nefes alma fırsatı ver
                self.msleep(10)
            
            self.scraped_businesses = businesses
            
            # Excel export
            if self.config.get('export_excel', True) and not self.should_stop:
                self.status_updated.emit("Excel dosyası oluşturuluyor...")
                self.progress_updated.emit(95)
                
                try:
                    excel_path = self._export_to_excel(businesses)
                    if excel_path:
                        self.log_message.emit(f"Excel dosyası oluşturuldu: {excel_path}")
                except Exception as e:
                    logger.error(f"Excel export hatası: {e}")
                    self.log_message.emit(f"Excel export hatası: {str(e)}")
            
            # İstatistikleri hazırla
            stats = {
                'total_found': len(businesses),
                'saved_count': saved_count,
                'updated_count': updated_count,
                'duplicate_count': getattr(self.scraper, 'duplicate_count', 0),
                'error_count': error_count,
                'search_query': search_query
            }
            
            # Tamamlandı
            if not self.should_stop:
                self.progress_updated.emit(100)
                self.status_updated.emit("Scraping tamamlandı")
                self.log_message.emit(f"Toplam {len(businesses)} işletme bulundu, {saved_count} yeni, {updated_count} güncellendi")
                
                # Finished signal
                self.scraping_finished.emit(stats)
            
        except Exception as e:
            logger.error(f"Scraper worker hatası: {e}")
            self.error_occurred.emit(f"Scraping hatası: {str(e)}")
            
        finally:
            # Thread-safe cleanup
            with QMutexLocker(self.mutex):
                self.is_running = False
            
            # Scraper cleanup
            if self.scraper:
                try:
                    self.scraper.cleanup()
                except Exception as e:
                    logger.error(f"Scraper cleanup hatası: {e}")
    
    def _process_business_batch(self, batch: List[Isletme]) -> tuple:
        """Thread-safe batch processing"""
        saved_count = 0
        updated_count = 0
        error_count = 0
        
        for business in batch:
            if self.should_stop:
                break
            
            try:
                # Thread-safe database operations
                existing = IsletmeManager.get_by_google_id(business.google_id)
                if existing:
                    business.id = existing.id
                    if IsletmeManager.update(business):
                        updated_count += 1
                    else:
                        error_count += 1
                else:
                    business_id = IsletmeManager.create(business)
                    if business_id:
                        business.id = business_id
                        saved_count += 1
                    else:
                        error_count += 1
                
                # Signal gönder
                self.business_scraped.emit(self._business_to_dict(business))
                
            except Exception as e:
                error_count += 1
                logger.error(f"Veritabanı kayıt hatası: {e}")
                self.log_message.emit(f"Kayıt hatası: {business.isim} - {str(e)}")
        
        return saved_count, updated_count, error_count
    
    def stop_scraping(self):
        """Thread-safe scraping durdurma"""
        with QMutexLocker(self.mutex):
            self.should_stop = True
        
        if self.scraper:
            try:
                self.scraper.stop_scraping()
            except Exception as e:
                logger.error(f"Scraper durdurma hatası: {e}")
        
        self.log_message.emit("Durdurma sinyali gönderildi...")
        
        # Thread'in bitmesini bekle (maksimum 5 saniye)
        if self.isRunning():
            self.wait(5000)
    
    def _build_search_description(self) -> str:
        """Arama açıklaması oluştur"""
        parts = []
        
        if self.search_params.get('sektor'):
            parts.append(self.search_params['sektor'])
        
        if self.search_params.get('ilce'):
            parts.append(self.search_params['ilce'])
        
        if self.search_params.get('il'):
            parts.append(self.search_params['il'])
        
        query = " ".join(parts)
        limit = self.search_params.get('limit', 50)
        
        return f"{query} (Limit: {limit})"
    
    def _business_to_dict(self, business: Isletme) -> Dict:
        """İşletme objesini dict'e çevir"""
        return {
            'id': business.id,
            'google_id': business.google_id,
            'isim': business.isim,
            'kategori': business.kategori,
            'telefon': business.telefon,
            'adres': business.adres,
            'website': business.website,
            'calisma_saatleri': business.calisma_saatleri,
            'puan': business.puan,
            'yorum_sayisi': business.yorum_sayisi,
            'yogunluk_bilgisi': business.yogunluk_bilgisi,
            'konum_linki': business.konum_linki,
            'resim_url': business.resim_url,
            'il': business.il,
            'ilce': business.ilce,
            'durum': business.durum,
            'notlar': business.notlar,
            'source_url': business.source_url,
            'eklenme_tarihi': business.eklenme_tarihi.isoformat() if business.eklenme_tarihi else None,
            'updated_at': business.updated_at.isoformat() if business.updated_at else None
        }
    
    def _export_to_excel(self, businesses: List[Isletme]) -> str:
        """Excel'e export et"""
        try:
            exporter = ExcelExporter()
            
            # Dosya adı oluştur
            search_desc = self._build_search_description().replace(" ", "_").replace(":", "")
            filename = f"google_maps_scraping_{search_desc}"
            
            # Export
            excel_path = exporter.export_businesses(businesses, filename)
            return excel_path
            
        except Exception as e:
            logger.error(f"Excel export hatası: {e}")
            raise

class ScraperController(QObject):
    """Scraper controller sınıfı"""
    
    # Signals
    progress_updated = Signal(int)
    status_updated = Signal(str)
    log_message = Signal(str)
    business_scraped = Signal(dict)
    scraping_finished = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.worker_thread = None
        
    def start_scraping(self, config: Dict[str, Any], search_params: Dict[str, Any]):
        """Scraping başlat"""
        if self.is_running():
            self.error_occurred.emit("Scraping zaten çalışıyor")
            return
        
        # Worker oluştur
        self.worker = ScraperWorker()
        self.worker_thread = QThread()
        
        # Worker'ı thread'e taşı
        self.worker.moveToThread(self.worker_thread)
        
        # Signals bağla
        self._connect_signals()
        
        # Ayarları yap
        self.worker.setup_scraper(config)
        self.worker.set_search_params(**search_params)
        
        # Thread başlat
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()
        
    def stop_scraping(self):
        """Scraping durdur"""
        if self.worker:
            self.worker.stop_scraping()
    
    def is_running(self) -> bool:
        """Scraping çalışıyor mu?"""
        return self.worker_thread and self.worker_thread.isRunning()
    
    def _connect_signals(self):
        """Signal bağlantılarını yap"""
        # Worker signals -> Controller signals
        self.worker.progress_updated.connect(self.progress_updated.emit)
        self.worker.status_updated.connect(self.status_updated.emit)
        self.worker.log_message.connect(self.log_message.emit)
        self.worker.business_scraped.connect(self.business_scraped.emit)
        self.worker.scraping_finished.connect(self.scraping_finished.emit)
        self.worker.error_occurred.connect(self.error_occurred.emit)
        
        # Thread finished -> cleanup
        self.worker.finished.connect(self._cleanup_worker)
        self.worker_thread.finished.connect(self._cleanup_thread)
    
    def _cleanup_worker(self):
        """Thread-safe worker temizleme"""
        if self.worker:
            try:
                # Worker'ı durdur
                if self.worker.isRunning():
                    self.worker.stop_scraping()
                    self.worker.wait(3000)  # 3 saniye bekle
                
                # Worker'ı temizle
                self.worker.deleteLater()
                self.worker = None
                
            except Exception as e:
                logger.error(f"Worker cleanup hatası: {e}")
    
    def _cleanup_thread(self):
        """Thread-safe thread temizleme"""
        if self.worker_thread:
            try:
                # Thread'i durdur
                if self.worker_thread.isRunning():
                    self.worker_thread.quit()
                    if not self.worker_thread.wait(3000):  # 3 saniye bekle
                        self.worker_thread.terminate()
                        self.worker_thread.wait(1000)  # 1 saniye daha bekle
                
                # Thread'i temizle
                self.worker_thread.deleteLater()
                self.worker_thread = None
                
            except Exception as e:
                logger.error(f"Thread cleanup hatası: {e}")