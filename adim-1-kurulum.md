# Adım 1 — Proje kurulumu

Bu adımda henüz özellik yazmıyoruz. Amacımız: boş ama çalışan bir Django projesi, git kaydı ve PostgreSQL bağlantısı.
Komutları **PowerShell**'de sırayla çalıştırın. Her komuttan sonra ekranda ne yazdığını bana iletin; hata olursa birlikte çözeriz.

---

## 1) Proje klasörüne gidin

```powershell
cd "$env:USERPROFILE\Desktop\bostanhane"
mkdir bostanhane
cd bostanhane
```

Bundan sonra tüm komutlar bu klasörde çalışacak. (Masaüstü\bostanhane → proje dosyaları; içindeki `bostanhane` klasörü → kod.)

## 2) Sanal ortamı kurun ve açın

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Komut satırının başında `(venv)` yazıyorsa ortam açılmış demektir.

> "Bu sistemde betik çalıştırma devre dışı" hatası alırsanız:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```
> deyip `E` (evet) yanıtını verin, sonra `Activate` komutunu tekrar çalıştırın.

## 3) Paketleri kurun

`requirements.txt` dosyasını sizin için hazırladım, klasörde duruyor.

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Kurulanlar ve ne işe yaradıkları:

| Paket | Ne işe yarar |
|---|---|
| Django | Sitenin ve panellerin temeli |
| djangorestframework | Mobil uygulamanın konuşacağı API |
| psycopg | PostgreSQL bağlantısı |
| python-dotenv | Şifre ve anahtarları koddan ayırmak |
| Pillow | Ürün görselleri |
| whitenoise | Canlıda statik dosyalar |
| gunicorn | Canlı sunucuda çalıştırma |

## 4) Django projesini oluşturun

```powershell
django-admin startproject bostanhane .
```

Sondaki nokta önemli: dosyaları bulunduğunuz klasöre kurar, iç içe klasör oluşmaz.

## 5) PostgreSQL veritabanını açın

Masaüstünüzde PostgreSQL kurulum dosyası duruyordu. Kuruluysa şu komutla veritabanını oluşturun (kurulumda belirlediğiniz `postgres` şifresi sorulacak):

```powershell
& "C:\Program Files\PostgreSQL\18\bin\createdb.exe" -U postgres bostanhane
```

Kurulu değilse kurulumu çalıştırın; şifreyi not edin, birazdan `.env` dosyasına yazacağız. (Sürüm numarası farklıysa yoldaki `18` kısmını ona göre düzeltin.)

## 6) `.env` dosyasını oluşturun

Klasörde `env-ornek.txt` adında bir örnek bıraktım. Kopyalayın:

```powershell
Copy-Item env-ornek.txt .env
```

Sonra `.env` dosyasını VS Code'da açıp `DB_PASSWORD` satırına PostgreSQL şifrenizi yazın. **Bu dosya asla git'e gönderilmez**, `.gitignore` ile dışarıda tutuluyor.

## 7) Git deposunu başlatın

```powershell
git init
git add .
git commit -m "Bostanhane: proje iskeleti"
```

## 8) Çalıştığını görün

```powershell
python manage.py migrate
python manage.py runserver
```

Tarayıcıda `http://127.0.0.1:8000` adresine gidin. Django'nun roket görselli karşılama sayfasını görmelisiniz.

Durdurmak için komut satırında `Ctrl + C`.

---

## Bu adım bitince bana şunları iletin

1. `pip install` çıktısının son satırları (hata var mı)
2. `createdb` komutu sorunsuz çalıştı mı
3. `runserver` sonrası tarayıcıda karşılama sayfasını gördünüz mü
4. Klasör listesi:

```powershell
dir
```

## Sırada ne var (Adım 2)

- Ayarların yerel/canlı diye ayrılması ve `.env` bağlantısı
- Veritabanının PostgreSQL'e bağlanması
- `core` ve `hesaplar` uygulamalarının oluşturulması
- İlk modeller: Mağaza, Mahalle, Teslim Takvimi
- Django yönetim paneline giriş ve ilk mağazanın açılması
