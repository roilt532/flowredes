"""
Descargador de videos de TikTok
Usa yt-dlp con cookies para máxima compatibilidad
"""
import os
import subprocess
import json
import random
import re
from datetime import datetime
from account_checker import get_active_accounts
from config import (
    VIDEOS_RAW_DIR, TIKTOK_COOKIES_FILE, 
    UPLOADED_VIDEOS_FILE, DATA_DIR, VIDEOS_PER_BATCH, AUTH_DIR
)

# Archivo de cookies en formato Netscape para yt-dlp
TIKTOK_COOKIES_TXT = os.path.join(AUTH_DIR, "tiktok_cookies.txt")

def get_uploaded_videos():
    """Obtiene la lista de videos ya subidos para no repetir"""
    if os.path.exists(UPLOADED_VIDEOS_FILE):
        with open(UPLOADED_VIDEOS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"uploaded": [], "failed": []}

def save_uploaded_video(video_id, platform="both"):
    """Registra un video como subido"""
    data = get_uploaded_videos()
    
    entry = {
        "video_id": video_id,
        "platform": platform,
        "uploaded_at": datetime.now().isoformat()
    }
    
    data["uploaded"].append(entry)
    
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(UPLOADED_VIDEOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def is_video_already_uploaded(video_id):
    """Verifica si un video ya fue subido"""
    data = get_uploaded_videos()
    uploaded_ids = [v["video_id"] for v in data.get("uploaded", [])]
    return video_id in uploaded_ids

def download_video_from_user(username, cookies_file=None):
    """
    Descarga el video más reciente de un usuario de TikTok
    Retorna: dict con info del video o None si falla
    """
    user_clean = username.replace('@', '').strip()
    url = f"https://www.tiktok.com/@{user_clean}"
    
    os.makedirs(VIDEOS_RAW_DIR, exist_ok=True)
    
    # Template para el nombre del archivo
    output_template = os.path.join(VIDEOS_RAW_DIR, f"{user_clean}_%(id)s.%(ext)s")
    
    # Archivo temporal para metadata
    info_file = os.path.join(VIDEOS_RAW_DIR, f"{user_clean}_info.json")
    
    print(f"📥 Intentando descargar de @{user_clean}...")
    
    command = [
        "yt-dlp",
        url,
        "--playlist-end", "3",      # Revisar los 3 más recientes
        "--max-downloads", "1",      # Solo descargar 1
        "--format", "mp4/best[ext=mp4]/best",
        "--output", output_template,
        "--write-info-json",         # Guardar metadata (descripción, etc)
        "--no-warnings",
        "--ignore-errors",
        "--no-check-certificates",
        "--extractor-args", "tiktok:api_hostname=api22-normal-c-alisg.tiktokv.com",
    ]
    
    # Añadir cookies si existen (formato Netscape .txt)
    if os.path.exists(TIKTOK_COOKIES_TXT):
        command.extend(["--cookies", TIKTOK_COOKIES_TXT])
    elif cookies_file and os.path.exists(cookies_file):
        command.extend(["--cookies", cookies_file])
    
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            timeout=120
        )
        
        # Buscar el archivo descargado
        for file in os.listdir(VIDEOS_RAW_DIR):
            if file.startswith(user_clean) and file.endswith('.mp4'):
                video_path = os.path.join(VIDEOS_RAW_DIR, file)
                
                # Extraer video_id del nombre
                match = re.search(r'_(\d+)\.mp4$', file)
                video_id = match.group(1) if match else file
                
                # Verificar si ya fue subido
                if is_video_already_uploaded(video_id):
                    print(f"  ⏭️ Video {video_id} ya fue subido anteriormente")
                    os.remove(video_path)
                    return None
                
                # Buscar archivo de info para la descripción
                description = ""
                info_files = [f for f in os.listdir(VIDEOS_RAW_DIR) if f.endswith('.info.json')]
                for info_f in info_files:
                    if user_clean in info_f:
                        info_path = os.path.join(VIDEOS_RAW_DIR, info_f)
                        try:
                            with open(info_path, 'r', encoding='utf-8') as f:
                                info = json.load(f)
                                description = info.get('description', '') or info.get('title', '')
                            os.remove(info_path)  # Limpiar
                        except:
                            pass
                        break
                
                print(f"  ✅ Descargado: {file}")
                return {
                    "path": video_path,
                    "video_id": video_id,
                    "username": user_clean,
                    "description": description,
                    "filename": file
                }
        
        # Si no se encontró archivo
        if "ERROR" in result.stderr or "Unable" in result.stderr:
            print(f"  ⏭️ No se pudo descargar de @{user_clean}")
        
        return None
        
    except subprocess.TimeoutExpired:
        print(f"  ⏱️ Timeout descargando de @{user_clean}")
        return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def download_batch(target_count=None):
    """
    Descarga un lote de videos de diferentes cuentas
    """
    if target_count is None:
        target_count = VIDEOS_PER_BATCH
    
    print("=" * 50)
    print(f"📥 DESCARGADOR DE VIDEOS - Objetivo: {target_count} videos")
    print("=" * 50)
    
    # Obtener cuentas activas
    accounts = get_active_accounts()
    if not accounts:
        print("❌ No hay cuentas disponibles")
        return []
    
    print(f"📋 {len(accounts)} cuentas disponibles")
    
    # Mezclar para variedad
    random.shuffle(accounts)
    
    downloaded = []
    attempts = 0
    max_attempts = target_count * 3  # Intentar con más cuentas por si fallan
    
    # Verificar si hay archivo de cookies
    cookies_file = TIKTOK_COOKIES_FILE if os.path.exists(TIKTOK_COOKIES_FILE) else None
    
    for username in accounts:
        if len(downloaded) >= target_count:
            break
        
        if attempts >= max_attempts:
            print(f"⚠️ Alcanzado límite de intentos ({max_attempts})")
            break
        
        attempts += 1
        result = download_video_from_user(username, cookies_file)
        
        if result:
            downloaded.append(result)
            print(f"  📊 Progreso: {len(downloaded)}/{target_count}")
    
    print(f"\n🏁 Descarga completada: {len(downloaded)}/{target_count} videos")
    return downloaded

def clean_raw_videos():
    """Limpia la carpeta de videos crudos"""
    if os.path.exists(VIDEOS_RAW_DIR):
        for file in os.listdir(VIDEOS_RAW_DIR):
            filepath = os.path.join(VIDEOS_RAW_DIR, file)
            try:
                os.remove(filepath)
            except:
                pass
    print("🧹 Carpeta de videos crudos limpiada")

if __name__ == "__main__":
    videos = download_batch(5)  # Prueba con 5 videos
    print(f"\n📦 Videos descargados:")
    for v in videos:
        print(f"  - {v['filename']}: {v['description'][:50]}...")
