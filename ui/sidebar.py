"""
Animated Sidebar Component for Google Maps Scraper
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFrame, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont, QIcon
import logging

logger = logging.getLogger(__name__)

class SidebarItem(QPushButton):
    """Sidebar menü öğesi"""
    
    def __init__(self, text: str, icon_text: str = "", parent=None):
        super().__init__(parent)
        
        self.text = text
        self.icon_text = icon_text
        self.is_active = False
        
        # Layout oluştur
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 12, 15, 12)
        self.layout.setSpacing(12)
        
        # İkon label
        self.icon_label = QLabel(icon_text)
        self.icon_label.setFont(QFont("Segoe UI", 14))
        self.icon_label.setFixedSize(20, 20)
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        # Text label
        self.text_label = QLabel(text)
        self.text_label.setFont(QFont("Segoe UI", 11))
        
        # Layout'a ekle
        self.layout.addWidget(self.icon_label)
        self.layout.addWidget(self.text_label, 1)
        
        # Stil sınıfı
        self.setObjectName("sidebar_item")
        self.setProperty("class", "sidebar-item")
        
        # Cursor
        self.setCursor(Qt.PointingHandCursor)
    
    def set_active(self, active: bool):
        """Aktif durumu ayarla"""
        self.is_active = active
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
    
    def set_collapsed(self, collapsed: bool):
        """Collapsed durumunu ayarla"""
        if collapsed:
            self.text_label.hide()
            self.layout.setContentsMargins(15, 12, 15, 12)
        else:
            self.text_label.show()
            self.layout.setContentsMargins(15, 12, 15, 12)
    
    def get_text(self) -> str:
        """Text'i al"""
        return self.text

class Sidebar(QWidget):
    """Animasyonlu sidebar bileşeni"""
    
    # Signals
    menu_item_clicked = Signal(str)  # Menü öğesi tıklandı
    sidebar_toggled = Signal(bool)   # Sidebar toggle edildi (collapsed state)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Boyut ayarları
        self.expanded_width = 220
        self.collapsed_width = 60
        self.is_collapsed = False
        
        # Ana layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # UI oluştur
        self.setup_ui()
        
        # Animasyon ayarla
        self.setup_animation()
        
        # İlk menü öğesini aktif yap
        self.set_active_item("Scraper")
        
        logger.info("Sidebar oluşturuldu")
    
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        # Header
        self.create_header()
        
        # Menu items
        self.create_menu_items()
        
        # Spacer
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.main_layout.addItem(spacer)
        
        # Footer
        self.create_footer()
    
    def create_header(self):
        """Header bölümünü oluştur"""
        self.header_frame = QFrame()
        self.header_frame.setObjectName("sidebar_header")
        self.header_frame.setFixedHeight(70)
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(15, 15, 15, 15)
        
        # Hamburger button
        self.hamburger_button = QPushButton("☰")
        self.hamburger_button.setObjectName("hamburger_button")
        self.hamburger_button.setFixedSize(30, 30)
        self.hamburger_button.setFont(QFont("Segoe UI", 16))
        self.hamburger_button.setCursor(Qt.PointingHandCursor)
        self.hamburger_button.clicked.connect(self.toggle_sidebar)
        
        # Logo/Title
        self.logo_label = QLabel("GMS")
        self.logo_label.setObjectName("sidebar_logo")
        self.logo_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        
        header_layout.addWidget(self.hamburger_button)
        header_layout.addWidget(self.logo_label, 1)
        
        self.main_layout.addWidget(self.header_frame)
    
    def create_menu_items(self):
        """Menü öğelerini oluştur"""
        self.menu_frame = QFrame()
        self.menu_frame.setObjectName("sidebar_menu")
        
        self.menu_layout = QVBoxLayout(self.menu_frame)
        self.menu_layout.setContentsMargins(0, 10, 0, 10)
        self.menu_layout.setSpacing(2)
        
        # Menü öğeleri
        menu_items = [
            ("Scraper", "🔍"),
            ("Kullanıcılar", "👥"),
            ("Müşteriler", "💼"),
            ("Ayarlar", "⚙️")
        ]
        
        self.menu_items = []
        
        for text, icon in menu_items:
            item = SidebarItem(text, icon)
            item.clicked.connect(lambda checked, t=text: self.on_menu_item_clicked(t))
            
            self.menu_items.append(item)
            self.menu_layout.addWidget(item)
        
        self.main_layout.addWidget(self.menu_frame)
    
    def create_footer(self):
        """Footer bölümünü oluştur"""
        self.footer_frame = QFrame()
        self.footer_frame.setObjectName("sidebar_footer")
        self.footer_frame.setFixedHeight(60)
        
        footer_layout = QVBoxLayout(self.footer_frame)
        footer_layout.setContentsMargins(15, 10, 15, 10)
        footer_layout.setSpacing(5)
        
        # Version label
        self.version_label = QLabel("v1.0.0")
        self.version_label.setFont(QFont("Segoe UI", 8))
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setStyleSheet("color: #808080;")
        
        # Theme toggle button (küçük)
        self.theme_button = QPushButton("🌙")
        self.theme_button.setFixedSize(25, 25)
        self.theme_button.setFont(QFont("Segoe UI", 12))
        self.theme_button.setCursor(Qt.PointingHandCursor)
        self.theme_button.setToolTip("Tema Değiştir")
        
        footer_layout.addWidget(self.version_label)
        footer_layout.addWidget(self.theme_button, 0, Qt.AlignCenter)
        
        self.main_layout.addWidget(self.footer_frame)
    
    def setup_animation(self):
        """Animasyonu ayarla"""
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Maximum width animasyonu
        self.max_width_animation = QPropertyAnimation(self, b"maximumWidth")
        self.max_width_animation.setDuration(300)
        self.max_width_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def toggle_sidebar(self):
        """Sidebar'ı aç/kapat"""
        if self.is_collapsed:
            self.expand_sidebar()
        else:
            self.collapse_sidebar()
    
    def collapse_sidebar(self):
        """Sidebar'ı kapat"""
        if self.is_collapsed:
            return
        
        self.is_collapsed = True
        
        # Animasyon ayarla
        self.animation.setStartValue(self.expanded_width)
        self.animation.setEndValue(self.collapsed_width)
        
        self.max_width_animation.setStartValue(self.expanded_width)
        self.max_width_animation.setEndValue(self.collapsed_width)
        
        # Animasyonu başlat
        self.animation.start()
        self.max_width_animation.start()
        
        # Text'leri gizle (animasyon bitince)
        QTimer.singleShot(150, self.hide_texts)
        
        # Logo'yu kısalt
        self.logo_label.setText("G")
        
        # Signal emit et
        self.sidebar_toggled.emit(True)
        
        logger.debug("Sidebar kapatıldı")
    
    def expand_sidebar(self):
        """Sidebar'ı aç"""
        if not self.is_collapsed:
            return
        
        self.is_collapsed = False
        
        # Text'leri göster (animasyon başlamadan önce)
        self.show_texts()
        
        # Animasyon ayarla
        self.animation.setStartValue(self.collapsed_width)
        self.animation.setEndValue(self.expanded_width)
        
        self.max_width_animation.setStartValue(self.collapsed_width)
        self.max_width_animation.setEndValue(self.expanded_width)
        
        # Animasyonu başlat
        self.animation.start()
        self.max_width_animation.start()
        
        # Logo'yu genişlet
        self.logo_label.setText("GMS")
        
        # Signal emit et
        self.sidebar_toggled.emit(False)
        
        logger.debug("Sidebar açıldı")
    
    def hide_texts(self):
        """Text'leri gizle"""
        for item in self.menu_items:
            item.set_collapsed(True)
        
        self.version_label.hide()
    
    def show_texts(self):
        """Text'leri göster"""
        for item in self.menu_items:
            item.set_collapsed(False)
        
        self.version_label.show()
    
    def on_menu_item_clicked(self, item_text: str):
        """Menü öğesi tıklandığında"""
        logger.debug(f"Menü öğesi tıklandı: {item_text}")
        
        # Aktif öğeyi ayarla
        self.set_active_item(item_text)
        
        # Signal emit et
        self.menu_item_clicked.emit(item_text)
    
    def set_active_item(self, item_text: str):
        """Aktif menü öğesini ayarla"""
        for item in self.menu_items:
            item.set_active(item.get_text() == item_text)
    
    def get_active_item(self) -> str:
        """Aktif menü öğesini al"""
        for item in self.menu_items:
            if item.is_active:
                return item.get_text()
        return ""
    
    def set_collapsed_state(self, collapsed: bool):
        """Collapsed durumunu programatik olarak ayarla"""
        if collapsed != self.is_collapsed:
            self.toggle_sidebar()
    
    def get_collapsed_state(self) -> bool:
        """Collapsed durumunu al"""
        return self.is_collapsed
    
    def add_menu_item(self, text: str, icon: str = "", index: int = -1):
        """Yeni menü öğesi ekle"""
        item = SidebarItem(text, icon)
        item.clicked.connect(lambda checked, t=text: self.on_menu_item_clicked(t))
        
        if index == -1:
            self.menu_items.append(item)
            self.menu_layout.addWidget(item)
        else:
            self.menu_items.insert(index, item)
            self.menu_layout.insertWidget(index, item)
        
        # Collapsed durumunu ayarla
        if self.is_collapsed:
            item.set_collapsed(True)
    
    def remove_menu_item(self, text: str):
        """Menü öğesini kaldır"""
        for i, item in enumerate(self.menu_items):
            if item.get_text() == text:
                self.menu_layout.removeWidget(item)
                self.menu_items.pop(i)
                item.deleteLater()
                break
    
    def update_menu_item_icon(self, text: str, new_icon: str):
        """Menü öğesi ikonunu güncelle"""
        for item in self.menu_items:
            if item.get_text() == text:
                item.icon_label.setText(new_icon)
                break
    
    def set_theme_button_callback(self, callback):
        """Tema butonu callback'ini ayarla"""
        self.theme_button.clicked.connect(callback)
    
    def update_theme_button(self, is_dark: bool):
        """Tema butonunu güncelle"""
        self.theme_button.setText("🌙" if not is_dark else "☀️")
        self.theme_button.setToolTip("Light Tema" if is_dark else "Dark Tema")