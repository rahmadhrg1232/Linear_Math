"""
modules/solver.py
==================
Modul kalkulasi matematika murni untuk aplikasi Program Linear.
TIDAK ADA kode GUI di sini -- murni logika matematika, supaya mudah
diuji secara terpisah (unit test) dan dimaintain.

Berisi dua mesin solver:
1. hitung_titik_sudut()   -> Metode Grafik (2 variabel)
2. SimpleksBigM           -> Metode Simpleks (Big-M), mendukung 2-8+ variabel
                             dan operator <=, >=, = , lengkap dengan riwayat
                             tiap iterasi (untuk ditampilkan di GUI).
"""

import numpy as np
from itertools import combinations

TOLERANSI = 1e-6
BIG_M = 1_000_000  # konstanta "M" untuk metode Big-M


# ======================================================================
# BAGIAN 1 : METODE GRAFIK (2 VARIABEL)
# ======================================================================

def _nilai_kendala(x, y, kendala):
    """Hitung a1*x + a2*y untuk satu kendala."""
    return kendala['a1'] * x + kendala['a2'] * y


def _memenuhi_kendala(x, y, kendala, toleransi=TOLERANSI):
    """Cek apakah titik (x, y) memenuhi satu kendala (dengan toleransi numerik)."""
    nilai = _nilai_kendala(x, y, kendala)
    op = kendala['operator']
    if op == '<=':
        return nilai <= kendala['rhs'] + toleransi
    elif op == '>=':
        return nilai >= kendala['rhs'] - toleransi
    else:  # '='
        return abs(nilai - kendala['rhs']) <= toleransi


def hitung_titik_sudut(kendala_list, c1, c2, obj_type='max'):
    """
    Menghitung seluruh titik sudut (corner points) daerah layak (feasible region)
    untuk masalah program linear 2 variabel, lalu menentukan titik optimal.

    Parameter
    ---------
    kendala_list : list[dict]
        Tiap elemen: {'a1': float, 'a2': float, 'operator': '<='|'>='|'=', 'rhs': float}
    c1, c2 : float
        Koefisien fungsi tujuan Z = c1*x1 + c2*x2
    obj_type : str
        'max' atau 'min'

    Return
    ------
    dict:
        'titik_sudut' : list of (x, y, z)  -- semua titik sudut feasible, terurut
                        berlawanan arah jarum jam supaya membentuk poligon yang rapi
        'optimal'     : (x, y, z) atau None
        'status'      : 'optimal' | 'infeasible'
    """
    # x >= 0 dan y >= 0 diperlakukan sebagai kendala tambahan (garis sumbu)
    semua_kendala = list(kendala_list) + [
        {'a1': 1.0, 'a2': 0.0, 'operator': '>=', 'rhs': 0.0},
        {'a1': 0.0, 'a2': 1.0, 'operator': '>=', 'rhs': 0.0},
    ]

    # Cari semua titik potong antar pasangan garis kendala
    titik_potong = set()
    n = len(semua_kendala)
    for i, j in combinations(range(n), 2):
        k1, k2 = semua_kendala[i], semua_kendala[j]
        A = np.array([[k1['a1'], k1['a2']], [k2['a1'], k2['a2']]], dtype=float)
        b = np.array([k1['rhs'], k2['rhs']], dtype=float)
        det = np.linalg.det(A)
        if abs(det) < 1e-9:
            continue  # dua garis sejajar -> tidak ada titik potong tunggal
        x, y = np.linalg.solve(A, b)
        titik_potong.add((round(x, 6), round(y, 6)))

    # Saring hanya titik yang memenuhi SEMUA kendala (termasuk x,y >= 0)
    titik_feasible = []
    for (x, y) in titik_potong:
        if x < -TOLERANSI or y < -TOLERANSI:
            continue
        if all(_memenuhi_kendala(x, y, k) for k in semua_kendala):
            z = round(c1 * x + c2 * y, 6)
            titik_feasible.append((round(x, 6), round(y, 6), z))

    if not titik_feasible:
        return {'titik_sudut': [], 'optimal': None, 'status': 'infeasible'}

    # Urutkan titik sudut agar membentuk poligon yang benar (searah sudut polar
    # terhadap titik pusat/centroid) -- supaya grafik feasible region rapi
    xs = [p[0] for p in titik_feasible]
    ys = [p[1] for p in titik_feasible]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    titik_terurut = sorted(
        titik_feasible,
        key=lambda p: np.arctan2(p[1] - cy, p[0] - cx)
    )

    if obj_type == 'max':
        optimal = max(titik_feasible, key=lambda p: p[2])
    else:
        optimal = min(titik_feasible, key=lambda p: p[2])

    return {'titik_sudut': titik_terurut, 'optimal': optimal, 'status': 'optimal'}


# ======================================================================
# BAGIAN 2 : METODE SIMPLEKS (BIG-M), n VARIABEL
# ======================================================================

class SimpleksBigM:
    """
    Implementasi Metode Simpleks dengan pendekatan Big-M sehingga mendukung
    operator <=, >=, dan = sekaligus (tidak hanya <=).

    Setiap iterasi disimpan lengkap (tableau, kolom pivot, baris pivot,
    elemen pivot, dan penjelasan berbahasa Indonesia) agar bisa ditampilkan
    satu per satu di GUI (mode "accordion/tab").

    Parameter
    ---------
    c : list[float]           koefisien fungsi tujuan untuk x1..xn
    kendala : list[dict]      tiap dict {'coeffs': [...], 'operator': '<='|'>='|'=', 'rhs': float}
    obj_type : 'max' | 'min'
    nama_variabel : list[str] opsional, nama variabel keputusan (default x1, x2, ...)
    """

    def __init__(self, c, kendala, obj_type='max', nama_variabel=None):
        self.n = len(c)
        self.m = len(kendala)
        self.obj_type = obj_type
        self.nama_asli = nama_variabel or [f"x{i+1}" for i in range(self.n)]
        self.c_asli = list(c)
        self.kendala = kendala
        self.iterasi = []          # riwayat semua iterasi (untuk ditampilkan di GUI)
        self.status = None
        self.pesan_error = None
        self._bangun_tableau_awal()

    # ------------------------------------------------------------------
    def _bangun_tableau_awal(self):
        """Membentuk tableau awal: menambahkan slack / surplus / artificial."""
        # Untuk MIN, kita ubah jadi MAX dengan mengalikan -1, lalu di akhir dibalik lagi
        if self.obj_type == 'min':
            c_kerja = [-v for v in self.c_asli]
        else:
            c_kerja = list(self.c_asli)

        nama_kolom = list(self.nama_asli)
        kolom_tambahan = []       # koefisien objektif untuk kolom tambahan
        baris_koef = []           # baris koefisien tiap kendala (akan diisi per kolom nanti)
        basis = []                # index kolom basis awal per baris
        indeks_artifisial = []    # menyimpan index kolom2 artificial (untuk cek infeasible)

        m = self.m
        n = self.n

        # Siapkan matriks A (m x n) untuk variabel asli
        A_asli = np.array([k['coeffs'] for k in self.kendala], dtype=float)
        b = np.array([k['rhs'] for k in self.kendala], dtype=float)

        # Pastikan RHS tidak negatif (kalikan baris dengan -1 & balik operator bila perlu)
        operator_list = []
        for i, k in enumerate(self.kendala):
            op = k['operator']
            if b[i] < 0:
                A_asli[i] = -A_asli[i]
                b[i] = -b[i]
                if op == '<=':
                    op = '>='
                elif op == '>=':
                    op = '<='
            operator_list.append(op)

        kolom_extra_per_baris = [[] for _ in range(m)]  # nilai kolom tambahan per baris
        nama_kolom_extra = []

        idx_slack = 1
        idx_artif = 1
        for i, op in enumerate(operator_list):
            if op == '<=':
                nama = f"s{idx_slack}"
                nama_kolom_extra.append(nama)
                for r in range(m):
                    kolom_extra_per_baris[r].append(1.0 if r == i else 0.0)
                kolom_tambahan.append(0.0)  # koefisien objektif slack = 0
                basis.append(('slack', i, nama))
                idx_slack += 1
            elif op == '>=':
                nama_s = f"s{idx_slack}"
                nama_kolom_extra.append(nama_s)
                for r in range(m):
                    kolom_extra_per_baris[r].append(-1.0 if r == i else 0.0)
                kolom_tambahan.append(0.0)
                idx_slack += 1

                nama_a = f"a{idx_artif}"
                nama_kolom_extra.append(nama_a)
                for r in range(m):
                    kolom_extra_per_baris[r].append(1.0 if r == i else 0.0)
                kolom_tambahan.append(-BIG_M)
                basis.append(('artif', i, nama_a))
                indeks_artifisial.append(len(nama_kolom) + len(nama_kolom_extra) - 1)
                idx_artif += 1
            else:  # '='
                nama_a = f"a{idx_artif}"
                nama_kolom_extra.append(nama_a)
                for r in range(m):
                    kolom_extra_per_baris[r].append(1.0 if r == i else 0.0)
                kolom_tambahan.append(-BIG_M)
                basis.append(('artif', i, nama_a))
                indeks_artifisial.append(len(nama_kolom) + len(nama_kolom_extra) - 1)
                idx_artif += 1

        nama_kolom_lengkap = nama_kolom + nama_kolom_extra
        C_lengkap = np.array(c_kerja + kolom_tambahan, dtype=float)

        kolom_extra_arr = np.array(kolom_extra_per_baris, dtype=float)
        Tabel = np.hstack([A_asli, kolom_extra_arr, b.reshape(-1, 1)])

        self.nama_kolom = nama_kolom_lengkap
        self.C = C_lengkap
        self.tabel = Tabel  # m x (total_kolom + 1), kolom terakhir = RHS
        self.basis_idx = []  # index kolom basis tiap baris
        for tipe, baris, nama in basis:
            self.basis_idx.append(nama_kolom_lengkap.index(nama))
        self.indeks_artifisial = indeks_artifisial
        self.n_var_asli = n

    # ------------------------------------------------------------------
    def _hitung_cj_zj(self):
        """Hitung baris Zj dan Cj - Zj berdasarkan tableau & basis saat ini."""
        cB = self.C[self.basis_idx]
        Zj = cB @ self.tabel[:, :-1]
        CjZj = self.C - Zj
        Z = cB @ self.tabel[:, -1]
        return Zj, CjZj, Z

    # ------------------------------------------------------------------
    def selesaikan(self, maks_iterasi=200):
        """Jalankan iterasi simpleks sampai optimal / unbounded / infeasible."""
        for it in range(1, maks_iterasi + 1):
            Zj, CjZj, Z = self._hitung_cj_zj()

            snapshot = {
                'nomor': it,
                'tabel': self.tabel.copy(),
                'basis_idx': list(self.basis_idx),
                'nama_kolom': list(self.nama_kolom),
                'Zj': Zj.copy(),
                'CjZj': CjZj.copy(),
                'Z': Z,
            }

            # Kondisi optimal: semua Cj - Zj <= 0 (toleransi numerik)
            if np.all(CjZj <= TOLERANSI):
                snapshot['pivot_kolom'] = None
                snapshot['pivot_baris'] = None
                snapshot['penjelasan'] = (
                    f"Iterasi {it}: Semua nilai baris Cj - Zj sudah <= 0. "
                    "Ini artinya tidak ada lagi variabel non-basis yang bisa "
                    "meningkatkan nilai Z. Solusi optimal telah tercapai."
                )
                self.iterasi.append(snapshot)
                self._finalisasi(Z)
                return self._hasil()

            # Pilih kolom pivot: Cj-Zj terbesar (paling positif)
            kolom_pivot = int(np.argmax(CjZj))
            nama_kolom_pivot = self.nama_kolom[kolom_pivot]

            kolom_nilai = self.tabel[:, kolom_pivot]
            rhs = self.tabel[:, -1]

            # Cek unbounded: tidak ada elemen positif di kolom pivot
            if np.all(kolom_nilai <= TOLERANSI):
                snapshot['pivot_kolom'] = kolom_pivot
                snapshot['pivot_baris'] = None
                snapshot['penjelasan'] = (
                    f"Iterasi {it}: Kolom pivot terpilih adalah '{nama_kolom_pivot}' "
                    f"(Cj-Zj = {CjZj[kolom_pivot]:.4f}, paling positif). Namun seluruh "
                    "elemen pada kolom ini <= 0, sehingga rasio tidak bisa dihitung. "
                    "Ini menandakan solusi TIDAK TERBATAS (unbounded)."
                )
                self.iterasi.append(snapshot)
                self.status = 'unbounded'
                return self._hasil()

            # Rasio minimum (hanya baris dengan elemen kolom pivot > 0)
            rasio = np.full(self.m, np.inf)
            for r in range(self.m):
                if kolom_nilai[r] > TOLERANSI:
                    rasio[r] = rhs[r] / kolom_nilai[r]
            baris_pivot = int(np.argmin(rasio))
            elemen_pivot = self.tabel[baris_pivot, kolom_pivot]
            nama_var_keluar = self.nama_kolom[self.basis_idx[baris_pivot]]

            snapshot['pivot_kolom'] = kolom_pivot
            snapshot['pivot_baris'] = baris_pivot
            snapshot['rasio'] = rasio.copy()
            snapshot['elemen_pivot'] = elemen_pivot
            snapshot['penjelasan'] = (
                f"Iterasi {it}: Kolom pivot = '{nama_kolom_pivot}' (Cj-Zj = "
                f"{CjZj[kolom_pivot]:.4f}, nilai terbesar/paling menguntungkan untuk "
                f"masuk basis). Rasio minimum RHS/kolom-pivot = {rasio[baris_pivot]:.4f} "
                f"terjadi pada baris variabel basis '{nama_var_keluar}', sehingga baris "
                f"ini menjadi baris pivot dan '{nama_var_keluar}' keluar dari basis "
                f"digantikan '{nama_kolom_pivot}'. Elemen pivot = {elemen_pivot:.4f}. "
                f"Operasi baris: baris pivot dibagi {elemen_pivot:.4f}, lalu kolom pivot "
                "pada baris-baris lain dieliminasi menjadi 0 (Operasi Baris Elementer / OBE)."
            )
            self.iterasi.append(snapshot)

            # --- Lakukan pivot (Operasi Baris Elementer) ---
            self.tabel[baris_pivot, :] = self.tabel[baris_pivot, :] / elemen_pivot
            for r in range(self.m):
                if r != baris_pivot and abs(self.tabel[r, kolom_pivot]) > 1e-12:
                    faktor = self.tabel[r, kolom_pivot]
                    self.tabel[r, :] = self.tabel[r, :] - faktor * self.tabel[baris_pivot, :]

            self.basis_idx[baris_pivot] = kolom_pivot

        # Jika keluar loop tanpa status -> dianggap tidak konvergen
        self.status = self.status or 'tidak_konvergen'
        _, _, Z = self._hitung_cj_zj()
        self._finalisasi(Z)
        return self._hasil()

    # ------------------------------------------------------------------
    def _finalisasi(self, Z):
        if self.status == 'unbounded':
            return
        # Cek apakah ada variabel artifisial tersisa di basis dengan nilai > 0
        for idx, kolom in enumerate(self.basis_idx):
            if kolom in self.indeks_artifisial:
                nilai = self.tabel[idx, -1]
                if nilai > TOLERANSI:
                    self.status = 'infeasible'
                    return
        self.status = 'optimal'
        self._Z_final = Z if self.obj_type == 'max' else -Z

    # ------------------------------------------------------------------
    def _hasil(self):
        nilai_var = {nama: 0.0 for nama in self.nama_asli}
        for idx, kolom in enumerate(self.basis_idx):
            nama_kolom = self.nama_kolom[kolom]
            if nama_kolom in nilai_var:
                nilai_var[nama_kolom] = round(float(self.tabel[idx, -1]), 6)

        z_final = None
        if self.status == 'optimal':
            z_final = round(float(self._Z_final), 6)

        return {
            'status': self.status,
            'nilai_variabel': nilai_var,
            'Z_optimal': z_final,
            'iterasi': self.iterasi,
            'nama_kolom': self.nama_kolom,
            'jumlah_iterasi': len(self.iterasi),
        }


def selesaikan_simpleks(c, kendala, obj_type='max', nama_variabel=None):
    """Fungsi pembungkus (wrapper) sederhana untuk dipanggil dari modul UI."""
    solver = SimpleksBigM(c, kendala, obj_type=obj_type, nama_variabel=nama_variabel)
    return solver.selesaikan()
