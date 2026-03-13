"""
Toast Notification System for PySide6 Applications
"""
from PySide6.QtWidgets import QWidget, QLabel, QGraphicsOpacityEffect, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, QRect, Qt, Signal
from PySide6.QtGui import QFont, QPainter, QPainterPath, QColor
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ToastNotification(QWidget):
    """Toast bildirim widget'ı"""
    
    # Toast türleri
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    
    # Signals
    clicked = Signal()
    closed = Signal()
    
    def __init__(self, message: str, toast_type: str = INFO, duration: int = 3000, parent=None):
        """
        Toast bildirimi oluştur
        
        Args:
            message: Bildirim mesajı
            toast_type: Bildirim türü (success, error, warning, info)
            duration: Gösterim süresi (ms)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.message = message
        self.toast_type = toast_type
        self.duration = duration
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        self.setup_ui()
        self.setup_animations()
        self.setup_timer()
        
        # Boyut ayarla
        self.adjustSize()
        self.setFixedSize(self.sizeHint())
    
    def setup_ui(self):
        """UI'ı ayarla"""
        # Ana layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        
        # İkon label (emoji kullanarak)
        self.icon_label = QLabel()
        self.icon_label.setFont(QFont("Segoe UI Emoji", 16))
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        # Mesaj label
        self.message_label = QLabel(self.message)
        self.message_label.setFont(QFont("Segoe UI", 10))
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignVCenter)
        
        # Layout'a ekle
        layout.addWidget(self.icon_label)
        layout.addWidget(self.message_label, 1)
        
        # Stil ayarla
        self.apply_style()
    
    def apply_style(self):
        """Toast türüne göre stil uygula"""
        styles = {
            self.SUCCESS: {
                'icon': '✅',
                'bg_color': '#4CAF50',
                'text_color': '#FFFFFF',
                'border_color': '#45A049'
            },
            self.ERROR: {
                'icon': '❌',
                'bg_color': '#F44336',
                'text_color': '#FFFFFF',
                'border_color': '#D32F2F'
            },
            self.WARNING: {
                'icon': '⚠️',
                'bg_color': '#FF9800',
                'text_color': '#FFFFFF',
                'border_color': '#F57C00'
            },
            self.INFO: {
                'icon': 'ℹ️',
                'bg_color': '#2196F3',
                'text_color': '#FFFFFF',
                'border_color': '#1976D2'
            }
        }
        
        style = styles.get(self.toast_type, styles[self.INFO])
        
        # İkon ayarla
        self.icon_label.setText(style['icon'])
        
        # Stil ayarla
        self.setStyleSheet(f"""
            ToastNotification {{
                background-color: {style['bg_color']};
                border: 2px solid {style['border_color']};
                border-radius: 8px;
                color: {style['text_color']};
            }}
            QLabel {{
                color: {style['text_color']};
                background: transparent;
                border: none;
            }}
        """)
    
    def setup_animations(self):
        """Animasyonları ayarla"""
        # Opacity effect
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        # Fade in animation
        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Fade out animation
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.InCubic)
        self.fade_out_animation.finished.connect(self.close)
    
    def setup_timer(self):
        """Timer ayarla"""
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.start_fade_out)
    
    def show_toast(self):
        """Toast'ı göster"""
        self.show()
        self.fade_in_animation.start()
        
        if self.duration > 0:
            self.timer.start(self.duration)
    
    def start_fade_out(self):
        """Fade out animasyonunu başlat"""
        self.fade_out_animation.start()
    
    def mousePressEvent(self, event):
        """Mouse tıklama eventi"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            self.start_fade_out()
        super().mousePressEvent(event)
    
    def closeEvent(self, event):
        """Kapanma eventi"""
        self.closed.emit()
        super().closeEvent(event)

class ToastManager:
    """Toast bildirim yöneticisi"""
    
    def __init__(self, parent_widget: QWidget):
        """
        Toast manager oluştur
        
        Args:
            parent_widget: Ana widget (toast'ların konumlandırılacağı)
        """
        self.parent_widget = parent_widget
        self.active_toasts = []
        self.toast_spacing = 10
        self.margin_right = 20
        self.margin_top = 20
    
    def show_success(self, message: str, duration: int = 3000):
        """Başarı bildirimi göster"""
        self._show_toast(message, ToastNotification.SUCCESS, duration)
    
    def show_error(self, message: str, duration: int = 5000):
        """Hata bildirimi göster"""
        self._show_toast(message, ToastNotification.ERROR, duration)
    
    def show_warning(self, message: str, duration: int = 4000):
        """Uyarı bildirimi göster"""
        self._show_toast(message, ToastNotification.WARNING, duration)
    
    def show_info(self, message: str, duration: int = 3000):
        """Bilgi bildirimi göster"""
        self._show_toast(message, ToastNotification.INFO, duration)
    
    def _show_toast(self, message: str, toast_type: str, duration: int):
        """Toast bildirimi göster"""
        try:
            # Toast oluştur
            toast = ToastNotification(message, toast_type, duration, self.parent_widget)
            
            # Pozisyon hesapla
            self._position_toast(toast)
            
            # Event bağla
            toast.closed.connect(lambda: self._remove_toast(toast))
            
            # Listeye ekle
            self.active_toasts.append(toast)
            
            # Göster
            toast.show_toast()
            
            logger.debug(f"Toast gösterildi: {message} ({toast_type})")
            
        except Exception as e:
            logger.error(f"Toast gösterme hatası: {e}")
    
    def _position_toast(self, toast: ToastNotification):
        """Toast pozisyonunu ayarla"""
        if not self.parent_widget:
            return
        
        parent_rect = self.parent_widget.rect()
        toast_size = toast.sizeHint()
        
        # X pozisyonu (sağ taraf)
        x = parent_rect.width() - toast_size.width() - self.margin_right
        
        # Y pozisyonu (üstten başlayarak)
        y = self.margin_top
        
        # Diğer toast'ların altına yerleştir
        for existing_toast in self.active_toasts:
            if existing_toast.isVisible():
                y += existing_toast.height() + self.toast_spacing
        
        # Pozisyonu ayarla
        toast.move(x, y)
    
    def _remove_toast(self, toast: ToastNotification):
        """Toast'ı listeden çıkar"""
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
            toast.deleteLater()
            
            # Kalan toast'ları yeniden konumlandır
            self._reposition_toasts()
    
    def _reposition_toasts(self):
        """Kalan toast'ları yeniden konumlandır"""
        y = self.margin_top
        
        for toast in self.active_toasts:
            if toast.isVisible():
                current_pos = toast.pos()
                new_pos = QRect(current_pos.x(), y, toast.width(), toast.height())
                
                # Animasyonlu hareket
                animation = QPropertyAnimation(toast, b"geometry")
                animation.setDuration(200)
                animation.setStartValue(toast.geometry())
                animation.setEndValue(new_pos)
                animation.setEasingCurve(QEasingCurve.OutCubic)
                animation.start()
                
                y += toast.height() + self.toast_spacing
    
    def clear_all(self):
        """Tüm toast'ları temizle"""
        for toast in self.active_toasts[:]:
            toast.start_fade_out()
    
    def get_active_count(self) -> int:
        """Aktif toast sayısını al"""
        return len([t for t in self.active_toasts if t.isVisible()])

# Global toast manager instance
_toast_manager: Optional[ToastManager] = None

def init_toast_manager(parent_widget: QWidget):
    """Global toast manager'ı başlat"""
    global _toast_manager
    _toast_manager = ToastManager(parent_widget)

def show_success(message: str, duration: int = 3000):
    """Global başarı bildirimi"""
    if _toast_manager:
        _toast_manager.show_success(message, duration)

def show_error(message: str, duration: int = 5000):
    """Global hata bildirimi"""
    if _toast_manager:
        _toast_manager.show_error(message, duration)

def show_warning(message: str, duration: int = 4000):
    """Global uyarı bildirimi"""
    if _toast_manager:
        _toast_manager.show_warning(message, duration)

def show_info(message: str, duration: int = 3000):
    """Global bilgi bildirimi"""
    if _toast_manager:
        _toast_manager.show_info(message, duration)

def clear_all_toasts():
    """Tüm toast'ları temizle"""
    if _toast_manager:
        _toast_manager.clear_all()