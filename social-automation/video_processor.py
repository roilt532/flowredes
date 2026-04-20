"""
Procesador de videos con FFmpeg
Aplica transformaciones anti-detección para evitar que las plataformas
detecten que son videos resubidos
"""
import os
import subprocess
import random
from config import VIDEOS_RAW_DIR, VIDEOS_READY_DIR, VIDEO_CRF, VIDEO_PRESET, AUDIO_BITRATE

def process_video(input_path, output_path):
    """
    Aplica transformaciones al video para evitar detección:
    1. Espejo horizontal (flip)
    2. Pequeño zoom y recorte
    3. Ajuste sutil de brillo/contraste
    4. Micro-cambio de velocidad
    5. Limpieza de metadatos
    """
    print(f"🛠️ Procesando: {os.path.basename(input_path)}")
    
    # Variaciones aleatorias para cada video
    zoom_factor = random.uniform(1.05, 1.12)  # 5-12% zoom
    brightness = random.uniform(0.01, 0.04)   # Brillo sutil
    contrast = random.uniform(1.02, 1.08)     # Contraste sutil
    speed = random.uniform(1.005, 1.02)       # 0.5-2% más rápido
    
    # Filtros de video
    vf_filters = (
        f"hflip,"                                    # Espejo horizontal
        f"scale=iw*{zoom_factor}:-1,"               # Zoom
        f"crop=iw/{zoom_factor}:ih/{zoom_factor},"  # Recorte para mantener ratio
        f"eq=contrast={contrast}:brightness={brightness},"  # Color
        f"setpts={1/speed}*PTS"                     # Velocidad video
    )
    
    # Filtro de audio (velocidad)
    af_filter = f"atempo={speed}"
    
    command = [
        "ffmpeg",
        "-i", input_path,
        "-vf", vf_filters,
        "-af", af_filter,
        "-map_metadata", "-1",           # Eliminar metadatos originales
        "-metadata", "title=",           # Limpiar título
        "-metadata", "comment=",         # Limpiar comentarios
        "-metadata", "description=",     # Limpiar descripción
        "-c:v", "libx264",
        "-preset", VIDEO_PRESET,         # Calidad mejorada
        "-crf", str(VIDEO_CRF),          # Mejor calidad
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,           # Mejor audio
        output_path,
        "-y"                             # Sobrescribir si existe
    ]
    
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            timeout=300
        )
        
        if result.returncode == 0:
            print(f"  ✅ Procesado: {os.path.basename(output_path)}")
            print(f"     Transformaciones: zoom={zoom_factor:.2f}x, brillo={brightness:.3f}, velocidad={speed:.3f}x")
            return True
        else:
            print(f"  ❌ Error FFmpeg: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"  ⏱️ Timeout procesando video")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def enhance_description(original_description):
    """
    Devuelve solo hashtags virales (sin descripción de texto)
    """
    import random
    
    # Hashtags virales para máximo alcance
    viral_hashtags = [
        "#fyp", "#foryou", "#viral", "#parati", "#foryoupage",
        "#trending", "#xyzbca", "#viralvideo"
    ]
    
    # Seleccionar 4-5 hashtags aleatorios
    num_hashtags = random.randint(4, 5)
    selected = random.sample(viral_hashtags, num_hashtags)
    
    return " ".join(selected)

def process_batch(video_list):
    """
    Procesa un lote de videos
    video_list: lista de dicts con {path, video_id, username, description}
    """
    print("=" * 50)
    print(f"🛠️ PROCESADOR DE VIDEOS - {len(video_list)} videos")
    print("=" * 50)
    
    os.makedirs(VIDEOS_READY_DIR, exist_ok=True)
    
    processed = []
    
    for i, video in enumerate(video_list):
        print(f"\n[{i+1}/{len(video_list)}]")
        
        input_path = video["path"]
        output_filename = f"ready_{video['username']}_{video['video_id']}.mp4"
        output_path = os.path.join(VIDEOS_READY_DIR, output_filename)
        
        success = process_video(input_path, output_path)
        
        if success:
            # Mejorar descripción
            enhanced_desc = enhance_description(video.get("description", ""))
            
            processed.append({
                "path": output_path,
                "video_id": video["video_id"],
                "username": video["username"],
                "original_description": video.get("description", ""),
                "description": enhanced_desc,
                "filename": output_filename
            })
            
            # Eliminar video crudo
            try:
                os.remove(input_path)
            except:
                pass
    
    print(f"\n🏁 Procesamiento completado: {len(processed)}/{len(video_list)} videos")
    return processed

def clean_ready_videos():
    """Limpia la carpeta de videos listos"""
    if os.path.exists(VIDEOS_READY_DIR):
        for file in os.listdir(VIDEOS_READY_DIR):
            filepath = os.path.join(VIDEOS_READY_DIR, file)
            try:
                os.remove(filepath)
            except:
                pass
    print("🧹 Carpeta de videos listos limpiada")

if __name__ == "__main__":
    # Prueba: procesar videos existentes en raw
    test_videos = []
    if os.path.exists(VIDEOS_RAW_DIR):
        for file in os.listdir(VIDEOS_RAW_DIR):
            if file.endswith('.mp4'):
                test_videos.append({
                    "path": os.path.join(VIDEOS_RAW_DIR, file),
                    "video_id": file.split('_')[-1].replace('.mp4', ''),
                    "username": file.split('_')[0],
                    "description": "Video de prueba"
                })
    
    if test_videos:
        process_batch(test_videos)
    else:
        print("No hay videos en la carpeta raw para procesar")
