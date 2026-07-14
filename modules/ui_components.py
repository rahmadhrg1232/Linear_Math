"""
modules/ui_components.py
=========================
Kumpulan komponen UI yang dipakai berulang kali di modul grafik.py dan
simpleks.py, supaya kode tidak duplikat (DRY) dan mudah dimaintain.
"""

import customtkinter as ctk
import tkinter as tk


def validasi_angka(teks):
    """
    Fungsi validasi untuk dipasang di Entry (validatecommand).
    Mengizinkan: kosong, tanda minus di depan, angka, dan satu titik desimal.
    Menolak huruf atau karakter lain -> mencegah input tidak valid dari akar masalahnya.
    """
    if teks == "" or teks == "-":
        return True
    try:
        float(teks)
        return True
    except ValueError:
        return False


class EntriAngka(ctk.CTkEntry):
    """
    CTkEntry yang hanya menerima input angka (boleh desimal & minus).
    Border akan otomatis merah jika kosong saat divalidasi lewat method
    `valid()`, membantu memberi pesan error yang jelas ke pengguna.
    """

    def __init__(self, master, nilai_awal=0.0, lebar=90, **kwargs):
        vcmd = (master.register(validasi_angka), "%P")
        super().__init__(
            master,
            width=lebar,
            justify="center",
            validate="key",
            validatecommand=vcmd,
            **kwargs,
        )
        self.insert(0, str(nilai_awal))

    def ambil_nilai(self, default=0.0):
        """Ambil isi entry sebagai float. Kalau kosong/invalid, pakai default."""
        teks = self.get().strip()
        if teks in ("", "-", "."):
            return default
        try:
            return float(teks)
        except ValueError:
            return default

    def valid(self):
        """Cek apakah isi entry adalah angka yang sah (bukan kosong/'-')."""
        teks = self.get().strip()
        if teks in ("", "-", "."):
            return False
        try:
            float(teks)
            return True
        except ValueError:
            return False

    def tandai_error(self, tema, aktif=True):
        """Beri border merah kalau input tidak valid, atau kembalikan ke normal."""
        if aktif:
            self.configure(border_color=tema["gagal"], border_width=2)
        else:
            self.configure(border_color=tema["border"], border_width=1)


def buat_kartu(parent, tema, judul=None):
    """Buat frame 'kartu' dengan sedikit padding & sudut membulat, opsional judul."""
    kartu = ctk.CTkFrame(parent, fg_color=tema["bg_kartu"], corner_radius=14,
                          border_width=1, border_color=tema["border"])
    if judul:
        label = ctk.CTkLabel(kartu, text=judul, font=("Segoe UI", 16, "bold"),
                              text_color=tema["teks_utama"])
        label.pack(anchor="w", padx=18, pady=(14, 4))
    return kartu


def buat_scrollable(parent, tema, tinggi=260):
    """Buat frame scrollable vertikal (dipakai untuk daftar kendala dinamis)."""
    frame = ctk.CTkScrollableFrame(parent, fg_color="transparent", height=tinggi)
    return frame


class BarisKendala(ctk.CTkFrame):
    """
    Satu baris input kendala: koefisien x1..xn, dropdown operator (<=, >=, =),
    entry RHS, dan tombol hapus (x). Dipakai di metode Grafik (n=2) maupun
    Simpleks (n bisa 2-8+).

    Callback `on_hapus(self)` dipanggil ketika tombol hapus ditekan supaya
    parent (halaman) bisa menghapus baris ini dari daftar & re-layout.
    """

    def __init__(self, master, tema, jumlah_var, nomor, on_hapus=None,
                 nilai_awal_koef=1.0, nilai_awal_rhs=10.0, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.tema = tema
        self.jumlah_var = jumlah_var
        self.nomor = nomor
        self.on_hapus = on_hapus
        self.entri_koef = []

        label_nomor = ctk.CTkLabel(self, text=f"K{nomor}:", width=32,
                                    font=("Segoe UI", 12, "bold"),
                                    text_color=tema["aksen"])
        label_nomor.pack(side="left", padx=(0, 4))

        for j in range(jumlah_var):
            if j > 0:
                tanda = ctk.CTkLabel(self, text="+", width=10, text_color=tema["teks_sekunder"])
                tanda.pack(side="left")
            e = EntriAngka(self, nilai_awal=nilai_awal_koef, lebar=56)
            e.pack(side="left", padx=2)
            self.entri_koef.append(e)
            var_label = ctk.CTkLabel(self, text=f"x{j+1}", width=20, text_color=tema["teks_sekunder"])
            var_label.pack(side="left")

        self.op_var = tk.StringVar(value="<=")
        self.dropdown_op = ctk.CTkOptionMenu(self, values=["<=", ">=", "="],
                                              variable=self.op_var, width=64,
                                              fg_color=tema["aksen"],
                                              button_color=tema["aksen_hover"])
        self.dropdown_op.pack(side="left", padx=6)

        self.entri_rhs = EntriAngka(self, nilai_awal=nilai_awal_rhs, lebar=70)
        self.entri_rhs.pack(side="left", padx=4)

        self.tombol_hapus = ctk.CTkButton(
            self, text="✕", width=28, height=28, fg_color=tema["gagal"],
            hover_color="#B91C1C", command=self._panggil_hapus
        )
        self.tombol_hapus.pack(side="left", padx=(8, 0))

    def _panggil_hapus(self):
        if self.on_hapus:
            self.on_hapus(self)

    def ambil_data(self):
        """Kembalikan dict {'coeffs': [...], 'operator': str, 'rhs': float}."""
        return {
            "coeffs": [e.ambil_nilai() for e in self.entri_koef],
            "operator": self.op_var.get(),
            "rhs": self.entri_rhs.ambil_nilai(),
        }

    def valid(self):
        """True kalau semua entry (koefisien & RHS) terisi angka yang sah."""
        return all(e.valid() for e in self.entri_koef) and self.entri_rhs.valid()

    def tandai_error(self):
        for e in self.entri_koef:
            e.tandai_error(self.tema, not e.valid())
        self.entri_rhs.tandai_error(self.tema, not self.entri_rhs.valid())


def tampilkan_pesan_error(parent, tema, pesan):
    """
    Tampilkan popup pesan error sederhana (dipakai untuk validasi input:
    field kosong, kendala tidak valid, dsb).
    """
    popup = ctk.CTkToplevel(parent)
    popup.title("Peringatan")
    popup.geometry("380x160")
    popup.grab_set()
    popup.configure(fg_color=tema["bg_utama"])

    label = ctk.CTkLabel(popup, text="⚠ Input Tidak Valid", font=("Segoe UI", 15, "bold"),
                          text_color=tema["gagal"])
    label.pack(pady=(20, 6))

    isi = ctk.CTkLabel(popup, text=pesan, wraplength=320, justify="center",
                        text_color=tema["teks_utama"])
    isi.pack(pady=6, padx=16)

    tombol = ctk.CTkButton(popup, text="Mengerti", fg_color=tema["aksen"],
                            hover_color=tema["aksen_hover"], command=popup.destroy)
    tombol.pack(pady=16)
    return popup
