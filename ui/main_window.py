"""
Main Window for Google Maps Scraper Application
"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                               QStackedWidget, QFrame, QLabel, QApplication)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, Signal
from PySide6.QtGui import QFont, QIcon
import os
import logging
from ui.sidebar import Sidebar
from ui.panels.scraper_panel import ScraperPanel
from ui.panels.users_panel import UsersPanel
from ui.panels.customers_panel import CustomersPanel
from ui.panels.settings_panel import SettingsPanel
from utils.toast import init_toast_manager
from utils.logger import get_ui_logger

logger = logging.getLogger(__name__)
ui_logger = get_ui_logger()

class MainWindow(QMainWindow):
    """Ana pencere sınıfı"""
    
    # Signals
    page_changed = Signal(str)  # Sayfa değişti
    
    def __init__(self):
        super().__init__()
        
        # Pencere ayarları
        self.setWindowTitle("Google Maps Scraper")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Ana widget ve layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Ana layout (horizontal)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # UI bileşenlerini oluştur
        self.setup_ui()
        
        # Toast manager'ı başlat
        init_toast_manager(self)
        
        # Stil yükle
        self.load_stylesheet()
        
        # İlk sayfayı göster
        self.show_scraper_panel()
        
        logger.info("Ana pencere oluşturuldu")
    
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        # Sidebar oluştur
        self.sidebar = Sidebar()
        self.sidebar.setFixedWidth(220)  # Açık genişlik
        self.sidebar.setObjectName("sidebar")
        
        # İçerik alanı oluştur
        self.content_frame = QFrame()
        self.content_frame.setObjectName("content_area")
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(0)
        
        # Stacked widget (sayfa değiştirici)
        self.stacked_widget = QStackedWidget()
        self.content_layout.addWidget(self.stacked_widget)
        
        # Panel'leri oluştur
        self.create_panels()
        
        # Layout'a ekle
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_frame, 1)  # Stretch factor 1
        
        # Sidebar sinyallerini bağla
        self.connect_sidebar_signals()
    
    def create_panels(self):
        """Panel'leri oluştur ve stacked widget'a ekle"""
        try:
            # Scraper Panel
            self.scraper_panel = ScraperPanel()
            self.stacked_widget.addWidget(self.scraper_panel)
            
            # Users Panel
            self.users_panel = UsersPanel()
            self.stacked_widget.addWidget(self.users_panel)
            
            # Customers Panel
            self.customers_panel = CustomersPanel()
            self.stacked_widget.addWidget(self.customers_panel)
            
            # Settings Panel
            self.settings_panel = SettingsPanel()
            self.stacked_widget.addWidget(self.settings_panel)
            
            logger.info("Tüm paneller oluşturuldu")
            
        except Exception as e:
            logger.error(f"Panel oluşturma hatası: {e}")
            # Hata durumunda basit label'lar oluştur
            self.create_fallback_panels()
    
    def create_fallback_panels(self):
        """Hata durumunda basit paneller oluştur"""
        panels = [
            ("Scraper", "Scraper Panel - Geliştiriliyor"),
            ("Kullanıcılar", "Kullanıcılar Panel - Geliştiriliyor"),
            ("Müşteriler", "Müşteriler Panel - Geliştiriliyor"),
            ("Ayarlar", "Ayarlar Panel - Geliştiriliyor")
        ]
        
        for title, text in panels:
            panel = QWidget()
            layout = QVBoxLayout(panel)
            
            title_label = QLabel(title)
            title_label.setObjectName("panel-title")
            title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
            
            content_label = QLabel(text)
            content_label.setFont(QFont("Segoe UI", 12))
            content_label.setAlignment(Qt.AlignCenter)
            
            layout.addWidget(title_label)
            layout.addWidget(content_label)
            layout.addStretch()
            
            self.stacked_widget.addWidget(panel)
    
    def connect_sidebar_signals(self):
        """Sidebar sinyallerini bağla"""
        self.sidebar.menu_item_clicked.connect(self.on_menu_item_clicked)
        self.sidebar.sidebar_toggled.connect(self.on_sidebar_toggled)
    
    def on_menu_item_clicked(self, item_name: str):
        """Menü öğesi tıklandığında"""
        ui_logger.user_action(f"Menü tıklandı: {item_name}")
        
        # Sayfa değiştir
        if item_name == "Scraper":
            self.show_scraper_panel()
        elif item_name == "Kullanıcılar":
            self.show_users_panel()
        elif item_name == "Müşteriler":
            self.show_customers_panel()
        elif item_name == "Ayarlar":
            self.show_settings_panel()
        
        # Signal emit et
        self.page_changed.emit(item_name)
    
    def on_sidebar_toggled(self, is_collapsed: bool):
        """Sidebar toggle edildiğinde"""
        ui_logger.user_action(f"Sidebar {'kapatıldı' if is_collapsed else 'açıldı'}")
        
        # İçerik alanının margin'ini ayarla
        if is_collapsed:
            self.content_layout.setContentsMargins(15, 20, 20, 20)
        else:
            self.content_layout.setContentsMargins(20, 20, 20, 20)
    
    def show_scraper_panel(self):
        """Scraper panelini göster"""
        self.stacked_widget.setCurrentIndex(0)
        self.sidebar.set_active_item("Scraper")
        ui_logger.navigation("", "Scraper")
    
    def show_users_panel(self):
        """Kullanıcılar panelini göster"""
        self.stacked_widget.setCurrentIndex(1)
        self.sidebar.set_active_item("Kullanıcılar")
        ui_logger.navigation("", "Kullanıcılar")
        
        # Panel'i yenile
        if hasattr(self, 'users_panel') and hasattr(self.users_panel, 'refresh_data'):
            self.users_panel.refresh_data()
    
    def show_customers_panel(self):
        """Müşteriler panelini göster"""
        self.stacked_widget.setCurrentIndex(2)
        self.sidebar.set_active_item("Müşteriler")
        ui_logger.navigation("", "Müşteriler")
        
        # Panel'i yenile
        if hasattr(self, 'customers_panel') and hasattr(self.customers_panel, 'refresh_data'):
            self.customers_panel.refresh_data()
    
    def show_settings_panel(self):
        """Ayarlar panelini göster"""
        self.stacked_widget.setCurrentIndex(3)
        self.sidebar.set_active_item("Ayarlar")
        ui_logger.navigation("", "Ayarlar")
    
    def load_stylesheet(self):
        """QSS stil dosyasını yükle"""
        try:
            # Premium dark theme'i dene
            premium_style_path = os.path.join(os.path.dirname(__file__), "styles", "premium_dark_theme.qss")
            
            if os.path.exists(premium_style_path):
                with open(premium_style_path, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
                self.setStyleSheet(stylesheet)
                logger.info("Premium dark theme yüklendi")
                return
            
            # Fallback: Normal dark theme
            style_path = os.path.join(os.path.dirname(__file__), "styles", "dark_theme.qss")
            
            if os.path.exists(style_path):
                with open(style_path, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
                self.setStyleSheet(stylesheet)
                logger.info("Dark theme yüklendi")
            else:
                logger.warning(f"Stil dosyası bulunamadı: {style_path}")
                
        except Exception as e:
            logger.error(f"Stil yükleme hatası: {e}")
    
    def get_current_panel_name(self) -> str:
        """Aktif panel adını al"""
        current_index = self.stacked_widget.currentIndex()
        panel_names = ["Scraper", "Kullanıcılar", "Müşteriler", "Ayarlar"]
        
        if 0 <= current_index < len(panel_names):
            return panel_names[current_index]
        return "Bilinmeyen"
    
    def toggle_sidebar(self):
        """Sidebar'ı aç/kapat"""
        self.sidebar.toggle_sidebar()
    
    def show_status_message(self, message: str, timeout: int = 3000):
        """Status bar'da mesaj göster"""
        if hasattr(self, 'statusBar'):
            self.statusBar().showMessage(message, timeout)
    
    def closeEvent(self, event):
        """Pencere kapatılırken"""
        ui_logger.user_action("Uygulama kapatılıyor")
        
        # Aktif işlemleri durdur
        try:
            if hasattr(self, 'scraper_panel') and hasattr(self.scraper_panel, 'stop_scraping'):
                self.scraper_panel.stop_scraping()
        except Exception as e:
            logger.error(f"Scraper durdurma hatası: {e}")
        
        # Ayarları kaydet
        try:
            if hasattr(self, 'settings_panel') and hasattr(self.settings_panel, 'save_settings'):
                self.settings_panel.save_settings()
        except Exception as e:
            logger.error(f"Ayar kaydetme hatası: {e}")
        
        logger.info("Ana pencere kapatıldı")
        event.accept()
    
    def resizeEvent(self, event):
        """Pencere boyutu değiştiğinde"""
        super().resizeEvent(event)
        
        # Toast pozisyonlarını güncelle (gerekirse)
        # Bu otomatik olarak toast manager tarafından yapılır
    
    def keyPressEvent(self, event):
        """Klavye tuşu basıldığında"""
        # Ctrl+1,2,3,4 ile hızlı panel değiştirme
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_1:
                self.show_scraper_panel()
            elif event.key() == Qt.Key_2:
                self.show_users_panel()
            elif event.key() == Qt.Key_3:
                self.show_customers_panel()
            elif event.key() == Qt.Key_4:
                self.show_settings_panel()
            elif event.key() == Qt.Key_B:  # Ctrl+B ile sidebar toggle
                self.toggle_sidebar()
        
        super().keyPressEvent(event)
    
    def get_scraper_panel(self):
        """Scraper panelini al"""
        return getattr(self, 'scraper_panel', None)
    
    def get_users_panel(self):
        """Users panelini al"""
        return getattr(self, 'users_panel', None)
    
    def get_customers_panel(self):
        """Customers panelini al"""
        return getattr(self, 'customers_panel', None)
    
    def get_settings_panel(self):
        """Settings panelini al"""
        return getattr(self, 'settings_panel', None)