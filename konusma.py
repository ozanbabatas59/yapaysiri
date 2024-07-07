import os
import json
import time
import requests
from gtts import gTTS
import pygame
import speech_recognition as sr
from datetime import datetime
from bs4 import BeautifulSoup
import locale

# Tarih formatını Türkçe olarak ayarlamak için
locale.setlocale(locale.LC_TIME, "tr_TR.UTF-8")

# Öğrenilen bilgileri kaydetmek için dosya yolu
knowledge_file = "knowledge.json"

# Bilgileri yükleme
def load_knowledge():
    if os.path.exists(knowledge_file):
        with open(knowledge_file, "r", encoding='utf-8') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}
    return {}

# Bilgileri kaydetme
def save_knowledge(knowledge):
    with open(knowledge_file, "w", encoding='utf-8') as file:
        json.dump(knowledge, file, ensure_ascii=False, indent=4)

# Sesli yanıt fonksiyonu
def speak(text):
    tts = gTTS(text=text, lang='tr')
    filename = "voice.mp3"
    tts.save(filename)
    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)  # Pygame için gerekli bekleme
    pygame.mixer.music.stop()  # Çalma işlemi bittikten sonra durdur
    pygame.mixer.quit()  # Mixer'ı kapat
    os.remove(filename)  # Dosyayı silebiliriz

# Ses tanıma fonksiyonu
def recognize_speech_from_mic():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Dinliyorum...")
        audio = recognizer.listen(source)
    
    response = {
        "success": True,
        "error": None,
        "transcription": None
    }
    
    try:
        response["transcription"] = recognizer.recognize_google(audio, language="tr-TR")
    except sr.RequestError:
        response["success"] = False
        response["error"] = "API hatası"
    except sr.UnknownValueError:
        response["error"] = "Anlaşılamayan ses"
    
    return response

# Hava durumu sorgulama fonksiyonu (Web Scraping)
def get_weather(city):
    url = f"https://www.weather-forecast.com/locations/{city}/forecasts/latest"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    try:
        weather_desc = soup.find("span", class_="phrase").text
        # Hava durumu açıklamasını Türkçe'ye çevirmek için
        weather_desc = weather_desc.replace("°C", "derece").replace("mm", "milimetre")
        return f"{city} için hava durumu: {weather_desc}."
    except AttributeError:
        return "Hava durumu bilgisi alınamadı. Lütfen şehri doğru girdiğinizden emin olun."

# Ana fonksiyon
def main():
    pygame.init()
    knowledge = load_knowledge()
    
    while True:
        print("Bir şey söyleyin (Çıkmak için 'kapat' deyin):")
        response = recognize_speech_from_mic()
        
        if response["error"]:
            print("Hata:", response["error"])
            speak("Anlaşılamayan ses. Lütfen tekrar deneyin.")
            continue
        
        if response["transcription"]:
            print("Siz: " + response["transcription"])
            user_input = response["transcription"].lower()
            
            if "merhaba" in user_input:
                speak("Merhaba!")
            elif "nasılsın" in user_input or "ne haber" in user_input:
                speak("İyiyim, teşekkür ederim. Sen nasılsın?")
            elif "kapat" in user_input:
                speak("Görüşürüz!")
                break
            elif "hava durumu" in user_input:
                speak("Hangi şehir için hava durumunu öğrenmek istersiniz?")
                response = recognize_speech_from_mic()
                if response["transcription"]:
                    city = response["transcription"].replace(" ", "-")
                    weather_info = get_weather(city)
                    speak(weather_info)
            elif "saat kaç" in user_input or "tarih nedir" in user_input:
                now = datetime.now()
                current_time = now.strftime("%H:%M")
                current_date = now.strftime("%d %B %Y %A")
                speak(f"Şu an saat {current_time}. Bugünün tarihi {current_date}.")
            elif "tanımla" in user_input:
                speak("Kaydetmek istediğiniz soruyu söyleyin.")
                response = recognize_speech_from_mic()
                if response["transcription"]:
                    question = response["transcription"]
                    speak("Bu sorunun cevabını söyleyin.")
                    response = recognize_speech_from_mic()
                    if response["transcription"]:
                        answer = response["transcription"]
                        speak(f"Şunu öğrendim: {question} - {answer}. Kaydedilsin mi?")
                        response = recognize_speech_from_mic()
                        if response["transcription"] and "evet" in response["transcription"].lower():
                            knowledge[question.lower()] = answer
                            save_knowledge(knowledge)
                            speak("Bilgi kaydedildi.")
                        else:
                            speak("Bilgi kaydedilmedi.")
            else:
                if user_input in knowledge:
                    speak(knowledge[user_input])
                else:
                    speak("Anlamadım, lütfen tekrar edin.")

# Uygulamayı başlat
if __name__ == "__main__":
    main()
