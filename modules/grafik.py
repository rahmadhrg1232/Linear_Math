"""
modules/grafik.py
==================
Halaman (Frame) untuk Metode Grafik: input fungsi tujuan & kendala dinamis,
lalu menampilkan grafik feasible region (matplotlib embedded, dengan zoom
bawaan toolbar) beserta tabel titik sudut dan solusi optimal.
"""

import os
import tkinter as tk
import customtkinter as ctk
import numpy as np
import matplotlib
matplotlib.use("Agg")  # akan diganti "TkAgg" saat benar-benar dirender di window (lihat main.py)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from modules.solver import hitung_titik_sudut
from modules.ui_components import BarisKendala, EntriAngka, buat_kartu, tampilkan_pesan_error
from modules.export import export_pdf_grafik, export_excel_grafik


class HalamanGrafik(ctk.CTkFrame):
    """Frame utama halaman Metode Grafik, dipasang di dalam main.py."""

    def __init__(self, master, tema, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.tema = tema
        self.daftar_baris_kendala = []
        self.hasil_terakhir = None
        self.data_soal_terakhir = None
        self._bangun_ui()

    # ------------------------------------------------------------------
    def _bangun_ui(self):
        judul = ctk.CTkLabel(self, text="📉 Metode Grafik (2 Variabel)",
                              font=("Segoe UI", 22, "bold"), text_color=self.tema["teks_utama"])
        judul.pack(anchor="w", pady=(0, 4), padx=4)
        sub = ctk.CTkLabel(self, text="Khusus untuk masalah dengan 2 variabel keputusan (x1 dan x2).",
                            text_color=self.tema["teks_sekunder"])
        sub.pack(anchor="w", padx=4, pady=(0, 12))

        # ---- Kartu: Fungsi Tujuan ----
        kartu_tujuan = buat_kartu(self, self.tema, "🎯 Fungsi Tujuan (Z)")
        kartu_tujuan.pack(fill="x", pady=8)
        baris_tujuan = ctk.CTkFrame(kartu_tujuan, fg_color="transparent")
        baris_tujuan.pack(anchor="w", padx=18, pady=(0, 16))

        self.obj_var = tk.StringVar(value="max")
        ctk.CTkLabel(baris_tujuan, text="Jenis:").pack(side="left", padx=(0, 4))
        ctk.CTkOptionMenu(baris_tujuan, values=["max", "min"], variable=self.obj_var,
                           width=80, fg_color=self.tema["aksen"]).pack(side="left", padx=(0, 16))

        ctk.CTkLabel(baris_tujuan, text="Z =").pack(side="left")
        self.entri_c1 = EntriAngka(baris_tujuan, nilai_awal=3.0, lebar=60)
        self.entri_c1.pack(side="left", padx=4)
        ctk.CTkLabel(baris_tujuan, text="x1  +").pack(side="left")
        self.entri_c2 = EntriAngka(baris_tujuan, nilai_awal=5.0, lebar=60)
        self.entri_c2.pack(side="left", padx=4)
        ctk.CTkLabel(baris_tujuan, text="x2").pack(side="left")

        # ---- Kartu: Fungsi Batasan ----
        kartu_batasan = buat_kartu(self, self.tema, "📐 Fungsi Batasan")
        kartu_batasan.pack(fill="x", pady=8)
        self.frame_kendala = ctk.CTkFrame(kartu_batasan, fg_color="transparent")
        self.frame_kendala.pack(fill="x", padx=18, pady=(0, 8))

        tombol_tambah = ctk.CTkButton(kartu_batasan, text="+ Tambah Batasan", width=160,
                                       fg_color=self.tema["aksen"], hover_color=self.tema["aksen_hover"],
                                       command=self._tambah_kendala)
        tombol_tambah.pack(anchor="w", padx=18, pady=(0, 16))

        self._tambah_kendala(a1=2, a2=1, rhs=18)
        self._tambah_kendala(a1=2, a2=3, rhs=42)
        self._tambah_kendala(a1=3, a2=1, rhs=24)

        # ---- Tombol Aksi ----
        frame_aksi = ctk.CTkFrame(self, fg_color="transparent")
        frame_aksi.pack(fill="x", pady=8)
        ctk.CTkButton(frame_aksi, text="🧮 Hitung & Tampilkan Grafik", height=40,
                       font=("Segoe UI", 13, "bold"), fg_color=self.tema["aksen"],
                       hover_color=self.tema["aksen_hover"],
                       command=self._hitung).pack(side="left", padx=(0, 8))
        ctk.CTkButton(frame_aksi, text="↺ Reset", height=40, width=90,
                       fg_color="transparent", border_width=1, border_color=self.tema["border"],
                       text_color=self.tema["teks_utama"],
                       command=self._reset).pack(side="left", padx=(0, 8))
        self.tombol_pdf = ctk.CTkButton(frame_aksi, text="⬇ Export PDF", height=40, width=110,
                                         state="disabled", command=self._export_pdf)
        self.tombol_pdf.pack(side="left", padx=(0, 8))
        self.tombol_excel = ctk.CTkButton(frame_aksi, text="⬇ Export Excel", height=40, width=120,
                                           state="disabled", command=self._export_excel)
        self.tombol_excel.pack(side="left")

        # ---- Kartu Hasil (grafik + tabel) ----
        self.kartu_hasil = buat_kartu(self, self.tema, "📊 Hasil Analisis Grafis")
        self.kartu_hasil.pack(fill="both", expand=True, pady=8)
        self.frame_hasil_isi = ctk.CTkFrame(self.kartu_hasil, fg_color="transparent")
        self.frame_hasil_isi.pack(fill="both", expand=True, padx=18, pady=(0, 16))
        self.label_placeholder = ctk.CTkLabel(
            self.frame_hasil_isi, text="Klik 'Hitung & Tampilkan Grafik' untuk melihat hasil.",
            text_color=self.tema["teks_sekunder"])
        self.label_placeholder.pack(pady=30)

    # ------------------------------------------------------------------
    def _tambah_kendala(self, a1=1.0, a2=2.0, rhs=10.0):
        nomor = len(self.daftar_baris_kendala) + 1
        baris = BarisKendala(self.frame_kendala, self.tema, jumlah_var=2, nomor=nomor,
                              on_hapus=self._hapus_kendala,
                              nilai_awal_koef=a1, nilai_awal_rhs=rhs)
        # override nilai koefisien kedua secara manual (a1 dan a2 beda default)
        baris.entri_koef[0].delete(0, "end")
        baris.entri_koef[0].insert(0, str(a1))
        baris.entri_koef[1].delete(0, "end")
        baris.entri_koef[1].insert(0, str(a2))
        baris.pack(fill="x", pady=3)
        self.daftar_baris_kendala.append(baris)

    def _hapus_kendala(self, baris):
        if len(self.daftar_baris_kendala) <= 1:
            tampilkan_pesan_error(self, self.tema, "Minimal harus ada 1 batasan.")
            return
        baris.destroy()
        self.daftar_baris_kendala.remove(baris)
        self._nomori_ulang_kendala()

    def _nomori_ulang_kendala(self):
        for i, baris in enumerate(self.daftar_baris_kendala, start=1):
            baris.nomor = i
            # label nomor adalah child pertama
            baris.winfo_children()[0].configure(text=f"K{i}:")

    def _reset(self):
        for baris in list(self.daftar_baris_kendala):
            baris.destroy()
        self.daftar_baris_kendala.clear()
        self._tambah_kendala(a1=2, a2=1, rhs=18)
        self._tambah_kendala(a1=2, a2=3, rhs=42)
        self._tambah_kendala(a1=3, a2=1, rhs=24)
        self.entri_c1.delete(0, "end")
        self.entri_c1.insert(0, "3")
        self.entri_c2.delete(0, "end")
        self.entri_c2.insert(0, "5")
        for w in self.frame_hasil_isi.winfo_children():
            w.destroy()
        self.label_placeholder = ctk.CTkLabel(
            self.frame_hasil_isi, text="Klik 'Hitung & Tampilkan Grafik' untuk melihat hasil.",
            text_color=self.tema["teks_sekunder"])
        self.label_placeholder.pack(pady=30)
        self.tombol_pdf.configure(state="disabled")
        self.tombol_excel.configure(state="disabled")
        self.hasil_terakhir = None

    # ------------------------------------------------------------------
    def _validasi_semua(self):
        """Validasi input: field kosong / bukan angka. Kembalikan True kalau semua valid."""
        semua_valid = True
        if not self.entri_c1.valid():
            self.entri_c1.tandai_error(self.tema, True)
            semua_valid = False
        else:
            self.entri_c1.tandai_error(self.tema, False)
        if not self.entri_c2.valid():
            self.entri_c2.tandai_error(self.tema, True)
            semua_valid = False
        else:
            self.entri_c2.tandai_error(self.tema, False)

        for baris in self.daftar_baris_kendala:
            if not baris.valid():
                baris.tandai_error()
                semua_valid = False
        return semua_valid

    # ------------------------------------------------------------------
    def _hitung(self):
        if not self._validasi_semua():
            tampilkan_pesan_error(
                self, self.tema,
                "Ada kolom yang masih kosong atau bukan angka. "
                "Mohon lengkapi seluruh koefisien, operator, dan nilai RHS."
            )
            return

        c1 = self.entri_c1.ambil_nilai()
        c2 = self.entri_c2.ambil_nilai()
        obj_type = self.obj_var.get()
        kendala = []
        for baris in self.daftar_baris_kendala:
            data = baris.ambil_data()
            kendala.append({'a1': data['coeffs'][0], 'a2': data['coeffs'][1],
                             'operator': data['operator'], 'rhs': data['rhs']})

        hasil = hitung_titik_sudut(kendala, c1, c2, obj_type)
        self.hasil_terakhir = hasil
        self.data_soal_terakhir = {'obj_type': obj_type, 'c1': c1, 'c2': c2, 'kendala': kendala}

        for w in self.frame_hasil_isi.winfo_children():
            w.destroy()

        if hasil['status'] == 'infeasible':
            ctk.CTkLabel(self.frame_hasil_isi,
                         text="⚠ Tidak ditemukan daerah layak (feasible region). "
                              "Periksa kembali kendala yang dimasukkan.",
                         text_color=self.tema["gagal"]).pack(pady=20)
            self.tombol_pdf.configure(state="disabled")
            self.tombol_excel.configure(state="disabled")
            return

        # --- Gambar grafik matplotlib ---
        fig = self._gambar_grafik(kendala, c1, c2, hasil)
        self._gambar_path = os.path.join(os.path.expanduser("~"), ".lp_app_grafik_tmp.png")
        fig.savefig(self._gambar_path, dpi=140, bbox_inches='tight')

        canvas = FigureCanvasTkAgg(fig, master=self.frame_hasil_isi)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        toolbar_frame = ctk.CTkFrame(self.frame_hasil_isi, fg_color="transparent")
        toolbar_frame.pack(fill="x")
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()

        # --- Tabel titik sudut ---
        ctk.CTkLabel(self.frame_hasil_isi, text="Titik-Titik Sudut & Nilai Z:",
                     font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(14, 4))
        frame_tabel = ctk.CTkFrame(self.frame_hasil_isi, fg_color=self.tema["bg_utama"], corner_radius=8)
        frame_tabel.pack(fill="x", pady=4)
        header = ["Titik", "X", "Y", "Z"]
        for c, teks in enumerate(header):
            ctk.CTkLabel(frame_tabel, text=teks, font=("Segoe UI", 12, "bold"),
                         width=90).grid(row=0, column=c, padx=4, pady=4)
        for r, (x, y, z) in enumerate(hasil['titik_sudut'], start=1):
            optimal_row = hasil['optimal'] and (x, y, z) == hasil['optimal']
            warna = self.tema["sukses"] if optimal_row else self.tema["teks_utama"]
            ctk.CTkLabel(frame_tabel, text=f"P{r}" + (" ★" if optimal_row else ""),
                         text_color=warna, width=90).grid(row=r, column=0, padx=4, pady=2)
            for c, val in enumerate((x, y, z), start=1):
                ctk.CTkLabel(frame_tabel, text=f"{val:.4f}", text_color=warna,
                             width=90).grid(row=r, column=c, padx=4, pady=2)

        # --- Solusi optimal ---
        opt = hasil['optimal']
        jenis = "Maksimum" if obj_type == 'max' else "Minimum"
        teks_solusi = (
            f"✅ Solusi Optimal ({jenis}): X = {opt[0]:.4f}, Y = {opt[1]:.4f}  →  Z = {opt[2]:.4f}\n\n"
            f"Penjelasan: Nilai Z dievaluasi pada setiap titik sudut daerah layak. "
            f"Titik (X={opt[0]:.4f}, Y={opt[1]:.4f}) memberikan nilai Z {'terbesar' if obj_type=='max' else 'terkecil'} "
            f"yaitu {opt[2]:.4f}, sehingga inilah solusi optimalnya."
        )
        ctk.CTkLabel(self.frame_hasil_isi, text=teks_solusi, font=("Segoe UI", 13, "bold"),
                     text_color=self.tema["sukses"], justify="left", wraplength=680).pack(anchor="w", pady=(16, 4))

        self.tombol_pdf.configure(state="normal")
        self.tombol_excel.configure(state="normal")

    # ------------------------------------------------------------------
    def _gambar_grafik(self, kendala, c1, c2, hasil):
        """Bangun objek Figure matplotlib berisi garis kendala & feasible region."""
        matplotlib.use("Agg")
        fig, ax = plt.subplots(figsize=(6.4, 4.8))

        titik_semua = hasil['titik_sudut']
        maks_x = max([p[0] for p in titik_semua] + [1]) * 1.3 + 2
        maks_y = max([p[1] for p in titik_semua] + [1]) * 1.3 + 2
        x = np.linspace(0, maks_x, 400)

        for i, k in enumerate(kendala):
            a1, a2, rhs = k['a1'], k['a2'], k['rhs']
            if a2 != 0:
                y = (rhs - a1 * x) / a2
                ax.plot(x, y, label=f"K{i+1}: {a1}x1+{a2}x2{k['operator']}{rhs}")
            elif a1 != 0:
                ax.axvline(x=rhs / a1, linestyle='--', label=f"K{i+1}: x1={rhs/a1}")

        # Feasible region (shading) memakai polygon dari titik sudut terurut
        if len(titik_semua) >= 3:
            poly_x = [p[0] for p in titik_semua] + [titik_semua[0][0]]
            poly_y = [p[1] for p in titik_semua] + [titik_semua[0][1]]
            ax.fill(poly_x, poly_y, alpha=0.25, color='#4F6EF7', label='Daerah Layak')

        for (px, py, pz) in titik_semua:
            ax.plot(px, py, 'o', color='#1B1F2A', markersize=5)
            ax.annotate(f"({px:.1f},{py:.1f})", (px, py), textcoords="offset points",
                        xytext=(5, 5), fontsize=8)

        if hasil['optimal']:
            ox, oy, oz = hasil['optimal']
            ax.plot(ox, oy, '*', color='red', markersize=16, label=f"Optimal Z={oz:.2f}")

        ax.axhline(0, color='gray', linewidth=0.8)
        ax.axvline(0, color='gray', linewidth=0.8)
        ax.set_xlabel('x1')
        ax.set_ylabel('x2')
        ax.set_title('Daerah Layak (Feasible Region)')
        ax.set_xlim(left=-0.5)
        ax.set_ylim(bottom=-0.5)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8, loc='upper right')
        fig.tight_layout()
        return fig

    # ------------------------------------------------------------------
    def _export_pdf(self):
        if not self.hasil_terakhir:
            return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                             filetypes=[("PDF", "*.pdf")],
                                             initialfile="hasil_metode_grafik.pdf")
        if not path:
            return
        export_pdf_grafik(path, self.data_soal_terakhir, self.hasil_terakhir['titik_sudut'],
                           self.hasil_terakhir['optimal'],
                           gambar_path=getattr(self, '_gambar_path', None))
        tampilkan_pesan_error(self, self.tema, f"PDF berhasil disimpan di:\n{path}")

    def _export_excel(self):
        if not self.hasil_terakhir:
            return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                             filetypes=[("Excel", "*.xlsx")],
                                             initialfile="hasil_metode_grafik.xlsx")
        if not path:
            return
        export_excel_grafik(path, self.data_soal_terakhir, self.hasil_terakhir['titik_sudut'],
                             self.hasil_terakhir['optimal'])
        tampilkan_pesan_error(self, self.tema, f"Excel berhasil disimpan di:\n{path}")
