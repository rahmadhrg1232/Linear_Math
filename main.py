"""
main.py
=======
Entry point Aplikasi Program Linear.

Cara menjalankan:
    python main.py

Lihat README.md untuk instalasi dependensi & instruksi lebih lengkap.
"""

import sys
import os
import platform
import subprocess
import customtkinter as ctk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from assets.style import ambil_tema
from modules.grafik import HalamanGrafik
from modules.simpleks import HalamanSimpleks


class AplikasiProgramLinear(ctk.CTk):
    """Window utama aplikasi: sidebar menu + area konten (grafik/simpleks)."""

    def __init__(self):
        super().__init__()
        self.mode_tema = "light"
        self.tema = ambil_tema(self.mode_tema)

        self.title("Aplikasi Program Linear")
        self.geometry("1180x760")
        self.minsize(980, 640)

        ctk.set_appearance_mode(self.tema["ctk_mode"])
        ctk.set_default_color_theme("blue")

        self._bangun_layout()
        self._tampilkan_halaman("grafik")

    # ------------------------------------------------------------------
    def _bangun_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---- Sidebar ----
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0,
                                     fg_color=self.tema["bg_sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_rowconfigure(6, weight=1)

        ctk.CTkLabel(self.sidebar, text="🧮 LP Solver",
                     font=("Segoe UI", 20, "bold"),
                     text_color=self.tema["aksen"]).grid(row=0, column=0, padx=20, pady=(24, 4), sticky="w")
        ctk.CTkLabel(self.sidebar, text="Aplikasi Program Linear",
                     font=("Segoe UI", 11), text_color=self.tema["teks_sekunder"]
                     ).grid(row=1, column=0, padx=20, pady=(0, 24), sticky="w")

        self.tombol_grafik = ctk.CTkButton(
            self.sidebar, text="📉  Metode Grafik", anchor="w", height=42,
            fg_color=self.tema["aksen"], hover_color=self.tema["aksen_hover"],
            command=lambda: self._tampilkan_halaman("grafik"))
        self.tombol_grafik.grid(row=2, column=0, padx=16, pady=4, sticky="ew")

        self.tombol_simpleks = ctk.CTkButton(
            self.sidebar, text="🧮  Metode Simpleks", anchor="w", height=42,
            fg_color="transparent", text_color=self.tema["teks_utama"],
            hover_color=self.tema["border"],
            command=lambda: self._tampilkan_halaman("simpleks"))
        self.tombol_simpleks.grid(row=3, column=0, padx=16, pady=4, sticky="ew")

        self.tombol_print = ctk.CTkButton(
            self.sidebar, text="🖨️  Print Hasil", anchor="w", height=38,
            fg_color="transparent", text_color=self.tema["teks_utama"],
            hover_color=self.tema["border"], command=self._print_hasil)
        self.tombol_print.grid(row=4, column=0, padx=16, pady=(20, 4), sticky="ew")

        # ---- Sakelar Light/Dark di bagian bawah sidebar ----
        frame_tema = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        frame_tema.grid(row=7, column=0, padx=16, pady=20, sticky="sew")
        ctk.CTkLabel(frame_tema, text="Mode Tampilan",
                     text_color=self.tema["teks_sekunder"], font=("Segoe UI", 11)).pack(anchor="w")
        self.sakelar_tema = ctk.CTkSwitch(frame_tema, text="Dark Mode", command=self._ganti_tema)
        self.sakelar_tema.pack(anchor="w", pady=(6, 0))

        # ---- Area Konten ----
        self.area_konten = ctk.CTkScrollableFrame(self, fg_color=self.tema["bg_utama"])
        self.area_konten.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)

        self.halaman_grafik = HalamanGrafik(self.area_konten, self.tema)
        self.halaman_simpleks = HalamanSimpleks(self.area_konten, self.tema)
        self.halaman_aktif = None

    # ------------------------------------------------------------------
    def _tampilkan_halaman(self, nama):
        for w in self.area_konten.winfo_children():
            w.pack_forget()

        if nama == "grafik":
            self.halaman_grafik.pack(fill="both", expand=True)
            self.halaman_aktif = self.halaman_grafik
            self.tombol_grafik.configure(fg_color=self.tema["aksen"], text_color="white")
            self.tombol_simpleks.configure(fg_color="transparent", text_color=self.tema["teks_utama"])
        else:
            self.halaman_simpleks.pack(fill="both", expand=True)
            self.halaman_aktif = self.halaman_simpleks
            self.tombol_simpleks.configure(fg_color=self.tema["aksen"], text_color="white")
            self.tombol_grafik.configure(fg_color="transparent", text_color=self.tema["teks_utama"])

    # ------------------------------------------------------------------
    def _ganti_tema(self):
        self.mode_tema = "dark" if self.sakelar_tema.get() else "light"
        ctk.set_appearance_mode(ambil_tema(self.mode_tema)["ctk_mode"])
        # Catatan: perubahan warna kartu/komponen secara penuh butuh rebuild halaman.
        # Untuk kesederhanaan & kestabilan, mode gelap/terang CustomTkinter (appearance
        # mode) sudah otomatis menyesuaikan sebagian besar warna widget bawaan.
        # Rebuild total halaman aktif supaya tema kartu kustom ikut berubah:
        self.tema = ambil_tema(self.mode_tema)
        for w in (self.halaman_grafik, self.halaman_simpleks):
            w.destroy()
        self.halaman_grafik = HalamanGrafik(self.area_konten, self.tema)
        self.halaman_simpleks = HalamanSimpleks(self.area_konten, self.tema)
        nama_aktif = "grafik" if self.halaman_aktif is self.halaman_grafik else "simpleks"
        self._tampilkan_halaman(nama_aktif)

    # ------------------------------------------------------------------
    def _print_hasil(self):
        """
        Tombol Print: karena dukungan print langsung berbeda-beda tiap OS,
        pendekatan paling stabil lintas-platform adalah export ke PDF lalu
        membuka file tersebut dengan aplikasi pembaca PDF default (dari sana
        pengguna tinggal tekan Ctrl+P / Cmd+P seperti biasa).
        """
        halaman = self.halaman_aktif
        if not getattr(halaman, "hasil_terakhir", None):
            from modules.ui_components import tampilkan_pesan_error
            tampilkan_pesan_error(self, self.tema, "Belum ada hasil untuk dicetak. "
                                                    "Silakan hitung solusi terlebih dahulu.")
            return

        import tempfile
        path_pdf = os.path.join(tempfile.gettempdir(), "cetak_hasil_lp.pdf")
        if halaman is self.halaman_grafik:
            from modules.export import export_pdf_grafik
            export_pdf_grafik(path_pdf, halaman.data_soal_terakhir,
                               halaman.hasil_terakhir['titik_sudut'],
                               halaman.hasil_terakhir['optimal'],
                               gambar_path=getattr(halaman, '_gambar_path', None))
        else:
            from modules.export import export_pdf_simpleks
            export_pdf_simpleks(path_pdf, halaman.data_soal_terakhir, halaman.hasil_terakhir)

        self._buka_file(path_pdf)

    @staticmethod
    def _buka_file(path):
        """Buka file dengan aplikasi default sesuai OS (Windows/macOS/Linux)."""
        try:
            if platform.system() == "Windows":
                os.startfile(path)  # noqa: F821 (hanya ada di Windows)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        except Exception as e:
            print(f"Tidak bisa membuka file otomatis: {e}")


if __name__ == "__main__":
    app = AplikasiProgramLinear()
    app.mainloop()
