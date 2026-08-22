import requests
from bs4 import BeautifulSoup
import time
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Bağlantı kopmalarına karşı dayanıklı oturum (Session)
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504, 429])
session.mount("https://", HTTPAdapter(max_retries=retries))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# GİB'deki 6 Kategorinin Tamamı (%100 Kapsam)
KATEGORILER = {
    "ozelgeler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=ozelge",
        "dosya": "mevzuat_md/1_ozelgeler.md",
        "max_sayfa": 370  # 18.358 Özelgenin tamamı (368 sayfa)
    },
    "sirkulerler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=sirkuler",
        "dosya": "mevzuat_md/2_sirkulerler.md",
        "max_sayfa": 20   # 588 Sirkülerin tamamı
    },
    "tebligler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=teblig",
        "dosya": "mevzuat_md/3_tebligler.md",
        "max_sayfa": 60   # 2.490 Tebliğin tamamı
    },
    "kanunlar": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=kanun",
        "dosya": "mevzuat_md/4_kanunlar.md",
        "max_sayfa": 10   # 221 Kanunun tamamı
    },
    "maddeler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=madde",
        "dosya": "mevzuat_md/5_maddeler.md",
        "max_sayfa": 150  # 6.998 Maddenin tamamı
    },
    "yonetmelikler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=yönetmelik",
        "dosya": "mevzuat_md/6_yonetmelikler.md",
        "max_sayfa": 5    # 66 Yönetmeliğin tamamı
    }
}

def get_detail_text(url):
    """Detay sayfasına girip tam karar ve gerekçe metnini alır."""
    try:
        r = session.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            body = soup.select_one(".field--name-body, .mevzuat-icerik, article, main")
            if body:
                return body.get_text(separator="\n\n", strip=True)
            return soup.get_text(separator="\n\n", strip=True)
    except Exception:
        pass
    return ""

def main():
    os.makedirs("mevzuat_md", exist_ok=True)
    toplam_kayit = 0
    
    for kat_adi, cfg in KATEGORILER.items():
        print(f"\n========================================================")
        print(f"KATEGORİ BAŞLATILDI: {kat_adi.upper()} -> {cfg['dosya']}")
        print(f"========================================================")
        
        with open(cfg["dosya"], "w", encoding="utf-8") as f:
            f.write(f"# GİB {kat_adi.title()} Tam Arşivi\n\n")
            
            for page in range(cfg["max_sayfa"]):
                target_url = f"{cfg['url']}&page={page}"
                print(f"[{kat_adi}] Sayfa taranıyor: {page + 1}/{cfg['max_sayfa']}...")
                
                try:
                    res = session.get(target_url, headers=HEADERS, timeout=15)
                    soup = BeautifulSoup(res.text, "html.parser")
                    items = soup.select(".views-row, .mevzuat-item, table tbody tr")
                    
                    if not items:
                        print(f"[{kat_adi}] Bu kategorideki tüm sayfalar tamamlandı.")
                        break
                        
                    for item in items:
                        a_tag = item.find("a")
                        if not a_tag:
                            continue
                            
                        title = a_tag.get_text(strip=True)
                        href = a_tag.get("href", "")
                        full_url = href if href.startswith("http") else f"https://gib.gov.tr{href}"
                        
                        # Detay metnini al
                        content = get_detail_text(full_url)
                        
                        # Markdown formatında anlık olarak dosyaya yaz
                        f.write(f"## {title}\n\n")
                        f.write(f"- **Kaynak Bağlantısı:** {full_url}\n\n")
                        f.write(f"### Metin / Karar Hükmü:\n{content}\n\n")
                        f.write("---\n\n")
                        f.flush() # Veri kaybını önlemek için anında diske yaz
                        
                        toplam_kayit += 1
                        time.sleep(0.2) # Sunucuyu yormamak için kısa bekleme
                        
                except Exception as e:
                    print(f"Hata oluştu ({kat_adi} - Sayfa {page + 1}): {e}")
                    
        print(f"Kategori Tamamlandı: {cfg['dosya']}")
        
    print(f"\nTÜM TARAMA TAMAMLANDI! Toplam İndekslenen Kayıt: {toplam_kayit}")

if __name__ == "__main__":
    main()
