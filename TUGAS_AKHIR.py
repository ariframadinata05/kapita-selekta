import os
import re
import time
import random
import requests
import pandas as pd
import torch
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from wordcloud import WordCloud
from collections import Counter
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
from transformers import pipeline
from dotenv import load_dotenv

# ==========================================
# LOAD ENV
# ==========================================
load_dotenv()

IG_USER  = os.getenv("IG_USER")
IG_PASS  = os.getenv("IG_PASS")
HF_TOKEN = os.getenv("HF_TOKEN")

# ==========================================
# CONFIG
# ==========================================
IG_POST_URL    = "https://www.instagram.com/p/DZJcFuDympN/"
COMMENTS_LIMIT = 10000
SCROLL_PAUSE   = (0.3, 0.5)

NEWS_SOURCES = [
    {
        "name": "Kompas.com",
        "url" : "https://money.kompas.com/read/2026/06/04/085746426/rupiah-tembus-rp-18000-per-dollar-as-terlemah-sepanjang-sejarah?page=1",
    },
]

TRIGGER_KEYWORDS = [
    "dollar", "dolar", "rupiah", "18000", "18rb", "18ribu",
    "kurs", "nilai tukar", "melemah", "turun", "naik",
    "impor", "ekspor", "ekonomi", "inflasi", "pemerintah",
    "bi", "bank indonesia", "jokowi", "prabowo", "menteri",
    "sembako", "harga", "mahal", "susah", "rakyat", "miskin",
    "utang", "hutang", "investasi", "modal", "asing",
    "bbm", "pertamina", "subsidi", "anggaran", "apbn",
    "resesi", "krisis", "khawatir", "takut", "panik",
    "nkri", "indonesia", "bangkrut", "solusi", "harap"
]

# ==========================================
# STOPWORD INDONESIA (KOMPREHENSIF)
# ==========================================
STOPWORDS_ID = set([
    # Kata ganti & kata tunjuk
    "yang", "di", "dan", "ini", "itu", "ke", "dari", "dengan", "untuk",
    "pada", "dalam", "atau", "juga", "adalah", "akan", "ada", "tidak",
    "kami", "kita", "mereka", "anda", "saya", "dia", "ia", "kamu",
    "aku", "gue", "gw", "lo", "lu", "nya", "si", "sang",
    # Kata sambung & partikel
    "tapi", "tetapi", "namun", "karena", "sebab", "sehingga", "agar",
    "supaya", "jika", "jikalau", "kalau", "bila", "apabila", "ketika",
    "saat", "waktu", "setelah", "sebelum", "sejak", "sampai", "hingga",
    "walaupun", "meskipun", "bahwa", "sebagai", "seperti", "yaitu",
    "yakni", "antara", "bagi", "oleh", "tentang", "terhadap", "kepada",
    "daripada", "atas", "bawah", "pun", "lah", "kah", "tah",
    # Kata keterangan
    "sudah", "telah", "belum", "sedang", "masih", "sudah", "baru",
    "hanya", "saja", "paling", "sangat", "sekali", "lebih", "kurang",
    "cukup", "agak", "hampir", "selalu", "sering", "jarang", "kadang",
    "kadang", "mungkin", "pernah", "lagi", "lalu", "kemudian", "terus",
    "juga", "pula", "bahkan", "malah", "justru", "memang", "tentu",
    "tentunya", "sebenarnya", "seharusnya", "semestinya", "mesti",
    "harus", "bisa", "bisa", "dapat", "mampu", "boleh", "perlu",
    "wajib", "jangan", "tolong", "mohon", "silakan",
    # Kata bilangan & urutan
    "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan",
    "sembilan", "sepuluh", "pertama", "kedua", "ketiga",
    # Kata tanya
    "apa", "siapa", "dimana", "kemana", "darimana", "kapan", "mengapa",
    "kenapa", "bagaimana", "berapa", "mana", "apakah", "apabila",
    # Kata umum tidak bermakna dalam konteks analisis
    "orang", "hal", "cara", "banyak", "semua", "tiap", "setiap",
    "lain", "berbagai", "beberapa", "para", "seluruh", "masing",
    "sama", "sendiri", "bersama", "antar", "inter",
    "sini", "sana", "situ", "sini", "begini", "begitu", "demikian",
    "seperti", "misalnya", "contoh", "antara", "lain",
    # Kata gaul / informal tidak bermakna
    "yg", "dgn", "utk", "tdk", "tak", "gak", "ga", "nggak", "ngga",
    "nih", "nih", "sih", "deh", "dong", "aja", "aja", "doang",
    "mah", "atuh", "loh", "lho", "wah", "weh", "hmm", "hm",
    "eh", "ah", "oh", "ih", "uh", "aduh", "astaga", "waduh",
    "kan", "kok", "toh", "nah", "yah", "ya", "iya", "iye",
    "ok", "oke", "oi", "wei", "woy", "hei",
    "tp", "jd", "sm", "dr", "pd", "krn", "sdh", "blm", "msh",
    "udah", "udh", "udh", "emang", "emg", "emng",
    "banget", "bgt", "bener", "beneran", "gitu", "gini",
    "gimana", "gimana", "kayak", "kayaknya", "kaya", "kek",
    "ngapain", "ngga", "nga", "napa", "apa", "apalagi",
    "balik", "balik", "balik",
    # Kata umum media/internet
    "baca", "view", "reply", "like", "follow", "share", "klik",
    "post", "komen", "komentar", "update", "upload", "download",
    "link", "chat", "pesan", "berita", "artikel", "info", "informasi",
    # Kata arah & posisi
    "atas", "bawah", "kiri", "kanan", "depan", "belakang",
    "dalam", "luar", "dalam", "tengah", "pinggir",
    # Kata hubung waktu
    "hari", "minggu", "bulan", "tahun", "menit", "detik", "jam",
    "kemarin", "besok", "sekarang", "dulu", "nanti", "tadi",
    # Huruf & kata tunggal
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l",
    "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x",
    "y", "z",
    # Tambahan spesifik dari word cloud screenshot
    "mau", "per", "kata", "ke", "buat", "nya", "jadi", "ada",
    "apa", "pak", "pake", "pakai", "dulu", "luar", "mata",
    "cuma", "ribu", "rb", "rp", "uang", "sampe", "kalo",
    "kalau", "kalian", "kali", "bila", "aman", "global",
    "rekor", "level", "bukan", "baik", "bagi", "sama",
    "sepanjang", "sejarah", "saja", "nih", "nih",
    "hancur", "keluar", "malah", "masalah", "katanya",
    "Siapa", "siapa", "demo", "nilai", "Mantap", "mantap",
    "wowo", "Purbaya", "purbaya", "aman", "per", "kata",
])

# ==========================================
# WARNA TEMA
# ==========================================
COLOR_NEGATIF = "#E05252"
COLOR_POSITIF = "#4CAF80"
COLOR_BERITA  = "#3A7DC9"
COLOR_IG      = "#C45AB3"
BG_COLOR      = "#F9F9F9"


# ==========================================
# HUMAN DELAY
# ==========================================
def human_delay(a=2, b=5):
    delay = random.uniform(a, b)
    print(f"  [delay] {round(delay, 2)} detik...")
    time.sleep(delay)


# ==========================================
# LOAD IndoBERT MODEL
# ==========================================
print("=" * 60)
print("MEMUAT MODEL IndoBERT...")
print("=" * 60)

device = 0 if torch.cuda.is_available() else -1
print(f"CUDA Available: {torch.cuda.is_available()} | Device: {'GPU' if device == 0 else 'CPU'}")

sentiment_model = pipeline(
    "text-classification",
    model="crypter70/IndoBERT-Sentiment-Analysis",
    token=HF_TOKEN,
    device=device
)

label_map = {
    "LABEL_0": "negatif",
    "LABEL_1": "positif"
}

print("Model berhasil dimuat!\n")

# ==========================================
# CLEAN COMMENT
# ==========================================
def clean_comment(text):
    if not text:
        return None
    text = text.strip()
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^\w\s.,!?]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    blacklist = [
        "like", "reply", "share", "follow", "following",
        "view", "more", "load", "see", "comment", "log in",
        "hidden", "likes", "replies"
    ]
    if text.lower() in blacklist:
        return None
    if len(text.split()) < 3:
        return None
    return text


# ==========================================
# CLEAN NEWS TEXT
# ==========================================
def clean_news_text(text):
    if not text:
        return None
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'http\S+', '', text)
    return text if len(text.split()) >= 5 else None

# ==========================================
# SENTIMENT ANALYSIS
# ==========================================
def analyze_sentiment(text):
    try:
        result     = sentiment_model(text[:512])[0]
        sentiment  = label_map.get(result["label"], result["label"])
        confidence = round(result["score"], 4)
        return sentiment, confidence
    except Exception:
        return "unknown", 0.0


# ==========================================
# KEYWORD EXTRACTION
# ==========================================
def extract_keywords(text, keywords=TRIGGER_KEYWORDS):
    text_lower = text.lower()
    return [kw for kw in keywords if kw in text_lower]


def top_keywords(texts, top_n=20):
    counter = Counter()
    for text in texts:
        if text:
            counter.update(extract_keywords(text))
    return pd.DataFrame(counter.most_common(top_n), columns=["keyword", "frekuensi"])

# ==========================================
# SETUP CHROME
# ==========================================
def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    })
    return driver


# ==========================================
# LOGIN INSTAGRAM
# ==========================================
def login_instagram(driver):
    print("\n[LOGIN] Membuka halaman login Instagram...")
    driver.get("https://www.instagram.com/accounts/login/")
    human_delay(6, 10)
    wait = WebDriverWait(driver, 30)

    username_selectors = [
        (By.NAME, "email"),
        (By.NAME, "username"),
        (By.XPATH, "//input[@aria-label='Nomor telepon, nama pengguna, atau email']"),
        (By.XPATH, "//input[@aria-label='Phone number, username, or email']"),
        (By.CSS_SELECTOR, "input[name='email']"),
        (By.CSS_SELECTOR, "input[name='username']"),
        (By.XPATH, "//input[@type='text']"),
        (By.CSS_SELECTOR, "input[type='text']"),
    ]
    password_selectors = [
        (By.NAME, "pass"),
        (By.NAME, "password"),
        (By.XPATH, "//input[@aria-label='Kata sandi']"),
        (By.XPATH, "//input[@aria-label='Password']"),
        (By.CSS_SELECTOR, "input[name='pass']"),
        (By.CSS_SELECTOR, "input[name='password']"),
        (By.XPATH, "//input[@type='password']"),
        (By.CSS_SELECTOR, "input[type='password']"),
    ]

    username_input = password_input = None

    print("  Mencari field email...")
    for by, selector in username_selectors:
        try:
            elem = wait.until(EC.presence_of_element_located((by, selector)))
            if elem.is_displayed():
                username_input = elem
                break
        except Exception:
            continue

    print("  Mencari field password...")
    for by, selector in password_selectors:
        try:
            elem = driver.find_element(by, selector)
            if elem.is_displayed():
                password_input = elem
                break
        except Exception:
            continue

    if username_input and password_input:
        username_input.clear()
        for char in IG_USER:
            username_input.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        human_delay(1, 2)
        password_input.clear()
        for char in IG_PASS:
            password_input.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        human_delay(1, 2)
        password_input.send_keys(Keys.RETURN)
        print("\n  Menunggu redirect setelah login...")
        human_delay(3, 8)
    else:
        print("\n  [GAGAL] Field otomatis tidak ditemukan.")

    print("\n   PERHATIAN: Jika ada CAPTCHA / pop-up 'Save Info', selesaikan MANUAL.")
    input("  >>> TEKAN ENTER HANYA JIKA ANDA SUDAH BERADA DI HALAMAN FEED INSTAGRAM UTAMA... ")


# ==========================================
# SCROLL & LOAD KOMENTAR INSTAGRAM
# ==========================================
def load_all_comments(driver):
    print(f"\n[INSTAGRAM] Membuka post & memuat komentar (: {COMMENTS_LIMIT})...")
    driver.get(IG_POST_URL)
    human_delay(3, 10)

    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "article")))
    except Exception:
        print("Post lambat dimuat, merefresh halaman...")
        driver.refresh()
        human_delay(3, 8)

    comment_container = None
    for selector in ["div.x5yr21d.xw2csxc.x1odjw0f.x1n2onr6", "div.x5yr21d[style*='overflow']"]:
        try:
            for elem in driver.find_elements(By.CSS_SELECTOR, selector):
                if elem.is_displayed():
                    comment_container = elem
                    print(f" Container ditemukan ({selector})")
                    break
            if comment_container:
                break
        except Exception:
            pass

    if not comment_container:
        print("  [WARN] Container spesifik tidak ditemukan. Mencari alternatif...")
        try:
            containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'x5yr21d')]")
            if containers:
                comment_container = containers[-1]
        except Exception:
            pass

        print("  Mencari tombol 'View all comments'...")
        view_all_selectors = [
            "//span[contains(text(), 'View all') and contains(text(), 'comment')]",
            "//span[contains(text(), 'Lihat semua') and contains(text(), 'komentar')]",
            "//div[@role='button']//span[contains(text(), 'View all')]",
            "//div[@role='button']//span[contains(text(), 'Lihat semua')]",
            "//a[contains(text(), 'View all')]",
            "//a[contains(text(), 'Lihat semua')]",
        ]
        for sel in view_all_selectors:
            try:
                btns = driver.find_elements(By.XPATH, sel)
                for btn in btns:
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click();", btn)
                        print("  [OK] Tombol 'View all comments' diklik.")
                        time.sleep(1.5)  # tunggu komentar termuat
                        break
            except Exception:
                pass
    collected_comments = set()
    no_new_data = 0

    for scroll_count in range(500):
        old_count = len(collected_comments)
        try:
            target = comment_container if comment_container else driver
            spans  = target.find_elements(By.CSS_SELECTOR, "span[dir='auto']")
            for span in spans:
                cleaned = clean_comment(span.text)
                if cleaned:
                    collected_comments.add(cleaned)
        except Exception:
            pass

        new_count = len(collected_comments)
        print(f"Komentar: {new_count} | Scroll: {scroll_count + 1}")
        if new_count >= COMMENTS_LIMIT:
            break
        no_new_data = no_new_data + 1 if new_count == old_count else 0
        if no_new_data >= 3:
            print("Tidak ada komentar baru, menghentikan scroll.")
            break

        try:
            for sel in [
                "//svg[@aria-label='Load more comments' or @aria-label='Muat komentar lainnya']//ancestor::div[@role='button']",
                "//button[contains(., 'View more') or contains(., 'Load more') or contains(., 'Muat komentar')]"
            ]:
                for btn in driver.find_elements(By.XPATH, sel):
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(random.uniform(1, 2))
        except Exception:
            pass

        try:
            if comment_container:
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", comment_container)
            else:
                driver.execute_script("window.scrollBy(0, 500);")
        except Exception:
            pass

        time.sleep(random.uniform(*SCROLL_PAUSE))

    result = list(collected_comments)[:COMMENTS_LIMIT]
    print(f"\nTOTAL KOMENTAR FINAL: {len(result)}")
    return result


# ==========================================
# SCRAPE ARTIKEL BERITA
# ==========================================
def scrape_news(url, source_name):
    print(f"\n  Scraping berita: {source_name}")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [ERROR] {e}")
        return []

    soup       = BeautifulSoup(resp.text, "html.parser")
    title      = soup.find("h1")
    title_text = clean_news_text(title.get_text()) if title else "N/A"
    rows       = []
    for p in soup.find_all("p"):
        text = clean_news_text(p.get_text())
        if text and len(text.split()) >= 8:
            rows.append({
                "sumber"    : source_name,
                "url"       : url,
                "judul"     : title_text,
                "konten"    : text,
                "tipe"      : "berita",
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
    print(f"    -> {len(rows)} paragraf berhasil diambil")
    return rows


# ==========================================
# VISUALISASI 1: WORD CLOUD (dengan stopword)
# ==========================================
def generate_wordcloud(texts, judul, filename, colormap="RdYlGn"):
    """Word Cloud dengan stopword Indonesia komprehensif."""
    # Filter stopword per kata, bukan per kalimat
    filtered_words = []
    for text in texts:
        if not text:
            continue
        for word in text.split():
            word_clean = re.sub(r'[^\w]', '', word).lower()
            if (
                word_clean
                and word_clean not in STOPWORDS_ID
                and len(word_clean) > 2          # hapus kata < 3 huruf
                and not word_clean.isdigit()     # hapus angka murni
            ):
                filtered_words.append(word_clean)

    if not filtered_words:
        print(f"  [SKIP] Tidak ada kata tersisa setelah filter stopword: {filename}")
        return

    gabung = " ".join(filtered_words)

    wc = WordCloud(
        width=1600,
        height=900,
        background_color="white",
        colormap=colormap,
        max_words=100,
        collocations=False,
        prefer_horizontal=0.85,
        margin=10,
        min_word_length=3,
    ).generate(gabung)

    fig, ax = plt.subplots(figsize=(16, 9), facecolor="white")
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(judul, fontsize=20, fontweight="bold", color="#1A1A2E", pad=18)
    plt.tight_layout(pad=1)
    plt.savefig(filename, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  [PNG] Word cloud tersimpan : {filename}")


# ==========================================
# VISUALISASI 2: PERBANDINGAN SENTIMEN (Donut Chart) — FIXED
# ==========================================
def generate_sentiment_comparison(df_sentimen, filename):
    """Donut chart sentimen Berita vs Instagram side-by-side.
    FIX: guard terhadap subset kosong / semua sizes == 0.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 7), facecolor=BG_COLOR)
    fig.suptitle(
        "Perbandingan Sentimen: Media Berita vs Komentar Instagram",
        fontsize=17, fontweight="bold", color="#1A1A2E", y=1.01
    )

    tipe_config = [
        ("berita",      "Media Berita",      COLOR_BERITA),
        ("komentar_ig", "Komentar Instagram", COLOR_IG),
    ]

    colors_map = {
        "negatif": COLOR_NEGATIF,
        "positif": COLOR_POSITIF,
        "unknown": "#AAAAAA",
    }
    sentimen_order = ["negatif", "positif", "unknown"]

    for ax, (tipe, label_tipe, warna_tipe) in zip(axes, tipe_config):
        ax.set_facecolor(BG_COLOR)
        subset = df_sentimen[df_sentimen["tipe"] == tipe]
        counts = subset["sentimen"].value_counts()

        # Hanya ambil label yang benar-benar ada DAN nilainya > 0
        labels_plot = [s for s in sentimen_order if s in counts.index and counts[s] > 0]
        sizes       = [int(counts[s]) for s in labels_plot]
        colors_plot = [colors_map[s] for s in labels_plot]

        # Guard: jika data kosong, tampilkan placeholder
        if not sizes or sum(sizes) == 0:
            ax.text(0.5, 0.5,
                    f"Tidak ada data\nuntuk {label_tipe}",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=14, color="#888888")
            ax.set_title(label_tipe, fontsize=14, fontweight="bold",
                         color=warna_tipe, pad=14)
            continue

        wedges, _, autotexts = ax.pie(
            sizes,
            labels=None,
            colors=colors_plot,
            autopct="%1.1f%%",
            startangle=90,
            pctdistance=0.78,
            wedgeprops={"width": 0.55, "edgecolor": "white", "linewidth": 2},
        )
        for at in autotexts:
            at.set_fontsize(13)
            at.set_fontweight("bold")
            at.set_color("white")

        # Total di tengah donut
        ax.text(0, 0, f"{sum(sizes)}\ndata",
                ha="center", va="center",
                fontsize=15, fontweight="bold", color="#1A1A2E")

        legend_patches = [
            mpatches.Patch(color=colors_map[s], label=f"{s.capitalize()} ({int(counts.get(s, 0))})")
            for s in labels_plot
        ]
        ax.legend(handles=legend_patches, loc="lower center",
                  bbox_to_anchor=(0.5, -0.12), ncol=len(labels_plot),
                  fontsize=11, frameon=False)
        ax.set_title(label_tipe, fontsize=14, fontweight="bold",
                     color=warna_tipe, pad=14)

    plt.tight_layout()
    plt.savefig(filename, dpi=180, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close()
    print(f"  [PNG] Sentimen comparison  : {filename}")


# ==========================================
# VISUALISASI 3: TOP KEYWORDS (Horizontal Bar)
# ==========================================
def generate_keyword_chart(df_keywords, filename, top_n=15):
    """Horizontal bar chart top keyword dengan warna gradient."""
    if df_keywords.empty:
        print(f"  [SKIP] Tidak ada keyword: {filename}")
        return

    df_plot = df_keywords.head(top_n).sort_values("frekuensi")
    norm    = plt.Normalize(df_plot["frekuensi"].min(), df_plot["frekuensi"].max())
    colors  = plt.cm.RdYlGn(norm(df_plot["frekuensi"].values))

    fig, ax = plt.subplots(figsize=(12, 8), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    bars = ax.barh(df_plot["keyword"], df_plot["frekuensi"],
                   color=colors, edgecolor="white", linewidth=0.8, height=0.65)

    for bar, val in zip(bars, df_plot["frekuensi"]):
        ax.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height() / 2,
                str(int(val)), va="center", ha="left",
                fontsize=11, fontweight="bold", color="#333333")

    ax.set_xlabel("Frekuensi Kemunculan", fontsize=12, color="#555555")
    ax.set_title(f"Top {top_n} Kata Kunci Pemicu Percakapan",
                 fontsize=16, fontweight="bold", color="#1A1A2E", pad=16)
    ax.tick_params(axis="y", labelsize=12)
    ax.tick_params(axis="x", labelsize=10, colors="#888888")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#DDDDDD")
    ax.spines["bottom"].set_color("#DDDDDD")
    ax.xaxis.grid(True, linestyle="--", alpha=0.5, color="#CCCCCC")
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(filename, dpi=180, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close()
    print(f"  [PNG] Keyword chart        : {filename}")


# ==========================================
# VISUALISASI 4: DISTRIBUSI CONFIDENCE SCORE
# ==========================================
def generate_confidence_chart(df_sentimen, filename):
    """Box plot + strip plot confidence score per tipe data."""
    df_plot = df_sentimen[df_sentimen["sentimen"].isin(["positif", "negatif"])].copy()

    if df_plot.empty:
        print(f"  [SKIP] Tidak ada data confidence: {filename}")
        return

    df_plot["label"] = df_plot.apply(
        lambda r: f"{'Berita' if r['tipe'] == 'berita' else 'Instagram'}\n({r['sentimen'].capitalize()})",
        axis=1
    )

    order      = sorted(df_plot["label"].unique())
    colors_map = {lbl: (COLOR_NEGATIF if "negatif" in lbl.lower() else COLOR_POSITIF) for lbl in order}

    fig, ax = plt.subplots(figsize=(13, 7), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    sns.boxplot(data=df_plot, x="label", y="confidence", order=order,
                palette=colors_map, width=0.45, linewidth=1.5, fliersize=0,
                boxprops={"alpha": 0.6}, ax=ax)
    sns.stripplot(data=df_plot, x="label", y="confidence", order=order,
                  palette=colors_map, size=5, alpha=0.55, jitter=True, ax=ax)

    ax.set_title("Distribusi Confidence Score per Kategori Sentimen",
                 fontsize=16, fontweight="bold", color="#1A1A2E", pad=16)
    ax.set_xlabel("Kategori", fontsize=12, color="#555555")
    ax.set_ylabel("Confidence Score", fontsize=12, color="#555555")
    ax.set_ylim(0, 1.05)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5, color="#CCCCCC")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#DDDDDD")
    ax.spines["bottom"].set_color("#DDDDDD")
    ax.tick_params(axis="x", labelsize=11)
    ax.tick_params(axis="y", labelsize=10)

    plt.tight_layout()
    plt.savefig(filename, dpi=180, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close()
    print(f"  [PNG] Confidence chart     : {filename}")


# ==========================================
# VISUALISASI 5: RINGKASAN EKSEKUTIF (Summary Card)
# ==========================================
def generate_summary_card(df_sentimen, timestamp, filename):
    """1 halaman ringkasan eksekutif dengan angka-angka kunci."""
    berita = df_sentimen[df_sentimen["tipe"] == "berita"]
    ig     = df_sentimen[df_sentimen["tipe"] == "komentar_ig"]

    def pct(df, label):
        total = len(df)
        if total == 0:
            return 0.0
        return round(len(df[df["sentimen"] == label]) / total * 100, 1)

    b_neg = pct(berita, "negatif")
    b_pos = pct(berita, "positif")
    i_neg = pct(ig, "negatif")
    i_pos = pct(ig, "positif")
    gap   = round(i_neg - b_neg, 1)

    fig, ax = plt.subplots(figsize=(14, 8), facecolor="#1A1A2E")
    ax.set_facecolor("#1A1A2E")
    ax.axis("off")

    # Judul
    ax.text(0.5, 0.95,
            "RINGKASAN EKSEKUTIF — ANALISIS SENTIMEN DOLLAR Rp18.000",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=17, fontweight="bold", color="white")
    ax.text(0.5, 0.88,
            f"Kapita Selekta  •  {datetime.now().strftime('%d %B %Y')}",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=12, color="#AAAAAA")

    ax.axhline(y=0.83, xmin=0.05, xmax=0.95, color="#FFFFFF", alpha=0.2, linewidth=1)

    # 3 kotak angka utama
    for val, lbl, col, xpos in [
        (str(len(df_sentimen)), "TOTAL DATA",           "#3A7DC9", 0.18),
        (str(len(berita)),      "PARAGRAF BERITA",      "#3A7DC9", 0.50),
        (str(len(ig)),          "KOMENTAR INSTAGRAM",   COLOR_IG,  0.82),
    ]:
        ax.text(xpos, 0.72, val,
                transform=ax.transAxes, ha="center", va="center",
                fontsize=36, fontweight="bold", color=col)
        ax.text(xpos, 0.62, lbl,
                transform=ax.transAxes, ha="center", va="center",
                fontsize=10, color="#CCCCCC")

    ax.axhline(y=0.56, xmin=0.05, xmax=0.95, color="#FFFFFF", alpha=0.2, linewidth=1)

    # Sentimen breakdown
    for (nama, neg, pos, col), yy in zip(
        [
            ("MEDIA BERITA",       b_neg, b_pos, COLOR_BERITA),
            ("KOMENTAR INSTAGRAM", i_neg, i_pos, COLOR_IG),
        ],
        [0.44, 0.30]
    ):
        ax.text(0.18, yy, nama,
                transform=ax.transAxes, ha="center", va="center",
                fontsize=12, fontweight="bold", color=col)
        ax.text(0.50, yy, f"🔴  Negatif : {neg}%",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=13, color=COLOR_NEGATIF, fontweight="bold")
        ax.text(0.82, yy, f"🟢  Positif : {pos}%",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=13, color=COLOR_POSITIF, fontweight="bold")

    ax.axhline(y=0.22, xmin=0.05, xmax=0.95, color="#FFFFFF", alpha=0.2, linewidth=1)

    gap_color = COLOR_NEGATIF if gap > 0 else COLOR_POSITIF
    gap_sign  = "+" if gap > 0 else ""
    ax.text(0.5, 0.15,
            f"Kesenjangan Narasi: Sentimen negatif publik Instagram lebih tinggi "
            f"{gap_sign}{gap}% dibanding media berita",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=12, color=gap_color, style="italic")

    ax.text(0.5, 0.05, f"Generated: {timestamp}",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=9, color="#666666")

    plt.tight_layout()
    plt.savefig(filename, dpi=180, bbox_inches="tight", facecolor="#1A1A2E")
    plt.close()
    print(f"  [PNG] Summary card         : {filename}")


# ==========================================
# MAIN
# ==========================================
def main():
    print("\n" + "=" * 60)
    print("  ANALISIS SENTIMEN: DOLLAR RP18.000")
    print("  Tugas Kapita Selekta - Pak Menteri Purbaya Brief")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ------------------------------------------
    # STEP 1: SCRAPING ARTIKEL BERITA
    # ------------------------------------------
    print("\n[STEP 1] SCRAPING ARTIKEL BERITA...")
    all_news_rows = []
    for source in NEWS_SOURCES:
        rows = scrape_news(source["url"], source["name"])
        all_news_rows.extend(rows)
        time.sleep(random.uniform(0.3, 0.5))

    if not all_news_rows:
        print("\n  [WARN] URL berita gagal. Menggunakan data contoh...")
        all_news_rows = [{
            "sumber"    : "Kompas.com (contoh)",
            "url"       : "https://money.kompas.com",
            "judul"     : "Rupiah Tembus Rp18.000 per Dollar AS, Terlemah Sepanjang Sejarah",
            "konten"    : "Nilai tukar rupiah terhadap dolar Amerika Serikat melemah dan menyentuh level Rp18.000 per dolar AS untuk pertama kalinya. Bank Indonesia segera mengambil langkah intervensi guna menstabilkan nilai tukar.",
            "tipe"      : "berita",
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }]

    print(f"\n  Total paragraf berita : {len(all_news_rows)}")

    # ------------------------------------------
    # STEP 2: SCRAPING KOMENTAR INSTAGRAM
    # ------------------------------------------
    print("\n[STEP 2] SCRAPING KOMENTAR INSTAGRAM...")
    driver = get_driver()
    try:
        login_instagram(driver)
        ig_comments = load_all_comments(driver)
    finally:
        driver.quit()
        print("  Browser ditutup.")

    scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ------------------------------------------
    # STEP 3: SIMPAN DATA BERSIH (RAW)
    # ------------------------------------------
    print("\n[STEP 3] MENYIMPAN DATA BERSIH (RAW)...")

    berita_bersih = [{
        "sumber": r["sumber"], "url": r["url"], "judul": r["judul"],
        "konten": r["konten"], "tipe": r["tipe"], "scraped_at": r["scraped_at"],
    } for r in all_news_rows]

    ig_bersih = [{
        "sumber"    : "Instagram",
        "url"       : IG_POST_URL,
        "judul"     : "Komentar Instagram - Dollar Rp18.000",
        "konten"    : c,
        "tipe"      : "komentar_ig",
        "scraped_at": scrape_time,
    } for c in ig_comments]

    # FILE 1: Data bersih (berita + IG raw, belum sentimen)
    df_bersih   = pd.concat([pd.DataFrame(berita_bersih), pd.DataFrame(ig_bersih)], ignore_index=True)
    file_bersih = f"data_bersih_{timestamp}.csv"
    df_bersih.to_csv(file_bersih, index=False, encoding="utf-8-sig")
    print(f"  [SAVED] 1. Dataset bersih (raw)       : {file_bersih}")
    print(f"          -> {len(berita_bersih)} baris berita + {len(ig_bersih)} komentar IG")

    # FILE 2: Komentar Instagram saja
    file_ig = f"komentar_instagram_{timestamp}.csv"
    pd.DataFrame(ig_bersih).to_csv(file_ig, index=False, encoding="utf-8-sig")
    print(f"  [SAVED] 2. Komentar Instagram saja     : {file_ig}")
    print(f"          -> {len(ig_bersih)} komentar")

    # ------------------------------------------
    # STEP 4: ANALISIS SENTIMEN
    # ------------------------------------------
    print("\n[STEP 4] ANALISIS SENTIMEN DENGAN IndoBERT...")

    print("  Menganalisis paragraf berita...")
    for i, row in enumerate(all_news_rows):
        sentimen, conf = analyze_sentiment(row["konten"])
        row["sentimen"]   = sentimen
        row["confidence"] = conf
        row["keywords"]   = ", ".join(extract_keywords(row["konten"]))
        print(f"    [{i+1}/{len(all_news_rows)}] {sentimen} ({conf}) — {row['konten'][:60]}...")

    print(f"\n  Menganalisis {len(ig_comments)} komentar Instagram...")
    ig_rows = []
    for i, comment in enumerate(ig_comments):
        sentimen, conf = analyze_sentiment(comment)
        ig_rows.append({
            "sumber"    : "Instagram",
            "url"       : IG_POST_URL,
            "judul"     : "Komentar Instagram - Dollar Rp18.000",
            "konten"    : comment,
            "tipe"      : "komentar_ig",
            "scraped_at": scrape_time,
            "sentimen"  : sentimen,
            "confidence": conf,
            "keywords"  : ", ".join(extract_keywords(comment)),
        })
        print(f"    [{i+1}/{len(ig_comments)}] {sentimen} ({conf}) — {comment[:60]}...")

    # ------------------------------------------
    # STEP 5: SIMPAN HASIL SENTIMEN
    # ------------------------------------------
    print("\n[STEP 5] MENYIMPAN HASIL SENTIMEN...")

    df_sentimen   = pd.concat([pd.DataFrame(all_news_rows), pd.DataFrame(ig_rows)], ignore_index=True)
    file_sentimen = f"hasil_sentimen_{timestamp}.csv"
    df_sentimen.to_csv(file_sentimen, index=False, encoding="utf-8-sig")
    print(f"  [SAVED] 3. Hasil sentimen lengkap      : {file_sentimen}")
    print(f"          -> {len(df_sentimen)} baris total")

    summary = df_sentimen.groupby(["tipe", "sentimen"]).size().reset_index(name="jumlah")
    summary["persen"] = summary.groupby("tipe")["jumlah"].transform(
        lambda x: (x / x.sum() * 100).round(2)
    )
    file_summary = f"ringkasan_sentimen_{timestamp}.csv"
    summary.to_csv(file_summary, index=False, encoding="utf-8-sig")
    print(f"  [SAVED] 4. Ringkasan sentimen          : {file_summary}")

    semua_teks  = df_sentimen["konten"].dropna().tolist()
    df_keywords = top_keywords(semua_teks, top_n=20)
    file_kw     = f"top_keywords_{timestamp}.csv"
    df_keywords.to_csv(file_kw, index=False, encoding="utf-8-sig")
    print(f"  [SAVED] 5. Top keyword pemicu          : {file_kw}")

    # ------------------------------------------
    # STEP 6: GENERATE VISUALISASI (PNG SIAP PPT)
    # ------------------------------------------
    print("\n[STEP 6] GENERATE VISUALISASI UNTUK PRESENTASI...")

    # 6a. Word Cloud gabungan
    generate_wordcloud(
        texts    = df_sentimen["konten"].dropna().tolist(),
        judul    = "Word Cloud — Kata Dominan (Berita + Komentar Instagram)",
        filename = f"viz_wordcloud_gabungan_{timestamp}.png",
        colormap = "RdYlGn",
    )

    # 6b. Word Cloud komentar IG
    ig_texts = df_sentimen[df_sentimen["tipe"] == "komentar_ig"]["konten"].dropna().tolist()
    if ig_texts:
        generate_wordcloud(
            texts    = ig_texts,
            judul    = "Word Cloud — Opini Publik Instagram",
            filename = f"viz_wordcloud_instagram_{timestamp}.png",
            colormap = "cool",
        )

    # 6c. Word Cloud berita
    berita_texts = df_sentimen[df_sentimen["tipe"] == "berita"]["konten"].dropna().tolist()
    if berita_texts:
        generate_wordcloud(
            texts    = berita_texts,
            judul    = "Word Cloud — Narasi Media Berita",
            filename = f"viz_wordcloud_berita_{timestamp}.png",
            colormap = "Blues",
        )

    # 6d. Donut chart perbandingan sentimen (FIXED)
    generate_sentiment_comparison(
        df_sentimen = df_sentimen,
        filename    = f"viz_sentimen_comparison_{timestamp}.png",
    )

    # 6e. Bar chart top keyword
    generate_keyword_chart(
        df_keywords = df_keywords,
        filename    = f"viz_keyword_chart_{timestamp}.png",
        top_n       = 15,
    )

    # 6f. Confidence score distribution
    generate_confidence_chart(
        df_sentimen = df_sentimen,
        filename    = f"viz_confidence_dist_{timestamp}.png",
    )

    # 6g. Summary card
    generate_summary_card(
        df_sentimen = df_sentimen,
        timestamp   = timestamp,
        filename    = f"viz_summary_card_{timestamp}.png",
    )

    # ------------------------------------------
    # RINGKASAN AKHIR
    # ------------------------------------------
    print("\n" + "=" * 60)
    print("  RINGKASAN OUTPUT:")
    print("=" * 60)
    print(f"  CSV:")
    print(f"    1. data_bersih_{timestamp}.csv")
    print(f"       Berita + IG raw, BELUM sentimen")
    print(f"    2. komentar_instagram_{timestamp}.csv")
    print(f"       Komentar Instagram saja")
    print(f"    3. hasil_sentimen_{timestamp}.csv")
    print(f"       Semua data + hasil sentimen IndoBERT")
    print(f"    4. ringkasan_sentimen_{timestamp}.csv")
    print(f"       Agregat sentimen per tipe data")
    print(f"    5. top_keywords_{timestamp}.csv")
    print(f"       20 keyword paling sering muncul")
    print(f"  PNG :")
    print(f"    6. viz_wordcloud_gabungan_{timestamp}.png")
    print(f"    7. viz_wordcloud_instagram_{timestamp}.png")
    print(f"    8. viz_wordcloud_berita_{timestamp}.png")
    print(f"    9. viz_sentimen_comparison_{timestamp}.png")
    print(f"   10. viz_keyword_chart_{timestamp}.png")
    print(f"   11. viz_confidence_dist_{timestamp}.png")
    print(f"   12. viz_summary_card_{timestamp}.png")
    print("=" * 60)
    print("  SELESAI! .")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
