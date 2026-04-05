import os
import time
import subprocess
import urllib.request
import zipfile
from datetime import datetime

# Sprawdzamy czysto pythonowe biblioteki
try:
    from PIL import Image, ImageDraw
    import numpy as np
    import tflite_runtime.interpreter as tflite
    AI_AVAILABLE = True
except ImportError as e:
    AI_AVAILABLE = False
    print(f"Ostrzeżenie: Brak wtyczek AI w nowym trybie! Błąd: {e}")
    print("\nAby odpalić ten tryb, wpisz w konsolę te 2 komendy:")
    print("pkg install python-pillow python-numpy")
    print("pip install tflite-runtime")

# Link do małego, niezawodnego modelu od Google (tylko 4MB!):
MODEL_URL = "http://storage.googleapis.com/download.tensorflow.org/models/tflite/coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.zip"

def download_model_if_needed():
    """Pobiera model z chmury TFLite."""
    os.makedirs("models", exist_ok=True)
    zip_path = "models/model.zip"
    model_path = "models/detect.tflite"
    
    if not os.path.exists(model_path):
        print("Trwa jednorazowe pobieranie skompresowanego mózgu TFLite (ok. 4MB)...")
        urllib.request.urlretrieve(MODEL_URL, zip_path)
        print("Rozpakowywanie...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("models/")
        os.remove(zip_path) # od razu sprzątamy
        
    return model_path

def take_photo(output_filename="snapshot.jpg", camera_id="1"):
    try:
        subprocess.run(
            ["termux-camera-photo", "-c", camera_id, output_filename],
            capture_output=True, text=True, check=True
        )
        return True
    except Exception:
        return False

def detect_human(image_path, interpreter):
    """
    Używa czystego Pythona (Pillow) i natywnego TFLite.
    Brak starych bibliotek C++.
    """
    if not AI_AVAILABLE:
        return False
        
    if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
        return False
        
    try:
        # OTWIERANIE (PILLOW):
        img = Image.open(image_path).convert('RGB')
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        height = input_details[0]['shape'][1]
        width = input_details[0]['shape'][2]
        
        # PRZESKALOWANIE ZDJĘCIA (Pillow to potrafi natywnie i lekko):
        img_resized = img.resize((width, height))
        
        # Zmiana z obrazka na tablicę jedynek (tzw. tensor)
        input_data = np.expand_dims(img_resized, axis=0)
        
        # SILNIK SZACOWANIA TFLITE:
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        
        # ODKODOWANIE WYNIKÓW MODELU:
        boxes = interpreter.get_tensor(output_details[0]['index'])[0]
        classes = interpreter.get_tensor(output_details[1]['index'])[0]
        scores = interpreter.get_tensor(output_details[2]['index'])[0]
        
        found_human = False
        
        # Przeszukujemy top wyniki w klatce, czy pewność jest spora:
        for i in range(len(scores)):
            if scores[i] > 0.60:
                # W modelu TFLite COCO index odpowiadający "człowiekowi" to 0
                if int(classes[i]) == 0:
                    found_human = True
                    
                    # Wizja odnaleziona! Rysujemy mu zieloną ramkę na zdjęciu (Dowód)
                    ymin, xmin, ymax, xmax = boxes[i]
                    im_width, im_height = img.size
                    (left, right, top, bottom) = (xmin * im_width, xmax * im_width, ymin * im_height, ymax * im_height)
                    
                    draw = ImageDraw.Draw(img)
                    draw.rectangle([(left, top), (right, bottom)], outline="green", width=4)
                    img.save(image_path) 
                    break
                    
        return found_human
    except Exception as e:
        print(f"Błąd analizy macierzy: {e}")
        return False

def speak(text):
    try: # S10 musi z kimś porozmawiać
        subprocess.run(["termux-tts-speak", text], capture_output=True)
    except Exception:
        pass

def main():
    print("="*40)
    print("S10 Smart Cam (Tryb ALTERNATYWNY - Brak błędu z kompilatorem C++)")
    print("Technologia: Pillow / Numpy / TFLite")
    print("="*40)
    
    camera_id = "1"
    
    interpreter = None
    if AI_AVAILABLE:
        print("Ładowanie zoptymalizowanej mapy AI pod procesory ARM...")
        model_path = download_model_if_needed()
        interpreter = tflite.Interpreter(model_path=model_path)
        interpreter.allocate_tensors()
        print("S10 jest gotowy!\n")
    
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
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Klatka P-AI złapana ({end_time - start_time:.1f}s)...")
                
                if AI_AVAILABLE and interpreter is not None:
                    is_human = detect_human(filename, interpreter)
                    
                    if is_human:
                        print(f"   => 🚨 ROZPOZNANO SYLWETKĘ. Zapisano kadr jako: {filename}")
                        speak("Dzień dobry! Zostałeś oceniony i wykryty przez Samsunga S 10!")
                        human_count += 1
                        time.sleep(2)
                    else:
                        print(f"   => 🟢 Brak obiektów do oceny. Kasowanie wolnej przestrzeni.")
                        os.remove(filename) 
                else:
                    print(f"   => Ostrzeżenie. Zapisano: {filename} (Brak pakietów TFLite by to zbadać)")
                    
                photo_count += 1
                
            time.sleep(1)
            
        except KeyboardInterrupt:
            print(f"\nUśpiono. Moduł przejrzał: {photo_count} zdjęć. Wykryć: {human_count}.")
            break

if __name__ == "__main__":
    main()
