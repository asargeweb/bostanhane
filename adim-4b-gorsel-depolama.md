# Adım 4B — Ürün görselleri için nesne depolama

Ürün ve kategori fotoğrafları sunucu diskine **yazılmayacak**. S3 uyumlu bir nesne
depolamaya gidecek.

---

## Neden

İki sebep, ikisi de sert:

1. **Railway'in dosya sistemi kalıcı değil.** Yüklenen görsel bir sonraki dağıtımda
   silinir. Hata mesajı da almazsınız — sessiz veri kaybı.
2. **Kalıcı disk kiralasak bile Hobby planında 5 GB sınırı var** ve bu bir faturalama
   aşımı değil, sert sınır. Ürün fotoğrafı + ileride iade talebi fotoğrafları o alanı
   hızla doldurur.

Asasistan için de aynı kararı vermiştiniz; Bostanhane de aynı yere gidiyor.

Kod **sağlayıcıdan bağımsız** yazıldı: Cloudflare R2, Backblaze B2 ve AWS S3 aynı
protokolü konuşur. Hangisini kullandığınız yalnızca iki ayar satırını değiştirir.

---

## Kova ayrı olsun

Asasistan'ın kovasını paylaşmak yerine **Bostanhane'ye ayrı bir kova** açın. İki sebep:

- Erişim anahtarı tek kovaya yetkili olur; bir proje sızdırsa diğeri etkilenmez
- Görselleri siteye açmak için kovayı herkese okunur yapacağız. Asasistan'ın
  kovasında çalışan fotoğrafları, imzalar ve sözleşmeler var — onlar **açık olmamalı**

Aynı hesap, ayrı kova. İsim: `bostanhane`.

---

# AŞAMA A — Sağlayıcı tarafı (Ersin, 10 dk)

## Cloudflare R2 kullanıyorsanız

1. Cloudflare panel → **R2** → **Create bucket** → ad: `bostanhane` → oluştur
2. Kovanın **Settings** sekmesi → **Public access**:
   - **Custom domain** ekleyin: `gorsel.bostanhane.com` (önerilen — kalıcı ve markalı)
   - ya da **r2.dev** alt alan adını açın (hızlı deneme için; adres çirkin ama çalışır)
3. R2 ana sayfası → sağdan **Manage R2 API Tokens** → **Create API token**
   - İzin: **Object Read & Write**
   - Kapsam: yalnızca `bostanhane` kovası
   - Oluşturunca **Access Key ID** ve **Secret Access Key** görünür —
     secret bir daha gösterilmez, hemen kaydedin
4. **Hesap kimliğinizi** (Account ID) alın; uç nokta adresi şu olur:
   `https://<hesap-kimligi>.r2.cloudflarestorage.com`

Custom domain eklerseniz DNS kaydını Cloudflare kendisi yapar — Squarespace'e
dokunmanız gerekmez, çünkü `bostanhane.com` Squarespace'te duruyor. Bu durumda
`gorsel.bostanhane.com` için Squarespace'e bir **CNAME** kaydı eklemeniz gerekebilir;
Cloudflare hangi değeri istediğini ekranda söyler.

## Backblaze B2 kullanıyorsanız

1. **Buckets** → **Create a Bucket** → ad: `bostanhane` → **Files in Bucket are: Public**
2. **Application Keys** → **Add a New Application Key**, yalnızca bu kovaya,
   Read and Write
3. Uç nokta kovanın bilgi ekranında yazar: `https://s3.<bolge>.backblazeb2.com`
4. Açık adres: `https://f<nnn>.backblazeb2.com/file/bostanhane` biçiminde olur

## AWS S3 kullanıyorsanız

Kova oluşturun, public read politikası tanımlayın, IAM kullanıcısı açıp anahtar alın.
`S3_ENDPOINT_URL` **boş** kalır, `S3_REGION` kovanın bölgesi olur.

> **CORS ayarı gerekmiyor.** Görselleri sunucu yüklüyor, tarayıcı yalnızca `<img>`
> ile okuyor. İleride tarayıcıdan doğrudan yükleme yaparsak o zaman gerekecek.

---

# AŞAMA B — Projeye tanıtma

## B1. Paketi kurun

```powershell
pip install -r requirements.txt
```

`django-storages[s3]` eklendi.

## B2. Dosyaları yerine koyun

```powershell
Copy-Item hazir\settings.py bostanhane\settings.py -Force
Copy-Item hazir\core_apps.py core\apps.py -Force
Copy-Item hazir\requirements.txt requirements.txt -Force
Copy-Item hazir\env-ornek.txt env-ornek.txt -Force
```

## B3. Anahtarları girin

`.env` dosyasını VS Code'da açıp sona ekleyin (kendi değerlerinizle):

```
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
S3_BUCKET=bostanhane
S3_ENDPOINT_URL=https://hesap-kimliginiz.r2.cloudflarestorage.com
S3_REGION=auto
S3_PUBLIC_URL=https://gorsel.bostanhane.com
```

> `.env` dosyası git'e gitmiyor, anahtarlar dışarı sızmaz. Kontrol: `git status`
> çıktısında `.env` **görünmemeli**.

## B4. Doğrulayın

```powershell
python manage.py check
python manage.py shell -c "from django.core.files.storage import default_storage as d; print(type(d).__name__); print(d.url('urun/deneme.jpg'))"
```

Beklenen: adres `https://gorsel.bostanhane.com/bostanhane/medya/urun/deneme.jpg` gibi
görünmeli. `?X-Amz-Signature=...` ile bitiyorsa `S3_PUBLIC_URL` tanımlı değil demektir —
görseller yine çalışır ama adresler bir saat geçerli olur, siteye konmaz.

## B5. Gerçek deneme

```powershell
python manage.py runserver
```

Panel → Katalog → Ürünler → bir ürün → **görsel** alanına küçük bir fotoğraf yükleyin,
kaydedin. Sonra:

- Sağlayıcı panelinde kovanın içine bakın: dosya `bostanhane/medya/urun/...` altında
  görünmeli
- Ürün sayfasındaki görsel bağlantısına tıklayın, fotoğraf açılmalı

Açılmıyorsa kova herkese okunur değil ya da açık adres yanlış — ikisini de
Aşama A'dan kontrol edin.

---

# AŞAMA C — Canlıya

```powershell
git add .
git commit -m "Gorseller nesne depolamaya tasindi"
git push
```

Railway → web servisi → **Variables** → altı değişkeni ekleyin:

| Değişken | Değer |
|---|---|
| `S3_ACCESS_KEY_ID` | … |
| `S3_SECRET_ACCESS_KEY` | … |
| `S3_BUCKET` | `bostanhane` |
| `S3_ENDPOINT_URL` | `https://hesap-kimliginiz.r2.cloudflarestorage.com` |
| `S3_REGION` | `auto` |
| `S3_PUBLIC_URL` | `https://gorsel.bostanhane.com` |

Sonra **Redeploy**. Dağıtım kayıtlarında şu uyarının **kaybolduğunu** görün:

```
(bostanhane.W001) Yüklenen görseller sunucu diskine yazılıyor; bir sonraki dağıtımda silinecek.
```

Bu uyarı `manage.py check` içine konuldu ve her dağıtımda çalışıyor — yani ayarı
unutursanız sessiz kalmıyor, logda görünüyor.

Son kontrol: canlı panelden bir ürüne fotoğraf yükleyip görselin açıldığını görün.

---

## Nasıl çalışıyor — bilmeniz gereken kadarı

**Anahtarlar tanımsızsa yerel diske yazar.** Bilgisayarda çalışırken hiçbir kurulum
gerekmesin diye. Bu yüzden `.env`'inize anahtar eklemek zorunda değilsiniz; eklemezseniz
yerelde `media/` klasörüne yazar, canlıda uyarı alırsınız.

**Açık adres vermezseniz imzalı adres üretir.** Kovayı herkese açmak istemiyorsanız
`S3_PUBLIC_URL`'i boş bırakın: görseller bir saat geçerli, imzalı adreslerle servis
edilir. Panelde çalışır, ama siteye koyacağınız kalıcı adresler için açık adres gerekir.

**Aynı adlı dosya eskisini silmez.** `file_overwrite=False`, yani `domates.jpg`'i ikinci
kez yüklerseniz `domates_XxYy.jpg` olur. Eski ürün kartlarının görseli bozulmaz.

**Kova içinde klasör:** her şey `bostanhane/medya/` altına yazılır (`S3_KLASOR`).
Kovayı başka bir projeyle paylaşmak zorunda kalırsanız karışmaz.

---

## Sonra yapılacak (şimdi değil)

- **Görsel küçültme.** Telefonla çekilen fotoğraf 4-5 MB oluyor; ürün kartı için
  800 px yeterli. Yükleme anında küçültmek sayfa hızını ciddi etkiler. Pillow zaten
  kurulu, bir sonraki adımda ekleyebiliriz.
- **İade talebi fotoğrafları** da aynı kovaya gidecek (Adım 8, `talep` modülü).
  Dikkat: o fotoğraflar müşteri mutfağından geliyor, **açık adresle servis edilmemeli** —
  imzalı adres kullanılacak. Kod bunu destekliyor, ayrı bir klasör ve ayar yeter.
