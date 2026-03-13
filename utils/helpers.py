"""
Helper functions for Google Maps Scraper Application
"""
import os
import re
from typing import Optional, List, Dict, Any
from utils.constants import (
    IP_PATTERN, DOMAIN_PATTERN, PHONE_PATTERN, EMAIL_PATTERN, URL_PATTERN,
    ALLOWED_PROXY_EXTENSIONS, ALLOWED_WEBDRIVER_EXTENSIONS, MAX_PROXY_FILE_SIZE
)

def validate_file_path(file_path: str, allowed_extensions: List[str] = None, 
                      max_size: int = None) -> tuple[bool, str]:
    """
    Dosya yolu validasyonu
    
    Args:
        file_path: Dosya yolu
        allowed_extensions: İzin verilen uzantılar
        max_size: Maksimum dosya boyutu (bytes)
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not file_path or not file_path.strip():
        return True, ""  # Boş dosya yolu geçerli (opsiyonel)
    
    file_path = file_path.strip()
    
    # Dosya var mı?
    if not os.path.exists(file_path):
        return False, f"Dosya bulunamadı: {file_path}"
    
    # Dosya mı klasör mü?
    if not os.path.isfile(file_path):
        return False, f"Belirtilen yol bir dosya değil: {file_path}"
    
    # Uzantı kontrolü
    if allowed_extensions:
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in allowed_extensions:
            return False, f"Geçersiz dosya uzantısı. İzin verilen: {', '.join(allowed_extensions)}"
    
    # Boyut kontrolü
    if max_size:
        try:
            file_size = os.path.getsize(file_path)
            if file_size > max_size:
                max_mb = max_size // (1024 * 1024)
                return False, f"Dosya çok büyük (max {max_mb}MB)"
        except OSError:
            return False, "Dosya boyutu okunamıyor"
    
    return True, ""

def validate_proxy_file(file_path: str) -> tuple[bool, str]:
    """Proxy dosyası validasyonu"""
    return validate_file_path(file_path, ALLOWED_PROXY_EXTENSIONS, MAX_PROXY_FILE_SIZE)

def validate_webdriver_file(file_path: str) -> tuple[bool, str]:
    """WebDriver dosyası validasyonu"""
    return validate_file_path(file_path, ALLOWED_WEBDRIVER_EXTENSIONS)

def validate_host(host: str) -> bool:
    """
    Host validasyonu (IP veya domain)
    
    Args:
        host: Host adresi
    
    Returns:
        bool: Geçerli mi?
    """
    if not host or not host.strip():
        return False
    
    host = host.strip()
    
    # Localhost kontrolü
    if host.lower() == 'localhost':
        return True
    
    # IP adresi kontrolü
    if re.match(IP_PATTERN, host):
        # IP adresinin geçerli aralıkta olup olmadığını kontrol et
        parts = host.split('.')
        for part in parts:
            if not (0 <= int(part) <= 255):
                return False
        return True
    
    # Domain kontrolü
    return bool(re.match(DOMAIN_PATTERN, host))

def validate_database_name(db_name: str) -> bool:
    """
    Database adı validasyonu
    
    Args:
        db_name: Database adı
    
    Returns:
        bool: Geçerli mi?
    """
    if not db_name or not db_name.strip():
        return False
    
    db_name = db_name.strip()
    
    # Uzunluk kontrolü
    if len(db_name) > 64:
        return False
    
    # Karakter kontrolü (sadece harf, rakam, alt çizgi)
    return bool(re.match(r'^[a-zA-Z0-9_]+$', db_name))

def validate_text_length(text: str, min_length: int = 0, max_length: int = None) -> tuple[bool, str]:
    """
    Metin uzunluğu validasyonu
    
    Args:
        text: Kontrol edilecek metin
        min_length: Minimum uzunluk
        max_length: Maksimum uzunluk
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not text:
        text = ""
    
    text = text.strip()
    
    if len(text) < min_length:
        return False, f"En az {min_length} karakter olmalıdır"
    
    if max_length and len(text) > max_length:
        return False, f"En fazla {max_length} karakter olabilir"
    
    return True, ""

def validate_pattern(text: str, pattern: str, error_message: str = "Geçersiz format") -> tuple[bool, str]:
    """
    Regex pattern validasyonu
    
    Args:
        text: Kontrol edilecek metin
        pattern: Regex pattern
        error_message: Hata mesajı
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not text or not text.strip():
        return True, ""  # Boş metin geçerli kabul edilir
    
    text = text.strip()
    
    if not re.match(pattern, text):
        return False, error_message
    
    return True, ""

def extract_phone_numbers(text: str) -> List[str]:
    """
    Metinden telefon numaralarını çıkar
    
    Args:
        text: Aranacak metin
    
    Returns:
        List[str]: Bulunan telefon numaraları
    """
    if not text:
        return []
    
    phones = re.findall(PHONE_PATTERN, text)
    # Temizle ve normalize et
    cleaned_phones = []
    for phone in phones:
        # Sadece rakam ve + işareti bırak
        cleaned = re.sub(r'[^\d\+]', '', phone)
        if len(cleaned) >= 7:  # Minimum telefon uzunluğu
            cleaned_phones.append(cleaned)
    
    return list(set(cleaned_phones))  # Duplicate'ları kaldır

def extract_emails(text: str) -> List[str]:
    """
    Metinden email adreslerini çıkar
    
    Args:
        text: Aranacak metin
    
    Returns:
        List[str]: Bulunan email adresleri
    """
    if not text:
        return []
    
    emails = re.findall(EMAIL_PATTERN, text)
    return list(set(emails))  # Duplicate'ları kaldır

def extract_urls(text: str) -> List[str]:
    """
    Metinden URL'leri çıkar
    
    Args:
        text: Aranacak metin
    
    Returns:
        List[str]: Bulunan URL'ler
    """
    if not text:
        return []
    
    urls = re.findall(URL_PATTERN, text)
    return list(set(urls))  # Duplicate'ları kaldır

def sanitize_filename(filename: str) -> str:
    """
    Dosya adını güvenli hale getir
    
    Args:
        filename: Orijinal dosya adı
    
    Returns:
        str: Güvenli dosya adı
    """
    if not filename:
        return "untitled"
    
    # Geçersiz karakterleri kaldır
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Çoklu alt çizgileri tek alt çizgi yap
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Başta ve sonda alt çizgi varsa kaldır
    sanitized = sanitized.strip('_')
    
    # Boş ise varsayılan ad ver
    if not sanitized:
        sanitized = "untitled"
    
    return sanitized

def format_file_size(size_bytes: int) -> str:
    """
    Dosya boyutunu okunabilir formata çevir
    
    Args:
        size_bytes: Byte cinsinden boyut
    
    Returns:
        str: Formatlanmış boyut (örn: "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"

def create_directory_if_not_exists(directory: str) -> bool:
    """
    Klasör yoksa oluştur
    
    Args:
        directory: Klasör yolu
    
    Returns:
        bool: Başarılı mı?
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        return True
    except OSError:
        return False

def is_valid_range(min_val: int, max_val: int) -> bool:
    """
    Min-max aralığının geçerli olup olmadığını kontrol et
    
    Args:
        min_val: Minimum değer
        max_val: Maksimum değer
    
    Returns:
        bool: Geçerli mi?
    """
    return min_val <= max_val

def clamp_value(value: int, min_val: int, max_val: int) -> int:
    """
    Değeri belirtilen aralığa sınırla
    
    Args:
        value: Sınırlanacak değer
        min_val: Minimum değer
        max_val: Maksimum değer
    
    Returns:
        int: Sınırlanmış değer
    """
    return max(min_val, min(value, max_val))

def parse_delay_range(delay_str: str) -> tuple[int, int]:
    """
    Delay string'ini parse et (örn: "2-5" -> (2, 5))
    
    Args:
        delay_str: Delay string'i
    
    Returns:
        tuple: (min_delay, max_delay)
    """
    try:
        if '-' in delay_str:
            parts = delay_str.split('-')
            if len(parts) == 2:
                min_delay = int(parts[0].strip())
                max_delay = int(parts[1].strip())
                return min_delay, max_delay
        else:
            # Tek değer ise hem min hem max olarak kullan
            delay = int(delay_str.strip())
            return delay, delay
    except (ValueError, AttributeError):
        pass
    
    # Varsayılan değerler
    return 2, 5

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Metni belirtilen uzunlukta kes
    
    Args:
        text: Kesilecek metin
        max_length: Maksimum uzunluk
        suffix: Kesim sonrası eklenecek suffix
    
    Returns:
        str: Kesilmiş metin
    """
    if not text or len(text) <= max_length:
        return text or ""
    
    return text[:max_length - len(suffix)] + suffix

def safe_int_conversion(value: Any, default: int = 0) -> int:
    """
    Güvenli integer dönüşümü
    
    Args:
        value: Dönüştürülecek değer
        default: Varsayılan değer
    
    Returns:
        int: Dönüştürülmüş değer
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """
    Güvenli float dönüşümü
    
    Args:
        value: Dönüştürülecek değer
        default: Varsayılan değer
    
    Returns:
        float: Dönüştürülmüş değer
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Birden fazla dictionary'yi birleştir
    
    Args:
        *dicts: Birleştirilecek dictionary'ler
    
    Returns:
        Dict[str, Any]: Birleştirilmiş dictionary
    """
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result

def get_nested_value(data: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Nested dictionary'den değer al (örn: "user.profile.name")
    
    Args:
        data: Dictionary
        key_path: Nokta ile ayrılmış key path
        default: Varsayılan değer
    
    Returns:
        Any: Bulunan değer veya varsayılan
    """
    try:
        keys = key_path.split('.')
        value = data
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default