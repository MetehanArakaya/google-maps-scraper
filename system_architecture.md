# Google Maps Scraper - Sistem Mimarisi

## Uygulama Genel Yapısı

```mermaid
graph TB
    A[Ana Uygulama - main.py] --> B[UI Katmanı - PySide6]
    A --> C[Scraper Katmanı - Selenium]
    A --> D[Database Katmanı - MySQL]
    A --> E[Utils Katmanı - Yardımcı Fonksiyonlar]
    
    B --> B1[Sidebar - Animasyonlu Menü]
    B --> B2[Scraper Panel]
    B --> B3[Kullanıcılar Panel]
    B --> B4[Müşteriler Panel]
    B --> B5[Ayarlar Panel]
    
    C --> C1[Google Maps Navigator]
    C --> C2[Business Data Extractor]
    C --> C3[QThread Worker]
    C --> C4[Proxy Manager]
    
    D --> D1[isletmeler Tablosu]
    D --> D2[musteriler Tablosu]
    D --> D3[blacklist Tablosu]
    
    E --> E1[Excel Export]
    E --> E2[Log System]
    E --> E3[Toast Notifications]
    E --> E4[Config Manager]
```

## Veri Akışı

```mermaid
sequenceDiagram
    participant U as Kullanıcı
    participant UI as UI Panel
    participant S as Scraper Thread
    participant GM as Google Maps
    participant DB as MySQL DB
    participant EX as Excel Export
    
    U->>UI: Scraping parametrelerini gir
    UI->>S: Scraping işlemini başlat
    S->>GM: Selenium ile arama yap
    GM->>S: İşletme verilerini döndür
    S->>DB: Verileri kaydet/güncelle
    S->>EX: Excel dosyası oluştur
    S->>UI: Progress ve log güncelle
    UI->>U: Sonuçları göster
```

## Klasör Yapısı

```
google_maps_scraper/
├── main.py                 # Ana uygulama giriş noktası
├── requirements.txt        # Python bağımlılıkları
├── config.json            # Uygulama ayarları
├── ui/                    # PySide6 UI bileşenleri
│   ├── __init__.py
│   ├── main_window.py     # Ana pencere
│   ├── sidebar.py         # Sidebar bileşeni
│   ├── panels/            # Panel bileşenleri
│   │   ├── scraper_panel.py
│   │   ├── users_panel.py
│   │   ├── customers_panel.py
│   │   └── settings_panel.py
│   └── styles/            # QSS stil dosyaları
│       └── dark_theme.qss
├── scraper/               # Scraping modülü
│   ├── __init__.py
│   ├── google_maps_scraper.py
│   ├── scraper_worker.py  # QThread worker
│   └── proxy_manager.py
├── database/              # Veritabanı modülü
│   ├── __init__.py
│   ├── connection.py      # DB bağlantısı
│   ├── models.py          # Veri modelleri
│   └── schema.sql         # Tablo şemaları
├── utils/                 # Yardımcı fonksiyonlar
│   ├── __init__.py
│   ├── excel_export.py
│   ├── logger.py
│   ├── toast.py
│   └── config.py
└── assets/                # Görsel kaynaklar
    ├── icons/
    └── images/
```

## Teknik Detaylar

### Gerekli Python Paketleri
- PySide6 (GUI framework)
- selenium (Web scraping)
- mysql-connector-python (MySQL bağlantısı)
- openpyxl (Excel işlemleri)
- requests (HTTP istekleri)
- beautifulsoup4 (HTML parsing)

### Önemli Özellikler
1. **Sidebar Animasyonu**: QPropertyAnimation ile 220px ↔ 60px geçiş
2. **Dark Theme**: Tam koyu tema QSS ile
3. **Thread Safety**: Scraping işlemleri QThread'de
4. **Model/View**: Tablolar için Qt Model/View mimarisi
5. **Toast Notifications**: Sağ üst köşede bildirimler
6. **Responsive Design**: Pencere boyutuna uyum