# Google Maps Scraper - Professional Desktop Application

A comprehensive desktop application built with Python and PySide6 for scraping business data from Google Maps, managing customer relationships, and exporting data to Excel.

## 🚀 Features

### Core Functionality
- **Google Maps Scraping**: Extract business information using Selenium WebDriver
- **Database Management**: MySQL integration with connection pooling and thread safety
- **Excel Export**: Memory-efficient export with batch processing and statistics
- **Customer Management**: Convert prospects to customers with notes and package tracking
- **Blacklist System**: Prevent scraping of unwanted businesses

### User Interface
- **Modern Dark Theme**: Professional dark mode interface with animations
- **Animated Sidebar**: Collapsible sidebar with smooth transitions (220px ↔ 60px)
- **Multi-Panel Layout**: Scraper, Users, Customers, and Settings panels
- **Real-time Progress**: Live progress bars and status updates
- **Toast Notifications**: Non-intrusive success/error notifications

### Technical Features
- **Thread Safety**: QThread-based workers with mutex protection
- **Memory Efficiency**: Streaming Excel export and batch processing
- **Input Validation**: Comprehensive validation with regex patterns
- **Error Recovery**: WebDriver crash recovery with exponential backoff
- **SQL Injection Protection**: Parameterized queries throughout

## 📋 Requirements

### System Requirements
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux
- **Python**: 3.8 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended for large datasets)
- **Storage**: 500MB free space

### Dependencies
```
PySide6>=6.5.0
selenium>=4.15.0
mysql-connector-python>=8.2.0
openpyxl>=3.1.0
webdriver-manager>=4.0.0
```

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/google-maps-scraper.git
cd google-maps-scraper
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Database
```sql
CREATE DATABASE google_maps_scraper;
CREATE USER 'scraper_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON google_maps_scraper.* TO 'scraper_user'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Configure Application
Run the application and go to Settings → Database to configure your MySQL connection.

## 🚀 Quick Start

### 1. Launch Application
```bash
python main.py
```

### 2. Configure Settings
- **Database**: Set MySQL connection details
- **WebDriver**: Configure Chrome/Firefox driver path (auto-download available)
- **Scraper**: Set default limits, delays, and proxy settings

### 3. Start Scraping
1. Select **Scraper** panel from sidebar
2. Choose **City** and **District** (optional)
3. Enter **Sector** keywords (e.g., "restaurant", "barber", "auto dealer")
4. Set **Limit** (1-1000 results)
5. Click **🔍 Start Scraping**

### 4. Manage Results
- **Users Panel**: View all scraped businesses with filters
- **Customers Panel**: Manage converted customers with packages and payments
- **Excel Export**: Export filtered results with statistics

## 📊 Database Schema

### Tables

#### `isletmeler` (Businesses)
```sql
CREATE TABLE isletmeler (
    id INT PRIMARY KEY AUTO_INCREMENT,
    google_id VARCHAR(255) UNIQUE,
    isim VARCHAR(255),
    kategori VARCHAR(255),
    telefon VARCHAR(50),
    adres TEXT,
    website VARCHAR(500),
    calisma_saatleri TEXT,
    puan DECIMAL(2,1),
    yorum_sayisi INT,
    yogunluk_bilgisi VARCHAR(255),
    konum_linki TEXT,
    resim_url TEXT,
    il VARCHAR(100),
    ilce VARCHAR(100),
    durum TINYINT DEFAULT 0,
    notlar TEXT,
    eklenme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### `musteriler` (Customers)
```sql
CREATE TABLE musteriler (
    id INT PRIMARY KEY AUTO_INCREMENT,
    isletme_id INT,
    paket VARCHAR(255),
    odeme_durumu VARCHAR(100),
    iletisim_tarihi DATE,
    notlar TEXT,
    kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (isletme_id) REFERENCES isletmeler(id)
);
```

#### `blacklist`
```sql
CREATE TABLE blacklist (
    id INT PRIMARY KEY AUTO_INCREMENT,
    google_id VARCHAR(255),
    source_url TEXT,
    sebep TEXT,
    tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## ⚙️ Configuration

### Application Settings
The application uses a JSON configuration file (`config.json`) with the following structure:

```json
{
    "database": {
        "host": "localhost",
        "port": 3306,
        "user": "scraper_user",
        "password": "your_password",
        "database": "google_maps_scraper"
    },
    "scraper": {
        "webdriver_path": "",
        "headless": false,
        "delay_min": 2,
        "delay_max": 5,
        "default_limit": 50,
        "export_excel": true,
        "user_agent": "",
        "proxy_file": ""
    },
    "ui": {
        "theme": "dark",
        "font_family": "Segoe UI",
        "font_size": 10,
        "window_width": 1200,
        "window_height": 800,
        "sidebar_width": 220
    },
    "export": {
        "output_directory": "exports",
        "auto_open_excel": false,
        "include_statistics": true
    },
    "logging": {
        "level": "INFO",
        "max_log_files": 5,
        "max_file_size_mb": 10
    }
}
```

### Environment Variables
```bash
# Optional: Override database settings
DB_HOST=localhost
DB_PORT=3306
DB_USER=scraper_user
DB_PASSWORD=your_password
DB_NAME=google_maps_scraper

# Optional: WebDriver settings
WEBDRIVER_PATH=/path/to/chromedriver
HEADLESS_MODE=false
```

## 🔧 Advanced Usage

### Proxy Configuration
Create a `proxy.txt` file with one proxy per line:
```
http://proxy1:port
http://user:pass@proxy2:port
socks5://proxy3:port
```

### Batch Processing
For large datasets (>1000 businesses), the application automatically:
- Uses streaming Excel export to minimize memory usage
- Processes data in batches of 1000 records
- Implements connection pooling for database operations
- Provides progress updates during long operations

### Custom Selectors
The scraper uses up-to-date Google Maps selectors (as of 2024). If selectors become outdated, update them in `scraper/google_maps_scraper.py`:

```python
BUSINESS_SELECTORS = {
    'results_container': '[role="main"] [role="region"]',
    'business_items': '[data-result-index]',
    'name': '[data-attrid="title"]',
    'phone': '[data-attrid="phone"]',
    # ... other selectors
}
```

## 🐛 Troubleshooting

### Common Issues

#### WebDriver Issues
```bash
# Error: WebDriver not found
Solution: Install ChromeDriver or use webdriver-manager
pip install webdriver-manager
```

#### Database Connection
```bash
# Error: Access denied for user
Solution: Check MySQL credentials and permissions
GRANT ALL PRIVILEGES ON google_maps_scraper.* TO 'user'@'localhost';
```

#### Memory Issues
```bash
# Error: Out of memory during export
Solution: Reduce batch size in constants.py
EXCEL_BATCH_SIZE = 500  # Reduce from 1000
```

### Debug Mode
Enable debug logging in Settings → Export & Log → Log Level → DEBUG

### Log Files
Application logs are stored in the `logs/` directory:
- `scraper.log`: Scraping operations
- `database.log`: Database operations
- `ui.log`: User interface events
- `error.log`: Error messages

## 🔒 Security Considerations

### Data Protection
- Database passwords are stored in encrypted configuration
- Proxy credentials are handled securely
- No sensitive data is logged in plain text

### Rate Limiting
- Configurable delays between requests (2-5 seconds default)
- Exponential backoff on errors
- Respect for robots.txt (when applicable)

### Legal Compliance
- Ensure compliance with Google's Terms of Service
- Respect website rate limits and robots.txt
- Use scraped data responsibly and ethically

## 📈 Performance Optimization

### Database
- Connection pooling with max 10 connections
- Prepared statements for SQL injection protection
- Batch inserts for improved performance
- Proper indexing on frequently queried columns

### Memory Management
- Streaming Excel export for large datasets
- Garbage collection after batch processing
- Resource cleanup in finally blocks
- Thread-safe operations with proper locking

### UI Responsiveness
- Background threads for long operations
- Progress indicators for user feedback
- Non-blocking UI updates
- Efficient data loading with pagination

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run tests: `python -m pytest tests/`
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints where applicable
- Add docstrings to all functions and classes
- Maintain test coverage above 80%

### Testing
```bash
# Run all tests
python -m pytest tests/

# Run specific test category
python -m pytest tests/test_scraper.py
python -m pytest tests/test_database.py
python -m pytest tests/test_ui.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **PySide6**: Modern Qt bindings for Python
- **Selenium**: Web automation framework
- **OpenPyXL**: Excel file manipulation
- **MySQL**: Reliable database system

## 📞 Support

For support, please:
1. Check the [Issues](https://github.com/yourusername/google-maps-scraper/issues) page
2. Review the troubleshooting section above
3. Create a new issue with detailed information

## 🔄 Changelog

### Version 1.0.0 (2024-11-18)
- Initial release
- Complete Google Maps scraping functionality
- Modern PySide6 interface with dark theme
- MySQL database integration
- Excel export with statistics
- Customer management system
- Comprehensive error handling and validation

---

**⚠️ Disclaimer**: This tool is for educational and research purposes. Users are responsible for complying with Google's Terms of Service and applicable laws. The developers are not responsible for any misuse of this software.