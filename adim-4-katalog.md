# Adım 4 — katalog: kategori, ürün, fiyat

Bu adımın sonunda panelde **50 ürün** olacak: kategorileriyle, birimleriyle, hangisinin
tartılı olduğu, hangisinin kargoyla gidebileceği belli. Fiyatları panelden tek ekranda
gireceksiniz.

---

## Üç model, neden üç

**Kategori** — "Sebze", "Yeşillik", "Yöresel ürün". Sitede gruplama başlığı.

**Ürün** — ürünün kendisi: domates nedir, kilogramla mı satılır, tartılı mı, kaç gün
dayanır, hangi kanallarda satılabilir. **Fiyat burada değil.**

**Mağaza ürünü** — o ürünün bir mağazadaki hali: fiyatı, stok durumu, satışta mı.

Ayrımın sebebi: domates Beyşehir'de 32,90 ₺, Karaman'da 29,90 ₺ olabilir; biri
tükenmişken diğerinde bulunabilir. Ürünün tanımı her yerde aynıdır, fiyatı değildir.
Mahalle ile hizmet mahallesi ayrımının aynısı.

### Fiyatsız ürün kaydedilir, satışa açılamaz

Listeyi fiyatsız içeri alıyoruz, fiyatları panelden giriyorsunuz. Fiyatı olmayan bir
ürün **satışa açılamaz** — sistem izin vermiyor. Yanlışlıkla fiyatsız ürün satışa
çıkmasın.

### Kargo kuralı kodda duruyor

Bir ürünü kargoya açmak için dört şart birden sağlanmalı:

1. Raf ömrü en az **14 gün**
2. Soğuk zincir **istemiyor**
3. **Tartısız** — sabit ağırlıklı ambalajda
4. Ambalajı dayanıklı

İlk üçünü sistem denetliyor. Panelde çabuk bozulan bir ürünü kargoya açmaya
kalkarsanız kaydetmiyor, sebebini yazıyor. Dördüncüsü gözle kontrol — cam kavanoza
ek koruma kararını siz vereceksiniz.

### Provizyon hesabı buraya girdi

Tartılı üründe karttan bloke edilecek tutar: `fiyat × miktar × (1 + tampon)`.

Domates 32,90 ₺/kg ise 1 kg sipariş için 37,84 ₺ bloke edilir. Tartıda 940 g
çıkarsa 30,93 ₺ çekilir, kalanı serbest bırakılır.

Tampon oranı **panelden** ayarlanıyor (aşağıdaki bölüm).

---

## Satış ayarları — eşikler panelden düzenlenir

Panelde **CORE → Satış ayarları** diye yeni bir bölüm var. Mağaza başına bir kayıt:

| Ayar | Değer | Ne yapar |
|---|---|---|
| Minimum sepet tutarı | 500 ₺ | Altındaki sepetle sipariş verilemez |
| Teslimat ücreti | 50 ₺ | Her siparişe eklenir |
| Ücretsiz teslimat eşiği | 1000 ₺ | Üstündeki siparişte teslimat alınmaz |
| Provizyon tamponu | %15 | Tartılı üründe karttan fazladan bloke edilen pay |
| Otomatik teslim onayı | 24 saat | Üye onay vermezse ne zaman onaylanmış sayılır |
| Talep açma süresi | 24 saat | Teslimden sonra iade/şikâyet süresi |

Üç sayı **listede doğrudan düzenlenebiliyor**: yazın, sayfanın altındaki Kaydet'e
basın, hepsi birden kaydedilir. Sayfa açmanız gerekmiyor.

Listede bir **örnek** sütunu var: "500 ₺ altı kapalı · 1000 ₺ üstü ücretsiz" diye
yazarak ayarın müşteriye nasıl yansıdığını gösterir.

**Mağaza başına ayrı olmasının sebebi:** Karaman açıldığında teslimat ücreti farklı
olabilir — mesafe ve mahalle yoğunluğu aynı değil. Yeni mağaza açtığınızda ayar kaydı
kendiliğinden oluşuyor, varsayılanlarla.

İki not:

- **Ücretsiz teslimat eşiğini boş bırakırsanız** ücretsiz teslimat hiç olmaz; her
  siparişten teslimat ücreti alınır.
- **Eşiği minimum sepetin altına yazamazsınız.** O halde her sipariş ücretsiz teslimat
  alırdı; muhtemelen kaza olacağı için sistem kabul etmiyor. Gerçekten her siparişte
  ücretsiz teslimat istiyorsanız teslimat ücretini 0 yapın — daha anlaşılır olur.

---

# AŞAMA A — Bilgisayarda (15 dk)

VS Code → Terminal, `(venv)` görünüyor olmalı.

### A1. Yeni paketi kurun

Excel okumak için `openpyxl` gerekiyor:

```powershell
pip install -r requirements.txt
```

### A2. katalog uygulamasını oluşturun

```powershell
python manage.py startapp katalog
```

### A3. Dosyaları yerine koyun

```powershell
Copy-Item hazir\settings.py bostanhane\settings.py -Force
Copy-Item hazir\katalog_models.py katalog\models.py -Force
Copy-Item hazir\katalog_admin.py katalog\admin.py -Force
Copy-Item hazir\katalog_apps.py katalog\apps.py -Force
Copy-Item hazir\hesaplar_izinler.py hesaplar\izinler.py -Force
Copy-Item hazir\requirements.txt requirements.txt -Force

New-Item -ItemType Directory -Force -Path katalog\management\commands | Out-Null
New-Item -ItemType File -Force -Path katalog\management\__init__.py | Out-Null
New-Item -ItemType File -Force -Path katalog\management\commands\__init__.py | Out-Null
Copy-Item hazir\urun_yukle.py katalog\management\commands\urun_yukle.py -Force
```

### A4. Veritabanını güncelleyin

```powershell
python manage.py makemigrations core
python manage.py makemigrations katalog
python manage.py migrate
python manage.py roller_kur
python manage.py ornek_veri
```

`makemigrations core` → **satış ayarları** tablosunu kurar (aşağıda anlatılıyor).
`roller_kur` yeni yetkileri mağaza yöneticisi grubuna ekler.
`ornek_veri` var olan mağazaya satış ayarları kaydını açar ve şu satırı yazar:

```
  Satış ayarları: minimum 500 ₺ · teslimat 50 ₺ · ücretsiz eşiği 1000 ₺ (panelden değiştirilir)
```

### A5. Ürünleri içeri alın

Önce ne olacağına bakın — hiçbir şey kaydetmez:

```powershell
python manage.py urun_yukle --kuru_prova
```

Sonra gerçekten:

```powershell
python manage.py urun_yukle
```

Beklenen son satırlar:

```
50 yeni ürün, 0 güncellenen, 6 yeni kategori, 0 fiyat yazıldı.

50 ürünün fiyatı yok, bu yüzden satışa açılmadı.
Fiyatları panelden girebilirsiniz: /yonetim/katalog/magazaurun/
```

Dosyayı başka yere koyduysanız: `python manage.py urun_yukle --dosya "C:\yol\urunler.xlsx"`

### A6. Bakın

```powershell
python manage.py runserver
```

`http://127.0.0.1:8000/yonetim/` → **KATALOG** bölümü:

- **Kategoriler** — 6 kategori, sıraları listeden değiştirilebilir
- **Ürünler** — 50 ürün. Satış sütununda "kilogram · 500 g'dan itibaren" gibi
  yazıyor, kanal sütununda "Yerel · Kargo · Kurumsal"
- **Mağaza ürünleri** — fiyat girme ekranı

> **Bana gönderin:** `urun_yukle` çıktısının son satırları ve üç listenin açıldığının onayı.

---

# AŞAMA B — Fiyatları girin (Ersin, 20–30 dk)

**Mağaza ürünleri** listesine girin. Burada 50 satır var ve üç sütun doğrudan
listede düzenlenebiliyor: **fiyat**, **durum**, **satışta**.

Yani sayfa sayfa dolaşmanıza gerek yok: fiyatları yukarıdan aşağı yazın, satmaya
hazır olanların **satışta** kutucuğunu işaretleyin, sayfanın altındaki **Kaydet**
düğmesine bir kez basın. Hepsi birlikte kaydedilir.

Kolaylıklar:

- Sağ üstteki **kategori** süzgeciyle önce sebzeleri, sonra meyveleri girebilirsiniz
- **müşteriye görünen** sütunu fiyatı `32,90 ₺` biçiminde gösterir — yazdığınızın
  müşteride nasıl göründüğünü anında görürsünüz
- Fiyatı olmayan satırda kırmızı **fiyat girilmedi** yazar
- İndirim yapacaksanız **eski fiyat** alanını doldurun; üstü çizili görünür ve
  yüzde kaç indirim olduğunu sistem hesaplar
- Mevsimi geçen ürünü silmeyin: durumunu **Mevsim dışı** yapın. Yılın o ayı gelince
  geri açarsınız, fiyat geçmişi kaybolmaz

Fiyatları Excel'de doldurmayı tercih ederseniz o da olur: `icerik\urunler.xlsx`
dosyasının sarı sütununu doldurup `python manage.py urun_yukle` komutunu tekrar
çalıştırın. **Panelden girdiğiniz fiyatlar silinmez** — komut yalnızca Excel'de
dolu olan hücreleri yazar.

### Toplu işlemler

Listede satırları seçip üstteki açılır menüden:

- **Satışa aç** — fiyatı olanları açar, fiyatsızları atlar ve kaçını atladığını söyler
- **Satışı kapat**
- **Tükendi olarak işaretle**

Ürünler listesinde de bir işlem var: **Seçili ürünleri bütün mağazalara ekle**.
Karaman açıldığında 50 ürünü tek tıkla oraya taşımak için.

---

# AŞAMA C — Canlıya alın

```powershell
git add .
git commit -m "Adim 4: katalog - kategori, urun, magaza fiyati"
git push
```

Railway dağıtımı `migrate` ile tabloları kurar. Sonra canlıda bir kez:

```
python manage.py roller_kur
```

Ürünleri canlıya iki yolla götürebilirsiniz:

1. **Panelden girin** (önerilen) — canlı panele girip fiyatlarla birlikte elle
   girmek, yereldeki ile canlıdaki verinin ayrışmasını önler
2. **Excel'i sunucuya taşıyıp `urun_yukle` çalıştırın** — dosyayı repoya koymak
   gerekir; şimdilik gerekmez

Yerelde fiyat girip canlıda tekrar girmek istemiyorsanız fiyatları **doğrudan canlı
panelde** girin. Yerel ortam deneme içindir.

> **Bana gönderin:** canlı panelde katalog bölümünün açıldığının onayı.

---

## Sırada ne var

**Adım 5 — siparis:** sepet, sipariş, kesim işlemi, alım listesi. İşin kalbi.

Sepet mantığı katalogdan şunları kullanacak: `satis_adimi` (artır/azalt adımı),
`tartili_mi` (provizyon gerekir mi), `provizyon_tutari()` (ne kadar bloke edilecek),
`gunluk_limit` (bir teslim gününde kaç birime kadar).

Bu adıma geçmeden karara bağlanacaklar:

- **Minimum sepet tutarı** şu an 150 ₺, **teslimat ücreti** 40 ₺, **ücretsiz teslimat
  eşiği** 300 ₺ (`.env`'de duruyor). Beyşehir için bu sayılar doğru mu?
- Kesim saatinden sonra sipariş değiştirme hakkı olacak mı?
- Ürün tükendiğinde müşteriye ne denecek: sipariş iptal mi, benzeri ürün önerisi mi,
  eksik teslim mi?
