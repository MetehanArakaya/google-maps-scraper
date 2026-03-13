-- Google Maps Scraper Database Schema
-- MySQL Database Schema

CREATE DATABASE IF NOT EXISTS google_maps_scraper 
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE google_maps_scraper;

-- İşletmeler tablosu
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Müşteriler tablosu
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Blacklist tablosu
CREATE TABLE IF NOT EXISTS blacklist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    google_id VARCHAR(255),
    source_url TEXT,
    sebep VARCHAR(500),
    tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_google_id (google_id),
    INDEX idx_tarih (tarih)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Trigger: İşletme müşteri yapıldığında durum güncelle
DELIMITER //
CREATE TRIGGER tr_musteri_durum_guncelle 
AFTER INSERT ON musteriler
FOR EACH ROW
BEGIN
    UPDATE isletmeler 
    SET durum = 1 
    WHERE id = NEW.isletme_id;
END//
DELIMITER ;

-- Trigger: Müşteri silindiğinde durum güncelle
DELIMITER //
CREATE TRIGGER tr_musteri_silme_durum_guncelle 
AFTER DELETE ON musteriler
FOR EACH ROW
BEGIN
    UPDATE isletmeler 
    SET durum = 0 
    WHERE id = OLD.isletme_id;
END//
DELIMITER ;