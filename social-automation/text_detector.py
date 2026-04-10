"""
Detector de texto flotante en videos
Filtra videos que contienen texto superpuesto para evitar texto invertido por el efecto espejo
"""
import os
import subprocess
import tempfile

# Intentar importar easyocr
try:
    import easyocr
    EASYOCR_AVAILABLE = True
    # Inicializar reader (solo español e inglés para rapidez)
    reader = easyocr.Reader(['es', 'en'], gpu=False, verbose=False)
except ImportError:
    EASYOCR_AVAILABLE = False
    reader = None
    print("⚠️ easyocr no disponible - detección de texto desactivada")

def extract_frames(video_path, num_frames=3):
    """
    Extrae frames del video para analizar (inicio, medio, final)
    """
    frames = []
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Obtener duración del video
        duration_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        result = subprocess.run(duration_cmd, capture_output=True, text=True, timeout=30)
        duration = float(result.stdout.strip()) if result.stdout.strip() else 10
        
        # Extraer frames en 25%, 50%, 75% del video
        for i, pct in enumerate([0.25, 0.5, 0.75]):
            timestamp = duration * pct
            frame_path = os.path.join(temp_dir, f"frame_{i}.jpg")
            
            extract_cmd = [
                "ffmpeg", "-ss", str(timestamp),
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "2",
                "-vf", "scale=640:-1",  # Reducir tamaño para análisis más rápido
                frame_path,
                "-y", "-loglevel", "error"
            ]
            subprocess.run(extract_cmd, capture_output=True, timeout=30)
            
            if os.path.exists(frame_path):
                frames.append(frame_path)
        
        return frames, temp_dir
        
    except Exception as e:
        print(f"  ⚠️ Error extrayendo frames: {e}")
        return [], temp_dir

def detect_text_in_frame(frame_path, min_confidence=0.4):
    """
    Detecta si hay texto significativo en un frame usando OCR.
    Solo detecta texto flotante/superpuesto (típicamente tiene alto contraste).
    
    Returns: (tiene_texto, cantidad_de_texto)
    """
    if not EASYOCR_AVAILABLE or reader is None:
        return False, 0
    
    try:
        # Detectar texto con easyocr
        results = reader.readtext(frame_path, detail=1)
        
        # Filtrar por confianza y longitud mínima
        significant_text = []
        for (bbox, text, confidence) in results:
            # Solo contar texto con buena confianza y más de 2 caracteres
            if confidence >= min_confidence and len(text.strip()) > 2:
                significant_text.append(text)
        
        has_text = len(significant_text) >= 1  # Al menos 1 texto detectado
        return has_text, len(significant_text)
        
    except Exception as e:
        print(f"  ⚠️ Error en OCR: {e}")
        return False, 0

def has_floating_text(video_path):
    """
    Analiza si un video tiene texto flotante/superpuesto.
    Retorna True si se detecta texto en al menos 2 de 3 frames.
    
    Esto indica texto consistente (subtítulos, overlay) vs texto momentáneo.
    """
    if not EASYOCR_AVAILABLE:
        print("  ⏭️ OCR no disponible, saltando detección")
        return False
    
    print(f"  🔍 Detectando texto flotante...")
    
    frames, temp_dir = extract_frames(video_path)
    
    if not frames:
        print(f"  ⚠️ No se pudieron extraer frames")
        return False
    
    frames_with_text = 0
    
    try:
        for frame_path in frames:
            has_text, text_count = detect_text_in_frame(frame_path)
            if has_text:
                frames_with_text += 1
        
        # Limpiar frames temporales
        for frame_path in frames:
            try:
                os.remove(frame_path)
            except:
                pass
        try:
            os.rmdir(temp_dir)
        except:
            pass
            
    except Exception as e:
        print(f"  ⚠️ Error en detección: {e}")
        return False
    
    # Si 2+ de 3 frames tienen texto = texto flotante persistente
    has_floating = frames_with_text >= 2
    
    if has_floating:
        print(f"  ⚠️ Texto flotante detectado ({frames_with_text}/3 frames) - DESCARTADO")
    else:
        print(f"  ✅ Sin texto flotante ({frames_with_text}/3 frames)")
    
    return has_floating

def filter_videos_without_text(video_list):
    """
    Filtra una lista de videos, removiendo los que tienen texto flotante.
    """
    if not EASYOCR_AVAILABLE:
        print("⚠️ Detección de texto desactivada (easyocr no disponible)")
        return video_list
    
    print(f"\n🔍 FILTRO DE TEXTO - Analizando {len(video_list)} videos...")
    
    filtered = []
    discarded = 0
    
    for i, video in enumerate(video_list):
        print(f"\n[{i+1}/{len(video_list)}] {os.path.basename(video['path'])}")
        
        if not has_floating_text(video["path"]):
            filtered.append(video)
        else:
            discarded += 1
            # Eliminar video descartado
            try:
                os.remove(video["path"])
            except:
                pass
    
    print(f"\n📊 Resultado: {len(filtered)} videos OK, {discarded} descartados por texto")
    
    return filtered
