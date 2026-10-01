# YAPILACAKLAR — Ersin

Bu liste **sizin** yapacaklarınız. Claude Code'un işleri `talimat.md` dosyasında,
onları siz takip etmeyeceksiniz.

Son güncelleme: 1 Ekim 2026

---

## AŞAMA 1 — Claude Code'u çalıştırın · 2 dakika sizde, gerisi onda

VS Code'da Bostanhane penceresini açın (artık yeşil olan pencere) ve Claude Code'a
şunu yazın:

```
talimat oku
```

O da şunları yapacak: değişen dosyaları yerine koyacak, görsel depolama ayarını
kuracak, GitHub'a gönderecek, Railway'de dağıtımı bekleyecek, canlı siteyi kontrol
edecek. Bitince `rapor.md`'ye yazacak.

Bu sırada siz Aşama 2'yi yapabilirsiniz, birbirini beklemiyorlar.

- [ ] CC'ye "talimat oku" dedim

---

## AŞAMA 2 — Cloudflare'da görsel kovası · 10 dakika

Asasistan için zaten kullandığınız hesapta, **ayrı bir kova** açacağız.

Neden ayrı: ürün görsellerini siteye koyabilmek için kovayı herkese okunur yapacağız.
Asasistan'ın kovasında çalışan fotoğrafları, imzalar ve sözleşmeler var — onlar açık
olmamalı.

- [ ] **Kova açtım** — ad: `bostanhane`
- [ ] **Açık erişim ayarladım** — ya `gorsel.bostanhane.com` alan adını bağladım,
      ya da r2.dev adresini açtım
- [ ] **API anahtarı oluşturdum** — yalnızca `bostanhane` kovasına, okuma+yazma yetkili

Elinizde şu altı değer olacak:

| | Örnek |
|---|---|
| Access Key ID | `a1b2c3...` |
| Secret Access Key | `uzun-bir-metin` (bir daha gösterilmez, kaydedin) |
| Kova adı | `bostanhane` |
| Uç nokta | `https://hesapkimliginiz.r2.cloudflarestorage.com` |
| Bölge | `auto` |
| Açık adres | `https://gorsel.bostanhane.com` |

> ⚠️ **Bu değerleri sohbete yazmayın.** Secret anahtar bir şifre gibidir. Doğru yer
> iki tane: bilgisayarınızdaki `.env` dosyası (Aşama 3) ve Railway'in Variables
> sekmesi (Aşama 4).

Ayrıntılı tıklama tarifi: `adim-4b-gorsel-depolama.md` → Aşama A

---

## AŞAMA 3 — Anahtarları bilgisayara girin · 3 dakika

Claude Code'a şunu yazın:

```
.env dosyasına S3 anahtarlarını ekleyeceğim, bana satırları hazırla
```

Hazırladığı satırları `.env` dosyasına yapıştırıp **kendi değerlerinizi** yazın.
Sonra CC'ye "test et" deyin; `python manage.py check` ile doğrulayacak.

- [ ] `.env` dosyasına anahtarları girdim
- [ ] CC "uyarı kalmadı" dedi

> `.env` dosyası GitHub'a gitmiyor, anahtarlarınız dışarı sızmıyor.

---

## AŞAMA 4 — Railway ayarları · 10 dakika

Railway panelinde web servisine girin → **Variables** sekmesi.

### 4a. Var olanları kontrol edin

| Değişken | Olması gereken |
|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `YONETICI_TELEFON` | `5330317288` |
| `YONETICI_AD` | `Ersin Öztürk` |
| `YONETICI_KULLANICI` | **olmamalı** — varsa silin |

- [ ] Dördünü kontrol ettim

### 4b. Görsel depolama değişkenlerini ekleyin

Aşama 2'deki altı değeri buraya girin:

```
S3_ACCESS_KEY_ID
S3_SECRET_ACCESS_KEY
S3_BUCKET
S3_ENDPOINT_URL
S3_REGION
S3_PUBLIC_URL
```

- [ ] Altısını ekledim
- [ ] **Redeploy** dedim

### 4c. Yönetici şifresini güvene alın

`bostanhane.com/yonetim/` adresine telefonunuzla girip **şifrenizi değiştirin**.
Sonra Railway'den `YONETICI_SIFRE` değişkenini **silin** — şifre orada durmasın.

- [ ] Şifremi değiştirdim
- [ ] `YONETICI_SIFRE`'yi Railway'den sildim

---

## AŞAMA 5 — Ürün fiyatlarını girin · 20–30 dakika

Bu aşama diğerlerini beklemiyor, canlı panel açıldığı an başlayabilirsiniz.

`bostanhane.com/yonetim/` → **KATALOG → Mağaza ürünleri**

50 satır var. Üç sütun doğrudan listede düzenlenebiliyor: **fiyat**, **durum**,
**satışta**. Yani sayfa sayfa dolaşmanıza gerek yok — fiyatları yukarıdan aşağı
yazın, satmaya hazır olanların **satışta** kutucuğunu işaretleyin, sayfanın altındaki
**Kaydet**'e bir kez basın.

Kolaylıklar:

- Sağ üstteki **kategori** süzgeciyle önce sebzeleri, sonra meyveleri girin
- **müşteriye görünen** sütunu fiyatı `32,90 ₺` diye gösterir — müşteride nasıl
  görüneceğini anında görürsünüz
- Fiyatı olmayan satırda kırmızı **fiyat girilmedi** yazar
- Mevsimi geçen ürünü silmeyin, durumunu **Mevsim dışı** yapın

> Canlı panelde ürün yoksa CC'ye sorun; ürünler panelden girilecek diye karar verdik,
> gerekirse taslak listeyi bir kez içeri alabilir.

- [ ] Sebze fiyatlarını girdim
- [ ] Meyve ve yeşillik fiyatlarını girdim
- [ ] Bakliyat, yöresel ürün ve yumurta fiyatlarını girdim

---

## AŞAMA 6 — Ürün fotoğrafları · acelesi yok

Aşama 2–4 bitmeden **fotoğraf yüklemeyin**; kaybolur.

Bittiğinde: her ürün için bir kare fotoğraf, açık zemin, en az 1200 × 1200 piksel.
Panelden ürüne girip **görsel** alanına yüklüyorsunuz.

- [ ] Depolama ayarı bitti, fotoğraf yüklemeye başlayabilirim

---

## ARKA PLANDA YÜRÜYEN İŞLER

Yazılımı beklemiyorlar, paralel gidebilir. Erken başlamak işe yarar.

### Sanal POS başvurusu — en uzun süren iş

`..\icerik\sanal-pos-sorulari.md` dosyasını iyzico ve PayTR'ye gönderin, **yazılı**
cevap isteyin. İlk beş soru eleyici: cevap "hayır" ise o sağlayıcıyla devam edilmez.

Başvuru haftalar sürüyor ve sitede yasal metinlerin **yayında** olmasını istiyorlar.
O yüzden bu ikisi birlikte yürümeli.

- [ ] iyzico'ya gönderdim
- [ ] PayTR'ye gönderdim
- [ ] Bankamın sanal POS teklifini istedim

### Yasal metinler — hukukçu gerekiyor

KVKK aydınlatma metni, açık rıza, mesafeli satış sözleşmesi, ön bilgilendirme formu,
iade ve cayma politikası, çerez politikası.

Hukukçuya sorulacak iki özel soru var:
- Çabuk bozulan ürünler 14 günlük cayma hakkından muaf mı?
- Tartılı üründe provizyon alıp kesin tutarı sonra çekmek, mesafeli satış mevzuatında
  nasıl anlatılmalı?

- [ ] Hukukçuyla görüştüm

### @bostanhane.tr Instagram hesabı

Görseller hazır: `..\sosyal-medya\` klasöründe profil fotoğrafı ve üç gönderi.
Yükleme sırası **3 → 2 → 1** (ızgara 1-2-3 diye okunsun).

- [ ] Hesabı açtım
- [ ] Profil fotoğrafını ve biyografiyi koydum
- [ ] Üç gönderiyi sırayla paylaştım

### Mağaza bilgileri

Panelde `Depo adresi girilecek` ve `0332 000 00 00` yer tutucuları duruyor.
Panel → CORE → Mağazalar → Bostanhane Beyşehir.

- [ ] Depo açık adresini girdim
- [ ] Telefon ve e-postayı girdim

### Kurumsal e-posta

`bostanhane.com` uzantılı e-posta için sağlayıcı kararı. Sistem e-postaları
(sipariş onayı, şifre sıfırlama) buradan gidecek.

- [ ] Sağlayıcıya karar verdim

---

## SIRADAKİ YAZILIM ADIMI — Adım 5: sipariş

Sepet, sipariş, kesim işlemi, alım listesi. İşin kalbi.

Başlamadan **iki karar** gerekiyor. Düşünün, acelesi yok:

1. **Kesim saatinden sonra müşteri siparişini değiştirebilsin mi?**
   Değiştiremezse iş kolay: kesim saatinde liste kapanır, sabah alım yapılır.
   Değiştirebilsin derseniz alım listesi kesimden sonra da oynar — o zaman
   "ürün ekleme yok, sadece çıkarma var" gibi bir orta yol gerekir.

2. **Bir ürün tükendiğinde ne olacak?**
   Üç seçenek: siparişi iptal etmek, benzer ürün önermek, ya da eksik teslim edip
   o kalemin parasını iade etmek. Üçünün müşteri deneyimi ve yazılım yükü farklı.
