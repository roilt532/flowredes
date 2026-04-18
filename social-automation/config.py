"""
Configuración central del sistema de automatización
"""
import os
from datetime import datetime

# ============ CUENTAS DESTINO ============
TIKTOK_USERNAME = "fishsinner._"
TIKTOK_EMAIL = "escobaralvaro698@gmail.com"

INSTAGRAM_USERNAME = "lennyyolosa"
INSTAGRAM_EMAIL = "escobaralvaro698@gmail.com"

# ============ CONFIGURACIÓN DE PUBLICACIÓN ============
# Ahora publicamos 1 video por ejecución, pero ejecutamos varias veces al día
VIDEOS_PER_EXECUTION = 1  # 1 video por ejecución

# Horas de publicación (hora en UTC, España es UTC+1/+2)
# TikTok: 6 veces al día (7:00, 10:00, 13:00, 17:00, 20:00, 22:00 hora España)
TIKTOK_HOURS_UTC = [6, 9, 12, 16, 19, 21]  # 6 ejecuciones

# Instagram: 3 veces al día (9:00, 14:00, 21:00 hora España) - horas de máximo alcance
INSTAGRAM_HOURS_UTC = [8, 13, 20]  # Solo 3 ejecuciones

# Delays entre videos (si se suben múltiples en una ejecución)
TIKTOK_DELAY_BETWEEN_VIDEOS = (30, 60)
INSTAGRAM_DELAY_BETWEEN_VIDEOS = (180, 300)

# ============ CONFIGURACIÓN DE VIDEO ============
VIDEO_CRF = 20
VIDEO_PRESET = "medium"
AUDIO_BITRATE = "192k"

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

def should_post_to_tiktok():
    """Verifica si la hora actual es hora de publicar en TikTok"""
    current_hour = datetime.utcnow().hour
    return current_hour in TIKTOK_HOURS_UTC

def should_post_to_instagram():
    """Verifica si la hora actual es hora de publicar en Instagram"""
    current_hour = datetime.utcnow().hour
    return current_hour in INSTAGRAM_HOURS_UTC
