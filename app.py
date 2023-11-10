from flask import Flask, render_template, jsonify,request
import os,cv2
from keras.models import Model,load_model
# from keras.preprocessing.image import img_to_array
from tensorflow.keras.utils import img_to_array
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


app = Flask(__name__)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1
size=224

app.secret_key = "Secrect Key"

# Untuk menghubungkan ke database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:rootku@localhost/rumahtbc'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Model untuk tabel artikel kesehatan
class ArtikelKesehatan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(100), nullable=False)
    penulis = db.Column(db.String(100), nullable=False)
    isi = db.Column(db.Text, nullable=False)
    tanggal_publikasi = db.Column(db.Date, nullable=False)
    kategori = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp(), nullable=False)
    
    def __init__(self, judul, penulis, isi, tanggal_publikasi, kategori):
        self.judul = judul
        self.penulis = penulis
        self.isi = isi
        self.tanggal_publikasi = tanggal_publikasi
        self.kategori = kategori
        
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

# Untuk membuat tabel di database
with app.app_context():
    db.create_all()

# Fungsi untuk memproses gambar
def processimg(img):
    img=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    img = cv2.resize(img, (size, size)) 
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    equalized_img = clahe.apply(img)
    crop=cv2.resize(equalized_img,(size,size))
    return crop

# Fungsi route untuk halaman index
@app.route("/")
def index():
    return render_template("index.html")

# Fungsi route untuk halaman home
@app.route('/home')
def home():
    return render_template('dashboard_dokter.html')

# Fungsi route untuk halaman deteksi dokter
@app.route('/deteksi')
def deteksi():
    return render_template('deteksi_dokter.html')

# Fungsi route untuk halaman tentang user
@app.route('/tentang')
def tentang():
    return render_template('tentang.html')

# Fungsi route untuk halaman riwayat user
@app.route('/riwayatuser')
def riwayatuser():
    return render_template('riwayatuser.html')

@app.route('/artikel')
def artikel():
    return render_template('artikel.html')

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
@app.route("/upload", methods=['POST'])
def upload():
    model=load_model('modelTBC.h5')   
    print("model_loaded")
    target = os.path.join(APP_ROOT, 'static/xray/')
    if not os.path.isdir(target):
        os.mkdir(target)
    filename = ""
    for file in request.files.getlist("file"):
        filename = file.filename
        destination = "/".join([target, filename])
        file.save(destination)
    img = cv2.imread(destination)
    cv2.imwrite('static/xray/file.png',img)
    img= processimg(img)
    cv2.imwrite('static/xray/processedfile.png',img)
    img = img.astype('uint8')
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    img = img_to_array(img)
    img = cv2.resize(img,(size,size))
    img=img.reshape(1,size,size,3)
    img = img.astype('float32')
    img = img / 255.0
    # result = model.predict_classes(img)
    result = np.argmax(model.predict(img), axis=-1)
    pred=model.predict(img)
    neg=pred[0][0]
    pos=pred[0][1]
    classes=['Negative','Positive']
    predicted=classes[result[0]]
    plot_dest = "/".join([target, "result.png"])

    return render_template("hasildeteksi_dokter.html", pred=predicted,pos=pos,neg=neg, filename=filename)

if __name__ == '__main__':
    app.run(debug=True)
