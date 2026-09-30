# Adım 3B — İl / İlçe / Mahalle

Bu adımda sisteme resmî adres yapısı giriyor: **İl → İlçe → Mahalle**.
Beyşehir'in **70 mahallesi** hazır yüklü geliyor; elle girmeniz gerekmiyor.

Bundan önce mahalle doğrudan mağazaya bağlıydı. Artık iki ayrı şey var —
ve bu ayrım işin üç kanalını birlikte yürütebilmek için şart.

---

## Neden iki ayrı şey

**Coğrafya** resmî yapıdır, herkes için aynıdır, değişmez:

```
Konya  →  Beyşehir  →  Müftü Mahallesi
```

**Hizmet alanı** ise sizin kararınızdır: hangi mahalleye gidiyorsunuz, hangi
günler, günde kaç siparişe kadar:

```
Bostanhane Beyşehir  →  Müftü Mahallesi  →  salı ve cuma  →  45 sipariş
```

Bu ayrım olmasa **kargo kanalı çalışmazdı**. Ankara'daki bir müşteri yöresel ürün
sipariş edecek; adresini girebilmesi gerekiyor, ama oraya kuryemiz gitmiyor.
Şimdi sistem şunu diyebiliyor: *"Bu adres kayıtlı bir mahallede, ama yerel
teslimat yok — sadece kargo."*

Mahalleye giden bir mağaza varsa yerel teslimat açık, yoksa kapalı. Kod tarafında
bu tek satır: `adres.yerel_teslimat_var`.

Bir yan fayda: aynı mahalleye ileride ikinci bir mağaza da hizmet verebilir, her
biri kendi günü ve kapasitesiyle. Eski yapıda bu mümkün değildi.

---

## Ne yüklü geliyor

| | Adet | Not |
|---|---|---|
| İl | 81 | Hepsi, plaka kodlarıyla |
| İlçe | 37 | Konya'nın 31, Karaman'ın 6 ilçesi |
| Mahalle | 70 | Beyşehir'in tamamı |
| Hizmet verilen mahalle | 13 aktif + 57 pasif | Merkez açık, köyler beklemede |

Beyşehir'in 70 mahallesi ikiye ayrılmış:

**Merkez mahallesi (13)** — kent merkezi, pilot burada başlıyor:
Avşar, Bahçelievler, Beytepe, Dalyan, Esentepe, Evsat, Hacıakif, Hacıarmağan,
Hamidiye, İçerişehir, Müftü, Yeni, Yeşilyurt

**Köy kökenli mahalle (57)** — Adaköy'den Yunuslar'a kadar. 6360 sayılı kanunla
Konya büyükşehir olunca Beyşehir'de köy kalmadı, hepsi mahalleye dönüştü.

### Gönderim nerede açık

**Merkezin 13 mahallesi aktif**, her biri haftada iki gün. Üç rotaya bölündü:

| Rota | Günler | Mahalleler |
|---|---|---|
| 1 | Pazartesi ve Perşembe | Müftü, Hamidiye, Dalyan, Esentepe, Beytepe |
| 2 | Salı ve Cuma | Bahçelievler, Hacıakif, Hacıarmağan, Evsat |
| 3 | Çarşamba ve Cumartesi | Yeni, İçerişehir, Avşar, Yeşilyurt |

**57 köy kökenli mahalle pasif.** Hizmet listesinde görünüyorlar ama teslim günleri
yok, takvimleri yok, sipariş almıyorlar. Açmak istediğinizde: Hizmet verilen
mahalleler → o satırın **aktif** kutucuğunu işaretleyin, teslim günü verin,
**8 haftalık takvim üret** işlemini çalıştırın.

Rotalardaki mahalle dağılımı bir başlangıç taslağı — kurye güzergâhını siz
bileceksiniz, panelden serbestçe değiştirebilirsiniz. Kapasiteler de öyle:
merkez mahalleleri günde 40 sipariş, köy kökenliler açıldığında 20 ile başlıyor.

Diğer illerin ilçe ve mahalleleri sonra eklenecek. Liste `core/cografya_verisi.py`
dosyasında; yeni il eklemek oraya satır yazıp bir komut çalıştırmaktan ibaret.

---

# AŞAMA A — Bilgisayarda (15 dk)

VS Code → Terminal (`bostanhane\bostanhane` klasöründe, `(venv)` görünüyor olmalı).

### A1. Hazır dosyaları yerine koyun

```powershell
Copy-Item hazir\core_models.py core\models.py -Force
Copy-Item hazir\core_admin.py core\admin.py -Force
Copy-Item hazir\core_views.py core\views.py -Force
Copy-Item hazir\core_araclar.py core\araclar.py -Force
Copy-Item hazir\core_admin_araclar.py core\admin_araclar.py -Force
Copy-Item hazir\core_cografya_verisi.py core\cografya_verisi.py -Force
Copy-Item hazir\hesaplar_models.py hesaplar\models.py -Force
Copy-Item hazir\hesaplar_admin.py hesaplar\admin.py -Force
Copy-Item hazir\hesaplar_izinler.py hesaplar\izinler.py -Force
Copy-Item hazir\cografya_yukle.py core\management\commands\cografya_yukle.py -Force
Copy-Item hazir\ornek_veri.py core\management\commands\ornek_veri.py -Force
Copy-Item hazir\ilk_veri.py core\management\commands\ilk_veri.py -Force
Copy-Item hazir\ornek_hesaplar.py hesaplar\management\commands\ornek_hesaplar.py -Force
Copy-Item hazir\Procfile Procfile -Force
```

### A2. Eski göç dosyalarını ve veritabanını silin

Mahalle tablosunun yapısı baştan değişti; eski göç dosyaları artık geçerli değil.
Canlıda gerçek veri olmadığı için en temizi sıfırdan kurmak.

```powershell
Remove-Item core\migrations\0*.py -Force
Remove-Item hesaplar\migrations\0*.py -Force
Remove-Item bostanhane.sqlite3 -Force -ErrorAction SilentlyContinue
```

> `__init__.py` dosyalarına dokunmuyoruz, sadece numarayla başlayanları siliyoruz.

### A3. Kurun

```powershell
python manage.py makemigrations core hesaplar
python manage.py migrate
python manage.py cografya_yukle
python manage.py roller_kur
python manage.py createsuperuser
python manage.py ornek_veri
python manage.py ornek_hesaplar
```

`cografya_yukle` çıktısında şunu görmelisiniz:

```
İl: 81 kayıt işlendi, 81 yeni.
İlçe: 37 yeni.
Konya / Beyşehir: 70 mahalle.
```

`createsuperuser` yine telefon soracak — **10 hane**, başında sıfır yok.
Numaranız `0533 031 72 88` ise `5330317288`.

### A4. Bakın

```powershell
python manage.py runserver
```

`http://127.0.0.1:8000/yonetim/` → giriş yapın. Panelde artık şunlar var:

**CORE bölümü**
- **İller** — 81 il, plaka koduyla. Her ilin kaç ilçesi, kaç mahallesi olduğunu gösterir
- **İlçeler** — Konya 31, Karaman 6. Hangi ilçede kaç mahalle hizmet alıyor sütunu var
- **Mahalleler** — 70 Beyşehir mahallesi. Sağdaki **yerel teslimat** sütunu o mahalleye
  hangi mağazanın gittiğini söyler; gidilmiyorsa `—` yazar
- **Hizmet verilen mahalleler** — asıl çalışma alanınız. 70 kayıt: üstte 13 aktif merkez
  mahallesi teslim günleriyle, altta 57 pasif köy kökenli mahalle. Sağ üstteki **aktif**
  süzgeciyle ayırabilirsiniz. Bir kayda girin: teslim günleri içinde satır satır duruyor
- **Mağazalar** — Beyşehir mağazası; il ve ilçe artık seçim listesinden geliyor

**Bir köyü açmayı deneyin:** Hizmet verilen mahalleler → listeden bir köy kökenli
mahalle seçin (örnek: Huğlu) → **aktif** kutucuğunu işaretleyin, içine girip bir teslim
günü ekleyin, kaydedin. Sonra listede o satırı seçip **8 haftalık takvim üret** işlemini
çalıştırın. Ana sayfada mahalle listesine eklendiğini göreceksiniz.

`http://127.0.0.1:8000` → ana sayfada mahalle listesi ve teslim günleri aynı şekilde
görünmeye devam ediyor.

> **Bana gönderin:** `cografya_yukle` çıktısı ve panelde İller/Mahalleler bölümlerinin
> açıldığının onayı. Hata varsa terminalin son satırlarını yapıştırın.

---

# AŞAMA B — GitHub'a gönderin

```powershell
git add .
git commit -m "Adim 3B: il/ilce/mahalle yapisi ve Beysehir mahalleleri"
git push
```

---

# AŞAMA C — Canlıyı yenileyin

`adim-3-hesaplar.md` dosyasındaki **AŞAMA C**'yi uygulayın (Railway'de PostgreSQL
servisini silip yenisini ekleme, değişkenleri güncelleme, redeploy).

Tek fark: sunucu artık açılışta coğrafyayı da yüklüyor. Dağıtım komut sırası:

```
migrate → collectstatic → roller_kur → ilk_yonetici → ilk_veri → gunicorn
```

`ilk_veri` boş veritabanı görünce 81 ili, 37 ilçeyi, Beyşehir'in 70 mahallesini,
Beyşehir mağazasını ve hizmet alanını (13 aktif + 57 pasif) kuruyor. Elle komut
çalıştırmanız gerekmiyor.

---

## Sırada ne var

**Adım 4 — katalog:** kategori, ürün, birim (kilogram / adet / demet), tartılı mı,
satış adımı, fiyat, stok ve kanal bayrakları (yerel teslimat / kargo / kurumsal).

Bir şeyi konuşmamız gerekecek: **ilk 30–40 ürünün listesi** ve hangilerinin kargoyla
gidebileceği (kuru gıda, bal, pekmez, kuruyemiş gibi dayanıklı olanlar).
