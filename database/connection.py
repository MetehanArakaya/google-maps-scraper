"""
MySQL Database Connection Manager with Thread-Safe Connection Pool
"""
import mysql.connector
from mysql.connector import Error, pooling
import logging
from typing import Optional, Dict, Any
import os
from contextlib import contextmanager
from threading import Lock
import time

class DatabaseConnectionPool:
    """Thread-safe veritabanı bağlantı havuzu yöneticisi"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Database connection pool manager başlat"""
        if hasattr(self, 'initialized'):
            return
            
        self.pool = None
        self.config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '',
            'database': 'google_maps_scraper',
            'charset': 'utf8mb4',
            'autocommit': True,
            'raise_on_warnings': True,
            'sql_mode': 'TRADITIONAL',
            'use_unicode': True
        }
        self.pool_name = "google_maps_scraper_pool"
        self.pool_size = 5
        self.max_overflow = 10
        self.initialized = False
        self.logger = logging.getLogger(__name__)
        self.last_error = None
        self._last_insert_id = None
        
        # Pool'u başlat
        self.create_pool()
        
        self.logger.info("Database connection pool oluşturuldu")
    
    def update_config(self, config: Dict[str, Any]):
        """Konfigürasyonu güncelle"""
        self.config.update(config)
        # Pool'u yeniden oluştur
        self.create_pool()
    
    def create_pool(self) -> bool:
        """Thread-safe bağlantı havuzunu oluştur"""
        try:
            with self._lock:
                if self.pool:
                    # Mevcut pool'u kapat
                    try:
                        # Pool'daki tüm bağlantıları kapat
                        pass  # mysql.connector pool otomatik olarak temizlenir
                    except:
                        pass
                
                pool_config = self.config.copy()
                pool_config.update({
                    'pool_name': self.pool_name,
                    'pool_size': self.pool_size,
                    'pool_reset_session': True
                })
                
                self.pool = pooling.MySQLConnectionPool(**pool_config)
                self.initialized = True
                self.logger.info(f"Bağlantı havuzu oluşturuldu: {self.pool_name} (boyut: {self.pool_size})")
                return True
                
        except Error as e:
            self.logger.error(f"Bağlantı havuzu oluşturma hatası: {e}")
            self.initialized = False
            return False
    
    @contextmanager
    def get_connection(self):
        """Thread-safe bağlantı context manager"""
        connection = None
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                if not self.initialized:
                    if not self.create_pool():
                        raise Exception("Bağlantı havuzu oluşturulamadı")
                
                connection = self.pool.get_connection()
                
                # Bağlantı sağlığını kontrol et
                if not connection.is_connected():
                    connection.reconnect(attempts=3, delay=1)
                
                yield connection
                return
                
            except Error as e:
                self.logger.warning(f"Bağlantı alma denemesi {attempt + 1} başarısız: {e}")
                if connection:
                    try:
                        connection.rollback()
                        connection.close()
                    except:
                        pass
                    connection = None
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self.logger.error(f"Bağlantı alma hatası (tüm denemeler başarısız): {e}")
                    raise
            finally:
                if connection and connection.is_connected():
                    connection.close()
    
    def execute_query(self, query: str, params: tuple = None, fetch_one: bool = False) -> Optional[Any]:
        """Thread-safe parameterized SQL sorgusu çalıştır"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor(dictionary=True, prepared=True)
                cursor.execute(query, params or ())
                
                if query.strip().upper().startswith('SELECT'):
                    if fetch_one:
                        result = cursor.fetchone()
                    else:
                        result = cursor.fetchall()
                    cursor.close()
                    return result
                else:
                    connection.commit()
                    affected_rows = cursor.rowcount
                    last_id = cursor.lastrowid
                    cursor.close()
                    
                    # Store last insert id for later retrieval
                    self._last_insert_id = last_id
                    
                    return {'affected_rows': affected_rows, 'last_id': last_id}
                    
        except Error as e:
            self.logger.error(f"Sorgu çalıştırma hatası: {e}")
            self.logger.error(f"Query: {query}")
            self.logger.error(f"Params: {params}")
            self.last_error = str(e)
            return None
    
    def execute_update(self, query: str, params: tuple = None) -> bool:
        """Thread-safe parameterized UPDATE/INSERT/DELETE sorgusu"""
        try:
            result = self.execute_query(query, params)
            if result and isinstance(result, dict):
                self.last_error = None
                return True
            return False
        except Exception as e:
            self.logger.error(f"Güncelleme hatası: {e}")
            self.last_error = str(e)
            return False
    
    def execute_many(self, query: str, params_list: list) -> bool:
        """Thread-safe çoklu parameterized sorgu çalıştır"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor(prepared=True)
                cursor.executemany(query, params_list)
                connection.commit()
                self._last_insert_id = cursor.lastrowid
                cursor.close()
                return True
                
        except Error as e:
            self.logger.error(f"Çoklu sorgu hatası: {e}")
            self.last_error = str(e)
            return False
    
    def test_connection(self) -> bool:
        """Bağlantıyı test et"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                return result is not None
                
        except Error as e:
            self.logger.error(f"Bağlantı test hatası: {e}")
            return False
    
    def get_last_insert_id(self) -> Optional[int]:
        """Son eklenen kaydın ID'sini al"""
        return self._last_insert_id
    
    def create_database_schema(self) -> bool:
        """Veritabanı şemasını oluştur"""
        schema_queries = [
            """
            CREATE DATABASE IF NOT EXISTS google_maps_scraper 
            CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """,
            "USE google_maps_scraper",
            """
            CREATE TABLE IF NOT EXISTS isletmeler (
                id INT AUTO_INCREMENT PRIMARY KEY,
                google_id VARCHAR(255) UNIQUE NOT NULL,
                isim VARCHAR(500) NOT NULL,
                kategori VARCHAR(255),
                telefon VARCHAR(50),
                adres TEXT,
                website VARCHAR(500),
                calisma_saatleri TEXT,
                puan DECIMAL(2,1),
                yorum_sayisi INT DEFAULT 0,
                yogunluk_bilgisi VARCHAR(255),
                konum_linki TEXT,
                resim_url TEXT,
                il VARCHAR(100),
                ilce VARCHAR(100),
                durum TINYINT DEFAULT 0 COMMENT '0=potansiyel, 1=müşteri',
                notlar TEXT,
                source_url TEXT,
                eklenme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                INDEX idx_google_id (google_id),
                INDEX idx_il_ilce (il, ilce),
                INDEX idx_kategori (kategori),
                INDEX idx_durum (durum),
                INDEX idx_eklenme_tarihi (eklenme_tarihi)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            """
            CREATE TABLE IF NOT EXISTS musteriler (
                id INT AUTO_INCREMENT PRIMARY KEY,
                isletme_id INT NOT NULL,
                paket VARCHAR(255),
                odeme_durumu ENUM('beklemede', 'odendi', 'iptal') DEFAULT 'beklemede',
                iletisim_tarihi DATE,
                notlar TEXT,
                kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (isletme_id) REFERENCES isletmeler(id) ON DELETE CASCADE,
                INDEX idx_isletme_id (isletme_id),
                INDEX idx_odeme_durumu (odeme_durumu),
                INDEX idx_kayit_tarihi (kayit_tarihi)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            """
            CREATE TABLE IF NOT EXISTS blacklist (
                id INT AUTO_INCREMENT PRIMARY KEY,
                google_id VARCHAR(255),
                source_url TEXT,
                sebep VARCHAR(500),
                tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                INDEX idx_google_id (google_id),
                INDEX idx_tarih (tarih)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        ]
        
        try:
            # Veritabanı oluşturmak için root bağlantısı
            temp_config = self.config.copy()
            temp_config.pop('database', None)
            
            temp_connection = mysql.connector.connect(**temp_config)
            cursor = temp_connection.cursor()
            
            for query in schema_queries:
                cursor.execute(query)
            
            temp_connection.commit()
            cursor.close()
            temp_connection.close()
            
            self.logger.info("Veritabanı şeması başarıyla oluşturuldu")
            return True
            
        except Error as e:
            self.logger.error(f"Şema oluşturma hatası: {e}")
            return False

# Backward compatibility için eski sınıf
class DatabaseConnection(DatabaseConnectionPool):
    """Backward compatibility için eski interface"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__()
        if config:
            self.update_config(config)
    
    def connect(self) -> bool:
        """Bağlantıyı test et"""
        return self.test_connection()
    
    def disconnect(self):
        """Pool tabanlı sistemde gerekli değil"""
        pass
    
    def is_connected(self) -> bool:
        """Pool durumunu kontrol et"""
        return self.initialized
    
    @contextmanager
    def get_cursor(self, dictionary=True):
        """Eski cursor interface"""
        with self.get_connection() as connection:
            cursor = connection.cursor(dictionary=dictionary)
            try:
                yield cursor
            finally:
                cursor.close()

# Global database instance
db = DatabaseConnectionPool()