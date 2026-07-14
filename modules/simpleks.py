"""
modules/simpleks.py
====================
Halaman (Frame) untuk Metode Simpleks (Big-M): mendukung 2 s/d 8+ variabel
keputusan, kendala dinamis dengan operator <=, >=, =, menampilkan tableau
tiap iterasi (highlight kolom/baris/elemen pivot) dalam bentuk tab
(accordion), lengkap dengan penjelasan otomatis berbahasa Indonesia.
"""

import tkinter as tk
import customtkinter as ctk

from modules.solver import selesaikan_simpleks
from modules.ui_components import BarisKendala, EntriAngka, buat_kartu, tampilkan_pesan_error
from modules.export import export_pdf_simpleks, export_excel_simpleks


class HalamanSimpleks(ctk.CTkFrame):
    """Frame utama halaman Metode Simpleks, dipasang di dalam main.py."""

    def __init__(self, master, tema, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.tema = tema
        self.jumlah_var = 2
        self.entri_c = []
        self.daftar_baris_kendala = []
        self.hasil_terakhir = None
        self.data_soal_terakhir = None
        self._bangun_ui()

    # ------------------------------------------------------------------
    def _bangun_ui(self):
        judul = ctk.CTkLabel(self, text="🧮 Metode Simpleks (Big-M)",
                              font=("Segoe UI", 22, "bold"), text_color=self.tema["teks_utama"])
        judul.pack(anchor="w", pady=(0, 4), padx=4)
        sub = ctk.CTkLabel(self, text="Mendukung 2 s/d 8 variabel keputusan, dan operator <=, >=, =.",
                            text_color=self.tema["teks_sekunder"])
        sub.pack(anchor="w", padx=4, pady=(0, 12))

        # ---- Kartu: Pengaturan Variabel & Jenis ----
        kartu_atur = buat_kartu(self, self.tema, "⚙️ Pengaturan")
        kartu_atur.pack(fill="x", pady=8)
        baris_atur = ctk.CTkFrame(kartu_atur, fg_color="transparent")
        baris_atur.pack(anchor="w", padx=18, pady=(0, 16))

        ctk.CTkLabel(baris_atur, text="Jenis:").pack(side="left", padx=(0, 4))
        self.obj_var = tk.StringVar(value="max")
        ctk.CTkOptionMenu(baris_atur, values=["max", "min"], variable=self.obj_var,
                           width=80, fg_color=self.tema["aksen"]).pack(side="left", padx=(0, 16))

        ctk.CTkLabel(baris_atur, text="Jumlah Variabel:").pack(side="left", padx=(0, 4))
        self.var_jumlah = tk.StringVar(value="2")
        dropdown_jumlah = ctk.CTkOptionMenu(
            baris_atur, values=[str(i) for i in range(2, 9)], variable=self.var_jumlah,
            width=70, fg_color=self.tema["aksen"], command=self._ubah_jumlah_variabel)
        dropdown_jumlah.pack(side="left")

        # ---- Kartu: Fungsi Tujuan ----
        self.kartu_tujuan = buat_kartu(self, self.tema, "🎯 Fungsi Tujuan (Z)")
        self.kartu_tujuan.pack(fill="x", pady=8)
        self.frame_tujuan = ctk.CTkFrame(self.kartu_tujuan, fg_color="transparent")
        self.frame_tujuan.pack(anchor="w", padx=18, pady=(0, 16))
        self._gambar_ulang_fungsi_tujuan()

        # ---- Kartu: Fungsi Batasan ----
        kartu_batasan = buat_kartu(self, self.tema, "📐 Fungsi Batasan")
        kartu_batasan.pack(fill="x", pady=8)
        self.frame_kendala = ctk.CTkFrame(kartu_batasan, fg_color="transparent")
        self.frame_kendala.pack(fill="x", padx=18, pady=(0, 8))

        tombol_tambah = ctk.CTkButton(kartu_batasan, text="+ Tambah Batasan", width=160,
                                       fg_color=self.tema["aksen"], hover_color=self.tema["aksen_hover"],
                                       command=lambda: self._tambah_kendala())
        tombol_tambah.pack(anchor="w", padx=18, pady=(0, 16))

        self._tambah_kendala(rhs=40)
        self._tambah_kendala(rhs=60)

        # ---- Tombol Aksi ----
        frame_aksi = ctk.CTkFrame(self, fg_color="transparent")
        frame_aksi.pack(fill="x", pady=8)
        ctk.CTkButton(frame_aksi, text="🧮 Selesaikan dengan Simpleks", height=40,
                       font=("Segoe UI", 13, "bold"), fg_color=self.tema["aksen"],
                       hover_color=self.tema["aksen_hover"],
                       command=self._selesaikan).pack(side="left", padx=(0, 8))
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

        # ---- Kartu Hasil: Tabview riwayat iterasi ----
        self.kartu_hasil = buat_kartu(self, self.tema, "📊 Hasil & Riwayat Iterasi")
        self.kartu_hasil.pack(fill="both", expand=True, pady=8)
        self.frame_hasil_isi = ctk.CTkFrame(self.kartu_hasil, fg_color="transparent")
        self.frame_hasil_isi.pack(fill="both", expand=True, padx=18, pady=(0, 16))
        self.label_placeholder = ctk.CTkLabel(
            self.frame_hasil_isi, text="Klik 'Selesaikan dengan Simpleks' untuk melihat hasil.",
            text_color=self.tema["teks_sekunder"])
        self.label_placeholder.pack(pady=30)

    # ------------------------------------------------------------------
    def _gambar_ulang_fungsi_tujuan(self):
        for w in self.frame_tujuan.winfo_children():
            w.destroy()
        self.entri_c = []
        ctk.CTkLabel(self.frame_tujuan, text="Z =").pack(side="left", padx=(0, 4))
        for i in range(self.jumlah_var):
            if i > 0:
                ctk.CTkLabel(self.frame_tujuan, text="+").pack(side="left", padx=2)
            e = EntriAngka(self.frame_tujuan, nilai_awal=1.0, lebar=56)
            e.pack(side="left", padx=2)
            self.entri_c.append(e)
            ctk.CTkLabel(self.frame_tujuan, text=f"x{i+1}").pack(side="left", padx=(2, 6))

    def _ubah_jumlah_variabel(self, nilai):
        self.jumlah_var = int(nilai)
        self._gambar_ulang_fungsi_tujuan()
        # Bangun ulang semua baris kendala dengan jumlah variabel baru (data lama tak dipakai lagi)
        for baris in list(self.daftar_baris_kendala):
            baris.destroy()
        self.daftar_baris_kendala.clear()
        self._tambah_kendala(rhs=40)
        self._tambah_kendala(rhs=60)

    # ------------------------------------------------------------------
    def _tambah_kendala(self, rhs=10.0):
        nomor = len(self.daftar_baris_kendala) + 1
        baris = BarisKendala(self.frame_kendala, self.tema, jumlah_var=self.jumlah_var, nomor=nomor,
                              on_hapus=self._hapus_kendala, nilai_awal_koef=1.0, nilai_awal_rhs=rhs)
        baris.pack(fill="x", pady=3)
        self.daftar_baris_kendala.append(baris)

    def _hapus_kendala(self, baris):
        if len(self.daftar_baris_kendala) <= 1:
            tampilkan_pesan_error(self, self.tema, "Minimal harus ada 1 batasan.")
            return
        baris.destroy()
        self.daftar_baris_kendala.remove(baris)
        for i, b in enumerate(self.daftar_baris_kendala, start=1):
            b.nomor = i
            b.winfo_children()[0].configure(text=f"K{i}:")

    def _reset(self):
        for baris in list(self.daftar_baris_kendala):
            baris.destroy()
        self.daftar_baris_kendala.clear()
        self.jumlah_var = 2
        self.var_jumlah.set("2")
        self._gambar_ulang_fungsi_tujuan()
        self._tambah_kendala(rhs=40)
        self._tambah_kendala(rhs=60)
        for w in self.frame_hasil_isi.winfo_children():
            w.destroy()
        self.label_placeholder = ctk.CTkLabel(
            self.frame_hasil_isi, text="Klik 'Selesaikan dengan Simpleks' untuk melihat hasil.",
            text_color=self.tema["teks_sekunder"])
        self.label_placeholder.pack(pady=30)
        self.tombol_pdf.configure(state="disabled")
        self.tombol_excel.configure(state="disabled")
        self.hasil_terakhir = None

    # ------------------------------------------------------------------
    def _validasi_semua(self):
        semua_valid = True
        for e in self.entri_c:
            if not e.valid():
                e.tandai_error(self.tema, True)
                semua_valid = False
            else:
                e.tandai_error(self.tema, False)
        for baris in self.daftar_baris_kendala:
            if not baris.valid():
                baris.tandai_error()
                semua_valid = False
        return semua_valid

    # ------------------------------------------------------------------
    def _selesaikan(self):
        if not self._validasi_semua():
            tampilkan_pesan_error(
                self, self.tema,
                "Ada kolom yang masih kosong atau bukan angka. "
                "Mohon lengkapi seluruh koefisien, operator, dan nilai RHS."
            )
            return

        c = [e.ambil_nilai() for e in self.entri_c]
        obj_type = self.obj_var.get()
        kendala = [baris.ambil_data() for baris in self.daftar_baris_kendala]

        hasil = selesaikan_simpleks(c, kendala, obj_type=obj_type)
        self.hasil_terakhir = hasil
        self.data_soal_terakhir = {'obj_type': obj_type, 'c': c, 'kendala': kendala}

        for w in self.frame_hasil_isi.winfo_children():
            w.destroy()

        if hasil['status'] not in ('optimal',):
            pesan = {
                'unbounded': "⚠ Solusi TIDAK TERBATAS (unbounded). Nilai Z bisa naik terus tanpa batas.",
                'infeasible': "⚠ Masalah TIDAK MEMILIKI SOLUSI LAYAK (infeasible). Periksa kembali kendala.",
                'tidak_konvergen': "⚠ Iterasi tidak konvergen dalam batas maksimum. Periksa kembali data.",
            }.get(hasil['status'], f"Status: {hasil['status']}")
            ctk.CTkLabel(self.frame_hasil_isi, text=pesan, text_color=self.tema["gagal"],
                         font=("Segoe UI", 13, "bold")).pack(pady=10, anchor="w")

        # ---- Tabview: satu tab per iterasi ----
        tabview = ctk.CTkTabview(self.frame_hasil_isi, fg_color=self.tema["bg_utama"])
        tabview.pack(fill="both", expand=True, pady=(4, 12))
        for it in hasil['iterasi']:
            nama_tab = f"Iterasi {it['nomor']}"
            tab = tabview.add(nama_tab)
            self._gambar_tableau(tab, it)
        if hasil['iterasi']:
            tabview.set(f"Iterasi {hasil['iterasi'][-1]['nomor']}")

        # ---- Ringkasan hasil akhir ----
        if hasil['status'] == 'optimal':
            teks = "✅ Hasil Akhir:\n"
            for nama, val in hasil['nilai_variabel'].items():
                teks += f"  • {nama} = {val:.4f}\n"
            teks += f"\nZ optimal = {hasil['Z_optimal']:.4f}  (tercapai dalam {hasil['jumlah_iterasi']} iterasi)"
            ctk.CTkLabel(self.frame_hasil_isi, text=teks, font=("Segoe UI", 13, "bold"),
                         text_color=self.tema["sukses"], justify="left").pack(anchor="w", pady=(4, 4))
            self.tombol_pdf.configure(state="normal")
            self.tombol_excel.configure(state="normal")
        else:
            self.tombol_pdf.configure(state="disabled")
            self.tombol_excel.configure(state="disabled")

    # ------------------------------------------------------------------
    def _gambar_tableau(self, parent, it):
        """Render satu tabel simpleks (1 iterasi) dengan highlight kolom/baris/elemen pivot."""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        nama_kolom = it['nama_kolom']
        n_kolom = len(nama_kolom)

        # Header
        ctk.CTkLabel(scroll, text="Basis", font=("Segoe UI", 11, "bold"),
                     width=70).grid(row=0, column=0, padx=2, pady=2)
        for c, nama in enumerate(nama_kolom):
            warna_bg = self.tema["pivot_kolom"] if it.get('pivot_kolom') == c else self.tema["bg_kartu"]
            ctk.CTkLabel(scroll, text=nama, font=("Segoe UI", 11, "bold"), width=64,
                         fg_color=warna_bg, corner_radius=4).grid(row=0, column=c + 1, padx=2, pady=2)
        ctk.CTkLabel(scroll, text="NK", font=("Segoe UI", 11, "bold"),
                     width=64).grid(row=0, column=n_kolom + 1, padx=2, pady=2)

        # Baris-baris tableau
        for r in range(it['tabel'].shape[0]):
            nama_basis = nama_kolom[it['basis_idx'][r]]
            warna_baris_label = self.tema["pivot_baris"] if it.get('pivot_baris') == r else "transparent"
            ctk.CTkLabel(scroll, text=nama_basis, width=70, fg_color=warna_baris_label,
                         corner_radius=4).grid(row=r + 1, column=0, padx=2, pady=1)
            for c in range(n_kolom):
                nilai = it['tabel'][r, c]
                is_pivot_col = it.get('pivot_kolom') == c
                is_pivot_row = it.get('pivot_baris') == r
                if is_pivot_col and is_pivot_row:
                    warna = self.tema["pivot_elemen"]
                elif is_pivot_col:
                    warna = self.tema["pivot_kolom"]
                elif is_pivot_row:
                    warna = self.tema["pivot_baris"]
                else:
                    warna = "transparent"
                ctk.CTkLabel(scroll, text=f"{nilai:.3f}", width=64, fg_color=warna,
                             corner_radius=4).grid(row=r + 1, column=c + 1, padx=2, pady=1)
            rhs = it['tabel'][r, -1]
            ctk.CTkLabel(scroll, text=f"{rhs:.3f}", width=64).grid(row=r + 1, column=n_kolom + 1, padx=2, pady=1)

        # Baris Cj - Zj
        baris_terakhir = it['tabel'].shape[0] + 1
        ctk.CTkLabel(scroll, text="Cj-Zj", font=("Segoe UI", 11, "bold"),
                     width=70).grid(row=baris_terakhir, column=0, padx=2, pady=(6, 2))
        for c, val in enumerate(it['CjZj']):
            warna = self.tema["pivot_kolom"] if it.get('pivot_kolom') == c else "transparent"
            ctk.CTkLabel(scroll, text=f"{val:.3f}", width=64, fg_color=warna,
                         corner_radius=4).grid(row=baris_terakhir, column=c + 1, padx=2, pady=(6, 2))

        # Penjelasan otomatis
        ctk.CTkLabel(scroll, text=it['penjelasan'], wraplength=760, justify="left",
                     text_color=self.tema["teks_sekunder"], font=("Segoe UI", 11)
                     ).grid(row=baris_terakhir + 1, column=0, columnspan=n_kolom + 2,
                            sticky="w", padx=4, pady=(10, 4))

        # Legenda warna
        legenda = ctk.CTkFrame(scroll, fg_color="transparent")
        legenda.grid(row=baris_terakhir + 2, column=0, columnspan=n_kolom + 2, sticky="w", pady=(6, 0))
        for teks, warna in [("Kolom Pivot", self.tema["pivot_kolom"]),
                             ("Baris Pivot", self.tema["pivot_baris"]),
                             ("Elemen Pivot", self.tema["pivot_elemen"])]:
            kotak = ctk.CTkLabel(legenda, text="  ", fg_color=warna, width=18, corner_radius=3)
            kotak.pack(side="left", padx=(0, 4))
            ctk.CTkLabel(legenda, text=teks, text_color=self.tema["teks_sekunder"],
                         font=("Segoe UI", 10)).pack(side="left", padx=(0, 14))

    # ------------------------------------------------------------------
    def _export_pdf(self):
        if not self.hasil_terakhir:
            return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                             filetypes=[("PDF", "*.pdf")],
                                             initialfile="hasil_metode_simpleks.pdf")
        if not path:
            return
        export_pdf_simpleks(path, self.data_soal_terakhir, self.hasil_terakhir)
        tampilkan_pesan_error(self, self.tema, f"PDF berhasil disimpan di:\n{path}")

    def _export_excel(self):
        if not self.hasil_terakhir:
            return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                             filetypes=[("Excel", "*.xlsx")],
                                             initialfile="hasil_metode_simpleks.xlsx")
        if not path:
            return
        export_excel_simpleks(path, self.data_soal_terakhir, self.hasil_terakhir)
        tampilkan_pesan_error(self, self.tema, f"Excel berhasil disimpan di:\n{path}")
