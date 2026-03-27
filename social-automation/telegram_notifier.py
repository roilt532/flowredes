"""
Notificaciones por Telegram
Envía alertas sobre el estado de la automatización
"""
import requests
from datetime import datetime

# Configuración del bot
TELEGRAM_BOT_TOKEN = "8764667046:AAFuLQbPSh9JGprM47bgAMoAIambirSXiwc"
TELEGRAM_CHAT_ID = "7060038271"

def send_telegram_message(message, parse_mode="HTML"):
    """
    Envía un mensaje a Telegram
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": parse_mode
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return True
        else:
            print(f"⚠️ Error enviando a Telegram: {response.text}")
            return False
    except Exception as e:
        print(f"⚠️ Error de conexión con Telegram: {e}")
        return False

def notify_start():
    """Notifica que comenzó la ejecución"""
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    message = f"""
🚀 <b>Media Flow Engine Iniciado</b>

📅 Fecha: {now}
🎯 Objetivo: 10 videos

⏳ Descargando videos...
"""
    return send_telegram_message(message)

def notify_success(stats):
    """Notifica ejecución exitosa"""
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    message = f"""
✅ <b>Ejecución Completada</b>

📅 {now}

📊 <b>Resultados:</b>
├ 📥 Descargados: {stats.get('downloaded', 0)}
├ 🛠️ Procesados: {stats.get('processed', 0)}
├ 📱 TikTok: {stats.get('tiktok_uploaded', 0)} subidos
└ 📸 Instagram: {stats.get('instagram_uploaded', 0)} subidos

🔄 Próxima ejecución en 2 horas
"""
    return send_telegram_message(message)

def notify_error(error_message):
    """Notifica un error"""
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    message = f"""
❌ <b>Error en Media Flow Engine</b>

📅 {now}

⚠️ <b>Error:</b>
<code>{error_message[:500]}</code>

🔧 Revisa los logs en GitHub Actions
"""
    return send_telegram_message(message)

def notify_cookies_expired():
    """Notifica que las cookies expiraron"""
    message = """
🍪 <b>¡Cookies Expiradas!</b>

Las cookies de TikTok han expirado y la subida falló.

<b>Cómo renovarlas:</b>
1. Abre TikTok en Chrome
2. Inicia sesión
3. Exporta cookies con la extensión
4. Sube el archivo a GitHub

⚠️ La automatización seguirá intentando cada 2 horas
"""
    return send_telegram_message(message)

def notify_video_uploaded(platform, username, description):
    """Notifica cuando se sube un video específico"""
    emoji = "📱" if platform == "tiktok" else "📸"
    platform_name = "TikTok" if platform == "tiktok" else "Instagram"
    
    # Truncar descripción
    desc_short = description[:100] + "..." if len(description) > 100 else description
    
    message = f"""
{emoji} <b>Video Subido a {platform_name}</b>

👤 Origen: @{username}
📝 {desc_short}
"""
    return send_telegram_message(message)

def notify_daily_summary(total_tiktok, total_instagram, total_errors):
    """Resumen diario (opcional, para ejecutar 1 vez al día)"""
    message = f"""
📊 <b>Resumen del Día</b>

📱 TikTok: {total_tiktok} videos
📸 Instagram: {total_instagram} videos
⚠️ Errores: {total_errors}

💪 ¡Sigue creciendo!
"""
    return send_telegram_message(message)

# Test rápido
if __name__ == "__main__":
    print("🔔 Probando notificación de Telegram...")
    success = send_telegram_message("✅ <b>Test exitoso!</b>\n\nLas notificaciones de Media Flow Engine están funcionando correctamente.")
    if success:
        print("✅ Mensaje enviado correctamente")
    else:
        print("❌ Error al enviar mensaje")
