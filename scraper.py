import os
import time
from playwright.sync_api import sync_playwright

KATEGORILER = {
    "ozelgeler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=ozelge",
        "dosya": "mevzuat_md/1_ozelgeler.md",
        "max_sayfa": 50  # Başlangıç için 50 sayfa (İsteğinize göre artırabilirsiniz)
    },
    "sirkulerler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=sirkuler",
        "dosya": "mevzuat_md/2_sirkulerler.md",
        "max_sayfa": 20
    },
    "tebligler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=teblig",
        "dosya": "mevzuat_md/3_tebligler.md",
        "max_sayfa": 30
    },
    "kanunlar": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=kanun",
        "dosya": "mevzuat_md/4_kanunlar.md",
        "max_sayfa": 10
    },
    "maddeler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=madde",
        "dosya": "mevzuat_md/5_maddeler.md",
        "max_sayfa": 40
    },
    "yonetmelikler": {
        "url": "https://gib.gov.tr/mevzuat/arama?tur=vergi-mevzuati&ktype=99&kanun-turu=yönetmelik",
        "dosya": "mevzuat_md/6_yonetmelikler.md",
        "max_sayfa": 5
    }
}

def run():
    os.makedirs("mevzuat_md", exist_ok=True)
    
    with sync_playwright() as p:
        # Gerçek Chromium tarayıcısı başlatılır
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="tr-TR"
        )
        page = context.new_page()

        for kat_adi, cfg in KATEGORILER.items():
            print(f"\n=======================================================")
            print(f"Kategori Başlatıldı: {kat_adi.upper()} -> {cfg['dosya']}")
            print(f"=======================================================")
            
            with open(cfg["dosya"], "w", encoding="utf-8") as f:
                f.write(f"# GİB {kat_adi.title()} Arşivi\n\n")
                
                for page_num in range(cfg["max_sayfa"]):
                    target_url = f"{cfg['url']}&page={page_num}"
                    print(f"[{kat_adi}] Sayfa açılıyor: {page_num + 1}/{cfg['max_sayfa']}...")
                    
                    try:
                        # JavaScript yüklenene kadar bekle
                        page.goto(target_url, wait_until="networkidle", timeout=30000)
                        time.sleep(2)
                        
                        # Tarayıcı içinden DOM'daki mevzuat linklerini çıkar
                        links_data = page.evaluate("""() => {
                            const results = [];
                            const anchors = document.querySelectorAll('a[href*="/mevzuat/"]');
                            anchors.forEach(a => {
                                const href = a.getAttribute('href') || '';
                                const text = a.innerText.trim();
                                if (text.length > 12 && !href.includes('/mevzuat/arama') && !href.startsWith('javascript')) {
                                    results.push({
                                        title: text,
                                        url: href.startsWith('http') ? href : 'https://gib.gov.tr' + href
                                    });
                                }
                            });
                            return results;
                        }""")
                        
                        unique_links = []
                        seen_urls = set()
                        for item in links_data:
                            if item["url"] not in seen_urls:
                                seen_urls.add(item["url"])
                                unique_links.append(item)
                                
                        if not unique_links:
                            print(f"[{kat_adi}] Bu sayfada kayıt bulunamadı, sonraki kategoriye geçiliyor.")
                            break
                            
                        print(f"  -> {len(unique_links)} adet mevzuat kaydı bulundu. Detaylar alınıyor...")
                        
                        for item in unique_links:
                            try:
                                detail_page = context.new_page()
                                detail_page.goto(item["url"], wait_until="domcontentloaded", timeout=20000)
                                time.sleep(1)
                                
                                content_text = detail_page.evaluate("""() => {
                                    const body = document.querySelector('.field--name-body, .mevzuat-icerik, article, main, #main-content, .region-content') || document.body;
                                    return body ? body.innerText : '';
                                }""")
                                detail_page.close()
                                
                                f.write(f"## {item['title']}\n\n")
                                f.write(f"- **Kaynak:** {item['url']}\n\n")
                                f.write(f"### İçerik:\n{content_text}\n\n")
                                f.write("---\n\n")
                                f.flush()
                            except Exception as err:
                                print(f"Detay çekme hatası ({item['url']}): {err}")
                                
                    except Exception as e:
                        print(f"Sayfa yükleme hatası: {e}")
                        
        browser.close()
        print("\nTÜM TARAMA İŞLEMİ TAMAMLANDI!")

if __name__ == "__main__":
    run()
