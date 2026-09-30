# Bostanhane — Proje Bağlamı

Bu dosya, bu klasörde çalışan Claude Code içindir. Projenin ne olduğunu, hangi kararların
alındığını ve nasıl çalışılacağını anlatır. Kod yazmaya başlamadan önce tamamını oku.

---

## 1. İş nedir

Bostanhane, mağaza bazlı çalışan **butik online manav**dır. Pilot: Konya / Beyşehir.

**Temel ilke: önce talep, sonra alım.**
Her mahallenin sabit teslim günleri vardır. Siparişler teslimattan bir gün önce belirlenen
**kesim saatinde** kapanır. Sistem toplam talebi ürün bazında birleştirir, mağaza sadece
satılmış kadar ürün alır. Ürün depoda beklemez, aynı gün tartılıp kapıya çıkar.

Klasik manav önce alır sonra satmaya çalışır; riski fireyle öder. Bostanhane bu sırayı tersine
çevirir. Yazılımın varlık sebebi bu akışı işletmektir.

### Üç satış kanalı (altyapı üçünü de kaldırmalı, sırayla açılacak)

| Kanal | Nasıl çalışır |
|---|---|
| **Yerel teslimat** | Mahalle + teslim günü, kesim saati, kendi kuryemiz, tartılı ürün + provizyon |
| **Ulusal kargo** | Dayanıklı ürünler, kesim saati yok, kargo entegrasyonu, 14 gün cayma hakkı |
| **Kurumsal (B2B)** | Kafe, pansiyon, yurt; ayrı fiyat listesi, düzenli sipariş şablonu |

Önce yerel teslimat kanalı çalışır hale gelecek. Kargo ve kurumsal sonra devreye alınacak,
ama veri modeli baştan üçünü de destekleyecek (ürün üzerinde kanal bayrakları).

---

## 2. Roller

| Rol | Ne yapar | Arayüz |
|---|---|---|
| **Süper Admin** | Mağaza açar, lokasyon seçer, yönetici atar, genel ayarlar, tüm raporlar | Web |
| **Mağaza Yöneticisi** | Ürün, fiyat, stok, personel, mahalle takvimi, siparişler, üye takibi, iade kararı | Web |
| **Paketleme Elemanı** | Mal kabul, toplama listesi, tartım, etiket, fire | Web (tablet) |
| **Kurye** | Günün rotası, navigasyon, teslim kaydı | Web (telefon) |
| **Üye** | Sipariş, ödeme, takip, teslim onayı, iade talebi | Web + mobil uygulama |

**Yetki kuralı (kritik):** Süper admin tüm mağazaları görür; diğer personel yalnızca kendi
mağazasını. Bu kısıtlama sorgu seviyesinde uygulanmalı, sadece şablonda gizlemek yeterli değil.

---

## 3. Alınan kararlar (değiştirmeden önce sor)

- Mahalle bazlı teslim günü; kesim saati teslimattan 1 gün önce, varsayılan 18:00
- Tartılı üründe **provizyon** alınır (tahmini tutar + tampon), tartımdan sonra kesin tutar çekilir
- Ödeme sadece sanal POS; kapıda ödeme yok. Kart bilgisi sistemde tutulmaz, yalnızca sağlayıcı token'ı
- **Giriş anahtarı telefon numarası** (10 hane, `5321112233`). Kullanıcı adı yok, e-posta isteğe bağlı
- Paketleme elemanı ve kurye Django yönetim paneline girmez; kendi sade ekranlarını kullanır
- Teslimde üye "eksiksiz teslim aldım" onayı verir; cevap gelmezse 24 saat sonra otomatik onay
- Kusurlu üründe fotoğraflı talep → mağaza yöneticisi kararı → kısmi iade
- Web ve mobil birlikte geliştirilir; ikisi aynı çekirdeği ve API'yi kullanır
- Yönetim paneli `/admin/` değil **`/yonetim/`** adresinde
- Geliştirmede SQLite, canlıda PostgreSQL. `.env` içindeki `DB_MOTOR` bunu belirler

---

## 4. Teknik yapı

| Katman | Teknoloji |
|---|---|
| Backend | Django + Django REST Framework |
| Veritabanı | SQLite (yerel) / PostgreSQL (canlı), `DB_MOTOR` ile seçilir |
| Web arayüz | Django template'leri |
| Mobil | React Native (Expo), repo içinde `mobile/` klasöründe (henüz yok) |
| Canlı ortam | Sunucu kararı verilmedi; Railway veya kendi sunucu |

### Klasör düzeni

```
bostanhane/            ← proje ayarları (settings.py, urls.py)
core/                  ← coğrafya (il/ilçe/mahalle), mağaza, hizmet alanı, teslim takvimi
hesaplar/              ← kullanıcı, roller, izinler, adres
hazir/                 ← Claude'un hazırladığı, kopyalanmayı bekleyen dosyalar
venv/                  ← sanal ortam (git'e girmez)
.env                   ← şifreler (git'e girmez)
adim-*.md              ← adım adım kurulum ve geliştirme notları
```

### Yönetim komutları

| Komut | Ne yapar |
|---|---|
| `roller_kur` | Rol gruplarını ve yetkilerini oluşturur/güvenceller. **Yeni uygulama eklendikçe `hesaplar/izinler.py`'ye satır ekleyip tekrar çalıştırılır.** |
| `ilk_yonetici` | Ortam değişkenlerinden süper admin açar (canlı ortam için) |
| `cografya_yukle` | 81 il, tanımlı ilçeler ve mahalleleri yükler. Liste `core/cografya_verisi.py`'de |
| `ilk_veri` | Coğrafyayı kontrol eder; veritabanı boşsa Beyşehir mağazasını da kurar |
| `ornek_veri` | Mağaza, pilot hizmet mahalleleri, teslim günleri, 8 haftalık takvim |
| `ornek_hesaplar` | Örnek personel ve üye (şifresiz — giriş yapamazlar) |

Canlı ortamda bu komutlar `Procfile` içinde her dağıtımda kendiliğinden çalışır.

### Planlanan uygulamalar (sırayla eklenecek)

`core` (var) → `hesaplar` → `katalog` → `siparis` → `odeme` → `depo` → `lojistik` → `talep` → `kampanya` → `panel` → `api`

---

## 5. Veri modeli — kurulan kısım

### hesaplar

- **Kullanici** — `AbstractBaseUser` üzerine kurulu; `USERNAME_FIELD = "telefon"`.
  `rol` alanı beş rolden birini taşır, `magaza` personeli şubesine bağlar.
  `save()` içinde: telefon tek biçime indirilir, role göre `is_staff` ayarlanır,
  rolün yetki grubu bağlanır.
- **Adres** — üyenin teslimat adresi. Resmî (coğrafi) mahalleye bağlı,
  bina/kat/daire ayrı alanlarda, enlem-boylam ile harita iğnesi.
  İlk adres otomatik varsayılan olur; varsayılan her zaman tektir.
- **hesaplar/izinler.py** — rol → yetki listesi. Yeni uygulama eklendikçe buraya satır
  eklenir ve `roller_kur` çalıştırılır.
- **core/admin_araclar.py** — `MagazaKisitliAdmin` karışımı. Mağaza izolasyonunu sorgu
  seviyesinde uygular. Yeni bir store-bazlı model eklerken admin sınıfına bu karışım
  eklenir, `magaza_yolu` (ve gerekiyorsa `suzulecek_modeller`) tanımlanır. `Magaza` panelinde
  yol `"pk"`. Karışım liste yan süzgeçlerini de daraltır (`liste_filtrelerini_daralt`);
  `suzulecek_modeller` varsayılanı `hizmetmahallesi`'ni içerir. Mağazaya bağlanamayan
  `IlgiKaydi`'ni yalnızca süper admin görür. **Yeni `hazir/` dosyası yazarken bunlar korunmalı.**

### core — coğrafya ile hizmet alanı ayrı

**Coğrafya** (resmî idari yapı, değişmez, `cografya_yukle` doldurur):

- **Il** — 81 il, plaka koduyla
- **Ilce** — şimdilik Konya (31) ve Karaman (6)
- **Mahalle** — resmî mahalle. `tip` alanı merkez mahallesi / köy kökenli ayrımını tutar
  (6360 sayılı kanunla büyükşehir ilçelerinde köyler mahalleye dönüştü).
  Beyşehir: 70 mahalle, 13'ü merkez

**Hizmet alanı** (bizim kararımız):

- **Magaza** — şube; aynı zamanda butik depo. `il` ve `ilce` artık FK
- **HizmetMahallesi** — "Beyşehir mağazası Müftü'ye gidiyor, günde 45 sipariş".
  Kapasite ve sıra buradadır
- **HaftalikTeslimGunu** — *kural*: "Müftü salı ve cuma, kesim 1 gün önce 18:00"
- **TeslimTakvimi** — *somut gün*: "3 Ekim Cuma, kapasite 45, durum açık"

**Coğrafya ile hizmet alanı neden ayrı?** Kargo kanalı. Üyenin adresi Türkiye'nin her
yerinde olabilir; yerel teslimat yalnızca mağazanın gittiği mahallelerde vardır.
`Adres` coğrafi mahalleye bağlanır, `adres.yerel_teslimat_var` yerel teslimatın açık
olup olmadığını söyler. Ayrıca aynı mahalleye ileride ikinci bir mağaza da hizmet
verebilir, her biri kendi günü ve kapasitesiyle.

**Kural ile takvim neden ayrı?** Hayat kuralı bozar: bayram olur, araç arızalanır, kapasite dolar.
Takvim kaydı sayesinde tek bir gün kapatılabilir veya kapasitesi değiştirilebilir; haftalık kural
bozulmaz. **Siparişler `TeslimTakvimi`'ne bağlanacak**, mahalleye değil.

`TeslimTakvimi.kural_uret()` bir kuraldan ileriye dönük takvim üretir; var olana dokunmaz.
`core/araclar.py` → `turkce_slug()`: Django'nun slugify'ı Türkçe harfleri düşürüyor ("Müftü"
→ "mft"), bu yüzden kendi çevirimizi kullanıyoruz.

---

## 6. Kod yazım kuralları

- **Model, alan ve değişken adları Türkçe.** `Magaza`, `teslim_gunleri`, `kesim_zamani`.
  Türkçe karakter kullanılmaz (ş, ğ, ı yerine s, g, i). `verbose_name` değerleri düzgün Türkçe olur.
  **Tek istisna:** Django'nun kendi aradığı alan adları İngilizce kalır —
  `password`, `last_login`, `is_active`, `is_staff`, `is_superuser`. Başka isim kabul etmiyor.
- Alan adı asla alt çizgiyle bitmez (Django `fields.E001` hatası verir): `not_` değil `aciklama`
- Her modelde `verbose_name`, `verbose_name_plural`, `__str__` ve `Meta.ordering` bulunur
- Ortak alanlar için `core.models.ZamanDamgali` soyut modeli kullanılır
- Para alanları `DecimalField(max_digits=10, decimal_places=2)`; float kullanılmaz
- Tarih/saat işlemlerinde `django.utils.timezone` kullanılır, `datetime.now()` kullanılmaz
- Yorumlar Türkçe ve **neden** sorusunu cevaplar; ne yaptığı koddan zaten anlaşılır
- Kullanıcıya görünen her metin Türkçe

---

## 7. Marka ve tasarım

Renkler (CSS değişkeni olarak tanımlanacak):

| İsim | Kod | Nerede |
|---|---|---|
| Bostan Yeşili | `#1F5132` | Ana renk, butonlar, başlıklar |
| Filiz | `#79A548` | Tazelik rozeti, başarı |
| Harman | `#D98A2B` | Kampanya, acil sipariş, uyarı |
| Krem | `#F6F3EA` | Bölüm zemini |
| Beyaz | `#FFFFFF` | Kart ve içerik zemini |
| Koyu | `#16281C` | Metin |

Tipografi: başlıklar **Fraunces** (serif), gövde **Karla**. Tasarım dili sıcak ve doğal:
krem zemin, yumuşak köşeler, bol beyaz alan.

Logo dosyaları: `..\logo\` klasöründe (SVG ve PNG, yazı eğriye çevrilmiş).
Ekran tasarımları: `..\tasarim\bostanhane-tasarim.html`.
Marka kılavuzu: `..\logo\bostanhane-marka-kilavuzu.html`.

### Arayüzde tutarlı olması gerekenler

- Kesim saati geri sayımı her ekranda görünür (ana sayfa kartı, sepet uyarısı, mobilde üst şerit)
- Ürün kartında birim ve satış adımı yazar ("kilogram · 500 g'dan itibaren")
- Provizyon mantığı **sepette** anlatılır, ödeme ekranında değil
- Para birimi tutardan sonra yazılır: `42,90 ₺`

---

## 8. Çalışma şekli

- Ersin'in **yazılım deneyimi yok**. Her adımı sade Türkçe anlat: ne yaptın, neden yaptın, o ne işe yarar
- Büyük değişikliklerden önce planı söyle, onay al
- Bir adımda bir iş yap; her adımın sonunda tarayıcıda görülebilen somut bir çıktı olsun
- Komutları çalıştırmadan önce ne yapacağını söyle
- Hata çıkarsa panik yaratma; hatanın ne dediğini Türkçe açıkla, sonra düzelt
- İş planı ve yol haritası bir üst klasörde: `..\bostanhane-is-plani-v4.md`, `..\bostanhane-web-yol-haritasi.md`

---

## 9. Şu anki durum (30 Eylül 2026)

**Yapıldı:** Marka adı ve logo kesinleşti, alan adı alındı (bostanhane.com), iş planı ve yol
haritası yazıldı, ana sayfa ve teslim günü akışı tasarlandı, yatırımcı dokümanı hazırlandı,
Instagram görselleri hazırlandı. Adım 1–2 tamam: `core` uygulaması, dört model, yönetim paneli,
"yakında" sayfası, GitHub + Railway + bostanhane.com canlıda.

**Şu anda:** Adım 3 (`hesaplar`) yerelde kuruldu. Adım 3B (`il/ilçe/mahalle`) dosyaları
`hazir/` klasöründe, talimat `adim-3b-cografya.md`. İkisi birlikte canlıya gidecek;
kullanıcı modeli ve mahalle tablosu değiştiği için veritabanı sıfırdan kuruluyor
(sitede henüz gerçek kayıt yok, kayıp yok).

**Sonraki adımlar:**
1. Adım 4: `katalog` — kategori, ürün, birim, tartılı mı, kanal bayrakları, fiyat, stok
   (önce Ersin'le ilk 30–40 ürün listesi ve hangilerinin kargoya uygun olduğu konuşulacak)
2. Adım 5: `siparis` — sepet, sipariş, kesim işlemi, alım listesi
3. Adım 6: üye girişi ve kayıt ekranları (SMS doğrulama), paketleme ve kurye ekranları

**Bekleyen işler (Ersin tarafı):**
- Apex alan adı: `bostanhane.com` → `https://www.bostanhane.com` yönlendirmesi
  (Squarespace 301) ve SSL doğrulaması
- @bostanhane.tr Instagram hesabının açılması
- Sanal POS başvurusu (iyzico / PayTR): provizyon + sonradan çekim, kart saklama (token),
  kısmi iade, provizyon geçerlilik süresi sorulacak
- Kurumsal e-posta sağlayıcısı kararı
- Pilot mahalleler ve teslim günlerinin kesinleşmesi, ilk 30–40 ürünün listesi

**Henüz karar verilmedi:** sunucu (Railway mi kendi sunucu mu), ödeme sağlayıcısı
(iyzico / PayTR), kurumsal e-posta sağlayıcısı, tedarikçi rolünün sisteme girip girmeyeceği.
