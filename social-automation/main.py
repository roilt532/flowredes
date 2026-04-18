"""
Script principal de automatización
Coordina todo el flujo: descarga → procesamiento → subida
Publica 1 video por ejecución en horarios específicos
"""
import os
import sys
import json
import time
from datetime import datetime

from config import (
    VIDEOS_PER_EXECUTION, TIKTOK_COOKIES_FILE, 
    INSTAGRAM_SESSION_FILE, DATA_DIR, LOGS_DIR,
    should_post_to_tiktok, should_post_to_instagram
)
from account_checker import get_active_accounts, fetch_accounts_from_sheet, verify_all_accounts, save_verified_accounts
from video_downloader import download_batch, save_uploaded_video, clean_raw_videos
from video_processor import process_batch, clean_ready_videos
from text_detector import filter_videos_without_text, EASYOCR_AVAILABLE
from tiktok_uploader import upload_videos_to_tiktok
from instagram_uploader import upload_batch_instagram, create_instagram_session, INSTAGRAPI_AVAILABLE
from telegram_notifier import notify_start, notify_success, notify_error, notify_cookies_expired

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
    Ejecuta el pipeline completo con publicación inteligente:
    - TikTok: 6 veces al día (en horarios específicos)
    - Instagram: 3 veces al día (en horarios de máximo alcance)
    - 1 video por ejecución para parecer más humano
    """
    if videos_count is None:
        videos_count = VIDEOS_PER_EXECUTION
    
    # Determinar a qué plataformas publicar según la hora
    post_tiktok = should_post_to_tiktok()
    post_instagram = should_post_to_instagram()
    
    current_hour = datetime.utcnow().hour
    
    print("=" * 60)
    print("🚀 MEDIA FLOW ENGINE - PUBLICACIÓN INTELIGENTE")
    print("=" * 60)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🕐 Hora UTC: {current_hour}:00")
    print(f"📱 TikTok: {'✅ SÍ' if post_tiktok else '❌ NO'}")
    print(f"📸 Instagram: {'✅ SÍ' if post_instagram else '❌ NO'}")
    print(f"🎯 Videos: {videos_count}")
    print("=" * 60)
    
    # Si no toca publicar en ninguna plataforma, salir
    if not post_tiktok and not post_instagram:
        print("\n⏭️ No es hora de publicar en ninguna plataforma. Saltando...")
        log_execution(f"Hora {current_hour}:00 UTC - No es hora de publicar")
        return {"success": True, "skipped": True, "reason": "No es hora de publicar"}
    
    log_execution(f"Iniciando - TikTok: {post_tiktok}, Instagram: {post_instagram}")
    
    # Notificar inicio por Telegram
    notify_start()
    
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
        notify_error("No hay cuentas disponibles para descargar videos")
        return {"success": False, "error": "No hay cuentas disponibles"}
    
    print(f"✅ {len(accounts)} cuentas disponibles")
    
    # PASO 2: Descargar videos
    print("\n📥 PASO 2: Descargando videos...")
    download_count = videos_count + 2 if EASYOCR_AVAILABLE else videos_count
    downloaded = download_batch(download_count)
    
    if not downloaded:
        log_execution("ERROR: No se descargaron videos")
        notify_error("No se pudieron descargar videos de ninguna cuenta")
        return {"success": False, "error": "No se pudieron descargar videos"}
    
    log_execution(f"Descargados: {len(downloaded)} videos")
    
    # PASO 2.5: Filtrar videos con texto flotante
    print("\n🔍 PASO 2.5: Filtrando videos con texto...")
    if EASYOCR_AVAILABLE:
        filtered = filter_videos_without_text(downloaded)
        discarded = len(downloaded) - len(filtered)
        if discarded > 0:
            log_execution(f"Filtrados: {discarded} videos descartados por texto flotante")
        downloaded = filtered
        
        if not downloaded:
            log_execution("ERROR: Todos los videos tenían texto")
            notify_error("Todos los videos descargados tenían texto flotante")
            return {"success": False, "error": "No hay videos sin texto"}
    else:
        print("  ⏭️ Detección de texto no disponible, continuando...")
    
    # Limitar a la cantidad necesaria
    downloaded = downloaded[:videos_count]
    
    # PASO 3: Procesar videos
    print("\n🛠️ PASO 3: Procesando videos...")
    processed = process_batch(downloaded)
    
    if not processed:
        log_execution("ERROR: No se procesaron videos")
        return {"success": False, "error": "No se pudieron procesar videos"}
    
    log_execution(f"Procesados: {len(processed)} videos")
    
    # PASO 4: Subir a TikTok (si es hora)
    tiktok_results = []
    total_tiktok = 0
    
    if post_tiktok:
        print("\n📤 PASO 4: Subiendo a TikTok...")
        if os.path.exists(TIKTOK_COOKIES_FILE):
            tiktok_results = upload_videos_to_tiktok(processed)
            total_tiktok = sum(1 for r in tiktok_results if r["success"])
            log_execution(f"TikTok: {total_tiktok}/{len(processed)} subidos")
            
            if total_tiktok == 0 and len(processed) > 0:
                notify_cookies_expired()
        else:
            log_execution("ADVERTENCIA: No hay cookies de TikTok")
            print("⚠️ No hay cookies de TikTok configuradas")
    else:
        print("\n⏭️ PASO 4: Saltando TikTok (no es hora)")
    
    # PASO 5: Subir a Instagram (si es hora)
    instagram_results = []
    total_ig = 0
    
    if post_instagram:
        print("\n📤 PASO 5: Subiendo a Instagram...")
        if INSTAGRAPI_AVAILABLE and os.path.exists(INSTAGRAM_SESSION_FILE):
            instagram_results = upload_batch_instagram(processed)
            total_ig = sum(1 for r in instagram_results if r["success"])
            log_execution(f"Instagram: {total_ig}/{len(processed)} subidos")
        else:
            log_execution("ADVERTENCIA: Instagram no configurado")
            print("⚠️ Instagram no configurado")
    else:
        print("\n⏭️ PASO 5: Saltando Instagram (no es hora)")
    
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
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE EJECUCIÓN")
    print("=" * 60)
    print(f"  📥 Videos descargados: {len(downloaded)}")
    print(f"  🛠️ Videos procesados: {len(processed)}")
    if post_tiktok:
        print(f"  📱 Subidos a TikTok: {total_tiktok}")
    if post_instagram:
        print(f"  📸 Subidos a Instagram: {total_ig}")
    print("=" * 60)
    
    log_execution(f"Pipeline completado - TikTok: {total_tiktok}, Instagram: {total_ig}")
    
    # Notificar éxito por Telegram
    stats = {
        "downloaded": len(downloaded),
        "processed": len(processed),
        "tiktok_uploaded": total_tiktok,
        "instagram_uploaded": total_ig
    }
    notify_success(stats)
    
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
    
    SESSIONID = "45402018416%3AzNcRyDnQ2nMuLT%3A9%3AAYhAh8a9YhFWtHlG6d09O9JX_dJd1RLRyC5UOXK2Ew"
    from config import INSTAGRAM_USERNAME
    create_instagram_session(SESSIONID, INSTAGRAM_USERNAME)
    
    print("✅ Credenciales configuradas")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--setup":
            setup_credentials()
        elif sys.argv[1] == "--verify":
            accounts = fetch_accounts_from_sheet()
            if accounts:
                results = verify_all_accounts(accounts, max_to_check=50)
                save_verified_accounts(results)
        elif sys.argv[1].isdigit():
            run_full_pipeline(int(sys.argv[1]))
        else:
            print("Uso: python main.py [--setup|--verify|numero_videos]")
    else:
        run_full_pipeline()
