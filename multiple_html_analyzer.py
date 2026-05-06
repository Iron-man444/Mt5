import os
import glob
import re

def dosya_oku_guvenli(dosya_yolu):
    """
    Dosyayı sırasıyla UTF-16 (MT4/5 standardı), UTF-8 ve Latin-1 olarak okumayı dener.
    Okunan içeriği tek satıra indirip döndürür.
    """
    encodings = ['utf-16', 'utf-8', 'latin-1', 'cp1252']
    
    for enc in encodings:
        try:
            with open(dosya_yolu, "r", encoding=enc) as f:
                icerik = f.read()
                # Okuma başarılıysa hemen işle
                # Satır sonlarını ve fazlalık boşlukları temizle
                temiz_icerik = icerik.replace("\n", " ").replace("\r", "")
                temiz_icerik = re.sub(' +', ' ', temiz_icerik)
                return temiz_icerik
        except (UnicodeError, UnicodeDecodeError):
            continue # Bu format uymadı, sonrakini dene
            
    return None

def veri_bul(html, baslik):
    """
    HTML içinden 'Başlık' sonrasındaki ilk <b>DEĞER</b> yapısını bulur.
    """
    # Desen: Başlık -> (herhangi bir karakter) -> <b> -> (DEĞER) -> </b>
    # Örnek: Total Net Profit: ... <b>123.45</b>
    desen = r"{}.*?<b>(.*?)</b>".format(re.escape(baslik))
    
    match = re.search(desen, html, re.IGNORECASE)
    if match:
        # Bulunan değerin içindeki HTML taglerini temizle (varsa)
        raw_val = match.group(1)
        clean_val = re.sub('<[^<]+?>', '', raw_val).strip()
        # &nbsp; gibi HTML boşluklarını temizle
        clean_val = clean_val.replace("&nbsp;", "")
        return clean_val
    return "-"

def raporlari_birlestir():
    # Sadece .html dosyalarını al (önceki kodla çevirdiklerini varsayıyoruz)
    dosyalar = glob.glob("*.html")
    
    cikti_ismi = "SONUC_TABLOSU.html"
    if cikti_ismi in dosyalar: dosyalar.remove(cikti_ismi)

    if not dosyalar:
        print("Klasörde .html dosyası yok! Önce dönüştürme kodunu çalıştırdın mı?")
        return

    print(f"{len(dosyalar)} dosya analiz ediliyor (UTF-16/8 Modu)...")

    html_satirlar = ""

    for dosya in dosyalar:
        try:
            icerik = dosya_oku_guvenli(dosya)
            
            if not icerik:
                print(f"HATA: {dosya} okunamadı (Encoding sorunu).")
                continue

            # Eğer içerik çok kısaysa (boş dosyaysa) atla
            if len(icerik) < 100:
                continue

            dosya_adi = os.path.basename(dosya)

            # --- VERİLERİ ÇEK ---
            symbol = veri_bul(icerik, "Symbol:")
            period = veri_bul(icerik, "Period:")
            net_profit = veri_bul(icerik, "Total Net Profit:")
            profit_factor = veri_bul(icerik, "Profit Factor:")
            trades = veri_bul(icerik, "Total Trades:")
            drawdown = veri_bul(icerik, "Balance Drawdown Relative:")
            sharpe = veri_bul(icerik, "Sharpe Ratio:")
            
            # Renklendirme
            renk = ""
            try:
                # 2 065.92 gibi boşluklu sayıları düzeltip kontrol et
                sayisal = float(net_profit.replace(" ", ""))
                renk = "win" if sayisal >= 0 else "loss"
            except:
                pass

            html_satirlar += f"""
            <tr>
                <td class="left">{dosya_adi}</td>
                <td>{symbol}</td>
                <td>{period}</td>
                <td class="{renk}">{net_profit}</td>
                <td>{profit_factor}</td>
                <td>{trades}</td>
                <td>{drawdown}</td>
                <td>{sharpe}</td>
            </tr>
            """
            
        except Exception as e:
            print(f"Dosya hatası ({dosya}): {e}")

    # --- HTML ÇIKTISI ---
    sablon = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <title>Analiz Raporu</title>
    <style>
        body {{ font-family: sans-serif; padding: 20px; background: #eee; }}
        table {{ width: 100%; border-collapse: collapse; background: #fff; }}
        th {{ background: #333; color: #fff; padding: 10px; position: sticky; top: 0; }}
        td {{ border: 1px solid #ccc; padding: 8px; text-align: center; }}
        .left {{ text-align: left; font-weight: bold; }}
        .win {{ color: green; font-weight: bold; }}
        .loss {{ color: red; font-weight: bold; }}
        tr:hover {{ background: #f0f0f0; }}
    </style>
    </head>
    <body>
        <h2>Backtest Sonuçları</h2>
        <table>
            <thead>
                <tr>
                    <th>Dosya Adı</th>
                    <th>Symbol</th>
                    <th>Period</th>
                    <th>Net Profit</th>
                    <th>P. Factor</th>
                    <th>Trades</th>
                    <th>Drawdown</th>
                    <th>Sharpe</th>
                </tr>
            </thead>
            <tbody>
                {html_satirlar}
            </tbody>
        </table>
    </body>
    </html>
    """

    with open(cikti_ismi, "w", encoding="utf-8") as f:
        f.write(sablon)

    print(f"\nBitti! '{cikti_ismi}' dosyasına bakabilirsin.")

if __name__ == "__main__":
    raporlari_birlestir()