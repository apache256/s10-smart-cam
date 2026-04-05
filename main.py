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

# Słownik 20 klas z darmowego i lekkiego modelu MobileNet-SSD (w języku polskim dla TTS!)
CLASSES = ["tło", "samolot", "rower", "ptak", "łódka",
           "butelka", "autobus", "samochód", "kot", "krzesło",
           "krowa", "stół", "pies", "koń", "motocykl",
           "człowieka", "roslinę", "owcę", "sofę", "pociąg", "telewizor"]

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

def detect_objects(image_path, net):
    """
    Przepuszcza zdjęcie przez OpenCV C++ i wykrywa do 20 popularnych obiektów w mgnieniu oka.
    Zwraca listę nazw wykrytych obiektów na zdjęciu.
    """
    if not OPENCV_AVAILABLE:
        return []
        
    if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
        return []
        
    image = cv2.imread(image_path)
    if image is None: 
        return []
    
    (h, w) = image.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 0.007843, (300, 300), 127.5)
    
    net.setInput(blob)
    detections = net.forward()
    
    found_objects = []
    
    for i in np.arange(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        idx = int(detections[0, 0, i, 1])
        
        # Jeśli pewność powyżej 60% i wykrywamy coś z listy
        if confidence > 0.60 and idx < len(CLASSES):
            obj_name = CLASSES[idx]
            found_objects.append(obj_name)
            
            # Wrysuj czerwoną ramkę dla tego obiektu
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")
            cv2.rectangle(image, (startX, startY), (endX, endY), (0, 0, 255), 2)
            cv2.putText(image, obj_name, (startX, startY - 15), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            cv2.imwrite(image_path, image) # Zapisujemy obraz z narysowanymi rzeczami
            
    # Zwracamy listę unikalnych znalezisk
    return list(set(found_objects))

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
    event_count = 0
    
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
                    detected_things = detect_objects(filename, net)
                    
                    if len(detected_things) > 0:
                        # Łączymy znaleziska w słowa ("psa i kota")
                        things_str = ", ".join(detected_things)
                        print(f"   => 🚨 ROZPOZNANO OBIEKTY: {things_str.upper()}. Zapisano.")
                        event_count += 1
                        
                        # Telefon automatycznie mówi co widzi!
                        speak(f"Dzień dobry! Zauważyłem {things_str}.")
                        time.sleep(1.5) # Odpoczynek na wygłoszenie
                    else:
                        print(f"   => 🟢 Spokój. Usuwam pustą klatkę...")
                        os.remove(filename) 
                else:
                    print(f"   => Ostrzeżenie. Zapisano: {filename} (OpenCV uszkodzone)")
                    
                photo_count += 1
                
            time.sleep(1)
            
        except KeyboardInterrupt:
            print(f"\nUśpiono. Zbadano {photo_count} scen. Wykryto incydentów wizyjnych: {event_count}.")
            break

if __name__ == "__main__":
    main()
