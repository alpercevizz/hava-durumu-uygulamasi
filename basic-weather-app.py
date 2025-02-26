import requests
import json
import os
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

# API Anahtarları
API_KEY_WEATHER = "0d24fa453aa4f2e54f381ed1368f9b5f"
API_KEY_CURRENCY = "f0018769f28c2c5f77b13c59"
JSON_DOSYA = "hava_durumu.json"

# Döviz kuru alma fonksiyonu
def doviz_kuru_cek(para_birimi):
    url = f"https://v6.exchangerate-api.com/v6/{API_KEY_CURRENCY}/latest/USD"
    
    try:
        response = requests.get(url)
        data = response.json()
        return data["conversion_rates"].get(para_birimi, "Bilinmiyor")
    except:
        return "Bilinmiyor"

# Hava durumu alma fonksiyonu
def hava_durumu_cek():
    sehir = sehir_entry.get().strip()
    if not sehir:
        messagebox.showerror("Hata", "Lütfen bir şehir adı girin!")
        return

    url = f"http://api.openweathermap.org/data/2.5/forecast?q={sehir}&appid={API_KEY_WEATHER}&units=metric"
    
    try:
        response = requests.get(url)
        data = response.json()

        if data["cod"] != "200":
            messagebox.showerror("Hata", "Şehir bulunamadı! Lütfen geçerli bir şehir girin.")
            return

        country_code = data["city"]["country"]
        para_birimleri = {"TR": "TRY", "US": "USD", "GB": "GBP", "DE": "EUR", "FR": "EUR"}
        para_birimi = para_birimleri.get(country_code, "USD")

        tahminler = {}
        for entry in data["list"]:
            tarih = entry["dt_txt"].split(" ")[0]
            sicaklik = int(round(entry["main"]["temp"]))
            hava_durumu = entry["weather"][0]["description"]

            if tarih not in tahminler:
                tahminler[tarih] = {"sicakliklar": [], "hava_durumu": []}

            tahminler[tarih]["sicakliklar"].append(sicaklik)
            tahminler[tarih]["hava_durumu"].append(hava_durumu)

        guncel_tahminler = {}
        for tarih, bilgiler in tahminler.items():
            ortalama_sicaklik = sum(bilgiler["sicakliklar"]) // len(bilgiler["sicakliklar"])
            en_sik_hava_durumu = max(set(bilgiler["hava_durumu"]), key=bilgiler["hava_durumu"].count)
            guncel_tahminler[tarih] = {"Sıcaklık": f"{ortalama_sicaklik}°C", "Hava Durumu": en_sik_hava_durumu}

        bugunun_tarihi = datetime.now().strftime("%d-%m-%Y")
        saat_bilgisi = datetime.now().strftime("%H:%M:%S")

        doviz_kuru = doviz_kuru_cek(para_birimi)

        hava_bilgisi = {
            "Şehir": data["city"]["name"],
            "Ülke": country_code,
            "Para Birimi": para_birimi,
            "Döviz Kuru (USD)": f"1 USD = {doviz_kuru} {para_birimi}",
            "Tahminler": guncel_tahminler,
            "Sorgu Saati": saat_bilgisi
        }

        kaydet_json(bugunun_tarihi, hava_bilgisi)

        # GUI Sonuçları Güncelleme
        sonuc_text.config(state=tk.NORMAL)
        sonuc_text.delete("1.0", tk.END)
        sonuc_text.insert(tk.END, f"🌍 {sehir} için 5 Günlük Hava Tahmini:\n")
        for gun, bilgiler in hava_bilgisi["Tahminler"].items():
            sonuc_text.insert(tk.END, f"{gun}: {bilgiler['Sıcaklık']}, {bilgiler['Hava Durumu']}\n")
        sonuc_text.insert(tk.END, f"\n💰 {hava_bilgisi['Döviz Kuru (USD)']}\n")
        messagebox.showinfo("Başarı", "Hava tahmini başarıyla alındı!")

    except requests.exceptions.RequestException:
        messagebox.showerror("Hata", "Bağlantı hatası! Lütfen internet bağlantınızı kontrol edin.")

# JSON dosyasına verileri kaydetme fonksiyonu
def kaydet_json(tarih, yeni_veri):
    if os.path.exists(JSON_DOSYA):
        with open(JSON_DOSYA, "r", encoding="utf-8") as dosya:
            try:
                veriler = json.load(dosya)
                if not isinstance(veriler, dict):
                    veriler = {}
            except json.JSONDecodeError:
                veriler = {}
    else:
        veriler = {}

    if tarih not in veriler:
        veriler[tarih] = []

    veriler[tarih].append(yeni_veri)

    with open(JSON_DOSYA, "w", encoding="utf-8") as dosya:
        json.dump(veriler, dosya, ensure_ascii=False, indent=4)

# Tkinter GUI
root = tk.Tk()
root.title("Hava Durumu ve Döviz Uygulaması")
root.geometry("550x450")
root.configure(bg="white")

title_label = tk.Label(root, text="Hava Durumu ve Döviz Uygulaması", font=("Arial", 16, "bold"), bg="white")
title_label.pack(pady=5)

frame = tk.Frame(root, bg="white")
frame.pack(pady=5)

tk.Label(frame, text="Şehir Girin:", font=("Arial", 12), bg="white").grid(row=0, column=0, padx=5)
sehir_entry = tk.Entry(frame, font=("Arial", 12), width=20)
sehir_entry.grid(row=0, column=1, padx=5)


sorgula_button = tk.Button(root, text="Hava Durumunu Öğren", command=hava_durumu_cek, font=("Arial", 12))
sorgula_button.pack(pady=10)

sonuc_frame = tk.LabelFrame(root, text="Sonuçlar", font=("Arial", 12, "bold"), bg="white", padx=10, pady=5)
sonuc_frame.pack(pady=5, fill="both", expand="yes")

sonuc_text = tk.Text(sonuc_frame, font=("Arial", 10), height=10, width=55, state=tk.DISABLED,bg="#f7f7f7")
sonuc_text.pack(pady=5)

root.mainloop()
