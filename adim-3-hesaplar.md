# Adım 3 — hesaplar: kullanıcı, roller, adres

Bu adımın sonunda yönetim panelinde **Kullanıcılar** ve **Adresler** bölümleri olacak;
beş rol tanımlı, personel mağazaya bağlı, üyelerin teslimat adresi mahalleye bağlı olacak.

Giriş anahtarı **telefon numarası**. Kullanıcı adı diye bir şey yok.

---

## Önce bilinmesi gereken tek şey

Django'da kullanıcı modeli projenin en temel taşıdır; sonradan değiştirilince bütün yetki
tabloları bozulur. Bu yüzden **veritabanını sıfırdan kuruyoruz** — hem bilgisayarda hem canlıda.

Şu an bunun maliyeti yok: sistemde sadece sizin yönetici hesabınız ve örnek mahalleler var.
Gerçek müşteri girdikten sonra aynı işi yapmak günler alırdı.

⚠️ Silmeden önce **canlıdaki ilgi kayıtlarına bakın**: `bostanhane.com/yonetim/` → İlgi kayıtları.
İçinde kayıt varsa not alın; sıfırlamada silinecekler.

---

# AŞAMA A — Bilgisayarda (20 dk)

VS Code → `Masaüstü\bostanhane\bostanhane` klasörü → Terminal.

### A1. Sanal ortamı açın

```powershell
.\venv\Scripts\Activate.ps1
```

Satır başında `(venv)` görünmeli.

### A2. hesaplar uygulamasını oluşturun

```powershell
python manage.py startapp hesaplar
```

### A3. Hazır dosyaları yerine koyun

```powershell
Copy-Item hazir\settings.py bostanhane\settings.py -Force
Copy-Item hazir\core_admin_araclar.py core\admin_araclar.py -Force
Copy-Item hazir\hesaplar_models.py hesaplar\models.py -Force
Copy-Item hazir\hesaplar_admin.py hesaplar\admin.py -Force
Copy-Item hazir\hesaplar_apps.py hesaplar\apps.py -Force
Copy-Item hazir\hesaplar_izinler.py hesaplar\izinler.py -Force
Copy-Item hazir\ilk_yonetici.py core\management\commands\ilk_yonetici.py -Force
Copy-Item hazir\ilk_veri.py core\management\commands\ilk_veri.py -Force
Copy-Item hazir\Procfile Procfile -Force
```

### A4. hesaplar için komut klasörünü açın

```powershell
New-Item -ItemType Directory -Force -Path hesaplar\management\commands | Out-Null
New-Item -ItemType File -Force -Path hesaplar\management\__init__.py | Out-Null
New-Item -ItemType File -Force -Path hesaplar\management\commands\__init__.py | Out-Null
Copy-Item hazir\roller_kur.py hesaplar\management\commands\roller_kur.py -Force
Copy-Item hazir\ornek_hesaplar.py hesaplar\management\commands\ornek_hesaplar.py -Force
```

### A5. Veritabanını sıfırlayın

```powershell
Remove-Item bostanhane.sqlite3 -Force -ErrorAction SilentlyContinue
Remove-Item db.sqlite3 -Force -ErrorAction SilentlyContinue
```

> `db.sqlite3` eski bir artık dosya; silinmesi iyi oldu.

### A6. Kurun

```powershell
python manage.py makemigrations hesaplar
python manage.py migrate
python manage.py roller_kur
python manage.py createsuperuser
python manage.py ornek_veri
python manage.py ornek_hesaplar
```

`createsuperuser` artık **telefon** soracak. 10 hane, başında sıfır olmadan: `5321112233`.
Sonra ad soyad ve şifre isteyecek. Şifre yazarken ekranda görünmez, normaldir.

### A7. Çalıştırın ve bakın

```powershell
python manage.py runserver
```

`http://127.0.0.1:8000/yonetim/` adresine telefonunuzla girin. Görmeniz gerekenler:

- **Hesaplar → Kullanıcılar**: bir süper admin (siz), bir mağaza yöneticisi, bir paketleme
  elemanı, bir kurye ve iki üye. Rol ve mağaza sütunları dolu.
- **Hesaplar → Adresler**: iki üyenin ev adresi, mahalleleriyle birlikte.
- Bir kullanıcıya tıklayın: altta **adresler** bölümü var, oradan adres ekleyip
  çıkarabiliyorsunuz.
- **Kullanıcı ekle** sayfasında telefonu `0532 111 22 33` diye boşluklu yazsanız da kabul eder,
  kaydederken düzeltir.

> Örnek personel ve üyeler **şifresiz** oluşturuldu; hiçbiri giriş yapamaz.
> Denemek isterseniz panelden birine şifre verin.

> **Bana gönderin:** Kullanıcılar listesi açıldı mı, altı kişi görünüyor mu.
> Hata çıkarsa terminaldeki son satırları yapıştırın.

---

# AŞAMA B — GitHub'a gönderin (2 dk)

```powershell
git add .
git commit -m "Adim 3: hesaplar uygulamasi - kullanici, roller, adres"
git push
```

Railway bunu görüp otomatik dağıtıma başlar — ama önce veritabanını değiştirmemiz gerekiyor,
yoksa hata verir. Hemen C aşamasına geçin.

---

# AŞAMA C — Canlı veritabanını yenileyin (15 dk)

Kullanıcı modeli değiştiği için eski PostgreSQL'i kullanamıyoruz.

### C1. Eski veritabanını silin

Railway → projeniz → **Postgres** servisine tıklayın → sağ üst **⋮** → **Delete service** →
onaylayın.

### C2. Yenisini ekleyin

**+ New** → **Database** → **PostgreSQL**. Adının `Postgres` olduğundan emin olun.

### C3. Web servisinin değişkenlerini güncelleyin

Web servisi → **Variables**. Şunları kontrol edin / düzeltin:

| Değişken | Değer |
|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` — yeni servisin adı farklıysa buradaki adı da düzeltin |
| `YONETICI_TELEFON` | **yeni** — 10 hane: `5321112233` |
| `YONETICI_AD` | **yeni** — `Ersin Öztürk` |
| `YONETICI_SIFRE` | güçlü bir şifre (girdikten sonra değiştirip bu değişkeni sileceğiz) |
| `YONETICI_KULLANICI` | **silin** — artık kullanılmıyor |

Diğerleri (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`) aynı kalıyor.

### C4. Yayına alın

**Deployments** → **Redeploy**. Kurulum sırasında sunucu şunları kendi yapar:

```
migrate → collectstatic → roller_kur → ilk_yonetici → ilk_veri → gunicorn
```

Yani tabloları kurar, yetki gruplarını oluşturur, yönetici hesabınızı açar ve Beyşehir
mağazasıyla üç mahalleyi yazar. Elle komut çalıştırmanız gerekmiyor.

### C5. Kontrol edin

- `https://www.bostanhane.com` → **mahalle listesi artık görünmeli** (Yeni Mahalle, Müftü,
  Bahçelievler ve teslim günleri). Önceden boştu, çünkü canlı veritabanında mahalle yoktu.
- `https://www.bostanhane.com/yonetim/` → telefonunuzla giriş yapın.
- Girdikten sonra sağ üstten şifrenizi değiştirin, ardından Railway'den `YONETICI_SIFRE`
  değişkenini silin.

> **Bana gönderin:** ana sayfada mahalleler göründü mü, panele girebildiniz mi.

---

## Bu adımda ne kuruldu

**Kullanıcı** — telefonla giriş, ad soyad, isteğe bağlı e-posta, rol, bağlı mağaza,
telefon doğrulandı işareti, KVKK onay zamanı, kampanya izni.

**Beş rol** — Süper Admin, Mağaza Yöneticisi, Paketleme Elemanı, Kurye, Üye.
Rol seçilince yetkiler kendiliğinden bağlanır; kırk kutucuk işaretlemek gerekmez.

**Yönetim paneline kim girer** — süper admin ve mağaza yöneticisi. Paketleme elemanı ve kurye
girmez; onlar için ayrı, sade ekranlar yapacağız (tablet ve telefon için).

**Mağaza izolasyonu** — mağaza yöneticisi yalnızca kendi mağazasının personelini ve kendi
mahallelerindeki üyeleri görür. Bu kısıtlama sorgu seviyesinde; adres çubuğuna başka bir
kaydın numarasını yazmak işe yaramaz. Ayrıca yetki kutucuklarını hiç görmez — kendini süper
admin yapamaz.

**Adres** — mahalleye bağlı. Bina/kat/daire ayrı alanlarda (etiket basarken işe yarayacak),
kuryeye not alanı var, haritadan iğne için enlem-boylam var. İlk adres otomatik varsayılan
olur, varsayılan her zaman tektir.

---

## Sırada ne var

**Adım 4 — katalog:** kategori, ürün, birim (kilogram / adet / demet), tartılı mı değil mi,
satış adımı (500 g'dan itibaren), fiyat, stok ve kanal bayrakları (yerel teslimat / kargo /
kurumsal). Bu adımdan sonra panelde gerçek ürün listesi olacak.

**Adım 5 — siparis:** sepet, sipariş, kesim işlemi ve alım listesi. İşin kalbi burada.
