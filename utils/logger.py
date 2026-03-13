"""
Logging System for Google Maps Scraper
"""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional
from PySide6.QtCore import QObject, Signal

class QtLogHandler(logging.Handler, QObject):
    """Qt Signal tabanlı log handler"""
    
    # Signals
    log_message = Signal(str, str)  # message, level
    
    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        
        # Formatter ayarla
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.setFormatter(formatter)
    
    def emit(self, record):
        """Log kaydını emit et"""
        try:
            message = self.format(record)
            level = record.levelname
            self.log_message.emit(message, level)
        except Exception:
            self.handleError(record)

class LogManager:
    """Log yönetici sınıfı"""
    
    def __init__(self, app_name: str = "GoogleMapsScraper", log_dir: str = "logs"):
        """
        Log manager oluştur
        
        Args:
            app_name: Uygulama adı
            log_dir: Log klasörü
        """
        self.app_name = app_name
        self.log_dir = log_dir
        self.qt_handler: Optional[QtLogHandler] = None
        
        # Log klasörünü oluştur
        self._ensure_log_dir()
        
        # Logger'ı ayarla
        self.setup_logging()
    
    def _ensure_log_dir(self):
        """Log klasörünü oluştur"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def setup_logging(self):
        """Logging sistemini ayarla"""
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Mevcut handler'ları temizle
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # File handler (rotating)
        log_file = os.path.join(self.log_dir, f"{self.app_name.lower()}.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Error file handler
        error_log_file = os.path.join(self.log_dir, f"{self.app_name.lower()}_errors.log")
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
        
        # Qt handler (GUI için)
        self.qt_handler = QtLogHandler()
        self.qt_handler.setLevel(logging.INFO)
        root_logger.addHandler(self.qt_handler)
        
        # İlk log mesajı
        logging.info(f"{self.app_name} logging sistemi başlatıldı")
    
    def get_qt_handler(self) -> Optional[QtLogHandler]:
        """Qt handler'ı al"""
        return self.qt_handler
    
    def set_log_level(self, level: str):
        """Log seviyesini ayarla"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        log_level = level_map.get(level.upper(), logging.INFO)
        
        # Root logger seviyesini ayarla
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Console handler seviyesini ayarla
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
                handler.setLevel(log_level)
        
        logging.info(f"Log seviyesi {level.upper()} olarak ayarlandı")
    
    def get_log_files(self) -> list:
        """Log dosyalarını listele"""
        log_files = []
        
        if os.path.exists(self.log_dir):
            for file in os.listdir(self.log_dir):
                if file.endswith('.log'):
                    file_path = os.path.join(self.log_dir, file)
                    file_size = os.path.getsize(file_path)
                    file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    log_files.append({
                        'name': file,
                        'path': file_path,
                        'size': file_size,
                        'modified': file_modified
                    })
        
        return sorted(log_files, key=lambda x: x['modified'], reverse=True)
    
    def clear_logs(self):
        """Log dosyalarını temizle"""
        try:
            if os.path.exists(self.log_dir):
                for file in os.listdir(self.log_dir):
                    if file.endswith('.log'):
                        file_path = os.path.join(self.log_dir, file)
                        os.remove(file_path)
            
            logging.info("Log dosyaları temizlendi")
            return True
            
        except Exception as e:
            logging.error(f"Log temizleme hatası: {e}")
            return False
    
    def get_recent_logs(self, lines: int = 100) -> list:
        """Son log kayıtlarını al"""
        logs = []
        
        try:
            log_file = os.path.join(self.log_dir, f"{self.app_name.lower()}.log")
            
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    
                    for line in recent_lines:
                        line = line.strip()
                        if line:
                            logs.append(line)
            
        except Exception as e:
            logging.error(f"Log okuma hatası: {e}")
        
        return logs

class ScraperLogger:
    """Scraper özel logger sınıfı"""
    
    def __init__(self, name: str = "scraper"):
        self.logger = logging.getLogger(name)
    
    def scraping_started(self, query: str, limit: int):
        """Scraping başladı"""
        self.logger.info(f"Scraping başlatıldı: {query} (Limit: {limit})")
    
    def scraping_finished(self, stats: dict):
        """Scraping tamamlandı"""
        message = (
            f"Scraping tamamlandı - "
            f"Bulunan: {stats.get('total_found', 0)}, "
            f"Yeni: {stats.get('saved_count', 0)}, "
            f"Güncellenen: {stats.get('updated_count', 0)}, "
            f"Hata: {stats.get('error_count', 0)}"
        )
        self.logger.info(message)
    
    def business_scraped(self, business_name: str, index: int, total: int):
        """İşletme çekildi"""
        self.logger.debug(f"İşletme çekildi ({index}/{total}): {business_name}")
    
    def scraping_error(self, error: str, context: str = ""):
        """Scraping hatası"""
        message = f"Scraping hatası: {error}"
        if context:
            message += f" - Bağlam: {context}"
        self.logger.error(message)
    
    def database_operation(self, operation: str, success: bool, details: str = ""):
        """Veritabanı işlemi"""
        level = logging.INFO if success else logging.ERROR
        status = "başarılı" if success else "başarısız"
        message = f"Veritabanı {operation} {status}"
        if details:
            message += f" - {details}"
        self.logger.log(level, message)
    
    def export_operation(self, export_type: str, file_path: str, success: bool):
        """Export işlemi"""
        if success:
            self.logger.info(f"{export_type} export başarılı: {file_path}")
        else:
            self.logger.error(f"{export_type} export başarısız: {file_path}")

class UILogger:
    """UI özel logger sınıfı"""
    
    def __init__(self, name: str = "ui"):
        self.logger = logging.getLogger(name)
    
    def user_action(self, action: str, details: str = ""):
        """Kullanıcı eylemi"""
        message = f"Kullanıcı eylemi: {action}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
    
    def ui_error(self, error: str, component: str = ""):
        """UI hatası"""
        message = f"UI hatası: {error}"
        if component:
            message += f" - Bileşen: {component}"
        self.logger.error(message)
    
    def navigation(self, from_page: str, to_page: str):
        """Sayfa navigasyonu"""
        self.logger.debug(f"Navigasyon: {from_page} -> {to_page}")
    
    def data_operation(self, operation: str, table: str, success: bool):
        """Veri işlemi"""
        status = "başarılı" if success else "başarısız"
        self.logger.info(f"Veri {operation} {status} - Tablo: {table}")

# Global log manager instance
_log_manager: Optional[LogManager] = None

def init_logging(app_name: str = "GoogleMapsScraper", log_dir: str = "logs") -> LogManager:
    """Global logging sistemini başlat"""
    global _log_manager
    _log_manager = LogManager(app_name, log_dir)
    return _log_manager

def get_log_manager() -> Optional[LogManager]:
    """Global log manager'ı al"""
    return _log_manager

def get_scraper_logger() -> ScraperLogger:
    """Scraper logger al"""
    return ScraperLogger()

def get_ui_logger() -> UILogger:
    """UI logger al"""
    return UILogger()