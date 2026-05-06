from bs4 import BeautifulSoup

def backtest_sonuclarini_siniflandir(dosya_yolu):
    with open(dosya_yolu, 'r', encoding='utf-8') as f:
        html_icerik = f.read()

    soup = BeautifulSoup(html_icerik, 'html.parser')
    satirlar = soup.find('tbody').find_all('tr')

    profit_olanlar = []
    zararda_olanlar = []
    islem_almayanlar = []

    for satir in satirlar:
        sutunlar = satir.find_all('td')
        if len(sutunlar) < 8:
            continue

        dosya_adi = sutunlar[0].text.strip()
        # Sayısal değerlerdeki boşlukları ve karakterleri temizle
        net_profit_str = sutunlar[3].text.replace(' ', '').replace(',', '.')
        trades_str = sutunlar[5].text.strip()

        try:
            net_profit = float(net_profit_str)
            trades = int(trades_str)
        except ValueError:
            continue

        veri = {
            "Dosya Adı": dosya_adi,
            "Net Profit": net_profit,
            "Trades": trades
        }

        # Sınıflandırma Mantığı
        if trades == 0:
            islem_almayanlar.append(veri)
        elif net_profit > 0:
            profit_olanlar.append(veri)
        else:
            zararda_olanlar.append(veri)

    return profit_olanlar, zararda_olanlar, islem_almayanlar

# Kullanım:
dosya = "SONUC_TABLOSU.html"
profit, zarar, pasif = backtest_sonuclarini_siniflandir(dosya)

print(f"--- ANALİZ SONUÇLARI ---\n")
print(f"✅ PROFİT OLANLAR ({len(profit)} adet):")
for kalem in profit[:5]: # Örnek olması için ilk 5'i listeler
    print(f" - {kalem['Dosya Adı']}: {kalem['Net Profit']}")

print(f"\n❌ ZARARDA OLANLAR ({len(zarar)} adet):")
for kalem in zarar[:5]:
    print(f" - {kalem['Dosya Adı']}: {kalem['Net Profit']}")

print(f"\n⚪ İŞLEM ALMAYANLAR ({len(pasif)} adet):")
for kalem in pasif[:5]:
    print(f" - {kalem['Dosya Adı']}")