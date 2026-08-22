import requests
from bs4 import BeautifulSoup
import time
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

KATEGORILER = {
    "ozelgeler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=ozelge",
        "dosya": "mevzuat_md/ozelgeler.md",
        "max_sayfa": 20  # GitHub Actions'ta istediğiniz kadar artırabilirsiniz (örn: 50, 100)
    },
    "sirkulerler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=sirkuler",
        "dosya": "mevzuat_md/sirkulerler.md",
        "max_sayfa": 10
    },
    "tebligler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=teblig",
        "dosya": "mevzuat_md/tebligler.md",
        "max_sayfa": 10
    }
}

def get_detail_text(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            body = soup.select_one(".field--name-body, .mevzuat-icerik, article")
            return body.get_text(separator="\n\n", strip=True) if body else soup.get_text(separator="\n\n", strip=True)
    except Exception:
        pass
    return ""

def main():
    os.makedirs("mevzuat_md", exist_ok=True)
    
    for kat_adi, cfg in KATEGORILER.items():
        print(f"--- {kat_adi.upper()} Taranıyor ---")
        with open(cfg["dosya"], "w", encoding="utf-8") as f:
            f.write(f"# GİB {kat_adi.title()} Arşivi\n\n")
            
            for page in range(cfg["max_sayfa"]):
                target = f"{cfg['url']}&page={page}"
                print(f"Sayfa {page + 1}/{cfg['max_sayfa']}...")
                try:
                    res = requests.get(target, headers=HEADERS, timeout=15)
                    soup = BeautifulSoup(res.text, "html.parser")
                    items = soup.select(".views-row, .mevzuat-item, table tbody tr")
                    
                    if not items:
                        break
                        
                    for item in items:
                        a = item.find("a")
                        if not a:
                            continue
                        title = a.get_text(strip=True)
                        href = a.get("href", "")
                        full_url = href if href.startswith("http") else f"https://gib.gov.tr{href}"
                        content = get_detail_text(full_url)
                        
                        f.write(f"## {title}\n\n")
                        f.write(f"- **Kaynak:** {full_url}\n\n")
                        f.write(f"### İçerik:\n{content}\n\n")
                        f.write("---\n\n")
                        time.sleep(0.3)
                except Exception as e:
                    print(f"Hata: {e}")

if __name__ == "__main__":
    main()
