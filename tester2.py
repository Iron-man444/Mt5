import cmd
import os
import subprocess
import json
import csv
from datetime import datetime
from pathlib import Path
import time
import re
import configparser

class MT5EAAutoTester:
    def __init__(self, mt_terminal_path):
        """
        MT5 EA Otomatik Test Sistemi
        
        Args:
            mt_terminal_path: MT5 terminal64.exe dosyasının tam yolu
        """
        self.mt_terminal_path = mt_terminal_path
        self.mt_data_path = self._find_data_folder()
        self.results = []
        
        print(f"✓ MT5 Terminal: {mt_terminal_path}")
        print(f"✓ Data Folder: {self.mt_data_path}")
        
    def _find_data_folder(self):
        """
        MT5 data klasörünü bul
        """
        # Genellikle AppData/Roaming/MetaQuotes altında
        terminal_dir = os.path.dirname(self.mt_terminal_path)
        
        # Eğer portable installation ise
        if os.path.exists(os.path.join(terminal_dir, 'MQL5')):
            return terminal_dir
        
        # Normal installation - AppData'da ara
        appdata = os.getenv('APPDATA')
        base_path = os.path.join(appdata, 'MetaQuotes', 'Terminal')
        
        if os.path.exists(base_path):
            # İlk klasörü al (genellikle tek bir installation var)
            folders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
            if folders:
                return os.path.join(base_path, folders[0])
        
        return terminal_dir
    
    def create_config_file(self, ea_name, symbol, timeframe, start_date, end_date, 
                          deposit=10000, leverage=100):
        """
        MT5 tester için config.ini dosyası oluştur
        """
        config = configparser.ConfigParser()
        
        # Common section
        config['Common'] = {
            'Login': '',
            'ProxyEnable': '0',
            'CertInstall': '0'
        }
        
        # Tester section
        # Timeframe mapping
        tf_map = {
            'M1': '1', 'M5': '5', 'M15': '15', 'M30': '30',
            'H1': '16385', 'H4': '16388', 'D1': '16408',
            'W1': '32769', 'MN1': '49153'
        }
        
        period_value = tf_map.get(timeframe, '16385')
        
        config['Tester'] = {
            'Expert': ea_name,
            'ExpertParameters': '',
            'Symbol': symbol,
            'Period': period_value,
            'Optimization': '0',
            'Model': '0',  # 0=Every tick, 1=1 minute OHLC, 2=Open prices only
            'ExecutionMode': '0',
            'OptimizationCriterion': '0',
            'FromDate': start_date,
            'ToDate': end_date,
            'ForwardMode': '0',
            'ForwardDate': end_date,
            'Report': f'{ea_name}_{symbol}_{timeframe}',
            'ReplaceReport': '1',
            'ShutdownTerminal': '1',
            'Deposit': str(deposit),
            'Currency': 'USD',
            'Leverage': f'1:{leverage}',
            'ExecutionDelay': '0',
            'Visual': '0'
        }
        
        # Config dosyasını yaz
        config_dir = os.path.join(self.mt_data_path, 'config')
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, 'common.ini')
        
        with open(config_path, 'w') as f:
            config.write(f)
        
        return config_path
    
    def run_backtest(self, ea_name, symbol, timeframe, start_date, end_date):
        """
        Backtest'i çalıştır
        """
        print(f"\n{'='*70}")
        print(f"🔧 Test Hazırlanıyor:")
        print(f"   EA      : {ea_name}")
        print(f"   Sembol  : {symbol}")
        print(f"   Zaman   : {timeframe}")
        print(f"   Tarih   : {start_date} → {end_date}")
        print(f"{'='*70}")
        
        # Config dosyasını oluştur
        config_path = self.create_config_file(ea_name, symbol, timeframe, 
                                              start_date, end_date)
        
        print(f"✓ Config oluşturuldu: {config_path}")
        
        # MT5'i tester mode'da başlat
        cmd = [
            self.mt_terminal_path,
            '/config:' + config_path
        ]
        
        print(f"⏳ MT5 başlatılıyor...")
        print(f"   Komut: {' '.join(cmd)}")
        
        try:
            # Terminal'i başlat
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # DEĞİŞİKLİK BURADA:
            # 0 (SW_HIDE) yerine 7 (SW_SHOWMINNOACTIVE) kullanıyoruz.
            # 7: Pencereyi minimize eder ve aktif etmez (sizin klavye/mouse odağınızı çalmaz).
            startupinfo.wShowWindow = 7 
            
            process = subprocess.Popen(
                cmd,
                startupinfo=startupinfo,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW # Ekstra önlem: Konsol penceresi açılmasını engeller
            )
            
            print(f"✓ MT5 başlatıldı (PID: {process.pid})")
            print(f"⏳ Test çalışıyor... (max 10 dakika)")
            
            # Process'in bitmesini bekle (timeout: 10 dakika)
            stdout, stderr = process.communicate(timeout=360)
            
            if process.returncode == 0:
                print("✅ Test tamamlandı!")
                return True
            else:
                print(f"❌ Test hata ile sonlandı (kod: {process.returncode})")
                if stderr:
                    print(f"   Hata: {stderr.decode('utf-8', errors='ignore')}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⚠️  Test 10 dakikada tamamlanamadı, sonlandırılıyor...")
            process.kill()
            return False
        except Exception as e:
            print(f"❌ Hata: {str(e)}")
            return False
    
    def find_latest_report(self, ea_name, symbol, timeframe): # ea_name eklendi
        """
        En son oluşturulan HTML raporunu bul
        """
        reports_folder = os.path.join(self.mt_data_path, 'Tester', 'Reports')
        
        if not os.path.exists(reports_folder):
            print(f"⚠️  Rapor klasörü bulunamadı: {reports_folder}")
            return None
        
        # Yeni isimlendirme formatına göre ara: EA_Symbol_TF
        pattern = f"{ea_name}_{symbol}_{timeframe}*.htm"
        reports = list(Path(reports_folder).glob(pattern))
        
        if not reports:
            print(f"⚠️  Rapor dosyası bulunamadı: {pattern}")
            return None
        
        # En son oluşturulan raporu al
        latest_report = max(reports, key=os.path.getctime)
        print(f"✓ Rapor bulundu: {latest_report.name}")
        
        return str(latest_report)
    


    def parse_report(self, report_path):
        """
        HTML raporunu parse et
        """
        results = {
            'net_profit': 0.0,
            'gross_profit': 0.0,
            'gross_loss': 0.0,
            'profit_factor': 0.0,
            'total_trades': 0,
            'win_rate': 0.0,
            'max_drawdown': 0.0,
            'max_drawdown_pct': 0.0,
            'balance': 0.0
        }
        
        try:
            with open(report_path, 'r', encoding='utf-16-le', errors='ignore') as f:
                content = f.read()
            
            # HTML'den değerleri çıkar (regex kullanarak)
            patterns = {
                'net_profit': r'Total net profit.*?<td[^>]*>([-\d.,\s]+)',
                'gross_profit': r'Gross profit.*?<td[^>]*>([-\d.,\s]+)',
                'gross_loss': r'Gross loss.*?<td[^>]*>([-\d.,\s]+)',
                'profit_factor': r'Profit factor.*?<td[^>]*>([-\d.,\s]+)',
                'total_trades': r'Total trades.*?<td[^>]*>(\d+)',
                'max_drawdown': r'Maximal drawdown.*?<td[^>]*>([-\d.,\s]+)',
                'balance': r'Balance.*?<td[^>]*>([-\d.,\s]+)'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    value_str = match.group(1).strip().replace(',', '').replace(' ', '')
                    try:
                        if key == 'total_trades':
                            results[key] = int(value_str)
                        else:
                            results[key] = float(value_str)
                    except:
                        pass
            
            # Win rate hesapla
            win_match = re.search(r'Profit trades.*?>(\d+)', content, re.IGNORECASE)
            if win_match and results['total_trades'] > 0:
                win_trades = int(win_match.group(1))
                results['win_rate'] = (win_trades / results['total_trades']) * 100
            
        except Exception as e:
            print(f"⚠️  Rapor parse hatası: {str(e)}")
        
        return results
    
    def save_single_result(self, result, output_file='ea_test_results.csv'):
        """
        Tek bir test sonucunu hemen dosyaya yaz
        """
        file_exists = os.path.isfile(output_file)
        
        # CSV'ye yaz
        with open(output_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=result.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(result)
        
        # JSON'a yaz
        json_file = output_file.replace('.csv', '.json')
        if os.path.isfile(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except:
                    data = []
        else:
            data = []
        
        data.append(result)
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def test_multiple_eas(self, ea_folder, symbols, timeframes, 
                         start_date, end_date, output_file='ea_test_results.csv'):
        """
        Birden fazla EA'yı test et
        """
        # EA dosyalarını bul (.ex5 uzantılı)
        ea_files = list(Path(ea_folder).glob('*.ex5'))
        
        print(f"\n{'='*70}")
        print(f"🔍 EA TARAMA SONUCU:")
        print(f"{'='*70}")
        print(f"📁 Klasör        : {ea_folder}")
        print(f"🤖 Bulunan EA    : {len(ea_files)}")
        print(f"📊 Sembol Sayısı : {len(symbols)}")
        print(f"⏰ Timeframe     : {len(timeframes)}")
        print(f"🔢 Toplam Test   : {len(ea_files) * len(symbols) * len(timeframes)}")
        print(f"💾 Çıktı Dosyası : {output_file}")
        print(f"{'='*70}\n")
        
        if not ea_files:
            print("❌ HATA: .ex5 uzantılı EA dosyası bulunamadı!")
            print(f"   Kontrol edin: {ea_folder}")
            return []
        
        # Liste EA'ları
        print("📋 Bulunan EA'lar:")
        for i, ea in enumerate(ea_files, 1):
            print(f"   {i}. {ea.name}")
        print()
        
       
        
        total_tests = 0
        successful_tests = 0
        
        # Her EA için
        for ea_idx, ea_file in enumerate(ea_files, 1):
            ea_name = ea_file.stem  # .ex5 olmadan sadece isim
            
            print(f"\n{'#'*70}")
            print(f"📁 EA {ea_idx}/{len(ea_files)}: {ea_name}")
            print(f"{'#'*70}")
            
            # Her sembol için
            for sym_idx, symbol in enumerate(symbols, 1):
                
                # Her zaman dilimi için
                for tf_idx, timeframe in enumerate(timeframes, 1):
                    total_tests += 1
                    
                    print(f"\n   [{total_tests}] {symbol} - {timeframe}")
                    
                    # Backtest çalıştır
                    success = self.run_backtest(
                        ea_name,
                        symbol,
                        timeframe,
                        start_date,
                        end_date
                    )
                    
                    # Sisteme nefes aldır
                    time.sleep(3)
                    
                    if success:
                        # Raporu bul ve parse et
                        report_path = self.find_latest_report(ea_name, symbol, timeframe)
                        
                        if report_path:
                            parsed_results = self.parse_report(report_path)
                            
                            # Sonuç objesi
                            result = {
                                'test_no': total_tests,
                                'ea_name': ea_name,
                                'symbol': symbol,
                                'timeframe': timeframe,
                                'start_date': start_date,
                                'end_date': end_date,
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                **parsed_results
                            }
                            
                            self.results.append(result)
                            self.save_single_result(result, output_file)
                            
                            successful_tests += 1
                            
                            # Konsola özet
                            print(f"\n   ✅ SONUÇ:")
                            print(f"      Net Kar      : ${parsed_results['net_profit']:.2f}")
                            print(f"      Profit Factor: {parsed_results['profit_factor']:.2f}")
                            print(f"      İşlem Sayısı : {parsed_results['total_trades']}")
                            print(f"      Win Rate     : {parsed_results['win_rate']:.1f}%")
                            print(f"      Max Drawdown : ${parsed_results['max_drawdown']:.2f}")
                            print(f"   💾 Kaydedildi → {output_file}")
                        else:
                            print(f"   ⚠️  Rapor bulunamadı")
                    else:
                        print(f"   ❌ Test başarısız")
        
        # Genel özet
        print(f"\n\n{'='*70}")
        print(f"📊 GENEL TEST ÖZETİ")
        print(f"{'='*70}")
        print(f"Toplam Test       : {total_tests}")
        print(f"Başarılı          : {successful_tests}")
        print(f"Başarısız         : {total_tests - successful_tests}")
        print(f"Başarı Oranı      : {(successful_tests/total_tests*100) if total_tests > 0 else 0:.1f}%")
        print(f"Sonuç Dosyaları   : {output_file}")
        print(f"                    {output_file.replace('.csv', '.json')}")
        print(f"{'='*70}\n")
        
        return self.results
    
    def generate_summary_report(self):
        """
        Özet rapor oluştur
        """
        if not self.results:
            print("⚠️  Rapor için veri yok")
            return
        
        print("\n" + "="*70)
        print("🏆 EN İYİ PERFORMANS GÖSTEREN EA'LAR")
        print("="*70)
        
        # Net kar'a göre top 10
        sorted_by_profit = sorted(
            self.results, 
            key=lambda x: x['net_profit'], 
            reverse=True
        )[:10]
        
        print("\n📈 Net Kar'a Göre Top 10:")
        for i, r in enumerate(sorted_by_profit, 1):
            print(f"{i:2d}. {r['ea_name']:30s} ({r['symbol']}-{r['timeframe']}) "
                  f"Net: ${r['net_profit']:10.2f}")
        
        # Profit Factor'e göre top 10
        sorted_by_pf = sorted(
            [r for r in self.results if r['profit_factor'] > 0],
            key=lambda x: x['profit_factor'],
            reverse=True
        )[:10]
        
        print("\n📊 Profit Factor'e Göre Top 10:")
        for i, r in enumerate(sorted_by_pf, 1):
            print(f"{i:2d}. {r['ea_name']:30s} ({r['symbol']}-{r['timeframe']}) "
                  f"PF: {r['profit_factor']:6.2f}")
        
        print("="*70 + "\n")


# KULLANIM
if __name__ == "__main__":
    
    # AYARLAR
    MT_TERMINAL_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"
    EA_FOLDER = r"C:\Users\Ben\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts"
    
    # Test parametreleri
    SYMBOLS = ['EURUSD']
    TIMEFRAMES = ['H1']
    START_DATE = '2024.06.01'
    END_DATE = '2024.07.01'  
    
    # Başlat
    tester = MT5EAAutoTester(MT_TERMINAL_PATH)
    
    # Testleri çalıştır
    results = tester.test_multiple_eas(
        ea_folder=EA_FOLDER,
        symbols=SYMBOLS,
        timeframes=TIMEFRAMES,
        start_date=START_DATE,
        end_date=END_DATE,
        output_file='ea_test_results.csv'
    )
    
    # Özet rapor
    tester.generate_summary_report()