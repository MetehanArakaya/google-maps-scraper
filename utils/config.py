"""
Configuration Management for Google Maps Scraper
"""
import json
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """Konfigürasyon yönetici sınıfı"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        Config manager oluştur
        
        Args:
            config_file: Konfigürasyon dosyası yolu
        """
        self.config_file = config_file
        self.config_data = {}
        
        # Varsayılan ayarlar
        self.default_config = {
            "database": {
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "password": "",
                "database": "google_maps_scraper",
                "charset": "utf8mb4",
                "autocommit": True
            },
            "scraper": {
                "delay_min": 2,
                "delay_max": 5,
                "headless": False,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "webdriver_path": "",
                "proxy_file": "",
                "default_limit": 50,
                "export_excel": True
            },
            "ui": {
                "theme": "dark",
                "sidebar_width": 220,
                "sidebar_collapsed_width": 60,
                "window_width": 1200,
                "window_height": 800,
                "font_family": "Segoe UI",
                "font_size": 10
            },
            "logging": {
                "level": "INFO",
                "max_log_files": 5,
                "max_file_size_mb": 10
            },
            "export": {
                "output_directory": "exports",
                "auto_open_excel": False,
                "include_statistics": True
            }
        }
        
        # Konfigürasyonu yükle
        self.load_config()
    
    def load_config(self):
        """Konfigürasyonu dosyadan güvenli şekilde yükle"""
        try:
            if os.path.exists(self.config_file):
                # Dosya boyutunu kontrol et (max 1MB)
                file_size = os.path.getsize(self.config_file)
                if file_size > 1024 * 1024:  # 1MB
                    logger.error(f"Konfigürasyon dosyası çok büyük: {file_size} bytes")
                    self._use_default_config()
                    return
                
                # Backup oluştur
                self._create_config_backup()
                
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # JSON formatını validate et
                    if not self._validate_json_format(content):
                        logger.error("Geçersiz JSON formatı tespit edildi")
                        self._restore_from_backup()
                        return
                    
                    loaded_config = json.loads(content)
                    
                    # Konfigürasyon yapısını validate et
                    if not self._validate_config_structure(loaded_config):
                        logger.error("Geçersiz konfigürasyon yapısı")
                        self._restore_from_backup()
                        return
                
                # Varsayılan ayarları güncelle
                self.config_data = self._merge_configs(self.default_config, loaded_config)
                logger.info("Konfigürasyon dosyası başarıyla yüklendi")
            else:
                # Varsayılan konfigürasyonu kullan
                self._use_default_config()
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse hatası: {e}")
            self._restore_from_backup()
        except Exception as e:
            logger.error(f"Konfigürasyon yükleme hatası: {e}")
            self._use_default_config()
    
    def _validate_json_format(self, content: str) -> bool:
        """JSON formatını validate et"""
        try:
            json.loads(content)
            return True
        except json.JSONDecodeError:
            return False
    
    def _validate_config_structure(self, config: dict) -> bool:
        """Konfigürasyon yapısını validate et"""
        try:
            # Temel bölümlerin varlığını kontrol et
            required_sections = ['database', 'scraper', 'ui', 'logging', 'export']
            for section in required_sections:
                if section not in config:
                    logger.warning(f"Eksik konfigürasyon bölümü: {section}")
                    # Eksik bölümü varsayılan ile doldur
                    config[section] = self.default_config.get(section, {})
            
            # Database ayarlarını validate et
            db_config = config.get('database', {})
            if not isinstance(db_config.get('port'), int):
                logger.warning("Geçersiz database port değeri")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Konfigürasyon validation hatası: {e}")
            return False
    
    def _create_config_backup(self):
        """Konfigürasyon backup'ı oluştur"""
        try:
            if os.path.exists(self.config_file):
                backup_file = f"{self.config_file}.backup"
                import shutil
                shutil.copy2(self.config_file, backup_file)
                logger.debug("Konfigürasyon backup'ı oluşturuldu")
        except Exception as e:
            logger.warning(f"Backup oluşturma hatası: {e}")
    
    def _restore_from_backup(self):
        """Backup'tan konfigürasyonu geri yükle"""
        try:
            backup_file = f"{self.config_file}.backup"
            if os.path.exists(backup_file):
                import shutil
                shutil.copy2(backup_file, self.config_file)
                logger.info("Konfigürasyon backup'tan geri yüklendi")
                # Tekrar yüklemeyi dene
                self.load_config()
            else:
                self._use_default_config()
        except Exception as e:
            logger.error(f"Backup geri yükleme hatası: {e}")
            self._use_default_config()
    
    def _use_default_config(self):
        """Varsayılan konfigürasyonu kullan"""
        self.config_data = self.default_config.copy()
        self.save_config()
        logger.info("Varsayılan konfigürasyon oluşturuldu")
    
    def save_config(self):
        """Konfigürasyonu dosyaya kaydet"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
            logger.info("Konfigürasyon kaydedildi")
            return True
            
        except Exception as e:
            logger.error(f"Konfigürasyon kaydetme hatası: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Konfigürasyon değeri al
        
        Args:
            key: Nokta notasyonu ile anahtar (örn: "database.host")
            default: Varsayılan değer
            
        Returns:
            Konfigürasyon değeri
        """
        keys = key.split('.')
        value = self.config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        Konfigürasyon değeri ayarla
        
        Args:
            key: Nokta notasyonu ile anahtar
            value: Yeni değer
        """
        keys = key.split('.')
        config = self.config_data
        
        # Son anahtar hariç tüm anahtarları dolaş
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Son anahtarı ayarla
        config[keys[-1]] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Konfigürasyon bölümünü al
        
        Args:
            section: Bölüm adı
            
        Returns:
            Bölüm verileri
        """
        return self.config_data.get(section, {})
    
    def set_section(self, section: str, data: Dict[str, Any]):
        """
        Konfigürasyon bölümünü ayarla
        
        Args:
            section: Bölüm adı
            data: Bölüm verileri
        """
        self.config_data[section] = data
    
    def reset_to_defaults(self):
        """Varsayılan ayarlara sıfırla"""
        self.config_data = self.default_config.copy()
        self.save_config()
        logger.info("Konfigürasyon varsayılan ayarlara sıfırlandı")
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """İki konfigürasyonu birleştir"""
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def validate_config(self) -> Dict[str, list]:
        """Konfigürasyonu doğrula"""
        errors = {}
        
        # Database ayarları
        db_config = self.get_section('database')
        db_errors = []
        
        if not db_config.get('host'):
            db_errors.append("Host boş olamaz")
        
        if not isinstance(db_config.get('port'), int) or db_config.get('port') <= 0:
            db_errors.append("Port geçerli bir sayı olmalı")
        
        if not db_config.get('user'):
            db_errors.append("Kullanıcı adı boş olamaz")
        
        if db_errors:
            errors['database'] = db_errors
        
        # Scraper ayarları
        scraper_config = self.get_section('scraper')
        scraper_errors = []
        
        delay_min = scraper_config.get('delay_min', 0)
        delay_max = scraper_config.get('delay_max', 0)
        
        if not isinstance(delay_min, (int, float)) or delay_min < 0:
            scraper_errors.append("Minimum delay 0 veya daha büyük olmalı")
        
        if not isinstance(delay_max, (int, float)) or delay_max < delay_min:
            scraper_errors.append("Maximum delay minimum delay'den büyük olmalı")
        
        if scraper_errors:
            errors['scraper'] = scraper_errors
        
        return errors
    
    def export_config(self, file_path: str) -> bool:
        """Konfigürasyonu dışa aktar"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Konfigürasyon dışa aktarma hatası: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """Konfigürasyonu içe aktar"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Doğrula
            temp_config = self.config_data
            self.config_data = self._merge_configs(self.default_config, imported_config)
            
            validation_errors = self.validate_config()
            if validation_errors:
                # Hatalı ise eski konfigürasyonu geri yükle
                self.config_data = temp_config
                logger.error(f"İçe aktarılan konfigürasyon geçersiz: {validation_errors}")
                return False
            
            self.save_config()
            logger.info("Konfigürasyon başarıyla içe aktarıldı")
            return True
            
        except Exception as e:
            logger.error(f"Konfigürasyon içe aktarma hatası: {e}")
            return False

# Global config manager instance
_config_manager: Optional[ConfigManager] = None

def init_config(config_file: str = "config.json") -> ConfigManager:
    """Global config manager'ı başlat"""
    global _config_manager
    _config_manager = ConfigManager(config_file)
    return _config_manager

def get_config() -> Optional[ConfigManager]:
    """Global config manager'ı al"""
    return _config_manager

def get_setting(key: str, default: Any = None) -> Any:
    """Ayar değeri al"""
    if _config_manager:
        return _config_manager.get(key, default)
    return default

def set_setting(key: str, value: Any):
    """Ayar değeri belirle"""
    if _config_manager:
        _config_manager.set(key, value)

def save_settings():
    """Ayarları kaydet"""
    if _config_manager:
        return _config_manager.save_config()
    return False