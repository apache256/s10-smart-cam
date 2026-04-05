import os
import time
import subprocess
import urllib.request
from datetime import datetime

# Próbujemy zaimportować OpenCV
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("Ostrzeżenie: Biblioteka cv2 (OpenCV) nie jest zainstalowana!")
    print("Aby działała AI, wpisz w Termuxie:")
    print("pkg install x11-repo")
    print("pkg install opencv python-numpy")

# URL do małego, super-szybkiego modelu Caffe MobileNet-SSD (ok. 22MB)
# W przeciwieństwie do ciężkiego YOLO, ten model działa natywnie pod OpenCV na 
# każdym procesorze i zjada bardzo mało RAM-u, idealnie pod Androida w tle!
PROTOTXT_URL = "https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/MobileNetSSD_deploy.prototxt"
MODEL_URL = "https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/MobileNetSSD_deploy.caffemodel"

def download_model_if_needed():
    """Pobiera model AI, jeśli nie ma go jeszcze w folderze."""
    os.makedirs("models", exist_ok=True)
    prototxt_path = "models/MobileNetSSD_deploy.prototxt"
    model_path = "models/MobileNetSSD_deploy.caffemodel"
    
    if not os.path.exists(prototxt_path):
        print("Pobieranie struktury modelu AI...")
        urllib.request.urlretrieve(PROTOTXT_URL, prototxt_path)
    
    if not os.path.exists(model_path):
        print("Pobieranie wag modelu AI (ok. 22MB) - to chwilę potrwa...")
        urllib.request.urlretrieve(MODEL_URL, model_path)
        
    return prototxt_path, model_path

def take_photo(output_filename="snapshot.jpg", camera_id="1"):
    """
    Kamera 0 = tył, Kamera 1 = przód (zazwyczaj)
    """
    try:
        subprocess.run(
            ["termux-camera-photo", "-c", camera_id, output_filename],
            capture_output=True, text=True, check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        return False
    except FileNotFoundError:
        return False

def detect_human(image_path, net):
    """
    Przepuszcza obraz przez małą sieć neuronową.
    Zwraca True, jeśli z pewnością > 60% wykryje człowieka.
    """
    if not OPENCV_AVAILABLE:
        return False
        
    if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
        return False
        
    image = cv2.imread(image_path)
    if image is None: 
        return False
    
    (h, w) = image.shape[:2]
    # Przeskaluj zdjęcie pod sztuczną inteligencję (optymalizacja dla procesora S10)
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 0.007843, (300, 300), 127.5)
    
    net.setInput(blob)
    detections = net.forward()
    
    found_human = False
    
    # Przeszukujemy wyniki ucięte powyżej progu pewności 0.6 (60%)
    for i in np.arange(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        
        # Klasa numer 15 w tym modelu obiektów to "osoba/człowiek"
        idx = int(detections[0, 0, i, 1])
        
        if confidence > 0.60 and idx == 15:
            found_human = True
            # Wrysuj zieloną ramkę na człowieka dla wizualnego potwierdzenia!
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")
            cv2.rectangle(image, (startX, startY), (endX, endY), (0, 255, 0), 2)
            cv2.putText(image, "Czlowiek", (startX, startY - 15), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Zapisujemy plik ze wrysowanym celownikiem (do przejrzenia później)
            cv2.imwrite(image_path, image)
            # Jeśli znaleźliśmy chociaż jednego człowieka, przerywamy skanowanie matrycy
            break
            
    return found_human

def speak(text):
    """Wypowiada tekst syntezatorem mowy smartfona"""
    try:
        subprocess.run(["termux-tts-speak", text], capture_output=True)
    except Exception:
        pass

def main():
    print("="*40)
    print("S10 Smart Cam - ETAP 2")
    print("Przednia Kamera + AI (MobileNet-SSD) + Powiadomienie Głosowe")
    print("="*40)
    print("Naciśnij Ctrl+C, aby zatrzymać.\n")
    
    # Wybieramy kamerę przednią
    camera_id = "1"
    print(f"Aktywowano aparat o ID: {camera_id} (Przód)")
    
    # Ładowanie Sztucznej Inteligencji
    net = None
    if OPENCV_AVAILABLE:
        print("Trwa ładowanie modelu i konfiguracja AI...")
        prototxt, model = download_model_if_needed()
        # Ładujemy model Caffe do modułu głębokiego uczenia w OpenCV
        net = cv2.dnn.readNetFromCaffe(prototxt, model)
        print("Gotowe. S10 analizuje otoczenie!\n")
    
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
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Klatka przechwycona ({end_time - start_time:.1f}s). Myślę...")
                
                # Uruchamiamy analizę z użyciem modelu
                if OPENCV_AVAILABLE and net is not None:
                    is_human = detect_human(filename, net)
                    
                    if is_human:
                        print(f"   => 🚨 WYKRYTO CZŁOWIEKA! Zapisano dowód w folderze photos.")
                        # S10 się do nas odezwie!
                        speak("Dzień dobry! Zostałeś zauważony.")
                        human_count += 1
                        time.sleep(2) # Dajemy mu czas na skończenie zdania
                    else:
                        print(f"   => 🟢 Czysto. (Usuwam pustą klatkę, by oszczędzać pamięć)")
                        # Super funkcja: Usuwa zdjęcie, na którym nikogo nie ma
                        # Telefon nie zapełni się śmieciowymi fotosami o rozmiarze kilku giga!
                        os.remove(filename) 
                else:
                    print(f"   => Zapisano: {filename} (ale brakuje OpenCV do oceny co na nim jest)")
                    
                photo_count += 1
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Pusty odczyt. Cykl zgubiony.")
                
            time.sleep(1) # Złapanie oddechu
            
        except KeyboardInterrupt:
            print(f"\nRozłączono. Wykonanych skanów: {photo_count}. Intruzów: {human_count}.")
            break

if __name__ == "__main__":
    main()
