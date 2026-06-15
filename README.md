ANALISIS SENTIMEN DOLLAR RP18.000
Proyek ini menganalisis sentimen dari artikel berita (Kompas.com) dan
komentar Instagram terkait pelemahan rupiah ke Rp18.000/USD menggunakan
model IndoBERT.
PERSYARATAN
- Python 3.9 atau lebih baru
- Google Chrome versi terbaru
- Koneksi internet (untuk scraping dan download model)
INSTALASI
1. Clone repository dan masuk ke folder:
   git clone https://github.com/ariframadinata05/kapita-selekta.git
   cd kapita-selekta-sentimen
2. Buat virtual environment:
3. Install dependency:
   pip install -r requirements.txt
4. Buat file .env di folder proyek, isi dengan:
   IG_USER=id_instagram_kamu
   IG_PASS=password_instagram_kamu
   HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxx
Cara dapat HF_TOKEN: daftar gratis di huggingface.co -> Settings -> Access Tokens -> New token (Read).
Gunakan akun Instagram terpisah dari akun pribadi untuk menghindari pemblokiran.
5. MENJALANKAN PROGRAM
Saat program berjalan, Chrome akan terbuka otomatis untuk login Instagram.
Jika muncul CAPTCHA atau pop-up, selesaikan secara manual di browser.
Tekan Enter di terminal setelah berada di halaman utama Instagram.
OUTPUT
Semua file tersimpan otomatis di folder yang sama dengan nama berisi timestamp.
CSV:
  data_bersih_[ts].csv           -- teks mentah sebelum analisis
  komentar_instagram_[ts].csv    -- komentar Instagram saja
  hasil_sentimen_[ts].csv        -- data lengkap + hasil IndoBERT
  ringkasan_sentimen_[ts].csv    -- agregat sentimen per sumber
  top_keywords_[ts].csv          -- frekuensi kata kunci
PNG:
  viz_wordcloud_gabungan_[ts].png
  viz_wordcloud_instagram_[ts].png
  viz_wordcloud_berita_[ts].png
  viz_sentimen_comparison_[ts].png
  viz_keyword_chart_[ts].png
  viz_confidence_dist_[ts].png
  viz_summary_card_[ts].png
MASALAH UMUM
ChromeDriver error     -> pip install --upgrade webdriver-manager
Model tidak terunduh   -> cek HF_TOKEN di .env dan koneksi internet
CAPTCHA terus muncul   -> selesaikan manual, tunggu beberapa menit lalu coba lagi
Komentar sedikit       -> ubah SCROLL_PAUSE = (1.0, 2.0) di baris konfigurasi kode
