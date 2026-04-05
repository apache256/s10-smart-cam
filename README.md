# S10 Smart Cam Test

Testowy projekt do sprawdzenia działania poleceń `termux-api` oraz szybkiego rejestrowania klatek na telefonie z Androidem (Samsung S10).

## Instalacja

1. Pobierz [Termux](https://f-droid.org/en/packages/com.termux/) ze sklepu F-Droid (nie z Google Play!).
2. Pobierz [Termux:API](https://f-droid.org/en/packages/com.termux.api/) także z F-Droid i zainstaluj na telefonie.
3. Włącz aplikację Termux i wpisz (by zainstalować uprawnienia API i Pythona):
   ```bash
   pkg update && pkg upgrade
   pkg install python git termux-api
   ```
4. Nakieruj aplikację Termux na swój aparat – może poprosić o dostęp do kamery podczas pierwszego użycia API.

## Jak uruchomić z GitHuba

1. Sklonuj to repozytorium do Termuxa na telefonie:
   ```bash
   git clone <URL_TWOJEGO_REPOZYTORIUM_GITHUB>
   cd s10-smart-cam
   ```
2. Uruchom skrypt główny:
   ```bash
   python main.py
   ```
3. Skrypt zacznie co sekundę pstrykać fotki i zapisywać do folderu `photos/`.
4. Przerwij skrypt za pomocą kombinacji `Ctrl + C` (w Termuxie możesz kliknąć guzik "CTRL" na pasku u dołu i następnie literę `c` na klawiaturze).
