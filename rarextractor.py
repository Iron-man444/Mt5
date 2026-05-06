import os
import zipfile
import rarfile

# DİKKAT: rarfile kütüphanesi Windows'ta çalışmak için WinRAR'ın UnRAR.exe'sine ihtiyaç duyar.
# Eğer bilgisayarında WinRAR farklı bir yere kuruluysa aşağıdaki yolu ona göre güncelle.
rarfile.UNRAR_TOOL = r"C:\Program Files\WinRAR\UnRAR.exe"

# İndirilen dosyaların bulunduğu ana klasör
MAIN_DIR = "Forex_EAs" 

def extract_archives():
    print("Arşivden çıkarma işlemi başlıyor...\n")
    
    # os.walk ile ana klasörün içindeki tüm alt klasörleri ve dosyaları tara
    for root, dirs, files in os.walk(MAIN_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            # Dosya adını ve uzantısını ayır (Örn: "system v1" ve ".rar")
            file_name_no_ext, ext = os.path.splitext(file)
            ext = ext.lower()
            
            # Sadece .zip ve .rar dosyalarını işle
            if ext in ['.zip', '.rar']:
                # Çıkartılacak hedef klasör (Arşivin kendi adıyla bir klasör açıyoruz ki içindekiler dağılmasın)
                extract_path = os.path.join(root, file_name_no_ext)
                
                # Eğer o isimde bir klasör zaten varsa işlemi atla (Gereksiz tekrarı önler)
                if os.path.exists(extract_path):
                    continue
                    
                print(f"[{ext.upper()}] Çıkarılıyor: {file} -> {file_name_no_ext}/")
                
                try:
                    # Hedef klasörü oluştur
                    os.makedirs(extract_path, exist_ok=True)
                    
                    if ext == '.zip':
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            zip_ref.extractall(extract_path)
                            
                    elif ext == '.rar':
                        with rarfile.RarFile(file_path, 'r') as rar_ref:
                            rar_ref.extractall(extract_path)
                            
                    print("  -> BAŞARILI.")
                    
                except rarfile.BadRarFile:
                    print(f"  -> [HATA] Bozuk RAR dosyası (Muhtemelen 0 KB veya anti-bot engeli): {file}")
                    # İçi boş olduğu için oluşturulan boş klasörü geri sil
                    os.rmdir(extract_path) 
                    
                except zipfile.BadZipFile:
                    print(f"  -> [HATA] Bozuk ZIP dosyası: {file}")
                    os.rmdir(extract_path)
                    
                except Exception as e:
                    print(f"  -> [BEKLENMEYEN HATA] {file}: {e}")

    print("\nBütün dosyalar başarıyla klasörlere çıkarıldı!")

if __name__ == "__main__":
    extract_archives()