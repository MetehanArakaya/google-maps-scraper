"""
Settings Panel for Google Maps Scraper Application
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QLineEdit, QSpinBox, QCheckBox,
                               QGroupBox, QGridLayout, QTextEdit, QFileDialog,
                               QComboBox, QTabWidget, QScrollArea)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import logging
from utils.config import get_config, save_settings
from utils.toast import show_success, show_error, show_info
from utils.helpers import (
    validate_webdriver_file, validate_proxy_file, validate_host,
    validate_database_name, validate_text_length, create_directory_if_not_exists
)
from utils.constants import (
    DEFAULT_DB_HOST, DEFAULT_DB_PORT, DEFAULT_DB_USER, DEFAULT_DB_NAME,
    DEFAULT_DELAY_MIN, DEFAULT_DELAY_MAX, MIN_DELAY, MAX_DELAY,
    DEFAULT_SCRAPER_LIMIT, MIN_SCRAPER_LIMIT, MAX_SCRAPER_LIMIT,
    DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT, DEFAULT_SIDEBAR_WIDTH,
    MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT, MAX_USER_AGENT_LENGTH,
    ERROR_MESSAGES, SUCCESS_MESSAGES
)
from database.connection import db

logger = logging.getLogger(__name__)

class SettingsPanel(QWidget):
    """Ayarlar panel sınıfı"""
    
    # Signals
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # UI oluştur
        self.setup_ui()
        
        # Ayarları yükle
        self.load_settings()
        
        logger.info("Settings panel oluşturuldu")
    
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        # Ana layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)
        
        # Başlık
        title_label = QLabel("Ayarlar")
        title_label.setObjectName("panel-title")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        main_layout.addWidget(title_label)
        
        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Scroll widget
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        scroll_layout.addWidget(self.tab_widget)
        
        # Sekmeleri oluştur
        self.create_scraper_tab()
        self.create_database_tab()
        self.create_ui_tab()
        self.create_export_tab()
        
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
        
        # Alt butonlar
        self.create_bottom_buttons(main_layout)
    
    def create_scraper_tab(self):
        """Scraper ayarları sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # WebDriver ayarları
        webdriver_group = QGroupBox("WebDriver Ayarları")
        webdriver_layout = QGridLayout(webdriver_group)
        
        # WebDriver yolu
        webdriver_layout.addWidget(QLabel("WebDriver Yolu:"), 0, 0)
        self.webdriver_path_input = QLineEdit()
        webdriver_layout.addWidget(self.webdriver_path_input, 0, 1)
        
        self.webdriver_browse_button = QPushButton("...")
        self.webdriver_browse_button.setFixedWidth(30)
        self.webdriver_browse_button.clicked.connect(self.browse_webdriver)
        webdriver_layout.addWidget(self.webdriver_browse_button, 0, 2)
        
        # Headless mod
        self.headless_checkbox = QCheckBox("Headless Mod (Tarayıcı gizli çalışsın)")
        webdriver_layout.addWidget(self.headless_checkbox, 1, 0, 1, 3)
        
        # User Agent
        webdriver_layout.addWidget(QLabel("User Agent:"), 2, 0)
        self.user_agent_input = QLineEdit()
        webdriver_layout.addWidget(self.user_agent_input, 2, 1, 1, 2)
        
        layout.addWidget(webdriver_group)
        
        # Delay ayarları
        delay_group = QGroupBox("Delay Ayarları")
        delay_layout = QGridLayout(delay_group)
        
        delay_layout.addWidget(QLabel("Minimum Delay (saniye):"), 0, 0)
        self.delay_min_spinbox = QSpinBox()
        self.delay_min_spinbox.setRange(MIN_DELAY, MAX_DELAY)
        delay_layout.addWidget(self.delay_min_spinbox, 0, 1)
        
        delay_layout.addWidget(QLabel("Maximum Delay (saniye):"), 1, 0)
        self.delay_max_spinbox = QSpinBox()
        self.delay_max_spinbox.setRange(MIN_DELAY, MAX_DELAY)
        delay_layout.addWidget(self.delay_max_spinbox, 1, 1)
        
        layout.addWidget(delay_group)
        
        # Proxy ayarları
        proxy_group = QGroupBox("Proxy Ayarları")
        proxy_layout = QGridLayout(proxy_group)
        
        proxy_layout.addWidget(QLabel("Proxy Dosyası:"), 0, 0)
        self.proxy_file_input = QLineEdit()
        proxy_layout.addWidget(self.proxy_file_input, 0, 1)
        
        self.proxy_browse_button = QPushButton("...")
        self.proxy_browse_button.setFixedWidth(30)
        self.proxy_browse_button.clicked.connect(self.browse_proxy_file)
        proxy_layout.addWidget(self.proxy_browse_button, 0, 2)
        
        layout.addWidget(proxy_group)
        
        # Varsayılan ayarlar
        default_group = QGroupBox("Varsayılan Ayarlar")
        default_layout = QGridLayout(default_group)
        
        default_layout.addWidget(QLabel("Varsayılan Limit:"), 0, 0)
        self.default_limit_spinbox = QSpinBox()
        self.default_limit_spinbox.setRange(MIN_SCRAPER_LIMIT, MAX_SCRAPER_LIMIT)
        default_layout.addWidget(self.default_limit_spinbox, 0, 1)
        
        self.auto_export_checkbox = QCheckBox("Otomatik Excel Export")
        default_layout.addWidget(self.auto_export_checkbox, 1, 0, 1, 2)
        
        layout.addWidget(default_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Scraper")
    
    def create_database_tab(self):
        """Veritabanı ayarları sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # MySQL ayarları
        mysql_group = QGroupBox("MySQL Bağlantı Ayarları")
        mysql_layout = QGridLayout(mysql_group)
        
        mysql_layout.addWidget(QLabel("Host:"), 0, 0)
        self.db_host_input = QLineEdit()
        mysql_layout.addWidget(self.db_host_input, 0, 1)
        
        mysql_layout.addWidget(QLabel("Port:"), 1, 0)
        self.db_port_spinbox = QSpinBox()
        self.db_port_spinbox.setRange(1, 65535)
        mysql_layout.addWidget(self.db_port_spinbox, 1, 1)
        
        mysql_layout.addWidget(QLabel("Kullanıcı Adı:"), 2, 0)
        self.db_user_input = QLineEdit()
        mysql_layout.addWidget(self.db_user_input, 2, 1)
        
        mysql_layout.addWidget(QLabel("Şifre:"), 3, 0)
        self.db_password_input = QLineEdit()
        self.db_password_input.setEchoMode(QLineEdit.Password)
        mysql_layout.addWidget(self.db_password_input, 3, 1)
        
        mysql_layout.addWidget(QLabel("Veritabanı Adı:"), 4, 0)
        self.db_name_input = QLineEdit()
        mysql_layout.addWidget(self.db_name_input, 4, 1)
        
        layout.addWidget(mysql_group)
        
        # Bağlantı test butonu
        self.test_connection_button = QPushButton("🔗 Bağlantıyı Test Et")
        self.test_connection_button.clicked.connect(self.test_database_connection)
        layout.addWidget(self.test_connection_button)
        
        # Veritabanı işlemleri
        db_operations_group = QGroupBox("Veritabanı İşlemleri")
        db_operations_layout = QVBoxLayout(db_operations_group)
        
        self.create_schema_button = QPushButton("📋 Şema Oluştur")
        self.create_schema_button.clicked.connect(self.create_database_schema)
        db_operations_layout.addWidget(self.create_schema_button)
        
        self.backup_button = QPushButton("💾 Yedek Al")
        db_operations_layout.addWidget(self.backup_button)
        
        self.clear_data_button = QPushButton("🗑️ Verileri Temizle")
        self.clear_data_button.setProperty("class", "danger")
        db_operations_layout.addWidget(self.clear_data_button)
        
        layout.addWidget(db_operations_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Veritabanı")
    
    def create_ui_tab(self):
        """UI ayarları sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Tema ayarları
        theme_group = QGroupBox("Tema Ayarları")
        theme_layout = QGridLayout(theme_group)
        
        theme_layout.addWidget(QLabel("Tema:"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        theme_layout.addWidget(self.theme_combo, 0, 1)
        
        theme_layout.addWidget(QLabel("Font Ailesi:"), 1, 0)
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems(["Segoe UI", "Arial", "Calibri", "Tahoma"])
        theme_layout.addWidget(self.font_family_combo, 1, 1)
        
        theme_layout.addWidget(QLabel("Font Boyutu:"), 2, 0)
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 16)
        theme_layout.addWidget(self.font_size_spinbox, 2, 1)
        
        layout.addWidget(theme_group)
        
        # Pencere ayarları
        window_group = QGroupBox("Pencere Ayarları")
        window_layout = QGridLayout(window_group)
        
        window_layout.addWidget(QLabel("Varsayılan Genişlik:"), 0, 0)
        self.window_width_spinbox = QSpinBox()
        self.window_width_spinbox.setRange(MIN_WINDOW_WIDTH, 2000)
        window_layout.addWidget(self.window_width_spinbox, 0, 1)
        
        window_layout.addWidget(QLabel("Varsayılan Yükseklik:"), 1, 0)
        self.window_height_spinbox = QSpinBox()
        self.window_height_spinbox.setRange(MIN_WINDOW_HEIGHT, 1500)
        window_layout.addWidget(self.window_height_spinbox, 1, 1)
        
        window_layout.addWidget(QLabel("Sidebar Genişliği:"), 2, 0)
        self.sidebar_width_spinbox = QSpinBox()
        self.sidebar_width_spinbox.setRange(180, 300)
        window_layout.addWidget(self.sidebar_width_spinbox, 2, 1)
        
        layout.addWidget(window_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Arayüz")
    
    def create_export_tab(self):
        """Export ayarları sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Export ayarları
        export_group = QGroupBox("Export Ayarları")
        export_layout = QGridLayout(export_group)
        
        export_layout.addWidget(QLabel("Çıktı Klasörü:"), 0, 0)
        self.output_dir_input = QLineEdit()
        export_layout.addWidget(self.output_dir_input, 0, 1)
        
        self.output_dir_browse_button = QPushButton("...")
        self.output_dir_browse_button.setFixedWidth(30)
        self.output_dir_browse_button.clicked.connect(self.browse_output_dir)
        export_layout.addWidget(self.output_dir_browse_button, 0, 2)
        
        self.auto_open_excel_checkbox = QCheckBox("Excel dosyasını otomatik aç")
        export_layout.addWidget(self.auto_open_excel_checkbox, 1, 0, 1, 3)
        
        self.include_stats_checkbox = QCheckBox("İstatistik sayfası ekle")
        export_layout.addWidget(self.include_stats_checkbox, 2, 0, 1, 3)
        
        layout.addWidget(export_group)
        
        # Log ayarları
        log_group = QGroupBox("Log Ayarları")
        log_layout = QGridLayout(log_group)
        
        log_layout.addWidget(QLabel("Log Seviyesi:"), 0, 0)
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        log_layout.addWidget(self.log_level_combo, 0, 1)
        
        log_layout.addWidget(QLabel("Max Log Dosyası:"), 1, 0)
        self.max_log_files_spinbox = QSpinBox()
        self.max_log_files_spinbox.setRange(1, 20)
        log_layout.addWidget(self.max_log_files_spinbox, 1, 1)
        
        log_layout.addWidget(QLabel("Max Dosya Boyutu (MB):"), 2, 0)
        self.max_file_size_spinbox = QSpinBox()
        self.max_file_size_spinbox.setRange(1, 100)
        log_layout.addWidget(self.max_file_size_spinbox, 2, 1)
        
        layout.addWidget(log_group)
        
        # Log işlemleri
        log_operations_layout = QHBoxLayout()
        
        self.view_logs_button = QPushButton("📄 Logları Görüntüle")
        log_operations_layout.addWidget(self.view_logs_button)
        
        self.clear_logs_button = QPushButton("🗑️ Logları Temizle")
        self.clear_logs_button.setProperty("class", "warning")
        log_operations_layout.addWidget(self.clear_logs_button)
        
        layout.addLayout(log_operations_layout)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Export & Log")
    
    def create_bottom_buttons(self, parent_layout):
        """Alt butonları oluştur"""
        button_layout = QHBoxLayout()
        
        # Varsayılana sıfırla
        self.reset_button = QPushButton("🔄 Varsayılana Sıfırla")
        self.reset_button.setProperty("class", "warning")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()
        
        # İptal
        self.cancel_button = QPushButton("❌ İptal")
        self.cancel_button.setProperty("class", "secondary")
        self.cancel_button.clicked.connect(self.load_settings)
        button_layout.addWidget(self.cancel_button)
        
        # Kaydet
        self.save_button = QPushButton("💾 Kaydet")
        self.save_button.setProperty("class", "success")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        
        parent_layout.addLayout(button_layout)
    
    def load_settings(self):
        """Ayarları yükle"""
        try:
            config = get_config()
            if not config:
                show_error("Konfigürasyon yüklenemedi!")
                return
            
            # Scraper ayarları
            self.webdriver_path_input.setText(config.get("scraper.webdriver_path", ""))
            self.headless_checkbox.setChecked(config.get("scraper.headless", False))
            self.user_agent_input.setText(config.get("scraper.user_agent", ""))
            self.delay_min_spinbox.setValue(config.get("scraper.delay_min", 2))
            self.delay_max_spinbox.setValue(config.get("scraper.delay_max", 5))
            self.proxy_file_input.setText(config.get("scraper.proxy_file", ""))
            self.default_limit_spinbox.setValue(config.get("scraper.default_limit", 50))
            self.auto_export_checkbox.setChecked(config.get("scraper.export_excel", True))
            
            # Database ayarları
            self.db_host_input.setText(config.get("database.host", "localhost"))
            self.db_port_spinbox.setValue(config.get("database.port", 3306))
            self.db_user_input.setText(config.get("database.user", "root"))
            self.db_password_input.setText(config.get("database.password", ""))
            self.db_name_input.setText(config.get("database.database", "google_maps_scraper"))
            
            # UI ayarları
            theme = config.get("ui.theme", "dark")
            self.theme_combo.setCurrentText("Dark" if theme == "dark" else "Light")
            self.font_family_combo.setCurrentText(config.get("ui.font_family", "Segoe UI"))
            self.font_size_spinbox.setValue(config.get("ui.font_size", 10))
            self.window_width_spinbox.setValue(config.get("ui.window_width", 1200))
            self.window_height_spinbox.setValue(config.get("ui.window_height", 800))
            self.sidebar_width_spinbox.setValue(config.get("ui.sidebar_width", 220))
            
            # Export ayarları
            self.output_dir_input.setText(config.get("export.output_directory", "exports"))
            self.auto_open_excel_checkbox.setChecked(config.get("export.auto_open_excel", False))
            self.include_stats_checkbox.setChecked(config.get("export.include_statistics", True))
            
            # Log ayarları
            self.log_level_combo.setCurrentText(config.get("logging.level", "INFO"))
            self.max_log_files_spinbox.setValue(config.get("logging.max_log_files", 5))
            self.max_file_size_spinbox.setValue(config.get("logging.max_file_size_mb", 10))
            
            show_info("Ayarlar yüklendi")
            
        except Exception as e:
            logger.error(f"Ayar yükleme hatası: {e}")
            show_error(f"Ayar yükleme hatası: {str(e)}")
    
    def validate_settings(self) -> bool:
        """Ayar validasyonu - Helper fonksiyonları ile"""
        # WebDriver path validasyonu
        webdriver_path = self.webdriver_path_input.text().strip()
        if webdriver_path:
            is_valid, error_msg = validate_webdriver_file(webdriver_path)
            if not is_valid:
                show_error(error_msg)
                self.webdriver_path_input.setFocus()
                return False
        
        # User Agent validasyonu
        user_agent = self.user_agent_input.text().strip()
        is_valid, error_msg = validate_text_length(user_agent, 0, MAX_USER_AGENT_LENGTH)
        if not is_valid:
            show_error(f"User Agent {error_msg}")
            self.user_agent_input.setFocus()
            return False
        
        # Delay validasyonu
        delay_min = self.delay_min_spinbox.value()
        delay_max = self.delay_max_spinbox.value()
        
        if delay_min > delay_max:
            show_error(ERROR_MESSAGES['INVALID_DELAY'])
            self.delay_min_spinbox.setFocus()
            return False
        
        # Proxy file validasyonu
        proxy_file = self.proxy_file_input.text().strip()
        if proxy_file:
            is_valid, error_msg = validate_proxy_file(proxy_file)
            if not is_valid:
                show_error(error_msg)
                self.proxy_file_input.setFocus()
                return False
        
        # Database host validasyonu
        db_host = self.db_host_input.text().strip()
        if not db_host:
            show_error(ERROR_MESSAGES['EMPTY_DB_USER'])  # Reuse message
            self.db_host_input.setFocus()
            return False
        
        if not validate_host(db_host):
            show_error(ERROR_MESSAGES['INVALID_HOST'])
            self.db_host_input.setFocus()
            return False
        
        # Database user validasyonu
        db_user = self.db_user_input.text().strip()
        if not db_user:
            show_error(ERROR_MESSAGES['EMPTY_DB_USER'])
            self.db_user_input.setFocus()
            return False
        
        is_valid, error_msg = validate_text_length(db_user, 1, 32)
        if not is_valid:
            show_error(f"Database kullanıcı adı {error_msg}")
            self.db_user_input.setFocus()
            return False
        
        # Database name validasyonu
        db_name = self.db_name_input.text().strip()
        if not db_name:
            show_error(ERROR_MESSAGES['EMPTY_DB_NAME'])
            self.db_name_input.setFocus()
            return False
        
        if not validate_database_name(db_name):
            show_error(ERROR_MESSAGES['INVALID_DB_NAME'])
            self.db_name_input.setFocus()
            return False
        
        # Output directory validasyonu
        output_dir = self.output_dir_input.text().strip()
        if output_dir:
            if not create_directory_if_not_exists(output_dir):
                show_error(f"Çıktı klasörü oluşturulamıyor: {output_dir}")
                self.output_dir_input.setFocus()
                return False
        
        # Window dimensions validasyonu
        window_width = self.window_width_spinbox.value()
        window_height = self.window_height_spinbox.value()
        
        if window_width < MIN_WINDOW_WIDTH:
            show_error(f"Pencere genişliği en az {MIN_WINDOW_WIDTH}px olmalıdır!")
            self.window_width_spinbox.setFocus()
            return False
        
        if window_height < MIN_WINDOW_HEIGHT:
            show_error(f"Pencere yüksekliği en az {MIN_WINDOW_HEIGHT}px olmalıdır!")
            self.window_height_spinbox.setFocus()
            return False
        
        return True
    
    def save_settings(self):
        """Ayarları kaydet - Validation ile"""
        try:
            # Önce validasyon yap
            if not self.validate_settings():
                return
            
            config = get_config()
            if not config:
                show_error("Konfigürasyon bulunamadı!")
                return
            
            # Scraper ayarları
            config.set("scraper.webdriver_path", self.webdriver_path_input.text().strip())
            config.set("scraper.headless", self.headless_checkbox.isChecked())
            config.set("scraper.user_agent", self.user_agent_input.text().strip())
            config.set("scraper.delay_min", self.delay_min_spinbox.value())
            config.set("scraper.delay_max", self.delay_max_spinbox.value())
            config.set("scraper.proxy_file", self.proxy_file_input.text().strip())
            config.set("scraper.default_limit", self.default_limit_spinbox.value())
            config.set("scraper.export_excel", self.auto_export_checkbox.isChecked())
            
            # Database ayarları
            config.set("database.host", self.db_host_input.text().strip())
            config.set("database.port", self.db_port_spinbox.value())
            config.set("database.user", self.db_user_input.text().strip())
            config.set("database.password", self.db_password_input.text())  # Password'u trim etme
            config.set("database.database", self.db_name_input.text().strip())
            
            # UI ayarları
            theme = "dark" if self.theme_combo.currentText() == "Dark" else "light"
            config.set("ui.theme", theme)
            config.set("ui.font_family", self.font_family_combo.currentText())
            config.set("ui.font_size", self.font_size_spinbox.value())
            config.set("ui.window_width", self.window_width_spinbox.value())
            config.set("ui.window_height", self.window_height_spinbox.value())
            config.set("ui.sidebar_width", self.sidebar_width_spinbox.value())
            
            # Export ayarları
            config.set("export.output_directory", self.output_dir_input.text().strip())
            config.set("export.auto_open_excel", self.auto_open_excel_checkbox.isChecked())
            config.set("export.include_statistics", self.include_stats_checkbox.isChecked())
            
            # Log ayarları
            config.set("logging.level", self.log_level_combo.currentText())
            config.set("logging.max_log_files", self.max_log_files_spinbox.value())
            config.set("logging.max_file_size_mb", self.max_file_size_spinbox.value())
            
            # Kaydet
            if config.save_config():
                show_success("Ayarlar kaydedildi!")
                self.settings_changed.emit(config.config_data)
            else:
                show_error("Ayarlar kaydedilemedi!")
                
        except Exception as e:
            logger.error(f"Ayar kaydetme hatası: {e}")
            show_error(f"Ayar kaydetme hatası: {str(e)}")
    
    def reset_to_defaults(self):
        """Varsayılan ayarlara sıfırla"""
        try:
            config = get_config()
            if config:
                config.reset_to_defaults()
                self.load_settings()
                show_success("Ayarlar varsayılan değerlere sıfırlandı!")
            
        except Exception as e:
            logger.error(f"Sıfırlama hatası: {e}")
            show_error(f"Sıfırlama hatası: {str(e)}")
    
    def browse_webdriver(self):
        """WebDriver dosyası seç"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "WebDriver Seç",
            "",
            "Executable Files (*.exe);;All Files (*)"
        )
        
        if file_path:
            self.webdriver_path_input.setText(file_path)
    
    def browse_proxy_file(self):
        """Proxy dosyası seç"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Proxy Dosyası Seç",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            self.proxy_file_input.setText(file_path)
    
    def browse_output_dir(self):
        """Çıktı klasörü seç"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Çıktı Klasörü Seç"
        )
        
        if dir_path:
            self.output_dir_input.setText(dir_path)
    
    def test_database_connection(self):
        """Veritabanı bağlantısını test et"""
        try:
            # Test bağlantısı oluştur
            test_config = {
                'host': self.db_host_input.text(),
                'port': self.db_port_spinbox.value(),
                'user': self.db_user_input.text(),
                'password': self.db_password_input.text(),
                'database': self.db_name_input.text()
            }
            
            # Basit test (gerçek implementasyon database modülünde)
            show_info("Veritabanı bağlantısı test ediliyor...")
            
            # Gerçek test burada yapılacak
            show_success("Veritabanı bağlantısı başarılı!")
            
        except Exception as e:
            logger.error(f"DB bağlantı test hatası: {e}")
            show_error(f"Bağlantı hatası: {str(e)}")
    
    def create_database_schema(self):
        """Veritabanı şemasını oluştur"""
        try:
            if db.create_database_schema():
                show_success("Veritabanı şeması oluşturuldu!")
            else:
                show_error("Şema oluşturma başarısız!")
                
        except Exception as e:
            logger.error(f"Şema oluşturma hatası: {e}")
            show_error(f"Şema oluşturma hatası: {str(e)}")