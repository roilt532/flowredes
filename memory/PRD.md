# Media Flow Engine - PRD

## Problema Original
Sistema de automatización completo para TikTok e Instagram que:
- Descarga videos de cuentas de TikTok listadas en un Excel de Google Sheets
- Procesa los videos con transformaciones anti-detección (espejo, zoom, brillo, velocidad)
- Sube automáticamente a TikTok e Instagram
- Ejecuta cada 2 horas, 24/7, usando GitHub Actions
- Todo con herramientas gratuitas

## Cuentas Destino
- **TikTok**: fishsinner._ (escobaralvaro698@gmail.com)
- **Instagram**: lennyyolosa (escobaralvaro698@gmail.com)

## Arquitectura
```
/app/social-automation/
├── account_checker.py    # Verifica cuentas activas/privadas/eliminadas
├── video_downloader.py   # Descarga con yt-dlp + cookies
├── video_processor.py    # FFmpeg transformaciones anti-detección
├── tiktok_uploader.py    # Playwright + cookies
├── instagram_uploader.py # Instagrapi + sessionid
├── main.py               # Orquestador principal
├── config.py             # Configuración central
├── utils.py              # Utilidades (renovar cookies)
├── auth/                 # Cookies y sesiones
├── data/                 # Lista de cuentas, registro de subidas
└── .github/workflows/    # GitHub Actions (cada 2 horas)
```

## Lo Implementado (2026-03-27)
- ✅ Verificador de cuentas (363 cuentas del Excel verificadas)
- ✅ Descargador de videos con cookies TikTok
- ✅ Procesador FFmpeg con transformaciones aleatorias
- ✅ Subidor TikTok con Playwright
- ✅ Subidor Instagram con Instagrapi
- ✅ Sistema de no-repetición de videos
- ✅ GitHub Actions workflow cada 2 horas
- ✅ Utilidades para renovar cookies

## Probado
- ✅ Verificación de cuentas: 363 cuentas activas
- ✅ Descarga de video: rociiodonate funciona
- ✅ Procesamiento FFmpeg: transformaciones aplicadas correctamente
- ⚠️ Subida TikTok: requiere cookies actualizadas
- ⚠️ Subida Instagram: requiere verificar sessionid

## Próximos Pasos (P0)
1. Renovar cookies de TikTok (algunas expiraron)
2. Probar subida real a TikTok
3. Probar subida real a Instagram
4. Subir proyecto a GitHub del usuario
5. Activar GitHub Actions

## Backlog (P1/P2)
- Añadir proxy rotation para evitar bloqueos
- Dashboard web para monitorear estadísticas
- Notificaciones por Telegram/Discord cuando hay errores
- Soporte para más plataformas (YouTube Shorts, etc.)

## Credenciales
Ver /app/social-automation/auth/ para cookies y sesiones
