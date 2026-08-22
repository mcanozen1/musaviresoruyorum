import requests
from bs4 import BeautifulSoup
import time
import os
import urllib.parse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 6 GİB Mevzuat Kategorisi ve Ayarları
KATEGORILER = {
    "ozelgeler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=ozelge",
        "dosya": "mevzuat_md/1_ozelgeler.md",
        "max_sayfa": 20  # İhtiyacınıza göre sayfa sayısını artırabilirsiniz
    },
    "sirkulerler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=sirkuler",
        "dosya": "mevzuat_md/2_sirkulerler.md",
        "max_sayfa": 15
    },
    "tebligler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=teblig",
        "dosya": "mevzuat_md/3_tebligler.md",
        "max_sayfa": 15
    },
    "kanunlar": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=kanun",
        "dosya": "mevzuat_md/4_kanunlar.md",
        "max_sayfa": 10
    },
    "maddeler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=madde",
        "dosya": "mevzuat_md/5_maddeler.md",
        "max_sayfa": 15
    },
    "yonetmelikler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=yönetmelik",
        "dosya": "mevzuat_md/6_yonetmelikler.md",
        "max_sayfa": 10
    }
}

def get_detail_text(url):
    """Her kaydın kendi detay sayfasına girip tam metnini alır."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            body = soup.select_one(".field--name-body, .mevzuat-icerik, article, main")
            return body.get_text(separator="\n\n", strip=True) if body else soup.get_text(separator="\n\n", strip=True)
    except Exception:
        pass
    return ""

def main():
    os.makedirs("mevzuat_md", exist_ok=True)
    
    for kat_adi, cfg in KATEGORILER.items():
        print(f"\n==========================================")
        print(f"BAŞLATILDI: {kat_adi.upper()} -> {cfg['dosya']}")
        print(f"==========================================")
        
        with open(cfg["dosya"], "w", encoding="utf-8") as f:
            f.write(f"# GİB {kat_adi.title()} Arşivi\n\n")
            
            for page in range(cfg["max_sayfa"]):
                target_url = f"{cfg['url']}&page={page}"
                print(f"[{kat_adi}] Sayfa taranıyor: {page + 1}/{cfg['max_sayfa']}...")
                
                try:
                    res = requests.get(target_url, headers=HEADERS, timeout=15)
                    soup = BeautifulSoup(res.text, "html.parser")
                    items = soup.select(".views-row, .mevzuat-item, table tbody tr")
                    
                    if not items:
                        print(f"[{kat_adi}] Başka kayıt bulunamadı, sonraki kategoriye geçiliyor.")
                        break
                        
                    for item in items:
                        a_tag = item.find("a")
                        if not a_tag:
                            continue
                            
                        title = a_tag.get_text(strip=True)
                        href = a_tag.get("href", "")
                        full_url = href if href.startswith("http") else f"https://gib.gov.tr{href}"
                        
                        # Detay metnini çek
                        content = get_detail_text(full_url)
                        
                        # Markdown formatında yaz
                        f.write(f"## {title}\n\n")
                        f.write(f"- **Kaynak Bağlantısı:** {full_url}\n\n")
                        f.write(f"### Metin / Hüküm:\n{content}\n\n")
                        f.write("---\n\n")
                        
                        time.sleep(0.3) # Sunucu koruma beklemesi
                        
                except Exception as e:
                    print(f"Hata oluştu ({kat_adi} - Sayfa {page + 1}): {e}")
                    
        print(f"Tamamlandı: {cfg['dosya']}")

if __name__ == "__main__":
    main()
