from flask import Flask, render_template, jsonify,request, redirect, url_for, flash, session
import os,cv2
from keras.models import Model,load_model
# from keras.preprocessing.image import img_to_array
from tensorflow.keras.utils import img_to_array
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bcrypt import Bcrypt
from termcolor import colored
import nltk
from nltk.stem import WordNetLemmatizer
import random
from keras.models import load_model
from werkzeug.utils import secure_filename
import pickle
import json
# from flask_socketio import SocketIO, emit
from sqlalchemy import or_
from flask_cors import CORS
import cloudinary
import cloudinary.uploader
import cloudinary.api



app = Flask(__name__)
CORS(app)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1
size=224


cloudinary.config(cloud_name = 'drjnb5zxa', 
                  api_key = '929863485773151',
                  api_secret = 'sNNeW8Zupqzo7uoxBap4XXSYmYk',
                  secure=True)


# Untuk Chatroom
app.config['SECRET_KEY'] = 'secret!'
# socketio = SocketIO(app)

connected_users = {}

UPLOAD_FOLDER_ARTIKEL = 'static/assets/gambar/artikel'
UPLOAD_FOLDER_PROFILE = 'static/assets/gambar/profile'
UPLOAD_FOLDER_RONTGEN = 'static/assets/gambar/rontgen'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}


app.secret_key = "Secrect Key"

# Untuk menghubungkan ke database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:123456@localhost/rumahtbc'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)


#Model untuk riwayat rontgen
# class RiwayatRontgen(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     nik = db.Column(db.String(16), nullable=False) 
#     rumah_sakit = db.Column(db.String(50), nullable=False)
#     alamat = db.Column(db.String(100), nullable=False)
#     tanggal_publikasi = db.Column(db.Date, nullable=False)
#     dokter = db.Column(db.String(50), nullable=False)
#     gambar = db.Column(db.String(1000), nullable=False)
#     analisa = db.Column(db.String(1000), nullable=False)
#     rekomendasi = db.Column(db.String(1000), nullable=False)

#     def __init__(self, nik,rumah_sakit,alamat,tanggal_publikasi,dokter,gambar,analisa,rekomendasi):
#         self.nik = nik
#         self.rumah_sakit = rumah_sakit
#         self.alamat = alamat
#         self.tanggal_publikasi = tanggal_publikasi
#         self.dokter = dokter
#         self.gambar = gambar
#         self.analisa = analisa
#         self.rekomendasi = rekomendasi



# Model untuk tabel artikel kesehatan
class ArtikelKesehatan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(100), nullable=False)
    penulis = db.Column(db.String(100), nullable=False)
    isi = db.Column(db.Text, nullable=False)
    tanggal_publikasi = db.Column(db.Date, nullable=False)
    kategori = db.Column(db.String(50), nullable=True)
    gambar = db.Column(db.String(255), nullable=True)  # Tambahkan kolom gambar dengan panjang maksimal 255 karakter
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp(), nullable=False)
    
    def __init__(self, judul, penulis, isi, tanggal_publikasi, kategori, gambar=None):  # Tambahkan parameter gambar dan set defaultnya ke None
        self.judul = judul
        self.penulis = penulis
        self.isi = isi
        self.tanggal_publikasi = tanggal_publikasi
        self.kategori = kategori
        self.gambar = gambar    # Set nilai gambar dengan nilai yang diberikan atau None jika tidak ada gambar

    @classmethod
    def cari_artikel(cls, kata_kunci):
        return cls.query.filter(or_(
            cls.judul.ilike(f"%{kata_kunci}%"),
            cls.penulis.ilike(f"%{kata_kunci}%"),
            cls.isi.ilike(f"%{kata_kunci}%")
        )).all()

        
# Model untuk tabel user
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nik = db.Column(db.String(16), unique=True, nullable=False) 
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    hak_akses = db.Column(db.Enum('dokter', 'admin', 'pengguna'), nullable=False)    

    def __init__(self, nik, email, password, hak_akses):
        self.nik = nik
        self.email = email
        self.password = password
        self.hak_akses = hak_akses
        
# untuk tabel input review
class InputReview(db.Model):
    id_review = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    tanggal = db.Column(db.Date, nullable=True)
    review = db.Column(db.Text, nullable=False)

    def __init__(self, nama, email, tanggal,review):
        self.nama = nama
        self.email = email
        self.tanggal = tanggal
        self.review = review
        
# Model untul hasil sentimen analisis

class HasilSentimen(db.Model):
    id_hasil_sentimen = db.Column(db.Integer, primary_key=True)
    id_review = db.Column(db.Integer, nullable=False)
    nama = db.Column(db.String(255), nullable=False)
    tanggal = db.Column(db.Date, nullable=False)
    review = db.Column(db.String(1000), nullable=False)
    label = db.Column(db.String(10), nullable=False)

    def __init__(self, id_review, nama, tanggal, review, label):
        self.id_review = id_review
        self.nama = nama
        self.tanggal = tanggal
        self.review = review
        self.label = label

#Model untuk tabel user_data
class DataPasien(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nik = db.Column(db.String(20), unique=True, nullable=False)
    nama_lengkap = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    no_hp = db.Column(db.String(15), nullable=True)
    jenis_kelamin = db.Column(db.Enum('lakilaki', 'perempuan'), nullable=True)
    tanggal_lahir = db.Column(db.Date, nullable=True)
    alamat = db.Column(db.Text, nullable=True)
    gambar = db.Column(db.String(255), nullable=True)

    def __init__(self, nik, nama_lengkap=None, email=None, no_hp=None,
                 jenis_kelamin=None, tanggal_lahir=None, alamat=None, gambar=None):
        self.nik = nik
        self.nama_lengkap = nama_lengkap
        self.email = email
        self.no_hp = no_hp
        self.jenis_kelamin = jenis_kelamin
        self.tanggal_lahir = tanggal_lahir
        self.alamat = alamat
        self.gambar = gambar
    

        
# Model data karyawan
class DataKaryawan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nik = db.Column(db.String(20), nullable=False, unique=True)
    nama = db.Column(db.String(255), nullable=True)
    no_hp = db.Column(db.String(15), nullable=True) 
    email = db.Column(db.String(255), nullable=False, unique=True) 
    jenis_kelamin = db.Column(db.String(10), nullable=True)  
    tanggal_lahir = db.Column(db.Date, nullable=True) 
    alamat = db.Column(db.Text, nullable=True) 
    gambar = db.Column(db.String(255), nullable=True) 
    jabatan = db.Column(db.String(50), nullable=True) 

    def __init__(self, nik, nama=None, no_hp=None, email=None, jenis_kelamin=None,
                 tanggal_lahir=None, alamat=None, gambar=None, jabatan=None):
        self.nik = nik
        self.nama = nama
        self.no_hp = no_hp
        self.email = email
        self.jenis_kelamin = jenis_kelamin
        self.tanggal_lahir = tanggal_lahir
        self.alamat = alamat
        self.gambar = gambar
        self.jabatan = jabatan

# Model pemeriksaan
class Pemeriksaan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tanggal_pemeriksaan = db.Column(db.Date, nullable=False)
    nik = db.Column(db.String(20), nullable=False)
    nama = db.Column(db.String(100), nullable=False)
    nama_rumah_sakit = db.Column(db.String(255), nullable=False)
    id_dokter = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Menunggu')
    persentase = db.Column(db.Float, nullable=True)
    gambar_rontgen = db.Column(db.String(255), nullable=True)
    hasil_analisa = db.Column(db.Text, nullable=True)

    def __init__(self, tanggal_pemeriksaan, nik, nama, nama_rumah_sakit, id_dokter=None, status='Menunggu',
                 persentase=None, gambar_rontgen=None, hasil_analisa=None):
        self.tanggal_pemeriksaan = tanggal_pemeriksaan
        self.nik = nik
        self.nama = nama
        self.nama_rumah_sakit = nama_rumah_sakit
        self.id_dokter = id_dokter
        self.status = status
        self.persentase = persentase
        self.gambar_rontgen = gambar_rontgen
        self.hasil_analisa = hasil_analisa      

# Untuk membuat tabel di database
with app.app_context():
    db.create_all()

# Fungsi untuk memproses gambar deteksi
def processimg(img):
    img=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    img = cv2.resize(img, (size, size)) 
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    equalized_img = clahe.apply(img)
    crop=cv2.resize(equalized_img,(size,size))
    return crop

# Fungsi untuk chatbot
intents_file = open('data/chatbot/data.json',)
intents = json.load(intents_file)

model = load_model('data/chatbot/chatbot_model.h5')
words = pickle.load(open('data/chatbot/words.pkl', 'rb'))
classes = pickle.load(open('data/chatbot/classes.pkl', 'rb'))

lemmatizer = WordNetLemmatizer()
nltk.download('punkt')


def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words


def bow(sentence, words, show_details=False):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                bag[i] = 1
                if show_details:
                    print('Found in %s' % w)
    return bag


def predict_class(sentence, model):
    p = bow(sentence, words, show_details=False)
    res = model.predict([p])[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list


def get_response(ints, intents_json):
    tag = ints[0]['intent']
    list_intents = intents_json['intents']
    for i in list_intents:
        if tag == i['tag']:
            result = random.choice(i['responses'])
            break
    return result

# fungsi route untuk chatbot
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form['user_message']
    print(f"Received user message: {user_message}")  # Tambahkan baris ini
    ints = predict_class(user_message, model)
    response = get_response(ints, intents)
    print(f"Generated response: {response}")  # Tambahkan baris ini
    return jsonify({'response': response})

# fungsi untuk mengambil kata pertama
def ambil_kata_pertama(teks):
    # Memisahkan kata-kata dari teks
    kata_kata = teks.split()
    # Mengambil kata pertama
    kata_pertama = ' '.join(kata_kata[:40])

    return kata_pertama

# fungsi untuk mevalidasi ekstensi file
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Fungsi route untuk halaman index
@app.route("/")
def index():
    # Ambil 4 data terbaru dari tabel Artikel
    latest_articles = ArtikelKesehatan.query.order_by(ArtikelKesehatan.tanggal_publikasi.desc()).limit(4).all()
    for artikel in latest_articles:
        artikel.isi = ambil_kata_pertama(artikel.isi)
    active = 'home'
    return render_template('index.html', latest_articles=latest_articles, aktif=active)

# fungsi route untuk tanya dokter
@app.route('/chat/dokter')
def chat_dokter():
    if 'nik' in session:
        hak_akses = session.get('hak_akses')
        if hak_akses is not None:
            if hak_akses == 'dokter':
                return render_template('chat.html', nik=session['nik'], user='Dr. Fadillah')
            elif hak_akses == 'admin':
                return redirect(url_for('home'))
            elif hak_akses == 'pengguna':
                return redirect(url_for('home'))
            else:
                flash('Hak akses tidak valid.', 'danger')
                return redirect(url_for('logout'))
        else:
            flash('Hak akses tidak tersedia.', 'danger')
            return redirect(url_for('logout'))
        return redirect(url_for('home'))
    return render_template('chat.html', user='Fadillah')

@app.route('/chat/pasien')
def chat_pasien():
    if 'nik' in session:
        return render_template('chat.html', user='Pasien')
    return redirect(url_for('home'))

# @socketio.on('connect')
# def handle_connect():
#     user_id = request.sid
#     connected_users[user_id] = request.sid
#     print(f"User {user_id} connected")
    
# @socketio.on('disconnect')
# def handle_disconnect():
#     user_id = request.sid
#     del connected_users[user_id]
#     print(f"User {user_id} disconnected")
    
# @socketio.on('message')
# def handle_message(data):
#     sender_id = request.sid
#     message = data['message']
#     sender_name = data['sender_name']
#     emit('message', {'sender': sender_name, 'message': message}, broadcast=True)

# Fungsi route untuk halaman login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'email' in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        # data = request.json
        # email = data['email']
        # password = data['password']

        email = request.form['email']
        password = request.form['password']

        user = Users.query.filter_by(email=email).first()

        print(f"Upaya login untuk username: {email}, password: {password}")
        print(f"User ditemukan: {user}")
        
        if user and check_password_hash(user.password, password):
            user_data = []
            user_data.append({
                'nik': user.nik,
                'code': '200',
            })



            session['user_id'] = user.id  
            session['nik'] = user.nik 
            session['email'] = email  
            session['hak_akses'] = user.hak_akses 
            print(f"Login berhasil untuk email: {email}")
            flash('Login berhasil!', 'success')
            # return redirect(url_for('home'))
            return ({'code': user.nik})
        elif not user:
            return ({'code': 404})
        else:
            flash('Login gagal. Periksa kembali username dan password Anda.', 'danger')
            return ({'code': 500})

    return render_template('login.html')

# Fungsi route untuk halaman home dokter/admin
@app.route('/home')
def home():
    active = 'home'
    if 'email' in session:
        hak_akses = session.get('hak_akses')

        if hak_akses is not None:
            if hak_akses == 'admin':
                return render_template('admin_dashboard.html', email=session['email'], aktif=active)
            elif hak_akses == 'dokter':
                return render_template('dokter_dashboard.html', email=session['email'], aktif=active)
            elif hak_akses == 'pengguna':
                return render_template('index.html', email=session['email'], aktif=active)
            else:
                flash('Hak akses tidak valid.', 'danger')
                return redirect(url_for('logout'))
        else:
            flash('Hak akses tidak tersedia.', 'danger')
            return redirect(url_for('logout'))
    else:
        flash('Anda harus login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))

# Fungsi route untuk keluar halaman admin/dokter
@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('login'))

# Fungsi route untuk halaman pendaftaran user
@app.route('/register')
def register():
    return render_template('register.html')

# fungsi untuk register akun pengguna
@app.route('/registerakun', methods=['POST'])
def registerakun():
    if request.method == 'POST':
        nik = request.form['nik']
        email = request.form['email']
        password = request.form['password']
        hak_akses = "pengguna"

        hashed_password = generate_password_hash(password)

        akun_karyawan = Users(nik=nik, email=email, password=hashed_password, hak_akses=hak_akses)
        db.session.add(akun_karyawan)
        db.session.commit()
        
        # Tambahkan data pasien secara otomatis ke tabel DataPasien
        data_pasien = DataPasien(nik=nik, email=email)
        db.session.add(data_pasien)
        db.session.commit()
        
        flash('Pendaftaran akun anda berhasil, silahkan login untuk masuk ke akun anda', 'success')  # Tambahkan flash message
        return redirect(url_for('login'))

    flash('Maaf pendaftaran akun anda gagal', 'danger')  # Tambahkan flash message
    return redirect(url_for('register'))

# Fungsi route untuk halaman tanya dokter
@app.route('/tanyadokter')
def tanyadokter():
    return render_template('chat.html')

# Fungsi route untuk halaman buat artikel dokter
@app.route('/dokter/artikel/form')
def dokter_artikel_form():
    active = 'artikel'
    return render_template('dokter_artikelform.html', aktif=active)

# Fungsi route untuk halaman daftar artikel dokter
@app.route('/dokter/artikel')
def dokter_artikel():
    articles = ArtikelKesehatan.query.all()
    active = 'artikel'
    return render_template('dokter_artikeldaftar.html', artikel=articles,  aktif=active)

# Fungsi route untuk membuat artikel baru dokter
@app.route('/dokter/artikel/submit', methods=['POST'])
def dokter_artikel_submit():
    # Ambil data dari form
    judul = request.form['judul']
    penulis = request.form['penulis']
    isi = request.form['isi']
    tanggal_publikasi = datetime.now()  # Gunakan tanggal dan waktu saat ini
    kategori = request.form['kategori']

    # Buat objek Artikel
    artikel_baru = ArtikelKesehatan(judul=judul, penulis=penulis, isi=isi, tanggal_publikasi=tanggal_publikasi, kategori=kategori)

    # Simpan artikel ke database
    db.session.add(artikel_baru)
    db.session.commit()

    # Redirect ke halaman utama atau halaman detail artikel
    return redirect(url_for('dokter_artikel'))

# Fungsi route untuk halaman daftar artikel admin
@app.route('/admin/artikel')
def admin_artikel():
    articles = ArtikelKesehatan.query.all()
    active = 'artikel'
    return render_template('admin_artikeldaftar.html', artikel=articles, aktif=active)


# Fungsi route untuk halaman buat artikel admin
@app.route('/admin/artikel/form', methods=['GET', 'POST'])
def admin_artikel_form():
    if request.method == 'POST':
        # Ambil data dari formulir
        judul = request.form['judul']
        penulis = request.form['penulis']
        isi = request.form['isi']
        kategori = request.form['kategori']
        tanggal_publikasi = request.form['tanggal_publikasi']

        # Proses gambar
        gambar = request.files['gambar']
        if gambar and allowed_file(gambar.filename):
            filename = secure_filename(gambar.filename)
            gambar.save(os.path.join(UPLOAD_FOLDER_ARTIKEL, filename))
        else:
            filename = None

        # Simpan data ke dalam database atau sistem penyimpanan
        artikel_baru = ArtikelKesehatan(judul=judul, tanggal_publikasi=tanggal_publikasi,penulis=penulis, isi=isi, kategori=kategori, gambar=filename)
        db.session.add(artikel_baru)
        db.session.commit()

        flash('Artikel berhasil disimpan', 'success')
        return redirect(url_for('admin_artikel'))

    active = 'artikel'
    return render_template('admin_artikelform.html', aktif=active)

# Fungsi route untuk halaman update artikel admin
@app.route('/admin/artikel/update/<int:artikel_id>', methods=['GET', 'POST'])
def admin_artikel_update(artikel_id):
    artikel = ArtikelKesehatan.query.get(artikel_id)

    if artikel:
        if request.method == 'POST':
            # Ambil data dari formulir update
            artikel.judul = request.form['judul']
            artikel.penulis = request.form['penulis']
            artikel.isi = request.form['isi']
            artikel.kategori = request.form['kategori']
            artikel.tanggal_publikasi = request.form['tanggal_publikasi']

            # Proses gambar
            gambar = request.files['gambar']
            if gambar and allowed_file(gambar.filename):
                filename = secure_filename(gambar.filename)
                gambar.save(os.path.join(UPLOAD_FOLDER_ARTIKEL, filename))
                artikel.gambar = filename
            elif 'hapus_gambar' in request.form:
                artikel.gambar = None

            # Lakukan commit ke database
            db.session.commit()

            flash('Artikel berhasil diupdate', 'success')
            return redirect(url_for('admin_artikel'))

        return render_template('admin_artikelformupdate.html', artikel=artikel)

    else:
        flash('Artikel tidak ditemukan', 'danger')
        return redirect(url_for('admin_artikel'))

# Fungsi route untuk menghapus artikel
@app.route('/admin/artikel/hapus/<int:artikel_id>', methods=['POST'])
def admin_artikel_hapus(artikel_id):
    artikel = ArtikelKesehatan.query.get(artikel_id)

    if artikel:
        # Hapus gambar terkait artikel
        if artikel.gambar:
            gambar_path = os.path.join(UPLOAD_FOLDER_ARTIKEL, artikel.gambar)
            if os.path.exists(gambar_path):
                os.remove(gambar_path)

        # Hapus artikel dari database
        db.session.delete(artikel)
        db.session.commit()

        flash('Artikel berhasil dihapus', 'success')
    else:
        flash('Artikel tidak ditemukan', 'danger')

    return redirect(url_for('admin_artikel'))

# Fungsi route untuk halaman daftar pasien admin
@app.route('/admin/pasien')
def admin_pasiendaftar():
    active = 'pasien'
    patients = DataPasien.query.all()
    return render_template('admin_pasiendaftar.html', patients=patients,aktif=active)

# Fungsi route untuk halaman tambah pasien
@app.route('/admin/pasien/form', methods=['GET', 'POST'])
def admin_pasien_form():
    active = 'pasien'
    if request.method == 'POST':
        nik = request.form['nik']
        nama_lengkap = request.form['nama']
        no_hp = request.form['no_hp']
        email = request.form['email']
        jenis_kelamin = request.form['jenis_kelamin']
        tanggal_lahir = datetime.strptime(request.form['tanggal_lahir'], '%Y-%m-%d')
        alamat = request.form['alamat']
        filename = None 
        # Upload foto jika ada
        if 'gambar' in request.files:
            photo = request.files['gambar']
            if photo.filename != '':
                filename = secure_filename(f"{nik}_{photo.filename}")
                filepath = os.path.join(UPLOAD_FOLDER_PROFILE, filename)
                photo.save(filepath)

        # Simpan data ke dalam database
        karyawan_baru = DataPasien(nik=nik, nama_lengkap=nama_lengkap, no_hp=no_hp, email=email,
                                 jenis_kelamin=jenis_kelamin, tanggal_lahir=tanggal_lahir,
                                 alamat=alamat, gambar=filename)
        db.session.add(karyawan_baru)
        db.session.commit()
        return redirect(url_for('admin_pasiendaftar'))
    
    return render_template('admin_pasienform.html', aktif=active)

# Route untuk halaman form ubah data pasien
@app.route('/admin/pasien/update/<int:pasien_id>', methods=['GET', 'POST'])
def admin_pasien_update(pasien_id):
    active = 'pasien'
    pasien = DataKaryawan.query.get(pasien_id)
    
    if pasien:
        if request.method == 'POST':
            pasien.nik = request.form['nik']
            pasien.nama = request.form['nama']
            pasien.no_hp = request.form['no_hp']
            pasien.email = request.form['email']
            pasien.jenis_kelamin = request.form['jenis_kelamin']
            pasien.tanggal_lahir = datetime.strptime(request.form['tanggal_lahir'], '%Y-%m-%d')
            pasien.alamat = request.form['alamat']
            
            # Proses gambar
            gambar = request.files['gambar']
            if gambar and allowed_file(gambar.filename):
                filename = secure_filename(gambar.filename)
                gambar.save(os.path.join(UPLOAD_FOLDER_PROFILE, filename))
                pasien.gambar = filename
            elif 'hapus_gambar' in request.form:
                pasien.gambar = None
            
            db.session.commit()
            
            flash('Data Pasien berhasil diupdate', 'success')
            return redirect(url_for('admin_pasien'))
            
        return render_template('admin_pasienformupdate.html', pasien=pasien, aktif=active)
    else:
        flash('Pasien tidak ditemukan', 'danger')
        return redirect(url_for('admin_pasien'))

# Fungsi route untuk menghapus data pasien
@app.route('/admin/pasien/hapus/<int:pasien_id>', methods=['POST'])
def admin_pasien_hapus(pasien_id):
    pasien = DataKaryawan.query.get(pasien_id)

    if pasien:
        # Hapus gambar terkait pasien
        if pasien.gambar:
            gambar_path = os.path.join(UPLOAD_FOLDER_PROFILE, pasien.gambar)
            if os.path.exists(gambar_path):
                os.remove(gambar_path)

        # Hapus artikel dari database
        db.session.delete(pasien)
        db.session.commit()

        flash('Pasien berhasil dihapus', 'success')
    else:
        flash('Pasien tidak ditemukan', 'danger')

    return redirect(url_for('admin_pasien'))

# fungsi route untuk halaman daftar akun dokter/ admin
@app.route('/admin/akun')
def admin_akun():
    active = 'akun'
    users = Users.query.all()
    return render_template('admin_akun.html', aktif=active, users=users)

# Route untuk halaman bikin akun
@app.route('/admin/akun/form')
def admin_akun_form():
    active = 'akun'
    return render_template('admin_akunform.html', aktif=active)

# route untuk halaman data pemeriksaan
@app.route('/admin/pemeriksaan')
def admin_pemeriksaan():
    active = 'pemeriksaan'
    pemeriksaan = Pemeriksaan.query.all()
    return render_template('admin_pemeriksaan.html', aktif=active, pemeriksaan=pemeriksaan)

# Route untuk halaman tambah data pemeriksaan
@app.route('/admin/pemeriksaan/form')
def admin_pemeriksaan_form():
    active = 'pemeriksaan'
    return render_template('admin_pemeriksaanform.html', aktif=active)

# route untuk menyimpan data pemeriksaan
@app.route('/admin/pemeriksaan/tambah', methods=['GET', 'POST'])
def admin_pemeriksaan_tambah():
    if request.method == 'POST':
        # Ambil data dari formulir
        tanggal_pemeriksaan = request.form['tanggal_pemeriksaan']
        nik = request.form['nik']
        nama = request.form['nama']
        nama_rumah_sakit = request.form['nama_rs']

        # Upload foto rontgen
        if 'foto_rontgen' in request.files:
            foto_rontgen = request.files['foto_rontgen']
            if foto_rontgen and allowed_file(foto_rontgen.filename):
                filename = secure_filename(f"{nik}_{foto_rontgen.filename}")
                filepath = os.path.join(UPLOAD_FOLDER_RONTGEN, filename)
                foto_rontgen.save(filepath)
            else:
                flash('File foto rontgen tidak valid', 'danger')
                return redirect(url_for('admin_pemeriksaan_tambah'))
        else:
            flash('File foto rontgen tidak ditemukan', 'danger')
            return redirect(url_for('admin_pemeriksaan_tambah'))

        # Buat objek Pemeriksaan
        pemeriksaan = Pemeriksaan(
            tanggal_pemeriksaan=datetime.strptime(tanggal_pemeriksaan, '%Y-%m-%d'),
            nik=nik,
            nama=nama,
            nama_rumah_sakit=nama_rumah_sakit,
            gambar_rontgen=filename  # Simpan nama file foto rontgen ke dalam database
        )

        # Simpan objek ke dalam database
        db.session.add(pemeriksaan)
        db.session.commit()

        flash('Data berhasil disimpan', 'success')
        return redirect(url_for('admin_pemeriksaan'))

    return render_template('admin_pemeriksaanform.html')

# route untuk halaman data dokter
@app.route('/admin/dokter')
def admin_dokter():
    active = 'dokter'
    dokters = DataKaryawan.query.filter_by(jabatan="Dokter Spesialis").all()
    return render_template('admin_dokter.html', aktif=active, dokters=dokters)

# route halaman tambah data dokter
@app.route('/admin/dokter/form', methods=['GET', 'POST'])
def admin_dokter_form():
    active = 'dokter'
    if request.method == 'POST':
        nik = request.form['nik']
        nama = request.form['nama']
        no_hp = request.form['no_hp']
        email = request.form['email']
        jenis_kelamin = request.form['jenis_kelamin']
        tanggal_lahir = datetime.strptime(request.form['tanggal_lahir'], '%Y-%m-%d')
        alamat = request.form['alamat']
        jabatan = "Dokter Spesialis"
        
        filename = None 
        
        # Upload foto jika ada
        if 'gambar' in request.files:
            photo = request.files['gambar']
            if photo.filename != '':
                filename = secure_filename(f"{nik}_{photo.filename}")
                filepath = os.path.join(UPLOAD_FOLDER_PROFILE, filename)
                photo.save(filepath)

        # Simpan data ke dalam database
        karyawan_baru = DataKaryawan(nik=nik, nama=nama, no_hp=no_hp, email=email,
                                 jenis_kelamin=jenis_kelamin, tanggal_lahir=tanggal_lahir,
                                 alamat=alamat, gambar=filename, jabatan=jabatan)
        db.session.add(karyawan_baru)
        db.session.commit()
        return redirect(url_for('admin_dokter'))
    
    return render_template('admin_dokterform.html', aktif=active)

# Route untuk halaman form ubah data dokter
@app.route('/admin/dokter/update/<int:dokter_id>', methods=['GET', 'POST'])
def admin_dokter_update(dokter_id):
    active = 'dokter'
    dokter = DataKaryawan.query.get(dokter_id)
    
    if dokter:
        if request.method == 'POST':
            dokter.nik = request.form['nik']
            dokter.nama = request.form['nama']
            dokter.no_hp = request.form['no_hp']
            dokter.email = request.form['email']
            dokter.jenis_kelamin = request.form['jenis_kelamin']
            dokter.tanggal_lahir = datetime.strptime(request.form['tanggal_lahir'], '%Y-%m-%d')
            dokter.alamat = request.form['alamat']
            dokter.jabatan = request.form['jabatan']
            
            # Proses gambar
            gambar = request.files['gambar']
            if gambar and allowed_file(gambar.filename):
                filename = secure_filename(gambar.filename)
                gambar.save(os.path.join(UPLOAD_FOLDER_PROFILE, filename))
                dokter.gambar = filename
            elif 'hapus_gambar' in request.form:
                dokter.gambar = None
            
            db.session.commit()
            
            flash('Data Dokter berhasil diupdate', 'success')
            return redirect(url_for('admin_dokter'))
            
        return render_template('admin_dokterformupdate.html', dokter=dokter, aktif=active)
    else:
        flash('Dokter tidak ditemukan', 'danger')
        return redirect(url_for('admin_dokter'))
    
# Fungsi route untuk menghapus data dokter
@app.route('/admin/dokter/hapus/<int:dokter_id>', methods=['POST'])
def admin_dokter_hapus(dokter_id):
    dokter = DataKaryawan.query.get(dokter_id)

    if dokter:
        # Hapus gambar terkait dokter
        if dokter.gambar:
            gambar_path = os.path.join(UPLOAD_FOLDER_PROFILE, dokter.gambar)
            if os.path.exists(gambar_path):
                os.remove(gambar_path)

        # Hapus artikel dari database
        db.session.delete(dokter)
        db.session.commit()

        flash('Dokter berhasil dihapus', 'success')
    else:
        flash('Dokter tidak ditemukan', 'danger')

    return redirect(url_for('admin_dokter'))
    
# route untuk halaman data ulasan pengguna
@app.route('/admin/review')
def admin_review():
    active = 'review'
    reviews = InputReview.query.all()
    return render_template('admin_review.html', reviews=reviews, aktif=active)

# Fungsi route untuk halaman tentang user
@app.route('/tentang')
def tentang():
    active = 'tentang'
    return render_template('tentang.html', aktif=active)

# route untuk halaman profile
@app.route('/profiluser')
def profiluser():
    active = 'profil'
    nik = session.get('nik')  # Ambil nik dari session

    if nik:
        # Cari data pengguna dari tabel Users berdasarkan nik
        user = Users.query.filter_by(nik=nik).first()

        if user:
            # Cari data profil pasien dari tabel DataPasien berdasarkan nik pengguna
            user_profile = DataPasien.query.filter_by(nik=user.nik).first()

            if user_profile:
                return render_template('profile.html', aktif=active, user_profile=user_profile)

    # Jika nik tidak ada, data pengguna tidak ditemukan, atau data profil tidak ditemukan, bisa ditangani di sini
    return redirect(url_for('login')) 

@app.route('/update_profileuser', methods=['GET', 'POST'])
def update_profileuser():
    active = 'profil'
    nik = session.get('nik')

    if nik:
        user = Users.query.filter_by(nik=nik).first()
        user_profile = DataPasien.query.filter_by(nik=nik).first()

        if request.method == 'POST':
            # Ambil data dari form
            user.nama_lengkap = request.form.get('nama_lengkap')
            user.email = request.form.get('email')

            if user_profile:
                user_profile.nama_lengkap = request.form.get('nama_lengkap')
                user_profile.email = request.form.get('email')
                user_profile.no_hp = request.form.get('no_hp')
                user_profile.jenis_kelamin = request.form.get('jenis_kelamin')
                user_profile.tanggal_lahir = request.form.get('tanggal_lahir')
                user_profile.alamat = request.form.get('alamat')

                # Upload foto jika ada
                if 'gambar' in request.files:
                    photo = request.files['gambar']
                    if photo.filename != '':
                        filename = secure_filename(f"{nik}_{photo.filename}")
                        filepath = os.path.join(UPLOAD_FOLDER_PROFILE, filename)
                        photo.save(filepath)
                        user_profile.gambar = filename

            db.session.commit()

            flash('Profile berhasil diperbarui', 'success')
            return redirect(url_for('profiluser'))

        return render_template('profile.html', aktif=active, user=user, user_profile=user_profile)

    return redirect(url_for('login'))

# Fungsi route untuk halaman riwayat user
@app.route('/riwayatuser')
def riwayatuser():
    active = 'riwayat'
    nik = session.get('nik')

    if nik:
        user_profile = DataPasien.query.filter_by(nik=nik).first()

        if user_profile:
            riwayat_pemeriksaan = Pemeriksaan.query.filter_by(nik=nik).all()

            if riwayat_pemeriksaan:
                return render_template('riwayatuser.html', aktif=active,user_profile=user_profile, riwayat_pemeriksaan=riwayat_pemeriksaan)
            else:
                return render_template('riwayatuser.html', aktif=active,user_profile=user_profile, riwayat_pemeriksaan=riwayat_pemeriksaan)
    
    flash('Anda harus login terlebih dahulu.', 'warning')
    return redirect(url_for('login'))

# Fungsi route untuk halaman artikel kesehatan user
@app.route('/artikel')
def artikel():
    latest_articles = ArtikelKesehatan.query.order_by(ArtikelKesehatan.tanggal_publikasi.desc()).limit(10).all()
    active = 'artikel'
    for artikel in latest_articles:
        artikel.isi = ambil_kata_pertama(artikel.isi)
    return render_template('artikel.html', latest_articles=latest_articles, aktif=active)

@app.route('/artikel/cari', methods=['GET'])
def artikel_cari():
    query = request.args.get('query', '')
    
    if query:
        hasil_pencarian = ArtikelKesehatan.cari_artikel(query)
        for artikel in hasil_pencarian:
            artikel.isi = ambil_kata_pertama(artikel.isi)
    else:
        hasil_pencarian = ArtikelKesehatan.query.all()
        for artikel in hasil_pencarian:
            artikel.isi = ambil_kata_pertama(artikel.isi)

    return render_template('artikel.html', latest_articles=hasil_pencarian)


# Fungsi route untuk halaman  detail artikel
@app.route('/detailartikel')
def detailartikel():
    return render_template('detailartikel2.html')

# Fungsi route untuk halaman artikel kesehatan user
@app.route('/detailartikel/<int:article_id>')
def artikel_by_id(article_id):
    article = ArtikelKesehatan.query.filter_by(id=article_id).first_or_404()
    return render_template('detailartikel.html', article=article)

# Fungsi route untuk halaman deteksi dokter
@app.route('/dokter/deteksi')
def dokter_deteksi():
    active = 'deteksi'
    return render_template('dokter_deteksi.html', aktif=active)

# Fungsi route untuk halaman deteksi dokter bagian pemilihan
@app.route('/dokter/datadeteksi', methods=['GET', 'POST'])
def dokter_datadeteksi():
    active = 'deteksi'
    daftar_tunggu = Pemeriksaan.query.filter_by(status='Menunggu').all()
    riwayat = Pemeriksaan.query.filter_by(id_dokter='1').all()
    

    if request.method == 'POST':
        data_pasien_id = request.form.get('data_pasien')
        data_pemeriksaan = Pemeriksaan.query.filter_by(id=data_pasien_id).first()
        daftar_tunggu = Pemeriksaan.query.filter_by(status='Menunggu').all()
        
        
        if data_pemeriksaan:
            return render_template('dokter_datadeteksi.html', aktif=active, data_pemeriksaan=data_pemeriksaan, daftar_tunggu=daftar_tunggu, riwayat=riwayat)
        else:
            flash('Data pasien tidak ditemukan', 'danger')
            return redirect(url_for('dokter_datadeteksi'))
        
    return render_template('dokter_datadeteksi.html', aktif=active, daftar_tunggu=daftar_tunggu, riwayat=riwayat)

# Fungsi route untuk halaman deteksi dokter
@app.route('/dokter/datadeteksi/deteksi')
def dokter_datadeteksi_deteksi():
    active = 'deteksi'
    return render_template('dokter_deteksitbc.html', aktif=active)

# Fungsi route untuk memproses deteksi TBC dokter
@app.route("/dokter/datadeteksi/upload", methods=['POST'])
def dokter_upload_tbc():
    active = 'deteksi'
    # Memuat Model Deep Learning
    model = load_model('modelTBC.h5')

    # Ambil ID Pemeriksaan dari formulir
    data_pasien_id = request.form.get('id_deteksi')
    print(f"ID Pemeriksaan: {data_pasien_id}")

    # Ambil data gambar dari database berdasarkan ID Pemeriksaan
    pemeriksaan = Pemeriksaan.query.filter_by(id=data_pasien_id).first()
    print(f"Data Pemeriksaan: {pemeriksaan.gambar_rontgen}")

    if pemeriksaan is None or pemeriksaan.gambar_rontgen is None:
        # Tangani kasus ketika gambar tidak ditemukan
        flash('Data gambar tidak ditemukan', 'error')
        return redirect(url_for('dokter_datadeteksi'))
    
    # Mengatur Direktori Target untuk Berkas yang Diunggah
    target = os.path.join(APP_ROOT, 'static/assets/gambar/rontgen/')
    # Menggunakan nama file dari database
    filename = pemeriksaan.gambar_rontgen
    destination = os.path.join(target, filename)

    # Menyiapkan Gambar untuk Prediksi Model
    img = cv2.imread(destination)
    cv2.imwrite('static/xray/file.png', img)

    # Pemrosesan Gambar
    img = processimg(img)
    cv2.imwrite('static/xray/processedfile.png', img)


    img = img.astype('uint8')
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    img = img_to_array(img)
    img = cv2.resize(img, (size, size))
    img = img.reshape(1, size, size, 3)
    img = img.astype('float32')
    img = img / 255.0

    # Prediksi Model
    result = np.argmax(model.predict(img), axis=-1)
    pred = model.predict(img)
    neg = pred[0][0]
    pos = pred[0][1]

    # Merender Template Hasil Deteksi
    classes = ['Negatif', 'Positif']
    predicted = classes[result[0]]

    return render_template("dokter_deteksitbc.html", pred=predicted, pos=pos, neg=neg, aktif=active, data_pemeriksaan=pemeriksaan)


# Fungsi route untuk update data pemeriksaan
@app.route("/dokter/datadeteksi/update", methods=['POST'])
def dokter_datadeteksi_update():
    active = 'deteksi'
    id_pemeriksaan = request.form.get('id_pemeriksaan')
    id_dokter = request.form.get('id_dokter')
    status = request.form.get('status')
    persentase = request.form.get('persentase')
    hasil_analisa = request.form.get('hasil_analisa')

    pemeriksaan = Pemeriksaan.query.filter_by(id=id_pemeriksaan).first()

    if pemeriksaan:
        pemeriksaan.id_dokter = id_dokter
        pemeriksaan.status = status
        pemeriksaan.persentase = persentase
        pemeriksaan.hasil_analisa = hasil_analisa

        db.session.commit()
        flash('Data diagnosa berhasil ditambahkan', 'success')
        return render_template("dokter_datadeteksi.html", aktif=active)
    else:
        flash('Data pemeriksaan tidak ditemukan', 'danger')
    
    return render_template("dokter_datadeteksi.html", aktif=active)
    

# Fungsi route untuk memproses deteksi TBC dokter
@app.route("/dokter/deteksi/upload", methods=['POST'])
def upload_tbc():
    active = 'deteksi'
    #Memuat Model Deep Learning
    model=load_model('modelTBC.h5')   
    print("model_loaded")
    # Mengatur Direktori Target untuk Berkas yang Diunggah
    target = os.path.join(APP_ROOT, 'static/xray/')
    # Membuat Direktori Target Jika Belum Ada
    if not os.path.isdir(target):
        os.mkdir(target)
    # Menyimpan Berkas yang Diunggah
    filename = ""
    for file in request.files.getlist("file"):
        filename = file.filename
        destination = "/".join([target, filename])
        file.save(destination)
    # Menyiapkan Gambar untuk Prediksi Model
    img = cv2.imread(destination)
    cv2.imwrite('static/xray/file.png',img)
    # Pemrosesan Gambar
    img= processimg(img)
    cv2.imwrite('static/xray/processedfile.png',img)
    img = img.astype('uint8')
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    img = img_to_array(img)
    img = cv2.resize(img,(size,size))
    img=img.reshape(1,size,size,3)
    img = img.astype('float32')
    img = img / 255.0
    # img = img / np.max(img)
    # Prediksi Model
    result = np.argmax(model.predict(img), axis=-1)
    pred=model.predict(img)
    neg=pred[0][0]
    pos=pred[0][1]
    # Merender Template Hasil Deteksi
    classes=['Negative','Positive']
    predicted=classes[result[0]]
    plot_dest = "/".join([target, "result.png"])

    return render_template("dokter_hasildeteksi.html", pred=predicted,pos=pos,neg=neg, filename=filename, aktif=active)

# fungsi untuk menambahkan akun baru via admin
@app.route('/admin/addakun', methods=['POST'])
def admin_addakun():
    if request.method == 'POST':
        nik = request.form['nik']
        email = request.form['email']
        password = request.form['password']
        hak_akses = request.form['hak_akses']

        hashed_password = generate_password_hash(password)

        akun_karyawan = Users(nik=nik, email=email, password=hashed_password, hak_akses=hak_akses)
        db.session.add(akun_karyawan)
        db.session.commit()
        return redirect(url_for('admin_akun'))

    return redirect(url_for('admin_akun'))

# fungsi untuk menghapus akun 
@app.route('/admin/deleteakun/<int:user_id>', methods=['POST'])
def admin_deleteakun(user_id):
    try:
        user = Users.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            flash('Akun karyawan berhasil dihapus', 'success')
        else:
            flash('Akun karyawan tidak ditemukan', 'danger')
    except Exception as e:
        flash('Terjadi kesalahan saat menghapus akun karyawan', 'danger')
        print(str(e))
    return redirect(url_for('admin_akun'))   

# Rute untuk menampilkan formulir edit akun
@app.route('/admin/editakun/<int:user_id>', methods=['GET'])
def admin_editakun(user_id):
    active = 'akun'
    user = Users.query.get_or_404(user_id)
    return render_template('admin_akunformupdate.html', user=user, aktif=active)

# Rute untuk menangani permintaan pembaruan akun
@app.route('/admin/updateakun/<int:user_id>', methods=['POST'])
def admin_updateakun(user_id):
    user = Users.query.get_or_404(user_id)
    
    # Mengambil data dari formulir
    user.nik = request.form['nik']
    user.email = request.form['email']
    user.hak_akses = request.form['hak_akses']

    # Memeriksa apakah ada password baru yang dimasukkan
    new_password = request.form['password']
    if new_password:
        user.password = generate_password_hash(new_password)

    # Memperbarui data ke database
    try:
        db.session.commit()
        flash('Akun karyawan berhasil diperbarui', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Terjadi kesalahan saat memperbarui akun karyawan', 'danger')
        print(str(e))

    return redirect(url_for('admin_akun'))

# route untuk meredirect ke ngrok
# Route untuk melakukan redirect ke situs internet
@app.route('/ngroksentimen')
def ngrok_sentimen():
    # Ganti URL berikut dengan URL situs yang Anda inginkan
    target_url = 'http://localhost:8501/'
    
    # Lakukan redirect ke URL target
    return redirect(target_url)

@app.route('/tambah_review', methods=['POST'])
def tambah_review():
    if request.method == 'POST':
        nama = request.form['name']
        email = request.form['email']
        review_text = request.form['message']
        tanggal = datetime.now()

        # Memastikan semua data yang diperlukan telah diberikan
        if nama and email and review_text:
            try:
                new_review = InputReview(nama=nama, email=email, tanggal=tanggal, review=review_text)
                db.session.add(new_review)
                db.session.commit()
                flash('Ulasan dari kamu sudah terkirim. Terima kasih!', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                flash(f'Error: {str(e)}', 'error')
                return redirect(url_for('index'))
        else:
            return jsonify({'status': 'error', 'message': 'Semua field harus diisi'}), 400
        


##API Mobile
###API User Data
#Get All user data
@app.route('/api/userdata', methods=['GET'])
def get_all_user_data():
    user_data = DataPasien.query.all()

    data_list = []
    for data in user_data:
        data_list.append({
            'id': data.id,
            'nik': data.nik,
            'nama_lengkap': data.nama_lengkap,
            'jenis_kelamin': data.jenis_kelamin,
            'tanggal_lahir': data.tanggal_lahir,
            'alamat': data.alamat,
            'no_hp': data.no_hp,
            'email': data.email,
            'gambar': data.gambar
        })
        
    return jsonify(data_list)

#Get user data by nik
@app.route('/api/user/<int:nik>', methods=['GET'])
def get_user_data_by_nik(nik):
    user_data = DataPasien.query.filter_by(nik=nik).first()
    if user_data is None:
        return jsonify({'message': 'Data tidak ditemukana!'}), 404
    
    data = []
    data.append({
        'id': user_data.id,
        'nik': user_data.nik,
        'nama_lengkap': user_data.nama_lengkap,
        'jenis_kelamin': user_data.jenis_kelamin,
        'tanggal_lahir': user_data.tanggal_lahir,
        'alamat': user_data.alamat,
        'no_hp': user_data.no_hp,
        'email': user_data.email,
        'gambar': user_data.gambar
    })
    return jsonify(data)


#Post user data
@app.route('/api/user/add', methods=['POST'])
def add_user_data():
    # new_data = request.get_json()

    user_data = DataPasien(
        nik=request.form['nik'],
        nama_lengkap=request.form['nama_lengkap'],
        jenis_kelamin=request.form['jenis_kelamin'],
        tanggal_lahir=request.form['tanggal_lahir'],
        alamat=request.form['alamat'],
        no_hp=request.form['no_hp'],
        email=request.form['email'],
        gambar="https://res.cloudinary.com/drjnb5zxa/image/upload/v1698804785/TBC/blank-profile.png"
    )

    db.session.add(user_data)
    db.session.commit()

    return jsonify({
        'message': 'Data berhasil ditambahkan!'
    })


#Update user data
@app.route('/api/user/<int:nik>', methods=['PUT'])
def update_user_data(nik):
    user_data = DataPasien.query.filter_by(nik=nik).first()
    if user_data is None:
        return jsonify({'message': 'Data tidak ditemukan!'})
    
    # input_data = request.get_json()
    # fileImg = request.files['gambar']

    if 'gambar' in request.files:
        fileImg = request.files['gambar']
        upload_result = cloudinary.uploader.upload(file=fileImg, folder="TBC/user_profile", public_id=nik, overwrite=True)
        user_data.gambar = upload_result['url']
    
    user_data.alamat = request.form['alamat']
    user_data.no_hp = request.form['no_hp']
    db.session.merge(user_data)
    db.session.commit()

    return jsonify({
        'message': 'Data berhasil diupdate!'
    })






###API Rontgen History
#All Get Rontgen History
@app.route('/api/rontgen', methods=['GET'])
def get_all_rontgen_data():
    rontgen_data = Pemeriksaan.query.all()

    rontgen_data_list = []
    for data in rontgen_data:
        dokter = DataKaryawan.query.get(data.id_dokter)
        rontgen_data_list.append({
            'id': data.id,
            'nik': data.nik,
            'nama_rumah_sakit': data.nama_rumah_sakit,
            'tanggal_pemeriksaan': str(data.tanggal_pemeriksaan),
            'dokter': dokter.nama,
            'gambar_rontgen': data.gambar_rontgen,
            'hasil_analisa': data.hasil_analisa
        })
    return rontgen_data_list

#Get Rontgen History by NIK
@app.route('/api/rontgen/<int:nik>', methods=['GET'])
def get_rontgen_data_nik(nik):
    rontgen_data = Pemeriksaan.query.filter(Pemeriksaan.nik==nik)

    if  rontgen_data is None:
        return jsonify({'message': 'Data tidak ditemukan!'}), 404

    rontgen_data_list = []
    for data in rontgen_data:
        dokter = DataKaryawan.query.get(data.id_dokter)
        rontgen_data_list.append({
            'id': data.id,
            'nik': data.nik,
            'nama_rumah_sakit': data.nama_rumah_sakit,
            'tanggal_pemeriksaan': str(data.tanggal_pemeriksaan),
            'dokter': dokter.nama,
            'gambar_rontgen': data.gambar_rontgen,
            'hasil_analisa': data.hasil_analisa            
        })
    return rontgen_data_list

#add rontgen history
@app.route('/api/rontgen/upload', methods=['POST'])
def add_rontgen_history():
    upload_result = None    # if request.method == 'POST':

    fileImg = request.files['gambar_rontgen']
    if fileImg:
        upload_result = cloudinary.uploader.upload(file=fileImg, folder="TBC/rontgen")
        img = ({
            'url': upload_result['url'],
            'public_id': upload_result['public_id']
        })

        rontgen_history = Pemeriksaan(
            nik= request.form['nik'],
            nama= request.form['nama'],
            nama_rumah_sakit= request.form['nama_rumah_sakit'],
            tanggal_pemeriksaan= request.form['tanggal_pemeriksaan'],
            id_dokter= request.form['id_dokter'],
            gambar_rontgen= img,
            hasil_analisa= request.form['hasil_analisa'],
            status= request.form['status'],
            persentase= request.form['persentase']
        )

        db.session.add(rontgen_history)
        db.session.commit()
        return jsonify({
            'message': 'Data berhasil ditambahkan!'
        })
        # return jsonify(upload_result)

#delete rontgen history
@app.route('/api/rontgen/<int:data_id>', methods=['DELETE'])
def delete_rontgen_hostory(data_id):
    data_to_delete = Pemeriksaan.query.get(data_id)

    if data_to_delete is None:
        return jsonify({'message': 'Data tidak ditemukan!'}), 404

    db.session.delete(data_to_delete)
    db.session.commit()

    return jsonify({'message': 'Data berhasil dihapus!'})





### Start API CRUD Artikel Kesehatan
# Route untuk mengambil artikel (API)
@app.route('/api/artikel', methods=['GET'])
def get_all_tbc_data():
    tbc_data = ArtikelKesehatan.query.all()
    tbc_data_list = []
    for data in tbc_data:
        tbc_data_list.append({
            'id': data.id,
            'judul': data.judul,
            'penulis': data.penulis,
            'isi': data.isi,
            'tanggal_publikasi': str(data.tanggal_publikasi),
            'kategori': data.kategori,
            'gambar': data.gambar
        })
    return tbc_data_list

# Route untuk menambahkan artikel baru (POST)
@app.route('/api/artikel', methods=['POST'])
def add_tbc_data():
    upload_result = None    # if request.method == 'POST':

    # artikel_tbc = ArtikelKesehatan(
    #     judul=new_data['judul'],
    #     penulis=new_data['penulis'],
    #     isi=new_data['isi'],
    #     tanggal_publikasi=new_data['tanggal_publikasi'],
    #     kategori=new_data['kategori'],
    #     gambar=new_data['gambar']
    # )

    # db.session.add(artikel_tbc)
    # db.session.commit()

    # return jsonify({
    #     'message': 'Data berhasil ditambahkan!',
    # })

    fileImg = request.files['gambar']
    if fileImg:
        upload_result = cloudinary.uploader.upload(file=fileImg, folder="TBC/article")
        img = {
            'url': upload_result['url'],
            'public_id': upload_result['public_id']
        }

        artikel_kesehatan = ArtikelKesehatan(
            judul= request.form['judul'],
            penulis= request.form['penulis'],
            isi= request.form['isi'],
            tanggal_publikasi= request.form['tanggal_publikasi'],
            kategori= request.form['kategori'],
            gambar= img,
        )

        db.session.add(artikel_kesehatan)
        db.session.commit()
        return jsonify({
            'message': 'Data berhasil ditambahkan!'
        })

# Route untuk mengupdate artikel (PUT)
@app.route('/api/artikel/<int:data_id>', methods=['PUT'])
def update_tbc_data(data_id):
    data_to_update = ArtikelKesehatan.query.get(data_id)

    if data_to_update is None:
        return jsonify({'message': 'Data tidak ditemukan!'}), 404

    updated_data = request.get_json()

    data_to_update.judul = updated_data['judul']
    data_to_update.penulis = updated_data['penulis']
    data_to_update.isi = updated_data['isi']
    data_to_update.tanggal_publikasi = updated_data['tanggal_publikasi']
    data_to_update.kategori = updated_data['kategori']

    db.session.commit()

    return jsonify({
        'message': 'Data berhasil diupdate!',
    })

# Route untuk menghapus artikel (DELETE)
@app.route('/api/artikel/<int:data_id>', methods=['DELETE'])
def delete_tbc_data(data_id):
    data_to_delete = ArtikelKesehatan.query.get(data_id)

    if data_to_delete is None:
        return jsonify({'message': 'Data tidak ditemukan!'}), 404

    db.session.delete(data_to_delete)
    db.session.commit()

    return jsonify({'message': 'Data berhasil dihapus!'})
### Finish API Mobile



if __name__ == '__main__':
    # app.run(debug=True)
    socketio.run(app, debug=True)
