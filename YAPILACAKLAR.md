# Yapılacaklar — adım adım

Hedef: bugünün sonunda **bostanhane.com canlıda**, üzerinde gerçek bir "yakında" sayfası ve
yönetim paneli çalışıyor olsun. Aşağıdaki dört aşamayı sırayla yapın.

Her aşamanın sonunda **"bana gönderin"** yazan şeyi bana iletin; hatalıysa birlikte düzeltiriz.

---

# AŞAMA A — Bilgisayarda çalışır hale getirme (15 dk)

VS Code'u açın → **File → Open Folder** → `Masaüstü\bostanhane\bostanhane`
→ **Terminal → New Terminal**. Komutları oraya yazın.

### A1. Sanal ortamı açın
```powershell
.\venv\Scripts\Activate.ps1
```
Satır başında `(venv)` görünmeli.

### A2. Django kurulu mu bakın
```powershell
python -m django --version
```
Hata verirse:
```powershell
pip install -r requirements.txt
```

### A3. Django projesini oluşturun
```powershell
python -m django startproject bostanhane .
```
Sondaki **nokta** şart. Sol taraftaki dosya listesinde `manage.py` belirmeli.

### A4. Ayar dosyalarını yerine koyun
```powershell
Copy-Item env-ornek.txt .env -Force
Copy-Item hazir\settings.py bostanhane\settings.py -Force
Copy-Item hazir\urls.py bostanhane\urls.py -Force
```

### A5. core uygulamasını oluşturun ve dosyalarını koyun
```powershell
python manage.py startapp core
Copy-Item hazir\core_models.py core\models.py -Force
Copy-Item hazir\core_admin.py core\admin.py -Force
Copy-Item hazir\core_views.py core\views.py -Force

New-Item -ItemType Directory -Force -Path core\management\commands | Out-Null
New-Item -ItemType File -Force -Path core\management\__init__.py | Out-Null
New-Item -ItemType File -Force -Path core\management\commands\__init__.py | Out-Null
Copy-Item hazir\ornek_veri.py core\management\commands\ornek_veri.py -Force
Copy-Item hazir\ilk_yonetici.py core\management\commands\ilk_yonetici.py -Force

New-Item -ItemType Directory -Force -Path templates\core | Out-Null
Copy-Item hazir\ana_sayfa.html templates\core\ana_sayfa.html -Force
```

### A6. Veritabanını kurun ve örnek veriyi oluşturun
```powershell
python manage.py makemigrations core
python manage.py migrate
python manage.py createsuperuser
python manage.py ornek_veri
```
`createsuperuser` kullanıcı adı, e-posta ve şifre soracak. Şifre yazarken ekranda görünmez, normaldir.

### A7. Çalıştırın
```powershell
python manage.py runserver
```
Tarayıcıda iki adrese bakın:
- `http://127.0.0.1:8000` → **yakında sayfası** (logo, dört adım, e-posta formu)
- `http://127.0.0.1:8000/yonetim/` → **yönetim paneli** (mağaza, mahalleler, teslim takvimi)

Durdurmak için terminalde **Ctrl + C**.

> **Bana gönderin:** iki sayfanın açıldığını doğrulayın; hata varsa terminaldeki son satırları yapıştırın.

---

# AŞAMA B — Kodu GitHub'a koyma (10 dk)

Railway, kodu GitHub'dan alır. Bu yüzden önce oraya koyacağız.

### B1. GitHub'da boş depo açın
1. github.com → giriş yapın
2. Sağ üstteki **+** → **New repository**
3. Repository name: `bostanhane`
4. **Private** seçin (kod herkese açık olmasın)
5. Aşağıdaki kutulardan **hiçbirini işaretlemeyin** (README, .gitignore, license)
6. **Create repository**

### B2. Kodu gönderin
Açılan sayfadaki adresi kopyalayın (`https://github.com/kullaniciadiniz/bostanhane.git` gibi),
sonra terminalde:

```powershell
git init
git add .
git commit -m "Bostanhane: ilk surum"
git branch -M main
git remote add origin https://github.com/KULLANICIADINIZ/bostanhane.git
git push -u origin main
```

`KULLANICIADINIZ` kısmını kendi adınızla değiştirin. Kullanıcı adı ve şifre sorarsa,
tarayıcıda GitHub girişi açılır; oradan onaylayın.

> **Kontrol:** GitHub'daki depo sayfasını yenileyin; dosyalar görünmeli.
> `.env` dosyası **görünmemeli** — şifreler orada, git'e gitmiyor. Görünüyorsa bana haber verin.

---

# AŞAMA C — Railway'e yayınlama (20 dk)

### C1. Proje oluşturun
1. railway.com → **Login with GitHub**
2. **New Project** → **Deploy from GitHub repo** → `bostanhane` deposunu seçin
3. Railway kurulumu başlatır. İlk denemede hata verebilir, normaldir — değişkenleri girmedik henüz

### C2. Veritabanı ekleyin
Proje ekranında **+ New** → **Database** → **PostgreSQL**. Birkaç saniyede hazır olur.

### C3. Ortam değişkenlerini girin
Web servisine tıklayın → **Variables** sekmesi → aşağıdakileri tek tek ekleyin:

| Değişken | Değer |
|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (aynen böyle yazın, Railway kendi doldurur) |
| `DJANGO_SECRET_KEY` | 50 karakterlik rastgele bir metin |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `bostanhane.com,www.bostanhane.com` |
| `YONETICI_KULLANICI` | `ersin` |
| `YONETICI_EPOSTA` | kendi e-postanız |
| `YONETICI_SIFRE` | güçlü bir şifre (sonra değiştireceğiz) |

> `DJANGO_DEBUG=False` önemli: hata sayfalarında kodunuzun içi ziyaretçilere görünmez.

### C4. Yayına alın
**Deployments** sekmesinde **Redeploy** deyin. Kurulum bitince yeşil olmalı.

### C5. Geçici adresi açın
**Settings → Networking → Generate Domain**. Railway size `bostanhane-production-xxxx.up.railway.app`
gibi bir adres verir. Tıklayın — yakında sayfası açılmalı.

> Adres "Bad Request (400)" verirse: `DJANGO_ALLOWED_HOSTS` değişkenine bu geçici adresi de ekleyin
> (virgülle ayırarak) ve tekrar deploy edin.

### C6. Yönetici hesabını ve örnek veriyi oluşturun
Railway panelinde servisin üç nokta menüsünden bir komut çalıştırma alanı vardır
(**Command / Run command**). Şu ikisini sırayla çalıştırın:

```
python manage.py ilk_yonetici
python manage.py ornek_veri
```

Sonra `geçici-adres/yonetim/` sayfasından giriş yapın.

> **Bana gönderin:** geçici Railway adresi.

---

# AŞAMA D — bostanhane.com'u bağlama (15 dk + bekleme)

### D1. Railway'de alan adını tanıtın
Servis → **Settings → Networking → Custom Domain** → `bostanhane.com` yazın.
Railway size iki şey verir:
- bir **CNAME hedefi** (`xxxx.up.railway.app` gibi)
- bir **TXT kaydı** (sahiplik doğrulaması için)

Aynı işlemi `www.bostanhane.com` için de yapın.

### D2. Squarespace'te kayıtları girin
Squarespace → **Domains** → bostanhane.com → **DNS Settings** → **Add record**:

| Tip | Host | Değer |
|---|---|---|
| ALIAS | `@` | Railway'in verdiği CNAME hedefi |
| CNAME | `www` | Railway'in verdiği CNAME hedefi |
| TXT | Railway'in söylediği host | Railway'in verdiği doğrulama değeri |

Kök alan adında (`@`) CNAME kullanılamaz; Squarespace bunun için **ALIAS** sunar, o yüzden ALIAS seçiyoruz.
Kayıtların **TTL** değerini `300` yapın.

### D3. Bekleyin ve kontrol edin
Yayılma genelde 10–60 dakika sürer. Railway'deki alan adı satırı yeşile döner ve SSL sertifikası
otomatik kurulur. Sonra `https://bostanhane.com` adresini açın.

> **Bana gönderin:** site açıldı mı, adres çubuğunda kilit simgesi var mı.

---

## Sonrası

Bu dördü bittiğinde şu düzen kurulmuş olur: bilgisayarınızda yazarsınız, `git push` dersiniz,
Railway otomatik yayınlar. Yani her adımda yaptığımız iş birkaç dakika içinde canlıda görünür.

**Bir hatırlatma:** Yakında sayfasına arama motorlarına kapatan bir satır koydum
(`noindex`). Site tamamlanınca o satırı sileceğiz; yarım sayfaların Google'a düşmesi
markanın ilk izlenimini bozar.

Sıradaki geliştirme adımı: `hesaplar` uygulaması — kullanıcı, roller ve üye adresi.
