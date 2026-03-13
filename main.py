#!/usr/bin/env python3
"""
Google Maps Scraper - Ana Uygulama
Profesyonel masaüstü uygulaması - PySide6 tabanlı

Bu uygulama Google Maps üzerindeki işletmeleri scrape eder,
MySQL veritabanına kaydeder ve Excel'e aktarır.

Özellikler:
- Google Maps Selenium scraping
- MySQL veritabanı entegrasyonu
- Excel export
- Modern dark theme UI
- Animasyonlu sidebar
- Toast bildirimler
- Kapsamlı log sistemi
"""

import sys
import os
import logging
from pathlib import Path

# PySide6 imports
from PySide6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont, QPainter, QColor

# Uygulama modülleri
from ui.main_window import MainWindow
from utils.logger import init_logging, get_log_manager
from utils.config import init_config, get_config
from utils.toast import show_error, show_success, show_info
from database.connection import db

# Uygulama bilgileri
APP_NAME = "Google Maps Scraper"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Metehan"
APP_DESCRIPTION = "Profesyonel Google Maps İşletme Scraper Uygulaması"

class GoogleMapsScraperApp:
    """Ana uygulama sınıfı"""
    
    def __init__(self):
        """Uygulamayı başlat"""
        self.app = None
        self.main_window = None
        self.splash = None
        
        # Logging başlat
        self.setup_logging()
        
        # Logger al
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"{APP_NAME} v{APP_VERSION} başlatılıyor...")
    
    def setup_logging(self):
        """Logging sistemini ayarla"""
        try:
            # Log klasörünü oluştur
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # Logging başlat
            init_logging(APP_NAME, str(log_dir))
            
        except Exception as e:
            print(f"Logging başlatma hatası: {e}")
    
    def setup_config(self):
        """Konfigürasyonu ayarla"""
        try:
            # Config başlat
            config = init_config("config.json")
            
            if config:
                self.logger.info("Konfigürasyon yüklendi")
                return True
            else:
                self.logger.error("Konfigürasyon yüklenemedi")
                return False
                
        except Exception as e:
            self.logger.error(f"Konfigürasyon hatası: {e}")
            return False
    
    def setup_database(self):
        """Veritabanını ayarla"""
        try:
            # Veritabanı bağlantısını test et
            if db.test_connection():
                self.logger.info("Veritabanı bağlantısı başarılı")
                
                # Şemayı oluştur (gerekirse)
                try:
                    db.create_database_schema()
                    self.logger.info("Veritabanı şeması kontrol edildi")
                except Exception as e:
                    self.logger.warning(f"Şema oluşturma uyarısı: {e}")
                
                return True
            else:
                self.logger.error("Veritabanı bağlantısı başarısız")
                return False
                
        except Exception as e:
            self.logger.error(f"Veritabanı ayarlama hatası: {e}")
            return False
    
    def create_splash_screen(self):
        """Splash screen oluştur"""
        try:
            # Basit splash screen oluştur
            pixmap = QPixmap(400, 300)
            pixmap.fill(QColor("#1e1e1e"))
            
            painter = QPainter(pixmap)
            painter.setPen(QColor("#0078d4"))
            painter.setFont(QFont("Segoe UI", 24, QFont.Bold))
            
            # Başlık
            painter.drawText(pixmap.rect(), Qt.AlignCenter, APP_NAME)
            
            # Versiyon
            painter.setFont(QFont("Segoe UI", 12))
            painter.setPen(QColor("#cccccc"))
            version_rect = pixmap.rect()
            version_rect.setTop(version_rect.center().y() + 30)
            painter.drawText(version_rect, Qt.AlignCenter, f"v{APP_VERSION}")
            
            # Yükleniyor
            loading_rect = pixmap.rect()
            loading_rect.setTop(loading_rect.bottom() - 50)
            painter.drawText(loading_rect, Qt.AlignCenter, "Yükleniyor...")
            
            painter.end()
            
            # Splash screen oluştur
            self.splash = QSplashScreen(pixmap)
            self.splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            self.splash.show()
            
            # Mesaj göster
            self.splash.showMessage(
                "Uygulama başlatılıyor...",
                Qt.AlignBottom | Qt.AlignCenter,
                QColor("#0078d4")
            )
            
            # Uygulamanın işlemesi için
            self.app.processEvents()
            
        except Exception as e:
            self.logger.error(f"Splash screen hatası: {e}")
    
    def update_splash_message(self, message: str):
        """Splash screen mesajını güncelle"""
        if self.splash:
            self.splash.showMessage(
                message,
                Qt.AlignBottom | Qt.AlignCenter,
                QColor("#0078d4")
            )
            self.app.processEvents()
    
    def close_splash_screen(self):
        """Splash screen'i kapat"""
        if self.splash:
            self.splash.close()
            self.splash = None
    
    def create_main_window(self):
        """Ana pencereyi oluştur"""
        try:
            self.main_window = MainWindow()
            
            # Pencere ayarları
            config = get_config()
            if config:
                width = config.get("ui.window_width", 1200)
                height = config.get("ui.window_height", 800)
                self.main_window.resize(width, height)
            
            self.logger.info("Ana pencere oluşturuldu")
            return True
            
        except Exception as e:
            self.logger.error(f"Ana pencere oluşturma hatası: {e}")
            return False
    
    def show_error_dialog(self, title: str, message: str):
        """Hata dialog'u göster"""
        try:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
        except Exception as e:
            print(f"Error dialog hatası: {e}")
    
    def run(self):
        """Uygulamayı çalıştır"""
        try:
            # QApplication oluştur
            self.app = QApplication(sys.argv)
            self.app.setApplicationName(APP_NAME)
            self.app.setApplicationVersion(APP_VERSION)
            self.app.setOrganizationName(APP_AUTHOR)
            
            # Uygulama ikonunu ayarla (varsa)
            # self.app.setWindowIcon(QIcon("assets/icons/app_icon.png"))
            
            # Splash screen göster
            self.create_splash_screen()
            
            # Konfigürasyonu ayarla
            self.update_splash_message("Konfigürasyon yükleniyor...")
            if not self.setup_config():
                self.close_splash_screen()
                self.show_error_dialog(
                    "Konfigürasyon Hatası",
                    "Uygulama konfigürasyonu yüklenemedi.\n"
                    "Lütfen config.json dosyasını kontrol edin."
                )
                return 1
            
            # Veritabanını ayarla
            self.update_splash_message("Veritabanı bağlantısı kuruluyor...")
            if not self.setup_database():
                self.close_splash_screen()
                self.show_error_dialog(
                    "Veritabanı Hatası",
                    "Veritabanı bağlantısı kurulamadı.\n"
                    "MySQL ayarlarını kontrol edin."
                )
                return 1
            
            # Ana pencereyi oluştur
            self.update_splash_message("Arayüz yükleniyor...")
            if not self.create_main_window():
                self.close_splash_screen()
                self.show_error_dialog(
                    "UI Hatası",
                    "Ana pencere oluşturulamadı."
                )
                return 1
            
            # Splash screen'i kapat ve ana pencereyi göster
            QTimer.singleShot(1000, self.show_main_window)
            
            # Uygulama döngüsünü başlat
            self.logger.info(f"{APP_NAME} başarıyla başlatıldı")
            return self.app.exec()
            
        except Exception as e:
            self.logger.error(f"Uygulama çalıştırma hatası: {e}")
            
            if self.splash:
                self.close_splash_screen()
            
            self.show_error_dialog(
                "Kritik Hata",
                f"Uygulama başlatılamadı:\n{str(e)}"
            )
            return 1
    
    def show_main_window(self):
        """Ana pencereyi göster"""
        try:
            self.close_splash_screen()
            
            if self.main_window:
                self.main_window.show()
                self.main_window.raise_()
                self.main_window.activateWindow()
                
                # Hoş geldin mesajı
                QTimer.singleShot(500, lambda: show_success(
                    f"{APP_NAME} v{APP_VERSION} başarıyla yüklendi!"
                ))
                
        except Exception as e:
            self.logger.error(f"Ana pencere gösterme hatası: {e}")

def check_dependencies():
    """Gerekli bağımlılıkları kontrol et"""
    missing_deps = []
    
    try:
        import PySide6
    except ImportError:
        missing_deps.append("PySide6")
    
    try:
        import selenium
    except ImportError:
        missing_deps.append("selenium")
    
    try:
        import mysql.connector
    except ImportError:
        missing_deps.append("mysql-connector-python")
    
    try:
        import openpyxl
    except ImportError:
        missing_deps.append("openpyxl")
    
    if missing_deps:
        print("[-] Eksik bağımlılıklar:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n[*] Yüklemek için:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def check_system_requirements():
    """Sistem gereksinimlerini kontrol et"""
    import platform
    
    print(f"[*] Sistem: {platform.system()} {platform.release()}")
    print(f"[*] Python: {platform.python_version()}")
    
    # Python versiyonu kontrolü
    if sys.version_info < (3, 8):
        print("[-] Python 3.8 veya üzeri gerekli!")
        return False
    
    return True

def main():
    """Ana fonksiyon"""
    print(f"[*] {APP_NAME} v{APP_VERSION}")
    print(f"[*] {APP_DESCRIPTION}")
    print("=" * 50)
    
    # Sistem gereksinimlerini kontrol et
    if not check_system_requirements():
        return 1
    
    # Bağımlılıkları kontrol et
    if not check_dependencies():
        return 1
    
    print("[+] Tüm gereksinimler karşılandı")
    print("[*] Uygulama başlatılıyor...\n")
    
    # Uygulamayı başlat
    app = GoogleMapsScraperApp()
    return app.run()

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n[!] Uygulama kullanıcı tarafından durduruldu")
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] Kritik hata: {e}")
        sys.exit(1)