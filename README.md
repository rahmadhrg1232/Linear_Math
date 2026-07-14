# 🧮 Aplikasi Program Linear (Python)

Aplikasi desktop untuk menyelesaikan masalah Program Linear dengan **Metode Grafik**
(2 variabel) dan **Metode Simpleks / Big-M** (2–8+ variabel, mendukung operator
`<=`, `>=`, dan `=`). Dilengkapi grafik interaktif, tabel iterasi simpleks dengan
highlight pivot, penjelasan otomatis berbahasa Indonesia, serta export ke PDF & Excel.

## Struktur Proyek

```
linear_program_app/
├── main.py                  # Entry point
├── requirements.txt
├── modules/
│   ├── solver.py             # Kalkulasi matematika murni (tanpa GUI)
│   ├── grafik.py             # Logika & UI Metode Grafik
│   ├── simpleks.py           # Logika & UI Metode Simpleks
│   ├── export.py             # Export PDF & Excel
│   └── ui_components.py      # Komponen UI reusable
└── assets/
    └── style.py              # Tema Light/Dark
```

## Instalasi

### 1. Pastikan Python 3.9+ terpasang
Cek dengan: `python --version` atau `python3 --version`

### 2. (Khusus Linux) Pasang Tkinter
Di sebagian besar distro Linux, Tkinter tidak otomatis ikut ter-install bersama
Python dan harus dipasang terpisah:

```bash
# Ubuntu/Debian
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

Di **Windows** dan **macOS**, Tkinter biasanya sudah bawaan installer resmi
python.org — tidak perlu langkah tambahan.

### 3. Install seluruh dependensi
Dari dalam folder `linear_program_app/`:

```bash
pip install -r requirements.txt
```

## Menjalankan Aplikasi

```bash
python main.py
```

atau `python3 main.py` tergantung konfigurasi sistem kalian.

## Fitur

**Halaman Utama**
- Sidebar menu: Metode Grafik | Metode Simpleks
- Sakelar Light Mode / Dark Mode di pojok kiri bawah

**Metode Grafik**
- Input fungsi tujuan (Max/Min) dan kendala dinamis (tambah/hapus baris)
- Grafik matplotlib embedded (garis kendala, daerah layak diarsir, titik sudut,
  titik optimal) — lengkap dengan toolbar zoom/pan/save bawaan matplotlib
- Tabel seluruh titik sudut beserta nilai Z, dan solusi optimal dengan penjelasan

**Metode Simpleks (Big-M)**
- 2 sampai 8 variabel keputusan, kendala dinamis, operator `<=`, `>=`, `=`
- Tiap iterasi ditampilkan dalam tab tersendiri (accordion), dengan:
  - Highlight kolom pivot (biru), baris pivot (kuning), elemen pivot (merah)
  - Penjelasan otomatis: alasan pemilihan kolom/baris pivot, rasio minimum,
    operasi baris elementer
- Hasil akhir: nilai seluruh variabel & Z optimal

**Export & Cetak**
- Export PDF (rekap soal + seluruh tabel iterasi + grafik)
- Export Excel (1 sheet per iterasi simpleks, lengkap dengan warna highlight)
- Tombol "Print Hasil": karena mekanisme print berbeda-beda tiap OS, aplikasi
  meng-export ke PDF sementara lalu membukanya dengan pembaca PDF default —
  dari sana tinggal `Ctrl+P` / `Cmd+P` seperti biasa

**Validasi Input**
- Mencegah huruf/karakter non-angka pada kolom koefisien & RHS (border merah)
- Peringatan jelas untuk field kosong sebelum perhitungan dijalankan
- Tombol Reset untuk mengulang dari awal

## Verifikasi Akurasi

Mesin solver (`modules/solver.py`) sudah diuji silang dengan `scipy.optimize.linprog`
untuk kasus `<=`, `>=`, `=`, serta Maksimasi & Minimasi — hasilnya identik.

Untuk contoh soal Simpleks di deskripsi awal:
```
Max Z = 5X1 + 4X2 + 3X3
X1 + 2X2 + X3 <= 40
2X1 + X2 + 3X3 <= 60
```
Hasil yang benar (dan dikonfirmasi lewat scipy): **X1 = 26.667, X2 = 6.667, X3 = 0,
Z = 160**.

**Catatan penting soal contoh Metode Grafik**: untuk kendala persis seperti yang
diberikan (`2X+Y<=18`, `2X+3Y<=42`, `3X+Y<=24`, Max Z=3X+5Y), solusi optimal yang
benar secara matematis (dikonfirmasi dengan scipy) adalah **X=0, Y=14, Z=70** —
bukan (3,12,69). Titik (3,12) memang salah satu titik sudut yang sah, tapi (0,14)
menghasilkan Z lebih besar sehingga itulah titik optimalnya. Kemungkinan ada
kendala tambahan yang tidak ikut tertulis di soal aslinya. Aplikasi ini tetap akan
menghitung dengan benar untuk data apa pun yang kalian masukkan — jadi tidak masalah,
cuma supaya kalian tidak bingung kalau hasil di aplikasi beda dari kunci jawaban
yang disebutkan.

## Build jadi .exe / Aplikasi Standalone (opsional)

Kalau butuh yang tidak perlu install Python sama sekali (misal buat dibagikan
ke teman/dosen), bisa dibundel pakai PyInstaller:

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed main.py
```

File hasil build akan muncul di folder `dist/`.
