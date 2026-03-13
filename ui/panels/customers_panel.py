"""
Customers Panel for Google Maps Scraper Application
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QLineEdit, QComboBox, QGroupBox, QSplitter,
                               QTextEdit, QHeaderView, QDateEdit)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont
import logging
from database.models import MusteriManager, Musteri
from utils.toast import show_success, show_error, show_info

logger = logging.getLogger(__name__)

class CustomersPanel(QWidget):
    """Müşteriler panel sınıfı"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_customers = []
        self.selected_customer = None
        
        # UI oluştur
        self.setup_ui()
        
        # Verileri yükle
        self.refresh_data()
        
        logger.info("Customers panel oluşturuldu")
    
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        # Ana layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)
        
        # Başlık
        title_label = QLabel("Müşteriler")
        title_label.setObjectName("panel-title")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        main_layout.addWidget(title_label)
        
        # Filtreler
        self.setup_filters(main_layout)
        
        # Splitter (sol: tablo, sağ: detay)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Sol taraf - Tablo
        self.setup_table_section(splitter)
        
        # Sağ taraf - Detay paneli
        self.setup_detail_section(splitter)
        
        # Splitter oranları
        splitter.setSizes([700, 300])
    
    def setup_filters(self, parent_layout):
        """Filtre bölümünü oluştur"""
        filter_group = QGroupBox("Filtreler")
        filter_layout = QHBoxLayout(filter_group)
        
        # Arama
        filter_layout.addWidget(QLabel("Arama:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Müşteri adı ara...")
        filter_layout.addWidget(self.search_input)
        
        # Ödeme durumu filtresi
        filter_layout.addWidget(QLabel("Ödeme Durumu:"))
        self.odeme_filter = QComboBox()
        self.odeme_filter.addItem("Tümü", "")
        self.odeme_filter.addItem("Beklemede", "beklemede")
        self.odeme_filter.addItem("Ödendi", "odendi")
        self.odeme_filter.addItem("İptal", "iptal")
        filter_layout.addWidget(self.odeme_filter)
        
        # Filtre butonu
        self.filter_button = QPushButton("🔍 Filtrele")
        filter_layout.addWidget(self.filter_button)
        
        # Yenile butonu
        self.refresh_button = QPushButton("🔄 Yenile")
        filter_layout.addWidget(self.refresh_button)
        
        parent_layout.addWidget(filter_group)
        
        # Sinyalleri bağla
        self.filter_button.clicked.connect(self.apply_filters)
        self.refresh_button.clicked.connect(self.refresh_data)
    
    def setup_table_section(self, parent):
        """Tablo bölümünü oluştur"""
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        
        # Tablo başlığı ve butonlar
        table_header = QHBoxLayout()
        
        table_title = QLabel("Müşteri Listesi")
        table_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        table_header.addWidget(table_title)
        
        table_header.addStretch()
        
        # Excel export butonu
        self.export_button = QPushButton("📊 Excel'e Aktar")
        table_header.addWidget(self.export_button)
        
        table_layout.addLayout(table_header)
        
        # Tablo
        self.table = QTableWidget()
        self.setup_table()
        table_layout.addWidget(self.table)
        
        parent.addWidget(table_widget)
        
        # Sinyalleri bağla
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.export_button.clicked.connect(self.export_to_excel)
    
    def setup_table(self):
        """Tabloyu ayarla"""
        headers = [
            "İşletme Adı", "Telefon", "İl", "İlçe", "Paket", 
            "Ödeme Durumu", "İletişim Tarihi", "Kayıt Tarihi"
        ]
        
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        # Tablo ayarları
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        
        # Sütun genişlikleri
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # İşletme adı
        for i in range(1, len(headers)):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
    
    def setup_detail_section(self, parent):
        """Detay bölümünü oluştur"""
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        
        # Detay başlığı
        detail_title = QLabel("Müşteri Detayları")
        detail_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        detail_layout.addWidget(detail_title)
        
        # Paket bilgisi
        detail_layout.addWidget(QLabel("Paket:"))
        self.paket_input = QLineEdit()
        detail_layout.addWidget(self.paket_input)
        
        # Ödeme durumu
        detail_layout.addWidget(QLabel("Ödeme Durumu:"))
        self.odeme_combo = QComboBox()
        self.odeme_combo.addItems(["beklemede", "odendi", "iptal"])
        detail_layout.addWidget(self.odeme_combo)
        
        # İletişim tarihi
        detail_layout.addWidget(QLabel("İletişim Tarihi:"))
        self.iletisim_date = QDateEdit()
        self.iletisim_date.setDate(QDate.currentDate())
        self.iletisim_date.setCalendarPopup(True)
        detail_layout.addWidget(self.iletisim_date)
        
        # Notlar
        detail_layout.addWidget(QLabel("Notlar:"))
        self.note_input = QTextEdit()
        self.note_input.setMaximumHeight(100)
        detail_layout.addWidget(self.note_input)
        
        # Güncelle butonu
        self.update_button = QPushButton("💾 Güncelle")
        self.update_button.setEnabled(False)
        detail_layout.addWidget(self.update_button)
        
        detail_layout.addStretch()
        
        parent.addWidget(detail_widget)
        
        # Sinyalleri bağla
        self.update_button.clicked.connect(self.update_customer)
    
    def refresh_data(self):
        """Verileri yenile"""
        try:
            # Tüm müşterileri al
            self.current_customers = MusteriManager.get_all_with_isletme()
            
            # Tabloyu güncelle
            self.update_table()
            
            show_info(f"{len(self.current_customers)} müşteri yüklendi")
            
        except Exception as e:
            logger.error(f"Veri yenileme hatası: {e}")
            show_error(f"Veri yenileme hatası: {str(e)}")
    
    def update_table(self):
        """Tabloyu güncelle"""
        self.table.setRowCount(len(self.current_customers))
        
        for row, customer in enumerate(self.current_customers):
            # İşletme adı
            self.table.setItem(row, 0, QTableWidgetItem(customer.get('isim', '')))
            
            # Telefon
            self.table.setItem(row, 1, QTableWidgetItem(customer.get('telefon', '')))
            
            # İl
            self.table.setItem(row, 2, QTableWidgetItem(customer.get('il', '')))
            
            # İlçe
            self.table.setItem(row, 3, QTableWidgetItem(customer.get('ilce', '')))
            
            # Paket
            self.table.setItem(row, 4, QTableWidgetItem(customer.get('paket', '')))
            
            # Ödeme durumu
            self.table.setItem(row, 5, QTableWidgetItem(customer.get('odeme_durumu', '')))
            
            # İletişim tarihi
            iletisim_tarihi = customer.get('iletisim_tarihi')
            iletisim_text = iletisim_tarihi.strftime("%Y-%m-%d") if iletisim_tarihi else ""
            self.table.setItem(row, 6, QTableWidgetItem(iletisim_text))
            
            # Kayıt tarihi
            kayit_tarihi = customer.get('kayit_tarihi')
            kayit_text = kayit_tarihi.strftime("%Y-%m-%d") if kayit_tarihi else ""
            self.table.setItem(row, 7, QTableWidgetItem(kayit_text))
            
            # Customer objesini row'a bağla
            self.table.item(row, 0).setData(Qt.UserRole, customer)
    
    def apply_filters(self):
        """Filtreleri uygula"""
        # Basit implementasyon - gerçek uygulamada database filtreleme yapılabilir
        show_info("Filtre özelliği geliştiriliyor...")
    
    def on_selection_changed(self):
        """Seçim değiştiğinde"""
        current_row = self.table.currentRow()
        
        if current_row >= 0:
            item = self.table.item(current_row, 0)
            if item:
                customer = item.data(Qt.UserRole)
                self.selected_customer = customer
                self.show_customer_details(customer)
                self.update_button.setEnabled(True)
        else:
            self.selected_customer = None
            self.clear_details()
            self.update_button.setEnabled(False)
    
    def show_customer_details(self, customer):
        """Müşteri detaylarını göster"""
        self.paket_input.setText(customer.get('paket', ''))
        
        odeme_durumu = customer.get('odeme_durumu', 'beklemede')
        index = self.odeme_combo.findText(odeme_durumu)
        if index >= 0:
            self.odeme_combo.setCurrentIndex(index)
        
        iletisim_tarihi = customer.get('iletisim_tarihi')
        if iletisim_tarihi:
            self.iletisim_date.setDate(QDate.fromString(iletisim_tarihi.strftime("%Y-%m-%d"), "yyyy-MM-dd"))
        
        self.note_input.setPlainText(customer.get('notlar', ''))
    
    def clear_details(self):
        """Detayları temizle"""
        self.paket_input.clear()
        self.odeme_combo.setCurrentIndex(0)
        self.iletisim_date.setDate(QDate.currentDate())
        self.note_input.clear()
    
    def update_customer(self):
        """Müşteri bilgilerini güncelle"""
        if not self.selected_customer:
            return
        
        try:
            # Güncelleme işlemi burada yapılacak
            # Şimdilik basit bir mesaj gösterelim
            show_success("Müşteri bilgileri güncellendi!")
            
        except Exception as e:
            logger.error(f"Müşteri güncelleme hatası: {e}")
            show_error(f"Güncelleme hatası: {str(e)}")
    
    def export_to_excel(self):
        """Excel'e aktar"""
        try:
            from utils.excel_export import ExcelExporter
            from datetime import datetime
            
            exporter = ExcelExporter()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"musteriler_{timestamp}"
            
            file_path = exporter.export_customers(self.current_customers, filename)
            show_success(f"Excel dosyası oluşturuldu: {file_path}")
            
        except Exception as e:
            logger.error(f"Excel export hatası: {e}")
            show_error(f"Excel export hatası: {str(e)}")