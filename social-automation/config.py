"""
Configuración central del sistema de automatización
"""
import os

# ============ CUENTAS DESTINO ============
TIKTOK_USERNAME = "fishsinner._"
TIKTOK_EMAIL = "escobaralvaro698@gmail.com"

INSTAGRAM_USERNAME = "lennyyolosa"
INSTAGRAM_EMAIL = "escobaralvaro698@gmail.com"

# ============ CONFIGURACIÓN DE PUBLICACIÓN ============
VIDEOS_PER_BATCH = 10  # Videos para TikTok cada ejecución
VIDEOS_PER_BATCH_INSTAGRAM = 3  # Solo 3 videos para Instagram (muy conservador)
BATCH_INTERVAL_HOURS = 2  # Cada 2 horas

# Delays entre videos (segundos)
TIKTOK_DELAY_BETWEEN_VIDEOS = (30, 60)  # 30-60 segundos
INSTAGRAM_DELAY_BETWEEN_VIDEOS = (180, 300)  # 3-5 minutos (mucho más seguro)

# ============ CONFIGURACIÓN DE VIDEO ============
# Calidad mejorada
VIDEO_CRF = 20  # Mejor calidad (antes era 23)
VIDEO_PRESET = "medium"  # Mejor balance calidad/velocidad (antes era veryfast)
AUDIO_BITRATE = "192k"  # Mejor audio (antes era 128k)

# ============ RUTAS ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUTH_DIR = os.path.join(BASE_DIR, "auth")
DATA_DIR = os.path.join(BASE_DIR, "data")
VIDEOS_RAW_DIR = os.path.join(BASE_DIR, "videos_raw")
VIDEOS_READY_DIR = os.path.join(BASE_DIR, "videos_ready")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Archivos de datos
ACCOUNTS_FILE = os.path.join(DATA_DIR, "source_accounts.json")
UPLOADED_VIDEOS_FILE = os.path.join(DATA_DIR, "uploaded_videos.json")
TIKTOK_COOKIES_FILE = os.path.join(AUTH_DIR, "tiktok_cookies.json")
INSTAGRAM_SESSION_FILE = os.path.join(AUTH_DIR, "instagram_session.json")

# ============ GOOGLE SHEETS URL ============
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTy-gwTrRtNuwCSw75qM-rsFs2jdpTuIBu0Hy7QCqtFr_beqHx9bDQiHfs0c8Ui8PAbqrFvjaZQ-0xL/pub?gid=0&single=true&output=csv"
