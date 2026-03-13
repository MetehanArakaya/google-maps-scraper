"""
Constants for Google Maps Scraper Application
"""

# Application Constants
APP_NAME = "Google Maps Scraper"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Metehan"

# UI Constants
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
DEFAULT_SIDEBAR_WIDTH = 220
SIDEBAR_COLLAPSED_WIDTH = 60
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600

# Animation Constants
ANIMATION_DURATION = 300  # milliseconds
FADE_DURATION = 200
SLIDE_DURATION = 250

# Database Constants
DEFAULT_DB_HOST = "localhost"
DEFAULT_DB_PORT = 3306
DEFAULT_DB_USER = "root"
DEFAULT_DB_NAME = "google_maps_scraper"
MAX_CONNECTION_POOL_SIZE = 10
CONNECTION_TIMEOUT = 30  # seconds
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY = 1  # seconds

# Scraper Constants
DEFAULT_SCRAPER_LIMIT = 50
MIN_SCRAPER_LIMIT = 1
MAX_SCRAPER_LIMIT = 1000
DEFAULT_DELAY_MIN = 2  # seconds
DEFAULT_DELAY_MAX = 5  # seconds
MIN_DELAY = 1
MAX_DELAY = 60
DEFAULT_BATCH_SIZE = 1000
MEMORY_BATCH_SIZE = 500
MAX_PROXY_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Validation Constants
MIN_SECTOR_LENGTH = 2
MAX_SECTOR_LENGTH = 100
MAX_USER_AGENT_LENGTH = 500
MAX_DB_HOST_LENGTH = 255
MAX_DB_USER_LENGTH = 32
MAX_DB_NAME_LENGTH = 64

# File Constants
EXCEL_BATCH_SIZE = 1000
MAX_LOG_FILE_SIZE = 10  # MB
DEFAULT_MAX_LOG_FILES = 5
EXPORT_DIR = "exports"
LOGS_DIR = "logs"
CONFIG_FILE = "config.json"

# UI Colors (for programmatic use)
PRIMARY_COLOR = "#0078d4"
SUCCESS_COLOR = "#107c10"
WARNING_COLOR = "#ff8c00"
ERROR_COLOR = "#d13438"
SECONDARY_COLOR = "#6c757d"

# Timeout Constants
WEBDRIVER_TIMEOUT = 30  # seconds
ELEMENT_WAIT_TIMEOUT = 10  # seconds
PAGE_LOAD_TIMEOUT = 30  # seconds
SCRIPT_TIMEOUT = 30  # seconds

# Google Maps Specific
GOOGLE_MAPS_BASE_URL = "https://www.google.com/maps"
SCROLL_PAUSE_TIME = 2  # seconds
MAX_SCROLL_ATTEMPTS = 50
ELEMENT_LOAD_WAIT = 3  # seconds

# Thread Constants
THREAD_POOL_SIZE = 4
WORKER_TIMEOUT = 3000  # milliseconds
DATA_LOADER_TIMEOUT = 5000  # milliseconds

# Excel Export Constants
EXCEL_HEADER_COLOR = "366092"
EXCEL_HEADER_FONT_COLOR = "FFFFFF"
EXCEL_DATA_FONT_SIZE = 10
EXCEL_HEADER_FONT_SIZE = 11
MAX_EXCEL_ROWS = 1048576  # Excel limit

# Network Constants
HTTP_TIMEOUT = 30  # seconds
MAX_REDIRECTS = 5
USER_AGENT_DEFAULT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Regex Patterns
PHONE_PATTERN = r'[\+]?[1-9]?[\d\s\-\(\)]{7,15}'
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
URL_PATTERN = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
IP_PATTERN = r'^(\d{1,3}\.){3}\d{1,3}$'
DOMAIN_PATTERN = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
SECTOR_PATTERN = r'^[a-zA-ZğüşıöçĞÜŞİÖÇ0-9\s\-]+$'
DB_NAME_PATTERN = r'^[a-zA-Z0-9_]+$'

# Status Codes
STATUS_POTENTIAL = 0
STATUS_CUSTOMER = 1
STATUS_BLACKLISTED = -1

# Log Levels
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Turkish Cities (sample)
TURKISH_CITIES = [
    "İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Adana", "Konya",
    "Gaziantep", "Mersin", "Diyarbakır", "Kayseri", "Eskişehir", "Urfa",
    "Malatya", "Erzurum", "Van", "Batman", "Elazığ", "İzmit", "Manisa",
    "Samsun", "Kahramanmaraş", "Denizli", "Muğla", "Tekirdağ", "Balıkesir",
    "Aydın", "Hatay", "Çorum", "Kütahya", "Sakarya", "Afyon", "Uşak",
    "Isparta", "Düzce", "Çanakkale", "Zonguldak", "Kastamonu", "Bolu",
    "Yalova", "Karabük", "Kırklareli", "Bilecik", "Kırşehir", "Karaman",
    "Kırıkkale", "Nevşehir", "Niğde", "Aksaray", "Yozgat", "Sivas",
    "Tokat", "Amasya", "Çankırı", "Sinop", "Ordu", "Giresun", "Trabzon",
    "Rize", "Artvin", "Gümüşhane", "Bayburt", "Erzincan", "Tunceli",
    "Bingöl", "Muş", "Bitlis", "Hakkari", "Şırnak", "Mardin", "Siirt",
    "Adıyaman", "Kilis", "Osmaniye", "Edirne"
]

# District Data (sample for major cities)
CITY_DISTRICTS = {
    "İstanbul": [
        "Kadıköy", "Beşiktaş", "Şişli", "Beyoğlu", "Fatih", "Üsküdar", 
        "Bakırköy", "Zeytinburnu", "Maltepe", "Kartal", "Pendik", "Tuzla",
        "Ataşehir", "Ümraniye", "Çekmeköy", "Sancaktepe", "Sultanbeyli"
    ],
    "Ankara": [
        "Çankaya", "Keçiören", "Yenimahalle", "Mamak", "Sincan", 
        "Altındağ", "Etimesgut", "Gölbaşı", "Pursaklar", "Elmadağ"
    ],
    "İzmir": [
        "Konak", "Karşıyaka", "Bornova", "Buca", "Bayraklı", 
        "Gaziemir", "Balçova", "Narlıdere", "Güzelbahçe", "Çiğli"
    ],
    "Konya": [
        "Meram", "Karatay", "Selçuklu", "Akşehir", "Beyşehir", 
        "Cihanbeyli", "Ereğli", "Ilgın", "Kulu", "Seydişehir"
    ]
}

# File Extensions
ALLOWED_PROXY_EXTENSIONS = ['.txt']
ALLOWED_WEBDRIVER_EXTENSIONS = ['.exe'] if __import__('platform').system() == 'Windows' else ['']
EXCEL_EXTENSIONS = ['.xlsx', '.xls']
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']

# Error Messages
ERROR_MESSAGES = {
    'INVALID_SECTOR': "Sektör alanında geçersiz karakter bulunuyor!",
    'EMPTY_SECTOR': "Sektör alanı boş olamaz!",
    'SECTOR_TOO_SHORT': "Sektör en az 2 karakter olmalıdır!",
    'SECTOR_TOO_LONG': "Sektör en fazla 100 karakter olabilir!",
    'INVALID_LIMIT': "Limit 1-1000 arasında olmalıdır!",
    'INVALID_DELAY': "Minimum delay maximum delay'den büyük olamaz!",
    'FILE_NOT_FOUND': "Dosya bulunamadı: {path}",
    'INVALID_FILE_TYPE': "Geçersiz dosya türü: {extension}",
    'DB_CONNECTION_FAILED': "Veritabanı bağlantısı başarısız!",
    'INVALID_HOST': "Geçersiz host formatı!",
    'EMPTY_DB_USER': "Database kullanıcı adı boş olamaz!",
    'EMPTY_DB_NAME': "Database adı boş olamaz!",
    'INVALID_DB_NAME': "Database adı sadece harf, rakam ve alt çizgi içerebilir!"
}

# Success Messages
SUCCESS_MESSAGES = {
    'SETTINGS_SAVED': "Ayarlar kaydedildi!",
    'DATA_LOADED': "{count} işletme yüklendi",
    'SCRAPING_STARTED': "Scraping başlatıldı: {query}",
    'SCRAPING_COMPLETED': "Scraping tamamlandı!",
    'EXCEL_EXPORTED': "Excel dosyası oluşturuldu: {path}",
    'CUSTOMER_CREATED': "{name} müşteri yapıldı!",
    'NOTE_SAVED': "Not kaydedildi!",
    'DB_SCHEMA_CREATED': "Veritabanı şeması oluşturuldu!"
}

# Info Messages
INFO_MESSAGES = {
    'FILTER_APPLIED': "Filtre uygulandı: {count} sonuç",
    'DB_CONNECTION_TESTING': "Veritabanı bağlantısı test ediliyor...",
    'SCRAPING_STOPPING': "Scraping durduruluyor...",
    'LOG_CLEARED': "Log temizlendi"
}