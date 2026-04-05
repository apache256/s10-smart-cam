import os
import time
import subprocess
from datetime import datetime

def take_photo(output_filename="snapshot.jpg", camera_id="0"):
    """
    Wykonuje zdjęcie używając systemowej komendy Termux:API.
    """
    try:
        # Wywołujemy termux-camera-photo
        # Opcja -c pozwala wybrać aparat (0 zazwyczaj tylny, 1 przedni)
        result = subprocess.run(
            ["termux-camera-photo", "-c", camera_id, output_filename],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Błąd komendy termux-camera-photo: {e.stderr}")
        return False
    except FileNotFoundError:
        print("Błąd: Nie znaleziono komendy termux-camera-photo.")
        print("Upewnij się, że masz zainstalowaną aplikację Termux:API ze sklepu F-Droid oraz pakiet w Termuxie: pkg install termux-api")
        return False

def main():
    print("="*40)
    print("S10 Smart Cam - Etap 1: Testowanie robienia zdjęć")
    print("="*40)
    print("Naciśnij Ctrl+C, aby zatrzymać aplikację.\n")
    
    # Tworzymy folder na zdjęcia testowe
    os.makedirs("photos", exist_ok=True)
    
    # Identyfikator aparatu (0 zazwyczaj tylny główny, zależy od telefonu)
    camera_id = "0" 
    
    try:
        photo_count = 0
        while True:
            # Tworzymy unikalną nazwę dla każdego zdjęcia na podstawie czasu
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"photos/snap_{timestamp}.jpg"
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Pstryk! Wykonuję zdjęcie {photo_count + 1}...")
            
            start_time = time.time()
            success = take_photo(filename, camera_id)
            end_time = time.time()
            
            if success:
                # Sprawdzamy czy plik faktycznie powstał i ile zajmuje miejsca
                if os.path.exists(filename):
                    size_kb = os.path.getsize(filename) / 1024
                    print(f"   -> Sukces! Zapisano: {filename} (Rozmiar: {size_kb:.1f} KB, Czas: {end_time - start_time:.2f}s)")
                    photo_count += 1
                else:
                    print(f"   -> Komenda na pozór się udała, ale nie znaleziono pliku {filename}!")
            else:
                print(f"   -> Wystąpił błąd podczas próby wykonania zdjęcia.")
            
            # Pauza 1 sekunda (w rzeczywistości pętla potrwa ok 1.5 - 2s jeśli dojdzie czas sprzętowy kamerki)
            # Na tym etapie sprawdzimy ile fizycznie S10 potrzebuje czasu na przeładowanie sensora.
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\nZakończono działanie. Łącznie zrobiono zdjęć: {photo_count}")

if __name__ == "__main__":
    main()
