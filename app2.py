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
import pickle
import json




app = Flask(__name__)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1
size=224

app.secret_key = "Secrect Key"

# Untuk menghubungkan ke database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:rootku@localhost/rumahtbc'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

# Model untuk tabel karyawan
class AkunKaryawan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nik = db.Column(db.String(16), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    hak_akses = db.Column(db.Enum('dokter', 'admin'), nullable=False)

    def __init__(self, nik, username, password, hak_akses):
        self.nik = nik
        self.username = username
        self.password = password
        self.hak_akses = hak_akses

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
        self.gambar = gambar  # Set nilai gambar dengan nilai yang diberikan atau None jika tidak ada gambar

        
# Model untuk tabel user
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nik = db.Column(db.String(16), unique=True, nullable=False) 
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)

    def __init__(self, nik, username, password, email):
        self.nik = nik
        self.username = username
        self.password = password
        self.email = email

# Model untuk tabel pemeriksaan
class Pemeriksaan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nik_pasien = db.Column(db.String(20), nullable=False)
    tanggal_pemeriksaan = db.Column(db.Date, nullable=False)
    id_dokter = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    persentase = db.Column(db.Float, nullable=True)
    gambar_rontgen = db.Column(db.String(255), nullable=True)
    hasil_analisa = db.Column(db.Text, nullable=True)

    def __init__(self, nik_pasien, tanggal_pemeriksaan, id_dokter, status, persentase=None, gambar_rontgen=None, hasil_analisa=None):
        self.nik_pasien = nik_pasien
        self.tanggal_pemeriksaan = tanggal_pemeriksaan
        self.id_dokter = id_dokter
        self.status = status
        self.persentase = persentase
        self.gambar_rontgen = gambar_rontgen
        self.hasil_analisa = hasil_analisa
        
# untuk tabel input review
class InputReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    review = db.Column(db.Text, nullable=False)

    def __init__(self, nama, email, review):
        self.nama = nama
        self.email = email
        self.review = review
        
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

# Load intents and other required files
intents_file = open('data.json',)
intents = json.load(intents_file)

model = load_model('chatbot_model.h5')
words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))

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


# Fungsi route untuk halaman index
@app.route("/")
def index():
    # Ambil 4 data terbaru dari tabel Artikel
    latest_articles = ArtikelKesehatan.query.order_by(ArtikelKesehatan.tanggal_publikasi.desc()).limit(4).all()
    active = 'home'
    return render_template('index.html', latest_articles=latest_articles, aktif=active)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form['user_message']
    print(f"Received user message: {user_message}")  # Tambahkan baris ini
    ints = predict_class(user_message, model)
    response = get_response(ints, intents)
    print(f"Generated response: {response}")  # Tambahkan baris ini
    return jsonify({'response': response})

# Fungsi route untuk memproses halaman login 
@app.route('/loginadmin', methods=['GET', 'POST'])
def loginadmin():
    if 'username' in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = AkunKaryawan.query.filter_by(username=username).first()

        print(f"Upaya login untuk username: {username}, password: {password}")
        print(f"User ditemukan: {user}")
        
        if user and check_password_hash(user.password, password):
            session['username'] = username  # Set the username in the session
            session['hak_akses'] = user.hak_akses 
            print(f"Login berhasil untuk username: {username}")
            flash('Login berhasil!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login gagal. Periksa kembali username dan password Anda.', 'danger')

    return render_template('login_admin.html')

# Fungsi route untuk halaman home dokter/admin
@app.route('/home')
def home():
    active = 'home'
    if 'username' in session:
        hak_akses = session.get('hak_akses')

        if hak_akses is not None:
            if hak_akses == 'admin':
                return render_template('admin_dashboard.html', username=session['username'], aktif=active)
            elif hak_akses == 'dokter':
                return render_template('dokter_dashboard.html', username=session['username'], aktif=active)
            else:
                flash('Hak akses tidak valid.', 'danger')
                return redirect(url_for('logout'))
        else:
            flash('Hak akses tidak tersedia.', 'danger')
            return redirect(url_for('logout'))
    else:
        flash('Anda harus login terlebih dahulu.', 'warning')
        return redirect(url_for('loginadmin'))

# Fungsi route untuk keluar halaman admin/dokter
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('loginadmin'))


# Fungsi route untuk halaman deteksi dokter
@app.route('/dokter/deteksi')
def dokter_deteksi():
    active = 'deteksi'
    return render_template('dokter_deteksi.html', aktif=active)

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
@app.route('/admin/artikel/form')
def admin_artikel_form():
    active = 'artikel'
    return render_template('admin_artikelform.html', aktif=active)

# Fungsi route untuk halaman daftar pasien admin
@app.route('/admin/pasien')
def admin_pasiendaftar():
    active = 'pasien'
    return render_template('admin_pasiendaftar.html', aktif=active)

# fungsi route untuk halaman daftar biki akun dokter/ admin
@app.route('/admin/akunkaryawan')
def admin_akunkaryawan():
    active = 'akunkaryawan'
    return render_template('admin_akunkaryawan.html', aktif=active)

# Fungsi route untuk halaman tentang user
@app.route('/tentang')
def tentang():
    active = 'tentang'
    return render_template('tentang.html', aktif=active)

# Fungsi route untuk halaman riwayat user
@app.route('/riwayatuser')
def riwayatuser():
    active = 'riwayat'
    return render_template('riwayatuser.html', aktif=active)

# Fungsi route untuk halaman artikel kesehatan user
@app.route('/artikel')
def artikel():
    latest_articles = ArtikelKesehatan.query.order_by(ArtikelKesehatan.tanggal_publikasi.desc()).limit(10).all()
    active = 'artikel'
    return render_template('artikel.html', latest_articles=latest_articles, aktif=active)

# Fungsi route untuk halaman pendaftaran user
@app.route('/register')
def register():
    return render_template('register.html')

# Fungsi route untuk halaman login user
@app.route('/login')
def login():
    return render_template('login.html')

# Fungsi route untuk halaman  detail artikel
@app.route('/detailartikel')
def detailartikel():
    return render_template('detailartikel2.html')

# Fungsi route untuk halaman artikel kesehatan user
@app.route('/detailartikel/<int:article_id>')
def artikel_by_id(article_id):
    article = ArtikelKesehatan.query.filter_by(id=article_id).first_or_404()
    return render_template('detailartikel.html', article=article)

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
            'kategori': data.kategori
        })
    return jsonify(tbc_data_list)

# Route untuk menambahkan artikel baru (POST)
@app.route('/api/artikel', methods=['POST'])
def add_tbc_data():
    new_data = request.get_json()

    artikel_tbc = ArtikelKesehatan(
        judul=new_data['judul'],
        penulis=new_data['penulis'],
        isi=new_data['isi'],
        tanggal_publikasi=new_data['tanggal_publikasi'],
        kategori=new_data['kategori']
    )

    db.session.add(artikel_tbc)
    db.session.commit()

    return jsonify({'message': 'Data berhasil ditambahkan!'})

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

    return jsonify({'message': 'Data berhasil diupdate!'})

# Route untuk menghapus artikel (DELETE)
@app.route('/api/artikel/<int:data_id>', methods=['DELETE'])
def delete_tbc_data(data_id):
    data_to_delete = ArtikelKesehatan.query.get(data_id)

    if data_to_delete is None:
        return jsonify({'message': 'Data tidak ditemukan!'}), 404

    db.session.delete(data_to_delete)
    db.session.commit()

    return jsonify({'message': 'Data berhasil dihapus!'})
### Finish API CRUD Artikel Kesehatan

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

# API untuk memproses deteksi TBC dokter
@app.route("/api/dokter/upload", methods=['POST'])
def dokter_upload():
    # Memuat Model Deep Learning
    model = load_model('modelTBC.h5')
    print("model_loaded")

    # Mengatur Direktori Target untuk Berkas yang Diunggah
    target = os.path.join(APP_ROOT, 'static/xray/')

    # Membuat Direktori Target Jika Belum Ada
    if not os.path.isdir(target):
        os.mkdir(target)

    try:
        # Menyimpan Berkas yang Diunggah
        file = request.files['file']
        filename = file.filename
        destination = os.path.join(target, filename)
        file.save(destination)

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

        # Membuat respons JSON
        classes = ['Negative', 'Positive']
        predicted = classes[result[0]]
        response_data = {
            'prediction': predicted,
            'positive_probability': float(pos),
            'negative_probability': float(neg),
            'filename': filename
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)})


# Bikin
@app.route('/adduser', methods=['GET', 'POST'])
def add_user():    
    if request.method == 'POST':
        nik = request.form['nik']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = Users(nik=nik, username=username, password=hashed_password, email=email)
        db.session.add(new_user)
        db.session.commit()

        flash('User added successfully!', 'success')
        return redirect(url_for('home'))

    return render_template('add_user.html')


@app.route('/add_karyawan', methods=['GET', 'POST'])
def add_karyawan():
    if request.method == 'POST':
        nik = request.form['nik']
        username = request.form['username']
        password = request.form['password']
        hak_akses = request.form['hak_akses']

        hashed_password = generate_password_hash(password)

        akun_karyawan = AkunKaryawan(nik=nik, username=username, password=hashed_password, hak_akses=hak_akses)
        db.session.add(akun_karyawan)
        db.session.commit()
        return redirect(url_for('loginadmin'))

    return render_template('add_akun_karyawan.html')

@app.route('/tambah_review', methods=['POST'])
def tambah_review():
    if request.method == 'POST':
        nama = request.form['name']
        email = request.form['email']
        review_text = request.form['message']

        # Memastikan semua data yang diperlukan telah diberikan
        if nama and email and review_text:
            try:
                new_review = InputReview(nama=nama, email=email, review=review_text)
                db.session.add(new_review)
                db.session.commit()
                flash('Ulasan dari kamu sudah terkirim. Terima kasih!', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                flash(f'Error: {str(e)}', 'error')
                return redirect(url_for('index'))
        else:
            return jsonify({'status': 'error', 'message': 'Semua field harus diisi'}), 400


if __name__ == '__main__':
    app.run(debug=True)
