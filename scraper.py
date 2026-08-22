import requests
from bs4 import BeautifulSoup
import time
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Bağlantı hatalarına karşı otomatik yeniden deneme
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504, 429])
session.mount("https://", HTTPAdapter(max_retries=retries))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

KATEGORILER = {
    "ozelgeler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=ozelge",
        "dosya": "mevzuat_md/1_ozelgeler.md",
        "max_sayfa": 370
    },
    "sirkulerler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=sirkuler",
        "dosya": "mevzuat_md/2_sirkulerler.md",
        "max_sayfa": 20
    },
    "tebligler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=teblig",
        "dosya": "mevzuat_md/3_tebligler.md",
        "max_sayfa": 60
    },
    "kanunlar": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=kanun",
        "dosya": "mevzuat_md/4_kanunlar.md",
        "max_sayfa": 10
    },
    "maddeler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=madde",
        "dosya": "mevzuat_md/5_maddeler.md",
        "max_sayfa": 150
    },
    "yonetmelikler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=yönetmelik",
        "dosya": "mevzuat_md/6_yonetmelikler.md",
        "max_sayfa": 5
    }
}

def extract_mevzuat_links(soup):
    """Sayfadaki tüm mevzuat detay linklerini sınıf farkı gözetmeksizin çeker."""
    links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(separator=" ", strip=True)
        
        # Sadece gerçek mevzuat detay bağlantılarını filtrele
        if "/mevzuat/" in href and not href.endswith("/mevzuat/arama") and not href.startswith("javascript"):
            if len(text) >= 12 and not any(skip in text.lower() for skip in ["arama sonuçları", "kurumsal", "iletişim", "e-işlemler", "başa dön", "erişilebilirlik", "dijital vergi dairesi"]):
                full_url = href if href.startswith("http") else f"https://gib.gov.tr{href}"
                if full_url not in seen:
                    seen.add(full_url)
                    links.append((text, full_url))
    return links

def get_detail_content(url):
    """Detay sayfasından sadece karar metnini çeker, menüleri temizler."""
    try:
        r = session.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            # Gereksiz menü, footer ve scriptleri sil
            for tag in soup(["header", "footer", "nav", "script", "style"]):
                tag.decompose()
            
            body = soup.select_one(".field--name-body, .mevzuat-icerik, article, main, #main-content, .region-content")
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
                    items = extract_mevzuat_links(soup)
                    
                    if not items:
                        print(f"[{kat_adi}] Bu sayfada başka kayıt bulunamadı, kategori tamamlandı.")
                        break
                        
                    print(f"  -> Bu sayfada {len(items)} adet mevzuat kaydı bulundu. İçerikler çekiliyor...")
                    
                    for title, full_url in items:
                        content = get_detail_content(full_url)
                        
                        # Markdown formatında yaz ve diske kaydet
                        f.write(f"## {title}\n\n")
                        f.write(f"- **Kaynak Bağlantısı:** {full_url}\n\n")
                        f.write(f"### Metin / Karar Hükmü:\n{content}\n\n")
                        f.write("---\n\n")
                        f.flush()
                        
                        toplam_kayit += 1
                        time.sleep(0.15)
                        
                except Exception as e:
                    print(f"Hata oluştu ({kat_adi} - Sayfa {page + 1}): {e}")
                    
        print(f"Kategori Tamamlandı: {cfg['dosya']}")
        
    print(f"\nTÜM TARAMA TAMAMLANDI! Toplam İndekslenen Kayıt: {toplam_kayit}")

if __name__ == "__main__":
    main()
