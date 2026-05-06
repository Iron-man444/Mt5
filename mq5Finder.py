import os
import shutil

# Çıkartılan dosyaların bulunduğu ana klasör (Arama yapılacak yer)
SOURCE_DIR = "Cikartilan_EAlar" 

# Tüm .mq5 dosyalarının toplanacağı yeni hedef klasör
DEST_DIR = "All_MQ5_Files"

def collect_mq5_files():
    # Hedef klasörü oluştur (yoksa)
    os.makedirs(DEST_DIR, exist_ok=True)
    
    print(f"'{SOURCE_DIR}' klasörü taranıyor...\n")
    copied_count = 0
    
    # os.walk ile tüm alt klasörleri derinlemesine tara
    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            # Sadece .mq5 uzantılı dosyaları yakala
            if file.lower().endswith('.mq5'):
                source_path = os.path.join(root, file)
                dest_path = os.path.join(DEST_DIR, file)
                
                # İSİM ÇAKIŞMASI KONTROLÜ
                if os.path.exists(dest_path):
                    # Aynı isimde dosya varsa, dosyanın başına geldiği klasörün adını ekle
                    parent_folder = os.path.basename(root)
                    file_name, file_ext = os.path.splitext(file)
                    new_file_name = f"{parent_folder}_{file_name}{file_ext}"
                    dest_path = os.path.join(DEST_DIR, new_file_name)
                    
                    # Eğer bu yeni isim de varsa, sonuna sayı ekleyerek benzersiz yap
                    counter = 1
                    while os.path.exists(dest_path):
                        new_file_name = f"{parent_folder}_{file_name}_{counter}{file_ext}"
                        dest_path = os.path.join(DEST_DIR, new_file_name)
                        counter += 1
                
                try:
                    # Dosyayı hedef klasöre kopyala
                    shutil.copy2(source_path, dest_path)
                    copied_count += 1
                    print(f"Kopyalandı: {os.path.basename(dest_path)}")
                except Exception as e:
                    print(f"[HATA] {file} kopyalanamadı: {e}")

    print(f"\nİşlem tamamlandı! Toplam {copied_count} adet .mq5 dosyası '{DEST_DIR}' klasöründe toplandı.")
    print(f"Dosyaların konumu: {os.path.abspath(DEST_DIR)}")

if __name__ == "__main__":
    collect_mq5_files()