"""
Google Maps Business Scraper using Selenium
"""
import time
import random
import re
import logging
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException,
    ElementClickInterceptedException, StaleElementReferenceException
)
from database.models import Isletme, BlacklistManager
import requests

logger = logging.getLogger(__name__)

class GoogleMapsScraper:
    """Google Maps işletme scraper sınıfı"""
    
    def __init__(self, config: Dict = None):
        """
        Scraper'ı başlat
        
        Args:
            config: Scraper ayarları
        """
        self.config = config or {}
        self.driver = None
        self.wait = None
        self.scraped_count = 0
        self.duplicate_count = 0
        self.error_count = 0
        self.is_running = False
        self.should_stop = False
        
        # Varsayılan ayarlar
        self.delay_min = self.config.get('delay_min', 2)
        self.delay_max = self.config.get('delay_max', 5)
        self.headless = self.config.get('headless', False)
        self.user_agent = self.config.get('user_agent', 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        self.proxy_list = self.config.get('proxy_list', [])
        self.webdriver_path = self.config.get('webdriver_path', '')
        
        # Türkiye il-ilçe verileri
        self.il_ilce_data = self._load_il_ilce_data()
    
    def setup_driver(self) -> bool:
        """WebDriver'ı crash recovery ile ayarla"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                chrome_options = Options()
                
                # Temel stability ayarları
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--disable-extensions')
                chrome_options.add_argument('--disable-plugins')
                chrome_options.add_argument('--disable-images')
                chrome_options.add_argument('--window-size=1920,1080')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # Memory optimization
                chrome_options.add_argument('--memory-pressure-off')
                chrome_options.add_argument('--max_old_space_size=4096')
                chrome_options.add_argument('--disable-background-timer-throttling')
                chrome_options.add_argument('--disable-renderer-backgrounding')
                chrome_options.add_argument('--disable-backgrounding-occluded-windows')
                
                # Headless mod
                if self.headless:
                    chrome_options.add_argument('--headless=new')
                
                # User agent
                chrome_options.add_argument(f'--user-agent={self.user_agent}')
                
                # Proxy ayarı
                if self.proxy_list:
                    proxy = random.choice(self.proxy_list)
                    chrome_options.add_argument(f'--proxy-server={proxy}')
                    logger.info(f"Proxy kullanılıyor: {proxy}")
                
                # WebDriver service
                if self.webdriver_path and os.path.exists(self.webdriver_path):
                    service = Service(self.webdriver_path)
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                else:
                    self.driver = webdriver.Chrome(options=chrome_options)
                
                # Anti-detection
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                # Wait objesi oluştur
                self.wait = WebDriverWait(self.driver, 15)  # Timeout artırıldı
                
                # Driver sağlık kontrolü
                self.driver.get("https://www.google.com")
                time.sleep(2)
                
                logger.info(f"WebDriver başarıyla ayarlandı (deneme {attempt + 1})")
                return True
                
            except Exception as e:
                logger.error(f"WebDriver ayarlama hatası (deneme {attempt + 1}): {e}")
                
                # Cleanup failed driver
                if hasattr(self, 'driver') and self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
                
                if attempt < max_retries - 1:
                    logger.info(f"WebDriver yeniden deneniyor... ({retry_delay} saniye bekleniyor)")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("WebDriver ayarlama başarısız (tüm denemeler tükendi)")
                    return False
        
        return False
    
    def search_businesses(self, il: str, ilce: str = "", sektor: str = "", limit: int = 50) -> List[Isletme]:
        """
        Google Maps'te işletme ara
        
        Args:
            il: İl adı
            ilce: İlçe adı (opsiyonel)
            sektor: Sektör/keyword
            limit: Maksimum sonuç sayısı
            
        Returns:
            List[Isletme]: Bulunan işletmeler
        """
        if not self.setup_driver():
            return []
        
        self.is_running = True
        self.should_stop = False
        businesses = []
        
        try:
            # Arama sorgusu oluştur
            query = self._build_search_query(il, ilce, sektor)
            logger.info(f"Arama sorgusu: {query}")
            
            # Google Maps'e git
            search_url = f"https://www.google.com/maps/search/{query}"
            self.driver.get(search_url)
            
            # Sayfanın yüklenmesini bekle
            self._wait_for_page_load()
            
            # CAPTCHA kontrolü
            if self._check_captcha():
                logger.warning("CAPTCHA tespit edildi, scraping durduruluyor")
                return businesses
            
            # Sonuçları scroll ederek yükle
            self._scroll_results(limit)
            
            # İşletme linklerini topla
            business_links = self._collect_business_links(limit)
            logger.info(f"{len(business_links)} işletme linki toplandı")
            
            # Her işletmenin detaylarını çek
            for i, link in enumerate(business_links):
                if self.should_stop:
                    break
                
                try:
                    business = self._scrape_business_details(link, il, ilce)
                    if business and not BlacklistManager.is_blacklisted(business.google_id):
                        businesses.append(business)
                        self.scraped_count += 1
                        logger.info(f"İşletme çekildi ({i+1}/{len(business_links)}): {business.isim}")
                    else:
                        self.duplicate_count += 1
                    
                    # Delay
                    self._random_delay()
                    
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"İşletme detay çekme hatası: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Scraping genel hatası: {e}")
        
        finally:
            self.cleanup()
            self.is_running = False
        
        return businesses
    
    def _build_search_query(self, il: str, ilce: str, sektor: str) -> str:
        """Arama sorgusunu oluştur"""
        query_parts = []
        
        if sektor:
            query_parts.append(sektor)
        
        if ilce:
            query_parts.append(ilce)
        
        if il:
            query_parts.append(il)
        
        return " ".join(query_parts)
    
    def _wait_for_page_load(self):
        """Sayfanın yüklenmesini bekle"""
        try:
            logger.info("🔍 DIAGNOSTIC: Sayfa yükleme başlatılıyor...")
            
            # Mevcut sayfa URL'ini logla
            current_url = self.driver.current_url
            logger.info(f"🔍 DIAGNOSTIC: Mevcut URL: {current_url}")
            
            # Sayfa başlığını logla
            try:
                page_title = self.driver.title
                logger.info(f"🔍 DIAGNOSTIC: Sayfa başlığı: {page_title}")
            except:
                logger.warning("🔍 DIAGNOSTIC: Sayfa başlığı alınamadı")
            
            # Daha güncel selector'ları dene
            selectors_to_try = [
                '[role="main"]',
                '[data-value="Search results"]',
                '.m6QErb',
                '[aria-label*="Results"]',
                '.Nv2PK',
                '#searchboxinput',
                '.widget-pane',
                '.section-layout'
            ]
            
            found_selector = None
            for selector in selectors_to_try:
                try:
                    self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    found_selector = selector
                    logger.info(f"✅ DIAGNOSTIC: Sayfa yüklendi, kullanılan selector: {selector}")
                    break
                except TimeoutException:
                    logger.debug(f"❌ DIAGNOSTIC: Selector bulunamadı: {selector}")
                    continue
            
            if not found_selector:
                logger.error("🚨 DIAGNOSTIC: Hiçbir selector bulunamadı!")
                # Sayfa kaynağının bir kısmını logla
                try:
                    page_source_snippet = self.driver.page_source[:1000]
                    logger.error(f"🔍 DIAGNOSTIC: Sayfa kaynağı örneği: {page_source_snippet}")
                except:
                    logger.error("🔍 DIAGNOSTIC: Sayfa kaynağı alınamadı")
            
            time.sleep(3)
            
        except Exception as e:
            logger.error(f"🚨 DIAGNOSTIC: Sayfa yükleme hatası: {e}")
            time.sleep(5)
    
    def _check_captcha(self) -> bool:
        """CAPTCHA kontrolü"""
        captcha_selectors = [
            '#captcha-form',
            '.g-recaptcha',
            '[data-callback="onCaptcha"]',
            'iframe[src*="recaptcha"]'
        ]
        
        for selector in captcha_selectors:
            try:
                self.driver.find_element(By.CSS_SELECTOR, selector)
                return True
            except NoSuchElementException:
                continue
        
        return False
    
    def _scroll_results(self, limit: int):
        """Sonuçları scroll ederek yükle"""
        try:
            logger.info(f"Scroll işlemi başlatılıyor, hedef: {limit} sonuç")
            
            # 2024 güncel Google Maps selector'ları
            results_panel = None
            panel_selectors = [
                '[role="main"]',
                '.widget-pane-content',
                '.section-layout',
                '[data-value="Search results"]',
                '.m6QErb',
                '.Nv2PK',
                '[aria-label*="Results"]',
                '.section-scrollbox',
                '[jsaction*="scroll"]'
            ]
            
            for selector in panel_selectors:
                try:
                    results_panel = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.info(f"✅ Results panel bulundu: {selector}")
                    break
                except NoSuchElementException:
                    logger.debug(f"❌ Panel selector bulunamadı: {selector}")
                    continue
            
            if not results_panel:
                logger.warning("⚠️ Results panel bulunamadı, body ile scroll deneniyor")
                results_panel = self.driver.find_element(By.TAG_NAME, 'body')
            
            # Daha agresif scroll stratejisi
            scroll_attempts = 0
            max_scroll_attempts = 20  # Daha fazla deneme
            no_change_count = 0
            max_no_change = 3
            
            while scroll_attempts < max_scroll_attempts and not self.should_stop:
                # Mevcut sonuç sayısını say
                current_results = self._count_current_results()
                logger.info(f"Mevcut sonuç sayısı: {current_results}, Hedef: {limit}")
                
                if current_results >= limit:
                    logger.info(f"Hedef sonuç sayısına ulaşıldı: {current_results}")
                    break
                
                # Scroll işlemi - birden fazla yöntem dene
                old_results = current_results
                
                # 1. Panel içinde scroll
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", results_panel)
                time.sleep(2)
                
                # 2. Sayfa scroll
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # 3. End tuşu ile scroll
                try:
                    from selenium.webdriver.common.keys import Keys
                    results_panel.send_keys(Keys.END)
                    time.sleep(2)
                except:
                    pass
                
                # 4. Mouse wheel scroll simulation
                try:
                    self.driver.execute_script("""
                        var element = arguments[0];
                        var event = new WheelEvent('wheel', {
                            deltaY: 1000,
                            bubbles: true,
                            cancelable: true
                        });
                        element.dispatchEvent(event);
                    """, results_panel)
                    time.sleep(2)
                except:
                    pass
                
                # Yeni sonuç sayısını kontrol et
                new_results = self._count_current_results()
                
                if new_results == old_results:
                    no_change_count += 1
                    logger.info(f"Sonuç sayısı değişmedi: {new_results}, No-change count: {no_change_count}")
                    
                    if no_change_count >= max_no_change:
                        logger.info("Daha fazla sonuç yüklenemedi, scroll durduruluyor")
                        break
                else:
                    no_change_count = 0
                    logger.info(f"Yeni sonuçlar yüklendi: {old_results} -> {new_results}")
                
                scroll_attempts += 1
                
                # "Daha fazla sonuç" butonu varsa tıkla
                try:
                    more_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'More results') or contains(text(), 'Daha fazla')]")
                    if more_button.is_displayed():
                        more_button.click()
                        time.sleep(3)
                        logger.info("'Daha fazla sonuç' butonuna tıklandı")
                except:
                    pass
                
        except Exception as e:
            logger.error(f"Scroll hatası: {e}")
    
    def _count_current_results(self) -> int:
        """Mevcut sonuç sayısını say"""
        try:
            # Farklı selector'larla sonuç sayısını say
            result_selectors = [
                'a[href*="/maps/place/"]',
                '[data-result-index]',
                '.hfpxzc',
                '[jsaction*="pane.resultCard"]',
                '.Nv2PK .TFQHme',
                '[role="article"]'
            ]
            
            max_count = 0
            for selector in result_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    count = len(elements)
                    if count > max_count:
                        max_count = count
                        logger.debug(f"Selector '{selector}' ile {count} sonuç bulundu")
                except:
                    continue
            
            return max_count
            
        except Exception as e:
            logger.error(f"Sonuç sayma hatası: {e}")
            return 0
    
    def _collect_business_links(self, limit: int) -> List[str]:
        """İşletme linklerini topla"""
        links = []
        
        try:
            logger.info(f"🔍 DIAGNOSTIC: İşletme linkleri toplanıyor, limit: {limit}")
            
            # Sayfa kaynağında kaç tane maps/place linki var kontrol et
            try:
                page_source = self.driver.page_source
                import re
                place_links_in_source = re.findall(r'/maps/place/[^"\'>\s]+', page_source)
                logger.info(f"🔍 DIAGNOSTIC: Sayfa kaynağında {len(place_links_in_source)} adet maps/place linki bulundu")
                if place_links_in_source:
                    logger.info(f"🔍 DIAGNOSTIC: İlk birkaç link örneği: {place_links_in_source[:3]}")
            except:
                logger.warning("🔍 DIAGNOSTIC: Sayfa kaynağı analiz edilemedi")
            
            # Farklı selector'larla işletme linklerini bul
            link_selectors = [
                'a[data-result-index]',
                'a[href*="/maps/place/"]',
                '.hfpxzc',
                'a[jsaction*="pane.resultCard"]',
                '[data-value="Business results"] a',
                'a[data-cid]',
                '.section-result a',
                '[role="article"] a',
                '.Nv2PK a'
            ]
            
            business_elements = []
            found_selector = None
            
            for selector in link_selectors:
                try:
                    logger.debug(f"🔍 DIAGNOSTIC: Selector deneniyor: {selector}")
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.debug(f"🔍 DIAGNOSTIC: {selector} ile {len(elements)} element bulundu")
                    
                    if elements:
                        # Elementlerin href attribute'larını kontrol et
                        valid_elements = []
                        for elem in elements:
                            try:
                                href = elem.get_attribute('href')
                                if href and ('/maps/place/' in href or 'place_id=' in href):
                                    valid_elements.append(elem)
                            except:
                                continue
                        
                        logger.info(f"🔍 DIAGNOSTIC: {selector} ile {len(valid_elements)} geçerli işletme linki bulundu")
                        
                        if valid_elements:
                            business_elements = valid_elements
                            found_selector = selector
                            break
                            
                except Exception as e:
                    logger.debug(f"🔍 DIAGNOSTIC: Selector hatası {selector}: {e}")
                    continue
            
            if not business_elements:
                logger.error("🚨 DIAGNOSTIC: Hiçbir işletme linki bulunamadı!")
                
                # Sayfadaki tüm linkleri logla
                try:
                    all_links = self.driver.find_elements(By.TAG_NAME, 'a')
                    logger.info(f"🔍 DIAGNOSTIC: Sayfada toplam {len(all_links)} link var")
                    
                    # İlk 10 linkin href'ini logla
                    for i, link in enumerate(all_links[:10]):
                        try:
                            href = link.get_attribute('href')
                            text = link.text.strip()[:50]
                            logger.info(f"🔍 DIAGNOSTIC: Link {i+1}: {href} - Text: {text}")
                        except:
                            continue
                            
                except:
                    logger.warning("🔍 DIAGNOSTIC: Sayfa linkleri analiz edilemedi")
                
                return links
            
            logger.info(f"✅ DIAGNOSTIC: {found_selector} ile {len(business_elements)} işletme elementi bulundu")
            
            for i, element in enumerate(business_elements[:limit]):
                try:
                    href = element.get_attribute('href')
                    text = element.text.strip()[:50] if element.text else "No text"
                    
                    logger.debug(f"🔍 DIAGNOSTIC: Element {i+1}: {href} - Text: {text}")
                    
                    if href and ('/maps/place/' in href or 'place_id=' in href):
                        if href not in links:  # Duplicate kontrolü
                            links.append(href)
                            logger.info(f"✅ DIAGNOSTIC: Link eklendi ({len(links)}): {href}")
                        else:
                            logger.debug(f"⚠️ DIAGNOSTIC: Duplicate link atlandı: {href}")
                    else:
                        logger.debug(f"❌ DIAGNOSTIC: Geçersiz link: {href}")
                        
                except StaleElementReferenceException:
                    logger.warning(f"⚠️ DIAGNOSTIC: Stale element reference, element {i+1}")
                    continue
                except Exception as e:
                    logger.debug(f"❌ DIAGNOSTIC: Link çıkarma hatası element {i+1}: {e}")
                    continue
            
            logger.info(f"🔍 DIAGNOSTIC: Toplam {len(links)} benzersiz işletme linki toplandı")
                
        except Exception as e:
            logger.error(f"🚨 DIAGNOSTIC: Link toplama genel hatası: {e}")
            import traceback
            logger.error(f"🚨 DIAGNOSTIC: Traceback: {traceback.format_exc()}")
        
        return links
    
    def _scrape_business_details(self, url: str, il: str, ilce: str) -> Optional[Isletme]:
        """İşletme detaylarını çek"""
        try:
            self.driver.get(url)
            time.sleep(3)
            
            # Google ID çıkar
            google_id = self._extract_google_id(url)
            if not google_id:
                return None
            
            # İşletme bilgilerini çek
            business = Isletme()
            business.google_id = google_id
            business.source_url = url
            business.il = il
            business.ilce = ilce
            
            # İsim - 2024 güncel selector'lar
            name_selectors = [
                'h1[data-attrid="title"]',
                'h1.DUwDvf',
                'h1.lfPIob',
                '[data-value="Business name"]',
                'h1.x3AX1-LfntMc-header-title-title',
                '.x3AX1-LfntMc-header-title-title',
                'h1[class*="fontHeadlineLarge"]',
                '.qrShPb h1',
                '.section-hero-header h1',
                '.widget-pane-section-header h1',
                'h1[jsaction]'
            ]
            for selector in name_selectors:
                business.isim = self._get_text_by_selector(selector)
                if business.isim:
                    logger.info(f"✅ İsim bulundu ({selector}): {business.isim}")
                    break
            
            # Kategori - 2024 güncel selector'lar
            category_selectors = [
                '[data-value="Category"]',
                '.DkEaL',
                'button[jsaction*="category"]',
                '.fontBodyMedium .fontBodyMedium',
                '.YhemCb',
                '.section-hero-header .fontBodyMedium',
                '.widget-pane-section-header .fontBodyMedium',
                'button[data-value*="category"]',
                '.section-result-content .fontBodyMedium'
            ]
            for selector in category_selectors:
                business.kategori = self._get_text_by_selector(selector)
                if business.kategori:
                    logger.info(f"✅ Kategori bulundu ({selector}): {business.kategori}")
                    break
            
            # Telefon - Geliştirilmiş telefon çıkarma
            business.telefon = self._extract_phone_number()
            
            # Adres - 2024 güncel selector'lar
            address_selectors = [
                '[data-value="Address"]',
                '.Io6YTe',
                'button[data-item-id*="address"]',
                '[data-item-id*="address"] .fontBodyMedium',
                '.section-info-line .fontBodyMedium',
                'button[jsaction*="address"]',
                '[aria-label*="Address"]',
                '.widget-pane-link .fontBodyMedium'
            ]
            for selector in address_selectors:
                business.adres = self._get_text_by_selector(selector)
                if business.adres:
                    logger.info(f"✅ Adres bulundu ({selector}): {business.adres}")
                    break
            
            # Website - 2024 güncel selector'lar
            website_selectors = [
                '[data-value="Website"] a',
                'a[data-item-id*="authority"]',
                'a[href*="http"]:not([href*="google"]):not([href*="maps"])',
                'button[data-item-id*="authority"] a',
                '.section-info-line a[href*="http"]',
                '.widget-pane-link a[href*="http"]'
            ]
            for selector in website_selectors:
                business.website = self._get_attribute_by_selector(selector, 'href')
                if business.website and not any(x in business.website for x in ['google', 'maps', 'youtube']):
                    logger.info(f"✅ Website bulundu ({selector}): {business.website}")
                    break
            
            # Çalışma saatleri
            business.calisma_saatleri = self._get_working_hours()
            
            # Puan ve yorum sayısı
            rating_info = self._get_rating_info()
            business.puan = rating_info.get('rating')
            business.yorum_sayisi = rating_info.get('review_count', 0)
            
            # Yoğunluk bilgisi
            business.yogunluk_bilgisi = self._get_text_by_selector('[data-value="Popular times"]')
            
            # Konum linki
            business.konum_linki = url
            
            # Resim URL
            business.resim_url = self._get_first_image_url()
            
            return business
            
        except Exception as e:
            logger.error(f"İşletme detay çekme hatası: {e}")
            return None
    
    def _extract_google_id(self, url: str) -> Optional[str]:
        """URL'den Google ID çıkar"""
        try:
            # place_id pattern
            place_id_match = re.search(r'place/([^/]+)', url)
            if place_id_match:
                return place_id_match.group(1)
            
            # cid pattern
            cid_match = re.search(r'cid:(\d+)', url)
            if cid_match:
                return cid_match.group(1)
            
            # data parameter
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            if 'data' in query_params:
                data_param = query_params['data'][0]
                cid_match = re.search(r'0x[a-f0-9]+:0x([a-f0-9]+)', data_param)
                if cid_match:
                    return cid_match.group(1)
            
            return None
            
        except Exception as e:
            logger.error(f"Google ID çıkarma hatası: {e}")
            return None
    
    def _get_text_by_selector(self, selector: str, timeout: int = 5) -> Optional[str]:
        """CSS selector ile text al - element validation ile"""
        try:
            # Element'in varlığını bekle
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            
            # Element'in görünür olmasını bekle
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of(element)
            )
            
            text = element.text.strip()
            return text if text else None
            
        except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
            return None
        except Exception as e:
            logger.debug(f"Text alma hatası ({selector}): {e}")
            return None
    
    def _get_attribute_by_selector(self, selector: str, attribute: str, timeout: int = 5) -> Optional[str]:
        """CSS selector ile attribute al - element validation ile"""
        try:
            # Element'in varlığını bekle
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            
            attr_value = element.get_attribute(attribute)
            return attr_value if attr_value else None
            
        except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
            return None
        except Exception as e:
            logger.debug(f"Attribute alma hatası ({selector}, {attribute}): {e}")
            return None
    
    def _safe_find_element(self, selector: str, timeout: int = 5) -> Optional[any]:
        """Güvenli element bulma"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element
        except (TimeoutException, NoSuchElementException):
            return None
    
    def _safe_find_elements(self, selector: str, timeout: int = 5) -> List[any]:
        """Güvenli element listesi bulma"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return self.driver.find_elements(By.CSS_SELECTOR, selector)
        except (TimeoutException, NoSuchElementException):
            return []
    
    def _extract_phone_number(self) -> Optional[str]:
        """Telefon numarasını çıkar"""
        try:
            # Önce tel: linklerini ara
            try:
                tel_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[href^="tel:"]')
                for tel_element in tel_elements:
                    tel_href = tel_element.get_attribute('href')
                    if tel_href:
                        phone = tel_href.replace('tel:', '').strip()
                        if phone and any(char.isdigit() for char in phone):
                            logger.info(f"Telefon bulundu (tel link): {phone}")
                            return phone
            except:
                pass
            
            # Daha kapsamlı selector'ları dene
            phone_selectors = [
                '[data-value="Phone"]',
                'button[data-item-id*="phone"]',
                '[data-item-id*="phone"] .fontBodyMedium',
                '[data-item-id*="phone"] .Io6YTe',
                'button[data-value="Phone"] .Io6YTe',
                '.rogA2c .Io6YTe',
                '[aria-label*="phone" i]',
                '[aria-label*="telefon" i]',
                'button[jsaction*="phone"]',
                '.CsEnBe[aria-label*="phone" i]'
            ]
            
            for selector in phone_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        phone = element.text.strip()
                        if phone and any(char.isdigit() for char in phone):
                            # Telefon numarası formatını kontrol et
                            if self._is_valid_phone(phone):
                                logger.info(f"Telefon bulundu ({selector}): {phone}")
                                return phone
                except:
                    continue
            
            # Sayfa kaynağında telefon numarası ara
            try:
                page_source = self.driver.page_source
                phone_patterns = [
                    r'\+90\s*\d{3}\s*\d{3}\s*\d{2}\s*\d{2}',  # +90 XXX XXX XX XX
                    r'0\d{3}\s*\d{3}\s*\d{2}\s*\d{2}',        # 0XXX XXX XX XX
                    r'\(\d{3}\)\s*\d{3}\s*\d{2}\s*\d{2}',     # (XXX) XXX XX XX
                    r'\d{3}-\d{3}-\d{2}-\d{2}',               # XXX-XXX-XX-XX
                    r'\d{10,11}'                               # XXXXXXXXXX
                ]
                
                import re
                for pattern in phone_patterns:
                    matches = re.findall(pattern, page_source)
                    for match in matches:
                        phone = match.strip()
                        if self._is_valid_phone(phone):
                            logger.info(f"Telefon bulundu (regex): {phone}")
                            return phone
            except:
                pass
            
            logger.warning("Telefon numarası bulunamadı")
            return None
            
        except Exception as e:
            logger.error(f"Telefon çıkarma hatası: {e}")
            return None
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Telefon numarası geçerli mi kontrol et"""
        if not phone:
            return False
        
        # Sadece rakam, boşluk, tire, parantez ve + içermeli
        import re
        cleaned = re.sub(r'[^\d]', '', phone)
        
        # En az 10 rakam olmalı
        if len(cleaned) < 10:
            return False
        
        # Türkiye telefon numarası formatları
        if cleaned.startswith('90') and len(cleaned) == 12:  # +90XXXXXXXXXX
            return True
        elif cleaned.startswith('0') and len(cleaned) == 11:  # 0XXXXXXXXXX
            return True
        elif len(cleaned) == 10:  # XXXXXXXXXX
            return True
        
        return False
    
    def _get_working_hours(self) -> Optional[str]:
        """Çalışma saatlerini al"""
        try:
            hours_elements = self.driver.find_elements(By.CSS_SELECTOR, '.t39EBf .G8aQO')
            if hours_elements:
                hours = []
                for element in hours_elements:
                    hours.append(element.text.strip())
                return '; '.join(hours)
            
            return None
            
        except Exception as e:
            logger.error(f"Çalışma saatleri hatası: {e}")
            return None
    
    def _get_rating_info(self) -> Dict:
        """Puan ve yorum sayısı bilgilerini al"""
        try:
            rating_info = {'rating': None, 'review_count': 0}
            
            # Puan
            rating_element = self.driver.find_element(By.CSS_SELECTOR, '.F7nice span[aria-hidden="true"]')
            if rating_element:
                rating_text = rating_element.text.replace(',', '.')
                try:
                    rating_info['rating'] = float(rating_text)
                except ValueError:
                    pass
            
            # Yorum sayısı
            review_element = self.driver.find_element(By.CSS_SELECTOR, '.F7nice button span')
            if review_element:
                review_text = review_element.text
                review_match = re.search(r'([\d,]+)', review_text)
                if review_match:
                    review_count = review_match.group(1).replace(',', '')
                    try:
                        rating_info['review_count'] = int(review_count)
                    except ValueError:
                        pass
            
            return rating_info
            
        except NoSuchElementException:
            return {'rating': None, 'review_count': 0}
    
    def _get_first_image_url(self) -> Optional[str]:
        """İlk resim URL'ini al"""
        try:
            img_element = self.driver.find_element(By.CSS_SELECTOR, '.ZKCDEc img')
            return img_element.get_attribute('src')
        except NoSuchElementException:
            return None
    
    def _random_delay(self):
        """Random delay"""
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)
    
    def _load_il_ilce_data(self) -> Dict:
        """Türkiye il-ilçe verilerini yükle"""
        # Basit il-ilçe verileri (gerçek uygulamada JSON dosyasından yüklenebilir)
        return {
            "İstanbul": ["Kadıköy", "Beşiktaş", "Şişli", "Beyoğlu", "Fatih", "Üsküdar"],
            "Ankara": ["Çankaya", "Keçiören", "Yenimahalle", "Mamak", "Sincan"],
            "İzmir": ["Konak", "Karşıyaka", "Bornova", "Buca", "Bayraklı"],
            "Konya": ["Meram", "Karatay", "Selçuklu"]
        }
    
    def stop_scraping(self):
        """Scraping'i durdur"""
        self.should_stop = True
        logger.info("Scraping durdurma sinyali gönderildi")
    
    def cleanup(self):
        """Temizlik işlemleri"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Driver kapatma hatası: {e}")
            finally:
                self.driver = None
        
        logger.info("Scraper temizlendi")
    
    def get_statistics(self) -> Dict:
        """Scraping istatistiklerini al"""
        return {
            'scraped_count': self.scraped_count,
            'duplicate_count': self.duplicate_count,
            'error_count': self.error_count,
            'is_running': self.is_running
        }