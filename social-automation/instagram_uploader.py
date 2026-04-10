"""
Subidor de videos a Instagram usando Instagrapi
Biblioteca oficial no-oficial para la API privada de Instagram
"""
import os
import json
import time
import random
from config import INSTAGRAM_SESSION_FILE, INSTAGRAM_USERNAME, LOGS_DIR, INSTAGRAM_DELAY_BETWEEN_VIDEOS

# Intentar importar instagrapi
try:
    from instagrapi import Client
    from instagrapi.exceptions import LoginRequired, ChallengeRequired
    INSTAGRAPI_AVAILABLE = True
except ImportError:
    INSTAGRAPI_AVAILABLE = False
    print("⚠️ instagrapi no instalado. Ejecuta: pip install instagrapi")

def create_instagram_session(sessionid, username):
    """
    Crea un archivo de sesión de Instagram a partir del sessionid
    """
    session_data = {
        "sessionid": sessionid,
        "username": username,
        "uuids": {
            "phone_id": f"{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(100000000000, 999999999999)}",
            "uuid": f"{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(100000000000, 999999999999)}",
            "client_session_id": f"{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(100000000000, 999999999999)}",
            "advertising_id": f"{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(100000000000, 999999999999)}",
            "device_id": f"android-{random.randint(1000000000000000, 9999999999999999)}"
        },
        "device_settings": {
            "app_version": "269.0.0.18.75",
            "android_version": 31,
            "android_release": "12.0",
            "dpi": "480dpi",
            "resolution": "1080x2400",
            "manufacturer": "samsung",
            "device": "SM-G998B",
            "model": "galaxy s21 ultra 5g",
            "cpu": "exynos2100",
            "version_code": "314665256"
        },
        "user_agent": "Instagram 269.0.0.18.75 Android (31/12.0; 480dpi; 1080x2400; samsung; SM-G998B; galaxy s21 ultra 5g; exynos2100; es_ES; 314665256)"
    }
    
    os.makedirs(os.path.dirname(INSTAGRAM_SESSION_FILE), exist_ok=True)
    
    with open(INSTAGRAM_SESSION_FILE, 'w') as f:
        json.dump(session_data, f, indent=2)
    
    print(f"✅ Sesión de Instagram creada: {INSTAGRAM_SESSION_FILE}")
    return session_data

def get_instagram_client():
    """
    Obtiene un cliente de Instagram autenticado
    """
    if not INSTAGRAPI_AVAILABLE:
        print("❌ instagrapi no disponible")
        return None
    
    cl = Client()
    
    # Configurar delays para parecer humano
    cl.delay_range = [1, 3]
    
    try:
        if os.path.exists(INSTAGRAM_SESSION_FILE):
            print("  📦 Cargando sesión existente...")
            with open(INSTAGRAM_SESSION_FILE, 'r') as f:
                session = json.load(f)
            
            # Configurar cliente con la sesión
            if "sessionid" in session:
                cl.login_by_sessionid(session["sessionid"])
            else:
                cl.load_settings(INSTAGRAM_SESSION_FILE)
            
            # Verificar que funciona
            cl.account_info()
            print("  ✅ Sesión válida")
            return cl
            
    except (LoginRequired, ChallengeRequired) as e:
        print(f"  ⚠️ Sesión expirada o requiere verificación: {e}")
        return None
    except Exception as e:
        print(f"  ❌ Error cargando sesión: {e}")
        return None
    
    return None

def upload_to_instagram(video_path, description):
    """
    Sube un video/reel a Instagram
    Retorna: True si éxito, False si falla
    """
    print(f"📸 Subiendo a Instagram: {os.path.basename(video_path)}")
    
    if not os.path.exists(video_path):
        print(f"  ❌ Video no encontrado: {video_path}")
        return False
    
    if not INSTAGRAPI_AVAILABLE:
        print("  ❌ instagrapi no disponible")
        return False
    
    cl = get_instagram_client()
    if not cl:
        print("  ❌ No se pudo obtener cliente de Instagram")
        return False
    
    try:
        # Subir como Reel (mejor alcance que video normal)
        print("  📤 Subiendo como Reel...")
        
        media = cl.clip_upload(
            video_path,
            caption=description,
        )
        
        if media:
            print(f"  ✅ ¡Reel publicado! ID: {media.pk}")
            return True
        else:
            print("  ❌ No se recibió confirmación de subida")
            return False
            
    except Exception as e:
        print(f"  ❌ Error subiendo a Instagram: {e}")
        
        # Guardar log del error
        os.makedirs(LOGS_DIR, exist_ok=True)
        with open(os.path.join(LOGS_DIR, "instagram_errors.log"), 'a') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Error: {e}\n")
        
        return False

def upload_batch_instagram(video_list):
    """
    Sube un lote de videos a Instagram
    video_list: lista de dicts con {path, description}
    """
    print("=" * 50)
    print(f"📤 SUBIDA A INSTAGRAM - {len(video_list)} videos")
    print("=" * 50)
    
    if not INSTAGRAPI_AVAILABLE:
        print("❌ instagrapi no disponible. Instalar con: pip install instagrapi")
        return []
    
    results = []
    
    for i, video in enumerate(video_list):
        print(f"\n[{i+1}/{len(video_list)}]")
        
        success = upload_to_instagram(
            video["path"],
            video["description"]
        )
        
        results.append({
            "video_id": video.get("video_id"),
            "success": success,
            "platform": "instagram"
        })
        
        # Delay entre uploads (Instagram es más estricto)
        if i < len(video_list) - 1:
            min_delay, max_delay = INSTAGRAM_DELAY_BETWEEN_VIDEOS
            delay = random.randint(min_delay, max_delay)  # 2-3 minutos entre videos
            print(f"  ⏳ Esperando {delay}s antes del siguiente video...")
            time.sleep(delay)
    
    successful = sum(1 for r in results if r["success"])
    print(f"\n🏁 Subida Instagram completada: {successful}/{len(video_list)} exitosos")
    
    return results

if __name__ == "__main__":
    # Crear sesión con el sessionid proporcionado
    SESSIONID = "45402018416%3A1jVgRHQfjyzwwR%3A11%3AAYg7uCIKGEX_mwFHXqK0LUwR87bGuxRgE91X0xxt8g"
    create_instagram_session(SESSIONID, INSTAGRAM_USERNAME)
