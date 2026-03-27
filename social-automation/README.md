# 🚀 Media Flow Engine

Sistema de automatización completo para TikTok e Instagram. Descarga, procesa y republica videos automáticamente cada 2 horas.

## 📋 Características

- ✅ **Descarga automática** de videos de TikTok usando yt-dlp
- ✅ **Verificación de cuentas** - Detecta cuentas privadas/eliminadas
- ✅ **Procesamiento anti-detección** con FFmpeg (espejo, zoom, brillo, velocidad)
- ✅ **Subida a TikTok** usando Playwright con cookies
- ✅ **Subida a Instagram** usando Instagrapi
- ✅ **No repite videos** - Registro de videos ya subidos
- ✅ **GitHub Actions** - Ejecución cada 2 horas 24/7

## 🔧 Configuración

### 1. Clonar y configurar

```bash
git clone https://github.com/TU_USUARIO/media-flow-engine.git
cd media-flow-engine
pip install -r requirements.txt
playwright install chromium
```

### 2. Configurar credenciales

#### TikTok Cookies
Las cookies de TikTok deben estar en `auth/tiktok_cookies.json`. 
Para exportarlas:
1. Instala la extensión "Get Cookies Locally" en Chrome
2. Inicia sesión en TikTok
3. Exporta las cookies en formato JSON

#### Instagram Session
Ejecuta para crear la sesión:
```bash
python main.py --setup
```

### 3. Ejecutar manualmente

```bash
# Verificar cuentas fuente
python main.py --verify

# Ejecutar pipeline completo (10 videos por defecto)
python main.py

# Ejecutar con número específico de videos
python main.py 5
```

## 📁 Estructura

```
media-flow-engine/
├── auth/
│   ├── tiktok_cookies.json    # Cookies de TikTok
│   └── instagram_session.json # Sesión de Instagram
├── data/
│   ├── source_accounts.json   # Lista de cuentas verificadas
│   └── uploaded_videos.json   # Registro de videos subidos
├── logs/                      # Logs de ejecución
├── videos_raw/               # Videos descargados (temporal)
├── videos_ready/             # Videos procesados (temporal)
├── .github/workflows/
│   └── automation.yml        # GitHub Actions workflow
├── account_checker.py        # Verificador de cuentas
├── video_downloader.py       # Descargador de TikTok
├── video_processor.py        # Procesador FFmpeg
├── tiktok_uploader.py        # Subidor a TikTok
├── instagram_uploader.py     # Subidor a Instagram
├── main.py                   # Script principal
├── config.py                 # Configuración
└── requirements.txt          # Dependencias
```

## ⚙️ GitHub Actions

El workflow se ejecuta automáticamente cada 2 horas. Para activarlo:

1. Sube el código a un repositorio de GitHub
2. Ve a Settings → Actions → General
3. Habilita "Read and write permissions"
4. El workflow comenzará a ejecutarse según el schedule

### Ejecución manual
Ve a Actions → "Media Flow Engine" → Run workflow

## ⚠️ Notas importantes

- **Límites de GitHub Actions**: Los repos privados tienen 2000 min/mes gratis
- **Cookies expiran**: Renueva las cookies de TikTok cada ~30 días
- **Instagram es estricto**: Puede requerir verificación si detecta actividad inusual
- **Rate limiting**: El sistema incluye delays para evitar bloqueos

## 📊 Configuración en config.py

```python
VIDEOS_PER_BATCH = 10        # Videos por ejecución
BATCH_INTERVAL_HOURS = 2     # Frecuencia de ejecución
```

## 🔒 Seguridad

Para mayor seguridad, puedes usar GitHub Secrets:
1. Ve a Settings → Secrets → Actions
2. Añade `TIKTOK_SESSIONID` e `INSTAGRAM_SESSIONID`
3. Modifica el workflow para usar estas variables

---

⚡ **Creado con automatización en mente**
