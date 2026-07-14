"""
assets/style.py
================
Definisi tema (warna, font, ukuran) untuk mode Light & Dark.
Dipakai oleh semua modul UI supaya tampilan konsisten & mudah diubah
dari satu tempat saja.
"""

FONT_UTAMA = "Segoe UI"
FONT_MONO = "Consolas"

TEMA = {
    "light": {
        "bg_utama": "#F4F6FB",
        "bg_sidebar": "#FFFFFF",
        "bg_kartu": "#FFFFFF",
        "aksen": "#4F6EF7",
        "aksen_hover": "#3D5AD9",
        "teks_utama": "#1B1F2A",
        "teks_sekunder": "#6B7280",
        "sukses": "#16A34A",
        "gagal": "#DC2626",
        "border": "#E4E7EC",
        "pivot_kolom": "#BFDBFE",   # biru muda -> highlight kolom pivot
        "pivot_baris": "#FEF08A",   # kuning -> highlight baris pivot
        "pivot_elemen": "#FCA5A5",  # merah muda -> highlight elemen pivot
        "grafik_bg": "#FFFFFF",
        "ctk_mode": "Light",
    },
    "dark": {
        "bg_utama": "#111827",
        "bg_sidebar": "#1B2333",
        "bg_kartu": "#1E293B",
        "aksen": "#6C8CFF",
        "aksen_hover": "#8AA3FF",
        "teks_utama": "#E5E7EB",
        "teks_sekunder": "#9CA3AF",
        "sukses": "#4ADE80",
        "gagal": "#F87171",
        "border": "#2D3748",
        "pivot_kolom": "#1E3A8A",
        "pivot_baris": "#78350F",
        "pivot_elemen": "#7F1D1D",
        "grafik_bg": "#1E293B",
        "ctk_mode": "Dark",
    },
}


def ambil_tema(mode="light"):
    """Ambil dict warna sesuai mode ('light' atau 'dark')."""
    return TEMA.get(mode, TEMA["light"])
