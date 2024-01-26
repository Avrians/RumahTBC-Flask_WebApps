# README Aplikasi RumahTBC

Selamat datang di aplikasi RumahTBC! Aplikasi ini dibangun menggunakan Flask untuk sisi server dan Bootstrap untuk antarmuka pengguna yang responsif. Aplikasi ini didesain untuk memberikan dukungan kepada pasien dan dokter dalam mengelola kasus TBC, dengan berbagai fitur yang bermanfaat.

## Instalasi

Pastikan Anda telah menginstal Python dan pip di sistem Anda sebelum memulai. Berikut langkah-langkah untuk menginstal dan menjalankan aplikasi:

1. Clone repositori ini ke sistem lokal Anda:

   ```bash
   git clone https://github.com/namareg/rumahtbc.git
   ```

2. Pindah ke direktori proyek:

   ```bash
   cd rumahtbc
   ```

3. Buat lingkungan virtual:

   ```bash
   python -m venv venv
   ```

4. Aktifkan lingkungan virtual:

   - Di Windows:

     ```bash
     venv\Scripts\activate
     ```

   - Di Unix atau MacOS:

     ```bash
     source venv/bin/activate
     ```

5. Instal dependencies:

   ```bash
   pip install -r requirements.txt
   ```

6. Jalankan aplikasi:

   ```bash
   python app.py
   ```

   Aplikasi akan berjalan di `http://127.0.0.1:5000/`. Buka browser dan akses URL tersebut.

## Fitur Aplikasi

### 1. Artikel Kesehatan

Aplikasi ini menyediakan artikel kesehatan terkait TBC yang dapat diakses oleh pengguna. Artikel-artikel ini memberikan informasi penting mengenai gejala, pengobatan, dan pencegahan TBC.

### 2. Chatbot

Chatbot yang terintegrasi membantu pengguna dalam mendapatkan informasi dasar mengenai TBC, memberikan saran umum, dan membantu dalam navigasi aplikasi.

### 3. Riwayat Pemeriksaan

Pasien dapat melihat riwayat pemeriksaan mereka, termasuk hasil tes, catatan dari dokter, dan rekomendasi pengobatan. Ini membantu dalam memantau perkembangan penyakit.

### 4. Tanya Dokter

Fitur ini memungkinkan pengguna untuk mengajukan pertanyaan kepada dokter. Dokter yang terdaftar dalam aplikasi akan memberikan jawaban dan saran berdasarkan pertanyaan yang diajukan.

### 5. Deteksi untuk Dokter

Dokter dapat menggunakan fitur ini untuk melakukan deteksi TBC berdasarkan data pemeriksaan pasien. Algoritma deteksi yang terintegrasi membantu dokter dalam membuat keputusan yang lebih akurat.

## Kontributor
