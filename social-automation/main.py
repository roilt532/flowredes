"""
Script principal de automatización
Coordina todo el flujo: descarga → procesamiento → subida
"""
import os
import sys
import json
import time
from datetime import datetime

from config import (
    VIDEOS_PER_BATCH, TIKTOK_COOKIES_FILE, 
    INSTAGRAM_SESSION_FILE, DATA_DIR, LOGS_DIR
)
from account_checker import get_active_accounts, fetch_accounts_from_sheet, verify_all_accounts, save_verified_accounts
from video_downloader import download_batch, save_uploaded_video, clean_raw_videos
from video_processor import process_batch, clean_ready_videos
from tiktok_uploader import upload_videos_to_tiktok
from instagram_uploader import upload_batch_instagram, create_instagram_session, INSTAGRAPI_AVAILABLE

def log_execution(message):
    """Registra la ejecución en un log"""
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file = os.path.join(LOGS_DIR, "execution.log")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")
    
    print(message)

def run_full_pipeline(videos_count=None):
    """
    Ejecuta el pipeline completo:
    1. Verificar cuentas (si es necesario)
    2. Descargar videos
    3. Procesar videos
    4. Subir a TikTok
    5. Subir a Instagram
    """
    if videos_count is None:
        videos_count = VIDEOS_PER_BATCH
    
    print("=" * 60)
    print("🚀 MEDIA FLOW ENGINE - AUTOMATIZACIÓN DE REDES SOCIALES")
    print("=" * 60)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Objetivo: {videos_count} videos")
    print("=" * 60)
    
    log_execution(f"Iniciando pipeline - Objetivo: {videos_count} videos")
    
    # PASO 1: Verificar que tenemos cuentas
    print("\n📋 PASO 1: Verificando cuentas fuente...")
    accounts = get_active_accounts()
    
    if not accounts:
        log_execution("ERROR: No hay cuentas disponibles")
        print("❌ No hay cuentas disponibles. Ejecutando verificación...")
        
        all_accounts = fetch_accounts_from_sheet()
        if all_accounts:
            results = verify_all_accounts(all_accounts, max_to_check=50)
            accounts = save_verified_accounts(results)
    
    if not accounts:
        log_execution("ERROR: No se pudieron obtener cuentas")
        return {"success": False, "error": "No hay cuentas disponibles"}
    
    print(f"✅ {len(accounts)} cuentas disponibles")
    
    # PASO 2: Descargar videos
    print("\n📥 PASO 2: Descargando videos...")
    downloaded = download_batch(videos_count)
    
    if not downloaded:
        log_execution("ERROR: No se descargaron videos")
        return {"success": False, "error": "No se pudieron descargar videos"}
    
    log_execution(f"Descargados: {len(downloaded)} videos")
    
    # PASO 3: Procesar videos
    print("\n🛠️ PASO 3: Procesando videos...")
    processed = process_batch(downloaded)
    
    if not processed:
        log_execution("ERROR: No se procesaron videos")
        return {"success": False, "error": "No se pudieron procesar videos"}
    
    log_execution(f"Procesados: {len(processed)} videos")
    
    # PASO 4: Subir a TikTok
    print("\n📤 PASO 4: Subiendo a TikTok...")
    tiktok_results = []
    
    if os.path.exists(TIKTOK_COOKIES_FILE):
        tiktok_results = upload_videos_to_tiktok(processed)
        tiktok_success = sum(1 for r in tiktok_results if r["success"])
        log_execution(f"TikTok: {tiktok_success}/{len(processed)} subidos")
    else:
        log_execution("ADVERTENCIA: No hay cookies de TikTok, omitiendo subida")
        print("⚠️ No hay cookies de TikTok configuradas")
    
    # PASO 5: Subir a Instagram
    print("\n📤 PASO 5: Subiendo a Instagram...")
    instagram_results = []
    
    if INSTAGRAPI_AVAILABLE and os.path.exists(INSTAGRAM_SESSION_FILE):
        instagram_results = upload_batch_instagram(processed)
        ig_success = sum(1 for r in instagram_results if r["success"])
        log_execution(f"Instagram: {ig_success}/{len(processed)} subidos")
    else:
        log_execution("ADVERTENCIA: Instagram no configurado, omitiendo subida")
        print("⚠️ Instagram no configurado")
    
    # PASO 6: Registrar videos subidos
    print("\n📝 PASO 6: Registrando videos...")
    for video in processed:
        tiktok_ok = any(r["video_id"] == video["video_id"] and r["success"] 
                       for r in tiktok_results)
        ig_ok = any(r["video_id"] == video["video_id"] and r["success"] 
                   for r in instagram_results)
        
        if tiktok_ok or ig_ok:
            platform = "both" if (tiktok_ok and ig_ok) else ("tiktok" if tiktok_ok else "instagram")
            save_uploaded_video(video["video_id"], platform)
    
    # PASO 7: Limpieza
    print("\n🧹 PASO 7: Limpiando archivos temporales...")
    clean_raw_videos()
    clean_ready_videos()
    
    # Resumen
    total_tiktok = sum(1 for r in tiktok_results if r["success"]) if tiktok_results else 0
    total_ig = sum(1 for r in instagram_results if r["success"]) if instagram_results else 0
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE EJECUCIÓN")
    print("=" * 60)
    print(f"  📥 Videos descargados: {len(downloaded)}")
    print(f"  🛠️ Videos procesados: {len(processed)}")
    print(f"  📱 Subidos a TikTok: {total_tiktok}")
    print(f"  📸 Subidos a Instagram: {total_ig}")
    print("=" * 60)
    
    log_execution(f"Pipeline completado - TikTok: {total_tiktok}, Instagram: {total_ig}")
    
    return {
        "success": True,
        "downloaded": len(downloaded),
        "processed": len(processed),
        "tiktok_uploaded": total_tiktok,
        "instagram_uploaded": total_ig
    }

def setup_credentials():
    """Configura las credenciales iniciales"""
    print("🔧 Configurando credenciales...")
    
    # Crear sesión de Instagram
    SESSIONID = "45402018416%3A1jVgRHQfjyzwwR%3A11%3AAYg7uCIKGEX_mwFHXqK0LUwR87bGuxRgE91X0xxt8g"
    from config import INSTAGRAM_USERNAME
    create_instagram_session(SESSIONID, INSTAGRAM_USERNAME)
    
    print("✅ Credenciales configuradas")

if __name__ == "__main__":
    # Argumentos de línea de comandos
    if len(sys.argv) > 1:
        if sys.argv[1] == "--setup":
            setup_credentials()
        elif sys.argv[1] == "--verify":
            # Solo verificar cuentas
            accounts = fetch_accounts_from_sheet()
            if accounts:
                results = verify_all_accounts(accounts, max_to_check=50)
                save_verified_accounts(results)
        elif sys.argv[1].isdigit():
            # Número de videos personalizado
            run_full_pipeline(int(sys.argv[1]))
        else:
            print("Uso: python main.py [--setup|--verify|numero_videos]")
    else:
        # Ejecución normal
        run_full_pipeline()
