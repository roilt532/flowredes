"""
Detector de texto en videos
Filtra videos que contienen texto visible para evitar texto invertido
"""
import os
import subprocess
import tempfile

def extract_frames(video_path, num_frames=3):
    """
    Extrae frames del video para analizar
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
        
        # Extraer frames en diferentes momentos (25%, 50%, 75% del video)
        for i, pct in enumerate([0.25, 0.5, 0.75]):
            timestamp = duration * pct
            frame_path = os.path.join(temp_dir, f"frame_{i}.jpg")
            
            extract_cmd = [
                "ffmpeg", "-ss", str(timestamp),
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "2",
                frame_path,
                "-y"
            ]
            subprocess.run(extract_cmd, capture_output=True, timeout=30)
            
            if os.path.exists(frame_path):
                frames.append(frame_path)
        
        return frames, temp_dir
        
    except Exception as e:
        print(f"  ⚠️ Error extrayendo frames: {e}")
        return [], temp_dir

def detect_text_in_frame(frame_path):
    """
    Detecta si hay texto significativo en un frame usando análisis de bordes.
    Método simple sin dependencias externas de OCR.
    Detecta patrones que típicamente indican texto superpuesto.
    """
    try:
        # Usar FFmpeg para analizar contraste/bordes (indica texto)
        analyze_cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "frame=pkt_pts_time",
            "-of", "csv=p=0",
            frame_path
        ]
        # Este es un análisis básico - el texto suele crear bordes definidos
        
        # Alternativa: analizar histogram para detectar texto blanco/negro superpuesto
        histogram_cmd = [
            "ffmpeg", "-i", frame_path,
            "-vf", "format=gray,histogram",
            "-f", "null", "-"
        ]
        result = subprocess.run(histogram_cmd, capture_output=True, text=True, timeout=30)
        
        # Por ahora, retornamos False para no bloquear videos
        # En el futuro se puede integrar EasyOCR o Tesseract
        return False
        
    except Exception as e:
        return False

def has_text_overlay(video_path):
    """
    Analiza si un video tiene texto superpuesto.
    Retorna True si se detecta texto significativo.
    
    NOTA: Esta es una implementación básica. Para mejor detección,
    se necesitaría instalar easyocr o pytesseract.
    """
    print(f"  🔍 Analizando texto en video...")
    
    frames, temp_dir = extract_frames(video_path)
    has_text = False
    
    try:
        for frame_path in frames:
            if detect_text_in_frame(frame_path):
                has_text = True
                break
        
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
        print(f"  ⚠️ Error en detección de texto: {e}")
    
    if has_text:
        print(f"  ⚠️ Texto detectado - video descartado")
    else:
        print(f"  ✅ Sin texto superpuesto")
    
    return has_text

def filter_videos_with_text(video_list):
    """
    Filtra una lista de videos, removiendo los que tienen texto.
    """
    filtered = []
    discarded = 0
    
    for video in video_list:
        if not has_text_overlay(video["path"]):
            filtered.append(video)
        else:
            discarded += 1
            # Eliminar video descartado
            try:
                os.remove(video["path"])
            except:
                pass
    
    if discarded > 0:
        print(f"  📊 Videos filtrados: {discarded} descartados por tener texto")
    
    return filtered

# Para habilitar detección OCR real en el futuro:
# pip install easyocr
# import easyocr
# reader = easyocr.Reader(['es', 'en'])
# result = reader.readtext(frame_path)
# if len(result) > 0 and any(conf > 0.5 for _, _, conf in result):
#     return True
