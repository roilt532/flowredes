"""
Subidor de videos a TikTok usando Playwright
Usa cookies para autenticación y técnicas anti-detección
"""
import asyncio
import os
import json
import random
from playwright.async_api import async_playwright
from config import TIKTOK_COOKIES_FILE, LOGS_DIR

# User agent móvil para mejor compatibilidad
USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"

async def human_delay(min_sec=1, max_sec=3):
    """Simula delay humano"""
    await asyncio.sleep(random.uniform(min_sec, max_sec))

async def close_popups(page):
    """Cierra popups y avisos comunes de TikTok"""
    popup_selectors = [
        "button:has-text('Got it')",
        "button:has-text('Entendido')",
        "button:has-text('Accept')",
        "button:has-text('Aceptar')",
        "button:has-text('Turn on')",
        "button:has-text('Cancel')",
        "button:has-text('Not now')",
        "button:has-text('Ahora no')",
        "[data-e2e='modal-close-icon']",
        ".modal-close-btn",
    ]
    
    for selector in popup_selectors:
        try:
            btn = page.locator(selector).first
            if await btn.is_visible(timeout=2000):
                await btn.click()
                await human_delay(1, 2)
        except:
            continue

async def upload_to_tiktok(video_path, description, cookies_file=None):
    """
    Sube un video a TikTok
    Retorna: True si éxito, False si falla
    """
    print(f"🎬 Subiendo a TikTok: {os.path.basename(video_path)}")
    
    if not os.path.exists(video_path):
        print(f"  ❌ Video no encontrado: {video_path}")
        return False
    
    async with async_playwright() as p:
        # Lanzar navegador con opciones anti-detección
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        )
        
        context = await browser.new_context(
            user_agent=USER_AGENT,
            viewport={'width': 390, 'height': 844},  # Tamaño móvil
            locale='es-ES',
            timezone_id='Europe/Madrid',
        )
        
        # Inyectar script anti-detección
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = {runtime: {}};
        """)
        
        page = await context.new_page()
        
        try:
            # Cargar cookies
            if cookies_file and os.path.exists(cookies_file):
                print("  📦 Cargando cookies...")
                with open(cookies_file, 'r') as f:
                    cookies = json.load(f)
                await context.add_cookies(cookies)
            else:
                print("  ⚠️ No hay archivo de cookies")
                await browser.close()
                return False
            
            # Ir a la página de subida
            print("  🌐 Navegando a TikTok Studio...")
            await page.goto("https://www.tiktok.com/tiktokstudio/upload", 
                          wait_until="domcontentloaded", 
                          timeout=90000)
            
            await human_delay(5, 8)
            await close_popups(page)
            
            # Verificar si estamos logueados
            if "login" in page.url.lower():
                print("  ❌ No se pudo iniciar sesión (cookies expiradas)")
                await take_screenshot(page, "login_required")
                await browser.close()
                return False
            
            # Buscar el input de archivo
            print("  📤 Subiendo archivo...")
            file_input = page.locator('input[type="file"]')
            await file_input.wait_for(state="attached", timeout=30000)
            await file_input.set_input_files(video_path)
            
            await human_delay(3, 5)
            
            # Esperar a que se procese el video
            print("  ⏳ Esperando procesamiento del video...")
            await page.wait_for_timeout(15000)  # TikTok necesita tiempo
            
            await close_popups(page)
            
            # Escribir descripción
            print("  📝 Escribiendo descripción...")
            try:
                # Intentar varios selectores para el campo de descripción
                caption_selectors = [
                    '.public-DraftEditor-content',
                    '[data-e2e="caption-editor"]',
                    '.caption-editor',
                    'div[contenteditable="true"]'
                ]
                
                caption_box = None
                for selector in caption_selectors:
                    try:
                        cap = page.locator(selector).first
                        if await cap.is_visible(timeout=5000):
                            caption_box = cap
                            break
                    except:
                        continue
                
                if caption_box:
                    await caption_box.click()
                    await human_delay(0.5, 1)
                    
                    # Limpiar y escribir
                    await page.keyboard.press("Control+a")
                    await page.keyboard.type(description, delay=random.randint(30, 80))
                    
            except Exception as e:
                print(f"  ⚠️ No se pudo escribir descripción: {e}")
            
            await human_delay(2, 4)
            await close_popups(page)
            
            # Buscar y hacer clic en el botón de publicar
            print("  🚀 Publicando...")
            publish_selectors = [
                'button[data-e2e="post_video_button"]',
                'button:has-text("Post")',
                'button:has-text("Publicar")',
                '.post-button',
            ]
            
            published = False
            for selector in publish_selectors:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=5000):
                        # Esperar a que esté habilitado
                        await btn.wait_for(state="visible", timeout=60000)
                        await human_delay(1, 2)
                        await btn.click(force=True)
                        published = True
                        break
                except:
                    continue
            
            if not published:
                print("  ❌ No se encontró el botón de publicar")
                await take_screenshot(page, "no_publish_button")
                await browser.close()
                return False
            
            # Esperar confirmación
            print("  ⏳ Esperando confirmación...")
            await page.wait_for_timeout(15000)
            
            # Verificar éxito
            success_indicators = ["uploaded", "success", "publicado", "éxito"]
            page_content = await page.content()
            
            if any(ind in page_content.lower() for ind in success_indicators):
                print("  ✅ ¡Video publicado en TikTok!")
                await browser.close()
                return True
            
            # Si no hay indicador claro, asumimos éxito si no hay error
            print("  ✅ Video enviado (verificar manualmente)")
            await take_screenshot(page, "upload_complete")
            await browser.close()
            return True
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            await take_screenshot(page, "error")
            await browser.close()
            return False

async def take_screenshot(page, name):
    """Guarda screenshot para debug"""
    os.makedirs(LOGS_DIR, exist_ok=True)
    path = os.path.join(LOGS_DIR, f"tiktok_{name}.png")
    try:
        await page.screenshot(path=path)
        print(f"  📸 Screenshot guardado: {path}")
    except:
        pass

async def upload_batch_tiktok(video_list, cookies_file=None):
    """
    Sube un lote de videos a TikTok
    video_list: lista de dicts con {path, description}
    """
    print("=" * 50)
    print(f"📤 SUBIDA A TIKTOK - {len(video_list)} videos")
    print("=" * 50)
    
    if cookies_file is None:
        cookies_file = TIKTOK_COOKIES_FILE
    
    results = []
    
    for i, video in enumerate(video_list):
        print(f"\n[{i+1}/{len(video_list)}]")
        
        success = await upload_to_tiktok(
            video["path"],
            video["description"],
            cookies_file
        )
        
        results.append({
            "video_id": video.get("video_id"),
            "success": success,
            "platform": "tiktok"
        })
        
        # Delay entre uploads para evitar rate limiting
        if i < len(video_list) - 1:
            delay = random.randint(30, 60)
            print(f"  ⏳ Esperando {delay}s antes del siguiente video...")
            await asyncio.sleep(delay)
    
    successful = sum(1 for r in results if r["success"])
    print(f"\n🏁 Subida TikTok completada: {successful}/{len(video_list)} exitosos")
    
    return results

def upload_videos_to_tiktok(video_list, cookies_file=None):
    """Wrapper síncrono para upload_batch_tiktok"""
    return asyncio.run(upload_batch_tiktok(video_list, cookies_file))

if __name__ == "__main__":
    # Prueba
    print("Este módulo debe ser importado, no ejecutado directamente")
