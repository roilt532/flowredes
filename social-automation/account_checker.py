"""
Verificador de cuentas de TikTok
Comprueba qué cuentas de la lista siguen activas y públicas
"""
import csv
import json
import requests
import os
import time
import random
from config import SHEET_CSV_URL, ACCOUNTS_FILE, DATA_DIR

# Headers para simular navegador real
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
}

def fetch_accounts_from_sheet():
    """Obtiene la lista de usernames desde Google Sheets"""
    print("📋 Descargando lista de cuentas desde Google Sheets...")
    try:
        response = requests.get(SHEET_CSV_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        decoded = response.content.decode('utf-8')
        reader = csv.DictReader(decoded.splitlines())
        
        accounts = []
        for row in reader:
            username = row.get('username', '').strip()
            if username:
                # Limpiar caracteres especiales y espacios
                username = username.replace('@', '').replace('"', '').strip()
                if username and len(username) > 2:
                    accounts.append(username)
        
        print(f"✅ Se encontraron {len(accounts)} cuentas en el sheet")
        return accounts
        
    except Exception as e:
        print(f"❌ Error al leer Google Sheets: {e}")
        return []

def check_account_status(username):
    """
    Verifica si una cuenta de TikTok está activa y pública
    Retorna: 'active', 'private', 'not_found', 'error'
    """
    url = f"https://www.tiktok.com/@{username}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        
        # Si redirige a página de error o login
        if "login" in response.url.lower() or response.status_code == 404:
            return "not_found"
        
        content = response.text.lower()
        
        # Verificar si la cuenta es privada
        if "this account is private" in content or "cuenta privada" in content:
            return "private"
        
        # Verificar si el usuario no existe
        if "couldn't find this account" in content or "no pudimos encontrar" in content:
            return "not_found"
        
        # Verificar si hay videos disponibles (indicador de cuenta activa)
        if '"videoCount":' in response.text or "video-feed" in content:
            return "active"
        
        # Si llegamos aquí, asumimos que está activa pero sin contenido verificable
        return "active"
        
    except requests.Timeout:
        return "error"
    except Exception as e:
        print(f"  ⚠️ Error verificando @{username}: {e}")
        return "error"

def verify_all_accounts(accounts, max_to_check=50):
    """
    Verifica el estado de las cuentas (con límite para no hacer spam)
    """
    print(f"\n🔍 Verificando estado de cuentas (máximo {max_to_check})...")
    
    results = {
        "active": [],
        "private": [],
        "not_found": [],
        "error": [],
        "unchecked": []
    }
    
    # Mezclar para verificar aleatoriamente
    shuffled = accounts.copy()
    random.shuffle(shuffled)
    
    to_check = shuffled[:max_to_check]
    unchecked = shuffled[max_to_check:]
    
    for i, username in enumerate(to_check):
        print(f"  [{i+1}/{len(to_check)}] Verificando @{username}...", end=" ")
        
        status = check_account_status(username)
        results[status].append(username)
        
        status_emoji = {
            "active": "✅",
            "private": "🔒",
            "not_found": "❌",
            "error": "⚠️"
        }
        print(status_emoji.get(status, "❓"))
        
        # Delay para evitar rate limiting
        time.sleep(random.uniform(1.5, 3.0))
    
    # Las no verificadas se asumen activas (se verificarán al descargar)
    results["unchecked"] = unchecked
    
    return results

def save_verified_accounts(results):
    """Guarda las cuentas verificadas en un archivo JSON"""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Combinar activas + no verificadas (se asumen activas)
    usable_accounts = results["active"] + results["unchecked"]
    
    data = {
        "total_usable": len(usable_accounts),
        "verified_active": len(results["active"]),
        "assumed_active": len(results["unchecked"]),
        "private": len(results["private"]),
        "not_found": len(results["not_found"]),
        "accounts": usable_accounts,
        "private_accounts": results["private"],
        "deleted_accounts": results["not_found"]
    }
    
    with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Resumen:")
    print(f"  ✅ Cuentas activas verificadas: {len(results['active'])}")
    print(f"  📋 Cuentas asumidas activas: {len(results['unchecked'])}")
    print(f"  🔒 Cuentas privadas: {len(results['private'])}")
    print(f"  ❌ Cuentas eliminadas/no encontradas: {len(results['not_found'])}")
    print(f"  📁 Total cuentas utilizables: {len(usable_accounts)}")
    print(f"\n💾 Guardado en: {ACCOUNTS_FILE}")
    
    return usable_accounts

def get_active_accounts():
    """
    Obtiene las cuentas activas (desde archivo si existe, si no verifica)
    """
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("accounts", [])
    
    # Si no existe, ejecutar verificación
    accounts = fetch_accounts_from_sheet()
    if accounts:
        results = verify_all_accounts(accounts)
        return save_verified_accounts(results)
    
    return []

if __name__ == "__main__":
    print("=" * 50)
    print("🔍 VERIFICADOR DE CUENTAS DE TIKTOK")
    print("=" * 50)
    
    accounts = fetch_accounts_from_sheet()
    
    if accounts:
        results = verify_all_accounts(accounts, max_to_check=30)
        save_verified_accounts(results)
    else:
        print("❌ No se pudieron obtener cuentas del sheet")
