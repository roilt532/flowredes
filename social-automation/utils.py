"""
Utilidades para gestión de cookies y credenciales
"""
import json
import os
from config import AUTH_DIR, TIKTOK_COOKIES_FILE

def convert_json_to_netscape(json_file, output_file):
    """
    Convierte cookies de formato JSON a formato Netscape (para yt-dlp)
    """
    with open(json_file, 'r') as f:
        cookies = json.load(f)
    
    lines = ['# Netscape HTTP Cookie File']
    
    for c in cookies:
        domain = c.get('domain', '.tiktok.com')
        flag = 'TRUE' if domain.startswith('.') else 'FALSE'
        path = c.get('path', '/')
        secure = 'TRUE' if c.get('secure', False) else 'FALSE'
        exp = int(c.get('expirationDate', 0))
        name = c.get('name', '')
        value = c.get('value', '')
        lines.append(f'{domain}\t{flag}\t{path}\t{secure}\t{exp}\t{name}\t{value}')
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Cookies convertidas: {output_file}")

def update_tiktok_cookies(new_cookies_json):
    """
    Actualiza las cookies de TikTok desde un nuevo archivo JSON
    """
    # Copiar el nuevo archivo
    import shutil
    shutil.copy(new_cookies_json, TIKTOK_COOKIES_FILE)
    
    # Convertir a formato Netscape
    netscape_file = os.path.join(AUTH_DIR, "tiktok_cookies.txt")
    convert_json_to_netscape(TIKTOK_COOKIES_FILE, netscape_file)
    
    print("✅ Cookies de TikTok actualizadas")

def update_instagram_session(sessionid, username):
    """
    Actualiza la sesión de Instagram con un nuevo sessionid
    """
    from instagram_uploader import create_instagram_session
    create_instagram_session(sessionid, username)
    print("✅ Sesión de Instagram actualizada")

def check_cookies_expiration():
    """
    Verifica si las cookies de TikTok están próximas a expirar
    """
    import time
    
    if not os.path.exists(TIKTOK_COOKIES_FILE):
        print("❌ No hay archivo de cookies de TikTok")
        return False
    
    with open(TIKTOK_COOKIES_FILE, 'r') as f:
        cookies = json.load(f)
    
    current_time = time.time()
    soon_expiring = []
    expired = []
    
    for c in cookies:
        exp = c.get('expirationDate', 0)
        name = c.get('name', '')
        
        if exp > 0:
            days_until_expiry = (exp - current_time) / 86400
            
            if days_until_expiry < 0:
                expired.append((name, int(-days_until_expiry)))
            elif days_until_expiry < 7:
                soon_expiring.append((name, int(days_until_expiry)))
    
    if expired:
        print("⚠️ Cookies EXPIRADAS:")
        for name, days in expired:
            print(f"  - {name}: expiró hace {days} días")
    
    if soon_expiring:
        print("⚠️ Cookies que expiran pronto:")
        for name, days in soon_expiring:
            print(f"  - {name}: {days} días restantes")
    
    if not expired and not soon_expiring:
        print("✅ Todas las cookies están vigentes")
        return True
    
    return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python utils.py check        - Verificar expiración de cookies")
        print("  python utils.py convert      - Convertir cookies JSON a Netscape")
        print("  python utils.py update-ig SESSIONID USERNAME - Actualizar Instagram")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "check":
        check_cookies_expiration()
    
    elif cmd == "convert":
        netscape_file = os.path.join(AUTH_DIR, "tiktok_cookies.txt")
        convert_json_to_netscape(TIKTOK_COOKIES_FILE, netscape_file)
    
    elif cmd == "update-ig" and len(sys.argv) >= 4:
        sessionid = sys.argv[2]
        username = sys.argv[3]
        update_instagram_session(sessionid, username)
    
    else:
        print("Comando no reconocido")
