import os
import time
import subprocess
import urllib.request
from datetime import datetime

# Sprawdzamy instalację OpenCV:
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError as e:
    OPENCV_AVAILABLE = False
    print(f"Ostrzeżenie: Błąd ładowania OpenCV: {e}")
    print("Spróbuj: pkg install opencv-python")

# Link do superszybkiego modelu sieci MobileNet-SSD (Caffe format ok. 22MB)
PROTOTXT_URL = "https://raw.githubusercontent.com/djmv/MobilNet_SSD_opencv/master/MobileNetSSD_deploy.prototxt"
MODEL_URL = "https://raw.githubusercontent.com/djmv/MobilNet_SSD_opencv/master/MobileNetSSD_deploy.caffemodel"

def download_model_if_needed():
    """Pobiera pliki sztucznej inteligencji, jeśli jeszcze ich nie ma."""
    os.makedirs("models", exist_ok=True)
    prototxt_path = "models/MobileNetSSD_deploy.prototxt"
    model_path = "models/MobileNetSSD_deploy.caffemodel"
    
    if not os.path.exists(prototxt_path):
        print("Pobieranie definicji sieci AI...")
        urllib.request.urlretrieve(PROTOTXT_URL, prototxt_path)
    
    if not os.path.exists(model_path):
        print("Pobieranie wag modelu AI (ok. 22MB) - to może chwilę potrwać...")
        urllib.request.urlretrieve(MODEL_URL, model_path)
        
    return prototxt_path, model_path

def take_photo(output_filename="snapshot.jpg", camera_id="1"):
    try:
        subprocess.run(
            ["termux-camera-photo", "-c", camera_id, output_filename],
            capture_output=True, text=True, check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False

def detect_human(image_path, net):
    """
    Przepuszcza zdjęcie przez OpenCV DNN i wykrywa człowieka.
    """
    if not OPENCV_AVAILABLE:
        return False
        
    if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
        return False
        
    image = cv2.imread(image_path)
    if image is None: 
        return False
    
    (h, w) = image.shape[:2]
    # S10 przerobi to momentalnie wykorzystując natywne binarki C++ Androida (dzięki twojej instlacji libandroid-stub!)
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 0.007843, (300, 300), 127.5)
    
    net.setInput(blob)
    detections = net.forward()
    
    found_human = False
    
    # Skanowanie wyników w klatce (bierzemy pod uwagę tylko powyżej 60% pewności)
    for i in np.arange(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        
        # 15 to indeks dla obiektu klasy "Czek" / "Osoba" w modelu MobileNetSSD
        idx = int(detections[0, 0, i, 1])
        
        if confidence > 0.60 and idx == 15:
            found_human = True
            
            # Wrysuj zieloną ramkę na dowód wykrycia!
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")
            cv2.rectangle(image, (startX, startY), (endX, endY), (0, 255, 0), 2)
            cv2.putText(image, "Czlowiek", (startX, startY - 15), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            cv2.imwrite(image_path, image)
            break
            
    return found_human

def speak(text):
    try:
        subprocess.run(["termux-tts-speak", text], capture_output=True)
    except Exception:
        pass

def main():
    print("="*40)
    print("S10 Smart Cam (Tryb OpenCV - Natywne C++)")
    print("Technologia: OpenCV DNN (Pełna Szybkość)")
    print("="*40)
    
    camera_id = "1"
    
    net = None
    if OPENCV_AVAILABLE:
        print("Trwa ładowanie silnika głębokiego uczenia w OpenCV...")
        prototxt, model = download_model_if_needed()
        net = cv2.dnn.readNetFromCaffe(prototxt, model)
        print("Gotowe. OpenCV przejął kontrolę!\n")
    
    os.makedirs("photos", exist_ok=True)
    photo_count = 0
    human_count = 0
    
    while True:
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"photos/snap_{timestamp}.jpg"
            
            start_time = time.time()
            success = take_photo(filename, camera_id)
            end_time = time.time()
            
            if success and os.path.exists(filename) and os.path.getsize(filename) > 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Zdjęcie przechwycone ({end_time - start_time:.1f}s)...")
                
                if OPENCV_AVAILABLE and net is not None:
                    is_human = detect_human(filename, net)
                    
                    if is_human:
                        print(f"   => 🚨 ROZPOZNANO SYLWETKĘ. Zbadano przez OpenCV. Plik zapamiętany w zdjęciach.")
                        speak("Dzień dobry! Zostałeś namierzony i wyłapany przez kamerę.")
                        human_count += 1
                        time.sleep(2)
                    else:
                        print(f"   => 🟢 Spokój. Usuwam pustą klatkę...")
                        os.remove(filename) 
                else:
                    print(f"   => Ostrzeżenie. Zapisano: {filename} (OpenCV uszkodzone)")
                    
                photo_count += 1
                
            time.sleep(1)
            
        except KeyboardInterrupt:
            print(f"\nUśpiono. Zbadano {photo_count} scen. Wykryto {human_count} podejrzanych.")
            break

if __name__ == "__main__":
    main()
