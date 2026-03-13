"""
Users Panel for Google Maps Scraper Application
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QLineEdit, QComboBox, QGroupBox, QSplitter,
                               QTextEdit, QHeaderView, QCheckBox)
from PySide6.QtCore import Qt, Signal, QThread, QMutex, QMutexLocker
from PySide6.QtGui import QFont
import logging
from typing import List, Dict, Any
from database.models import IsletmeManager, Isletme
from utils.toast import show_success, show_error, show_info

class DataLoaderWorker(QThread):
    """UI thread'i bloklamayan veri yükleme worker'ı"""
    
    # Signals
    data_loaded = Signal(list)  # Yüklenen veriler
    error_occurred = Signal(str)  # Hata mesajı
    progress_updated = Signal(int)  # Progress (0-100)
    
    def __init__(self, filters: Dict[str, Any] = None, limit: int = 1000):
        super().__init__()
        self.filters = filters or {}
        self.limit = limit
        self.mutex = QMutex()
        self.should_stop = False
    
    def run(self):
        """Veri yükleme işlemi"""
        try:
            with QMutexLocker(self.mutex):
                if self.should_stop:
                    return
            
            self.progress_updated.emit(10)
            
            # Filtrelere göre veri çek
            if self.filters:
                businesses = IsletmeManager.search(self.filters)
            else:
                businesses = IsletmeManager.get_all(limit=self.limit)
            
            self.progress_updated.emit(80)
            
            with QMutexLocker(self.mutex):
                if self.should_stop:
                    return
            
            self.progress_updated.emit(100)
            self.data_loaded.emit(businesses)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def stop(self):
        """Worker'ı durdur"""
        with QMutexLocker(self.mutex):
            self.should_stop = True

logger = logging.getLogger(__name__)

class UsersPanel(QWidget):
    """Kullanıcılar (tüm işletmeler) panel sınıfı"""
    
    # Signals
    business_selected = Signal(dict)
    customer_created = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_businesses = []
        self.selected_business = None
        self.data_loader = None
        
        # UI oluştur
        self.setup_ui()
        
        # Verileri yükle
        self.refresh_data()
        
        logger.info("Users panel oluşturuldu")
    
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        # Ana layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)
        
        # Başlık
        title_label = QLabel("Tüm İşletmeler")
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
        self.search_input.setPlaceholderText("İşletme adı ara...")
        filter_layout.addWidget(self.search_input)
        
        # İl filtresi
        filter_layout.addWidget(QLabel("İl:"))
        self.il_filter = QComboBox()
        self.il_filter.addItem("Tümü", "")
        filter_layout.addWidget(self.il_filter)
        
        # Durum filtresi
        filter_layout.addWidget(QLabel("Durum:"))
        self.durum_filter = QComboBox()
        self.durum_filter.addItem("Tümü", -1)
        self.durum_filter.addItem("Potansiyel", 0)
        self.durum_filter.addItem("Müşteri", 1)
        filter_layout.addWidget(self.durum_filter)
        
        # Telefon filtresi
        self.telefon_filter = QCheckBox("Sadece telefonu olanlar")
        filter_layout.addWidget(self.telefon_filter)
        
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
        self.search_input.returnPressed.connect(self.apply_filters)
    
    def setup_table_section(self, parent):
        """Tablo bölümünü oluştur"""
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        
        # Tablo başlığı ve butonlar
        table_header = QHBoxLayout()
        
        table_title = QLabel("İşletme Listesi")
        table_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        table_header.addWidget(table_title)
        
        table_header.addStretch()
        
        # Müşteri yap butonu
        self.make_customer_button = QPushButton("💼 Müşteri Yap")
        self.make_customer_button.setProperty("class", "success")
        self.make_customer_button.setEnabled(False)
        table_header.addWidget(self.make_customer_button)
        
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
        self.make_customer_button.clicked.connect(self.make_customer)
        self.export_button.clicked.connect(self.export_to_excel)
    
    def setup_table(self):
        """Tabloyu ayarla"""
        headers = [
            "İşletme Adı", "Kategori", "Telefon", "İl", "İlçe", 
            "Puan", "Durum", "Eklenme Tarihi"
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
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Kategori
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Telefon
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # İl
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # İlçe
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Puan
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Durum
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Tarih
    
    def setup_detail_section(self, parent):
        """Detay bölümünü oluştur"""
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        
        # Detay başlığı
        detail_title = QLabel("İşletme Detayları")
        detail_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        detail_layout.addWidget(detail_title)
        
        # Detay text area
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(300)
        detail_layout.addWidget(self.detail_text)
        
        # Not ekleme
        note_label = QLabel("Notlar:")
        detail_layout.addWidget(note_label)
        
        self.note_input = QTextEdit()
        self.note_input.setMaximumHeight(100)
        self.note_input.setPlaceholderText("İşletme hakkında notlar...")
        detail_layout.addWidget(self.note_input)
        
        # Not kaydet butonu
        self.save_note_button = QPushButton("💾 Not Kaydet")
        self.save_note_button.setEnabled(False)
        detail_layout.addWidget(self.save_note_button)
        
        detail_layout.addStretch()
        
        parent.addWidget(detail_widget)
        
        # Sinyalleri bağla
        self.save_note_button.clicked.connect(self.save_note)
    
    def refresh_data(self):
        """Verileri yenile - Thread-safe"""
        try:
            # Önceki worker'ı durdur
            if self.data_loader and self.data_loader.isRunning():
                self.data_loader.stop()
                self.data_loader.wait(3000)  # 3 saniye bekle
            
            # Yeni worker oluştur
            self.data_loader = DataLoaderWorker(limit=1000)
            
            # Sinyalleri bağla
            self.data_loader.data_loaded.connect(self.on_data_loaded)
            self.data_loader.error_occurred.connect(self.on_data_error)
            self.data_loader.progress_updated.connect(self.on_progress_updated)
            
            # UI'ı güncelle
            self.refresh_button.setEnabled(False)
            self.refresh_button.setText("⏳ Yükleniyor...")
            
            # Worker'ı başlat
            self.data_loader.start()
            
        except Exception as e:
            logger.error(f"Veri yenileme başlatma hatası: {e}")
            show_error(f"Veri yenileme hatası: {str(e)}")
            self.refresh_button.setEnabled(True)
            self.refresh_button.setText("🔄 Yenile")
    
    def update_table(self):
        """Tabloyu güncelle"""
        self.table.setRowCount(len(self.current_businesses))
        
        for row, business in enumerate(self.current_businesses):
            # İşletme adı
            self.table.setItem(row, 0, QTableWidgetItem(business.isim or ""))
            
            # Kategori
            self.table.setItem(row, 1, QTableWidgetItem(business.kategori or ""))
            
            # Telefon
            self.table.setItem(row, 2, QTableWidgetItem(business.telefon or ""))
            
            # İl
            self.table.setItem(row, 3, QTableWidgetItem(business.il or ""))
            
            # İlçe
            self.table.setItem(row, 4, QTableWidgetItem(business.ilce or ""))
            
            # Puan
            puan_text = str(business.puan) if business.puan else ""
            self.table.setItem(row, 5, QTableWidgetItem(puan_text))
            
            # Durum
            durum_text = "Müşteri" if business.durum == 1 else "Potansiyel"
            self.table.setItem(row, 6, QTableWidgetItem(durum_text))
            
            # Tarih
            tarih_text = business.eklenme_tarihi.strftime("%Y-%m-%d") if business.eklenme_tarihi else ""
            self.table.setItem(row, 7, QTableWidgetItem(tarih_text))
            
            # Business objesini row'a bağla
            self.table.item(row, 0).setData(Qt.UserRole, business)
    
    def update_il_filter(self):
        """İl filtresini güncelle"""
        current_il = self.il_filter.currentData()
        self.il_filter.clear()
        self.il_filter.addItem("Tümü", "")
        
        # Unique iller
        iller = set()
        for business in self.current_businesses:
            if business.il:
                iller.add(business.il)
        
        for il in sorted(iller):
            self.il_filter.addItem(il, il)
        
        # Önceki seçimi geri yükle
        if current_il:
            index = self.il_filter.findData(current_il)
            if index >= 0:
                self.il_filter.setCurrentIndex(index)
    
    def apply_filters(self):
        """Filtreleri uygula - Thread-safe"""
        try:
            # Önceki worker'ı durdur
            if self.data_loader and self.data_loader.isRunning():
                self.data_loader.stop()
                self.data_loader.wait(3000)
            
            filters = {}
            
            # Arama
            search_text = self.search_input.text().strip()
            if search_text:
                filters['isim'] = search_text
            
            # İl
            il = self.il_filter.currentData()
            if il:
                filters['il'] = il
            
            # Durum
            durum = self.durum_filter.currentData()
            if durum >= 0:
                filters['durum'] = durum
            
            # Telefon
            if self.telefon_filter.isChecked():
                filters['telefon_var'] = True
            
            # Yeni worker oluştur
            self.data_loader = DataLoaderWorker(filters=filters, limit=1000)
            
            # Sinyalleri bağla
            self.data_loader.data_loaded.connect(self.on_data_loaded)
            self.data_loader.error_occurred.connect(self.on_data_error)
            self.data_loader.progress_updated.connect(self.on_progress_updated)
            
            # UI'ı güncelle
            self.filter_button.setEnabled(False)
            self.filter_button.setText("⏳ Filtreleniyor...")
            
            # Worker'ı başlat
            self.data_loader.start()
            
        except Exception as e:
            logger.error(f"Filtre uygulama hatası: {e}")
            show_error(f"Filtre hatası: {str(e)}")
            self.filter_button.setEnabled(True)
            self.filter_button.setText("🔍 Filtrele")
    
    def on_selection_changed(self):
        """Seçim değiştiğinde"""
        current_row = self.table.currentRow()
        
        if current_row >= 0:
            item = self.table.item(current_row, 0)
            if item:
                business = item.data(Qt.UserRole)
                self.selected_business = business
                self.show_business_details(business)
                self.make_customer_button.setEnabled(business.durum == 0)  # Sadece potansiyel müşteriler
                self.save_note_button.setEnabled(True)
        else:
            self.selected_business = None
            self.detail_text.clear()
            self.note_input.clear()
            self.make_customer_button.setEnabled(False)
            self.save_note_button.setEnabled(False)
    
    def show_business_details(self, business: Isletme):
        """İşletme detaylarını göster"""
        details = f"""
<h3>{business.isim or 'İsimsiz İşletme'}</h3>
<p><b>Kategori:</b> {business.kategori or 'Belirtilmemiş'}</p>
<p><b>Telefon:</b> {business.telefon or 'Yok'}</p>
<p><b>Adres:</b> {business.adres or 'Belirtilmemiş'}</p>
<p><b>Website:</b> {business.website or 'Yok'}</p>
<p><b>Çalışma Saatleri:</b> {business.calisma_saatleri or 'Belirtilmemiş'}</p>
<p><b>Puan:</b> {business.puan or 'Yok'} ({business.yorum_sayisi or 0} yorum)</p>
<p><b>Konum:</b> {business.il or ''} {business.ilce or ''}</p>
<p><b>Durum:</b> {'Müşteri' if business.durum == 1 else 'Potansiyel'}</p>
<p><b>Eklenme Tarihi:</b> {business.eklenme_tarihi.strftime('%Y-%m-%d %H:%M') if business.eklenme_tarihi else 'Bilinmiyor'}</p>
        """
        
        self.detail_text.setHtml(details)
        
        # Mevcut notları yükle
        self.note_input.setPlainText(business.notlar or "")
    
    def make_customer(self):
        """Seçili işletmeyi müşteri yap"""
        if not self.selected_business:
            return
        
        try:
            # İşletmeyi müşteri yap
            success = IsletmeManager.make_customer(self.selected_business.id)
            
            if success:
                # Tabloyu güncelle
                self.refresh_data()
                show_success(f"{self.selected_business.isim} müşteri yapıldı!")
                
                # Signal emit et
                self.customer_created.emit(self.selected_business.id)
            else:
                show_error("Müşteri yapma işlemi başarısız!")
                
        except Exception as e:
            logger.error(f"Müşteri yapma hatası: {e}")
            show_error(f"Müşteri yapma hatası: {str(e)}")
    
    def save_note(self):
        """Not kaydet"""
        if not self.selected_business:
            return
        
        try:
            # Notu güncelle
            self.selected_business.notlar = self.note_input.toPlainText()
            success = IsletmeManager.update(self.selected_business)
            
            if success:
                show_success("Not kaydedildi!")
            else:
                show_error("Not kaydetme başarısız!")
                
        except Exception as e:
            logger.error(f"Not kaydetme hatası: {e}")
            show_error(f"Not kaydetme hatası: {str(e)}")
    
    def export_to_excel(self):
        """Excel'e aktar"""
        try:
            from utils.excel_export import ExcelExporter
            from datetime import datetime
            
            exporter = ExcelExporter()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tum_isletmeler_{timestamp}"
            
            file_path = exporter.export_businesses(self.current_businesses, filename)
            show_success(f"Excel dosyası oluşturuldu: {file_path}")
            
        except Exception as e:
            logger.error(f"Excel export hatası: {e}")
            show_error(f"Excel export hatası: {str(e)}")
    
    def on_data_loaded(self, businesses):
        """Veri yükleme tamamlandığında"""
        try:
            self.current_businesses = businesses
            
            # Tabloyu güncelle
            self.update_table()
            
            # İl filtresini güncelle
            self.update_il_filter()
            
            show_info(f"{len(self.current_businesses)} işletme yüklendi")
            
        except Exception as e:
            logger.error(f"Veri yükleme callback hatası: {e}")
            show_error(f"Veri yükleme hatası: {str(e)}")
        finally:
            # UI'ı eski haline getir
            self.refresh_button.setEnabled(True)
            self.refresh_button.setText("🔄 Yenile")
            self.filter_button.setEnabled(True)
            self.filter_button.setText("🔍 Filtrele")
    
    def on_data_error(self, error_message):
        """Veri yükleme hatası"""
        logger.error(f"DataLoader hatası: {error_message}")
        show_error(f"Veri yükleme hatası: {error_message}")
        
        # UI'ı eski haline getir
        self.refresh_button.setEnabled(True)
        self.refresh_button.setText("🔄 Yenile")
        self.filter_button.setEnabled(True)
        self.filter_button.setText("🔍 Filtrele")
    
    def on_progress_updated(self, progress):
        """Progress güncellemesi"""
        # Progress bar yoksa sadece log
        logger.debug(f"Veri yükleme progress: {progress}%")
    
    def get_selected_business(self):
        """Seçili işletmeyi al"""
        return self.selected_business