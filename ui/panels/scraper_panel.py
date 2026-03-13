"""
Scraper Panel for Google Maps Scraper Application
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QPushButton, QComboBox, QLineEdit, QSpinBox,
                               QProgressBar, QTextEdit, QGroupBox, QCheckBox,
                               QFrame, QSplitter, QScrollArea)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
import logging
from scraper.scraper_worker import ScraperController
from utils.toast import show_success, show_error, show_info, show_warning
from utils.logger import get_scraper_logger
from utils.config import get_setting
from utils.constants import (
    DEFAULT_SCRAPER_LIMIT, MIN_SCRAPER_LIMIT, MAX_SCRAPER_LIMIT,
    DEFAULT_DELAY_MIN, DEFAULT_DELAY_MAX, MIN_DELAY, MAX_DELAY,
    MIN_SECTOR_LENGTH, MAX_SECTOR_LENGTH, SECTOR_PATTERN,
    MAX_PROXY_FILE_SIZE, TURKISH_CITIES, CITY_DISTRICTS,
    ERROR_MESSAGES, SUCCESS_MESSAGES, INFO_MESSAGES
)

logger = logging.getLogger(__name__)
scraper_logger = get_scraper_logger()

class ScraperPanel(QWidget):
    """Scraper panel sınıfı"""
    
    # Signals
    scraping_started = Signal()
    scraping_finished = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Scraper controller
        self.scraper_controller = ScraperController()
        
        # İstatistikler
        self.stats = {
            'total_found': 0,
            'saved_count': 0,
            'updated_count': 0,
            'error_count': 0
        }
        
        # UI oluştur
        self.setup_ui()
        
        # Sinyalleri bağla
        self.connect_signals()
        
        # İl-ilçe verilerini yükle
        self.load_location_data()
        
        logger.info("Scraper panel oluşturuldu")
    
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        # Ana layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)
        
        # Başlık
        title_label = QLabel("Google Maps Scraper")
        title_label.setObjectName("panel-title")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        main_layout.addWidget(title_label)
        
        # Splitter (üst: ayarlar, alt: log)
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)
        
        # Üst bölüm (ayarlar ve kontroller)
        top_widget = QWidget()
        self.setup_top_section(top_widget)
        splitter.addWidget(top_widget)
        
        # Alt bölüm (log ve progress)
        bottom_widget = QWidget()
        self.setup_bottom_section(bottom_widget)
        splitter.addWidget(bottom_widget)
        
        # Splitter oranları
        splitter.setSizes([400, 300])
    
    def setup_top_section(self, parent):
        """Üst bölümü oluştur (ayarlar)"""
        layout = QHBoxLayout(parent)
        layout.setSpacing(20)
        
        # Sol taraf - Arama ayarları
        left_group = QGroupBox("Arama Ayarları")
        left_layout = QGridLayout(left_group)
        left_layout.setSpacing(10)
        
        # İl seçimi
        left_layout.addWidget(QLabel("İl:"), 0, 0)
        self.il_combo = QComboBox()
        self.il_combo.setMinimumWidth(150)
        left_layout.addWidget(self.il_combo, 0, 1)
        
        # İlçe seçimi
        left_layout.addWidget(QLabel("İlçe:"), 1, 0)
        self.ilce_combo = QComboBox()
        self.ilce_combo.setMinimumWidth(150)
        left_layout.addWidget(self.ilce_combo, 1, 1)
        
        # Sektör
        left_layout.addWidget(QLabel("Sektör:"), 2, 0)
        self.sektor_input = QLineEdit()
        self.sektor_input.setPlaceholderText("örn: berber, kafe, oto galerici")
        left_layout.addWidget(self.sektor_input, 2, 1)
        
        # Limit
        left_layout.addWidget(QLabel("Limit:"), 3, 0)
        self.limit_spinbox = QSpinBox()
        self.limit_spinbox.setRange(MIN_SCRAPER_LIMIT, MAX_SCRAPER_LIMIT)
        self.limit_spinbox.setValue(DEFAULT_SCRAPER_LIMIT)
        left_layout.addWidget(self.limit_spinbox, 3, 1)
        
        layout.addWidget(left_group)
        
        # Orta - Kontrol butonları ve istatistikler
        middle_layout = QVBoxLayout()
        
        # Kontrol butonları
        control_group = QGroupBox("Kontrol")
        control_layout = QVBoxLayout(control_group)
        
        self.start_button = QPushButton("🔍 Scraping Başlat")
        self.start_button.setMinimumHeight(40)
        self.start_button.setProperty("class", "success")
        control_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("⏹️ Durdur")
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setProperty("class", "danger")
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Hazır")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #cccccc; font-size: 11pt;")
        control_layout.addWidget(self.status_label)
        
        middle_layout.addWidget(control_group)
        
        # İstatistikler
        stats_group = QGroupBox("İstatistikler")
        stats_layout = QGridLayout(stats_group)
        
        # İstatistik label'ları
        self.stats_labels = {}
        stats_items = [
            ("Bulunan", "total_found"),
            ("Yeni", "saved_count"),
            ("Güncellenen", "updated_count"),
            ("Hata", "error_count")
        ]
        
        for i, (label, key) in enumerate(stats_items):
            stats_layout.addWidget(QLabel(f"{label}:"), i, 0)
            value_label = QLabel("0")
            value_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
            value_label.setStyleSheet("color: #0078d4;")
            self.stats_labels[key] = value_label
            stats_layout.addWidget(value_label, i, 1)
        
        middle_layout.addWidget(stats_group)
        middle_layout.addStretch()
        
        layout.addLayout(middle_layout)
        
        # Sağ taraf - Gelişmiş ayarlar
        right_group = QGroupBox("Gelişmiş Ayarlar")
        right_layout = QVBoxLayout(right_group)
        
        # Headless modu
        self.headless_checkbox = QCheckBox("Headless Mod (Tarayıcı gizli)")
        self.headless_checkbox.setChecked(get_setting("scraper.headless", False))
        right_layout.addWidget(self.headless_checkbox)
        
        # Excel export
        self.excel_export_checkbox = QCheckBox("Excel'e otomatik export")
        self.excel_export_checkbox.setChecked(get_setting("scraper.export_excel", True))
        right_layout.addWidget(self.excel_export_checkbox)
        
        # Delay ayarları
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Delay (sn):"))
        
        self.delay_min_spinbox = QSpinBox()
        self.delay_min_spinbox.setRange(MIN_DELAY, MAX_DELAY)
        self.delay_min_spinbox.setValue(get_setting("scraper.delay_min", DEFAULT_DELAY_MIN))
        self.delay_min_spinbox.setSuffix(" min")
        delay_layout.addWidget(self.delay_min_spinbox)
        
        delay_layout.addWidget(QLabel("-"))
        
        self.delay_max_spinbox = QSpinBox()
        self.delay_max_spinbox.setRange(MIN_DELAY, MAX_DELAY)
        self.delay_max_spinbox.setValue(get_setting("scraper.delay_max", DEFAULT_DELAY_MAX))
        self.delay_max_spinbox.setSuffix(" max")
        delay_layout.addWidget(self.delay_max_spinbox)
        
        right_layout.addLayout(delay_layout)
        
        # Proxy dosyası
        proxy_layout = QHBoxLayout()
        proxy_layout.addWidget(QLabel("Proxy Dosyası:"))
        
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("proxy.txt")
        proxy_layout.addWidget(self.proxy_input)
        
        self.proxy_browse_button = QPushButton("...")
        self.proxy_browse_button.setFixedWidth(30)
        proxy_layout.addWidget(self.proxy_browse_button)
        
        right_layout.addLayout(proxy_layout)
        
        right_layout.addStretch()
        layout.addWidget(right_group)
    
    def setup_bottom_section(self, parent):
        """Alt bölümü oluştur (log ve sonuçlar)"""
        layout = QVBoxLayout(parent)
        
        # Log başlığı
        log_header = QHBoxLayout()
        log_title = QLabel("Scraping Logları")
        log_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        log_header.addWidget(log_title)
        
        log_header.addStretch()
        
        # Log temizle butonu
        self.clear_log_button = QPushButton("🗑️ Temizle")
        self.clear_log_button.setProperty("class", "secondary")
        log_header.addWidget(self.clear_log_button)
        
        layout.addLayout(log_header)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setObjectName("log-widget")
        self.log_text.setProperty("class", "log-widget")
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
    
    def load_location_data(self):
        """İl-ilçe verilerini yükle"""
        # İl combobox'ını doldur
        self.il_combo.addItem("Tümü", "")
        for il in sorted(TURKISH_CITIES):
            self.il_combo.addItem(il, il)
        
        # İl değiştiğinde ilçeleri güncelle
        self.il_combo.currentTextChanged.connect(self.on_il_changed)
        
        # İlk ilçe yüklemesi
        self.on_il_changed(self.il_combo.currentText())
    
    def on_il_changed(self, il_name: str):
        """İl değiştiğinde ilçeleri güncelle"""
        self.ilce_combo.clear()
        self.ilce_combo.addItem("Tümü", "")
        
        if il_name and il_name != "Tümü":
            # İlçe verilerini constants'tan al
            ilceler = CITY_DISTRICTS.get(il_name, [])
            for ilce in sorted(ilceler):
                self.ilce_combo.addItem(ilce, ilce)
    
    def connect_signals(self):
        """Sinyalleri bağla"""
        # Buton sinyalleri
        self.start_button.clicked.connect(self.start_scraping)
        self.stop_button.clicked.connect(self.stop_scraping)
        self.clear_log_button.clicked.connect(self.clear_log)
        self.proxy_browse_button.clicked.connect(self.browse_proxy_file)
        
        # Scraper controller sinyalleri
        self.scraper_controller.progress_updated.connect(self.on_progress_updated)
        self.scraper_controller.status_updated.connect(self.on_status_updated)
        self.scraper_controller.log_message.connect(self.on_log_message)
        self.scraper_controller.business_scraped.connect(self.on_business_scraped)
        self.scraper_controller.scraping_finished.connect(self.on_scraping_finished)
        self.scraper_controller.error_occurred.connect(self.on_error_occurred)
    
    def start_scraping(self):
        """Scraping başlat"""
        # Validasyon
        if not self.validate_inputs():
            return
        
        # UI durumunu güncelle
        self.set_scraping_state(True)
        
        # İstatistikleri sıfırla
        self.reset_stats()
        
        # Ayarları hazırla
        config = self.get_scraper_config()
        search_params = self.get_search_params()
        
        # Log mesajı
        query_desc = self.build_query_description()
        self.add_log_message(f"Scraping başlatılıyor: {query_desc}", "info")
        
        # Scraping başlat
        self.scraper_controller.start_scraping(config, search_params)
        
        # Signal emit et
        self.scraping_started.emit()
        
        show_info(f"Scraping başlatıldı: {query_desc}")
    
    def stop_scraping(self):
        """Scraping durdur"""
        self.scraper_controller.stop_scraping()
        self.add_log_message("Scraping durduruluyor...", "warning")
        show_warning("Scraping durdurma sinyali gönderildi")
    
    def validate_inputs(self) -> bool:
        """Kapsamlı girdi validasyonu"""
        import re
        import os
        
        # Sektör validasyonu
        sektor = self.sektor_input.text().strip()
        if not sektor:
            show_error(ERROR_MESSAGES['EMPTY_SECTOR'])
            self.sektor_input.setFocus()
            return False
        
        # Sektör uzunluk kontrolü
        if len(sektor) < MIN_SECTOR_LENGTH:
            show_error(ERROR_MESSAGES['SECTOR_TOO_SHORT'])
            self.sektor_input.setFocus()
            return False
        
        if len(sektor) > MAX_SECTOR_LENGTH:
            show_error(ERROR_MESSAGES['SECTOR_TOO_LONG'])
            self.sektor_input.setFocus()
            return False
        
        # Sektör karakter kontrolü
        if not re.match(SECTOR_PATTERN, sektor):
            show_error(ERROR_MESSAGES['INVALID_SECTOR'])
            self.sektor_input.setFocus()
            return False
        
        # Limit validasyonu
        limit = self.limit_spinbox.value()
        if limit < MIN_SCRAPER_LIMIT or limit > MAX_SCRAPER_LIMIT:
            show_error(ERROR_MESSAGES['INVALID_LIMIT'])
            self.limit_spinbox.setFocus()
            return False
        
        # Delay validasyonu
        delay_min = self.delay_min_spinbox.value()
        delay_max = self.delay_max_spinbox.value()
        
        if delay_min > delay_max:
            show_error(ERROR_MESSAGES['INVALID_DELAY'])
            self.delay_min_spinbox.setFocus()
            return False
        
        if delay_min < MIN_DELAY:
            show_error(f"Minimum delay en az {MIN_DELAY} saniye olmalıdır!")
            self.delay_min_spinbox.setFocus()
            return False
        
        if delay_max > MAX_DELAY:
            show_error(f"Maximum delay en fazla {MAX_DELAY} saniye olabilir!")
            self.delay_max_spinbox.setFocus()
            return False
        
        # Proxy dosyası validasyonu
        proxy_file = self.proxy_input.text().strip()
        if proxy_file:
            if not os.path.exists(proxy_file):
                show_error(ERROR_MESSAGES['FILE_NOT_FOUND'].format(path=proxy_file))
                self.proxy_input.setFocus()
                return False
            
            if not proxy_file.lower().endswith('.txt'):
                show_error(ERROR_MESSAGES['INVALID_FILE_TYPE'].format(extension='.txt'))
                self.proxy_input.setFocus()
                return False
            
            # Dosya boyutu kontrolü
            try:
                file_size = os.path.getsize(proxy_file)
                if file_size > MAX_PROXY_FILE_SIZE:
                    show_error(f"Proxy dosyası çok büyük (max {MAX_PROXY_FILE_SIZE // (1024*1024)}MB)!")
                    self.proxy_input.setFocus()
                    return False
            except OSError:
                show_error("Proxy dosyası okunamıyor!")
                self.proxy_input.setFocus()
                return False
        
        # İl-İlçe kombinasyon kontrolü
        il = self.il_combo.currentText()
        ilce = self.ilce_combo.currentText()
        
        if ilce and ilce != "Tümü" and (not il or il == "Tümü"):
            show_error("İlçe seçildiğinde il de seçilmelidir!")
            self.il_combo.setFocus()
            return False
        
        return True
    
    def get_scraper_config(self) -> dict:
        """Scraper konfigürasyonunu al"""
        return {
            'headless': self.headless_checkbox.isChecked(),
            'delay_min': self.delay_min_spinbox.value(),
            'delay_max': self.delay_max_spinbox.value(),
            'proxy_file': self.proxy_input.text().strip(),
            'export_excel': self.excel_export_checkbox.isChecked(),
            'user_agent': get_setting("scraper.user_agent", ""),
            'webdriver_path': get_setting("scraper.webdriver_path", "")
        }
    
    def get_search_params(self) -> dict:
        """Arama parametrelerini al"""
        il = self.il_combo.currentData() or ""
        ilce = self.ilce_combo.currentData() or ""
        
        return {
            'il': il,
            'ilce': ilce,
            'sektor': self.sektor_input.text().strip(),
            'limit': self.limit_spinbox.value()
        }
    
    def build_query_description(self) -> str:
        """Sorgu açıklaması oluştur"""
        parts = []
        
        sektor = self.sektor_input.text().strip()
        if sektor:
            parts.append(sektor)
        
        ilce = self.ilce_combo.currentText()
        if ilce and ilce != "Tümü":
            parts.append(ilce)
        
        il = self.il_combo.currentText()
        if il and il != "Tümü":
            parts.append(il)
        
        query = " ".join(parts)
        limit = self.limit_spinbox.value()
        
        return f"{query} (Limit: {limit})"
    
    def set_scraping_state(self, is_scraping: bool):
        """Scraping durumuna göre UI'ı güncelle"""
        self.start_button.setEnabled(not is_scraping)
        self.stop_button.setEnabled(is_scraping)
        
        # Input'ları devre dışı bırak
        inputs = [
            self.il_combo, self.ilce_combo, self.sektor_input, self.limit_spinbox,
            self.headless_checkbox, self.excel_export_checkbox,
            self.delay_min_spinbox, self.delay_max_spinbox, self.proxy_input
        ]
        
        for input_widget in inputs:
            input_widget.setEnabled(not is_scraping)
        
        # Progress bar
        self.progress_bar.setVisible(is_scraping)
        if not is_scraping:
            self.progress_bar.setValue(0)
    
    def reset_stats(self):
        """İstatistikleri sıfırla"""
        self.stats = {
            'total_found': 0,
            'saved_count': 0,
            'updated_count': 0,
            'error_count': 0
        }
        self.update_stats_display()
    
    def update_stats_display(self):
        """İstatistik görünümünü güncelle"""
        for key, value in self.stats.items():
            if key in self.stats_labels:
                self.stats_labels[key].setText(str(value))
    
    def add_log_message(self, message: str, level: str = "info"):
        """Log mesajı ekle"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Renk kodları
        colors = {
            'info': '#ffffff',
            'success': '#107c10',
            'warning': '#ff8c00',
            'error': '#d13438'
        }
        
        color = colors.get(level, '#ffffff')
        formatted_message = f'<span style="color: {color};">[{timestamp}] {message}</span>'
        
        self.log_text.append(formatted_message)
        
        # Auto scroll
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """Log'u temizle"""
        self.log_text.clear()
        self.add_log_message("Log temizlendi", "info")
    
    def browse_proxy_file(self):
        """Proxy dosyası seç"""
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Proxy Dosyası Seç",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            self.proxy_input.setText(file_path)
    
    # Scraper Controller Signal Handlers
    def on_progress_updated(self, progress: int):
        """Progress güncellendiğinde"""
        self.progress_bar.setValue(progress)
    
    def on_status_updated(self, status: str):
        """Status güncellendiğinde"""
        self.status_label.setText(status)
    
    def on_log_message(self, message: str):
        """Log mesajı geldiğinde"""
        self.add_log_message(message, "info")
    
    def on_business_scraped(self, business_data: dict):
        """İşletme çekildiğinde"""
        self.stats['total_found'] += 1
        self.update_stats_display()
    
    def on_scraping_finished(self, stats: dict):
        """Scraping tamamlandığında"""
        self.set_scraping_state(False)
        
        # İstatistikleri güncelle
        self.stats.update(stats)
        self.update_stats_display()
        
        # Status güncelle
        self.status_label.setText("Tamamlandı")
        
        # Log mesajı
        message = (
            f"Scraping tamamlandı! "
            f"Bulunan: {stats.get('total_found', 0)}, "
            f"Yeni: {stats.get('saved_count', 0)}, "
            f"Güncellenen: {stats.get('updated_count', 0)}"
        )
        self.add_log_message(message, "success")
        
        # Toast bildirim
        show_success(message)
        
        # Signal emit et
        self.scraping_finished.emit(stats)
    
    def on_error_occurred(self, error_message: str):
        """Hata oluştuğunda"""
        self.set_scraping_state(False)
        self.status_label.setText("Hata")
        self.add_log_message(f"Hata: {error_message}", "error")
        show_error(f"Scraping hatası: {error_message}")
        
        self.stats['error_count'] += 1
        self.update_stats_display()
    
    def get_current_stats(self) -> dict:
        """Mevcut istatistikleri al"""
        return self.stats.copy()
    
    def is_scraping_active(self) -> bool:
        """Scraping aktif mi?"""
        return self.scraper_controller.is_running()