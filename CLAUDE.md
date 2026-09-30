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
core/                  ← mağaza, mahalle, teslim takvimi
hazir/                 ← Claude'un hazırladığı, kopyalanmayı bekleyen dosyalar
venv/                  ← sanal ortam (git'e girmez)
.env                   ← şifreler (git'e girmez)
adim-*.md              ← adım adım kurulum ve geliştirme notları
```

### Planlanan uygulamalar (sırayla eklenecek)

`core` (var) → `hesaplar` → `katalog` → `siparis` → `odeme` → `depo` → `lojistik` → `talep` → `kampanya` → `panel` → `api`

---

## 5. Veri modeli — kurulan kısım

`core` uygulamasında dört model var:

- **Magaza** — şube; aynı zamanda butik depo
- **Mahalle** — mağazanın hizmet verdiği mahalle; günlük kapasitesi var
- **HaftalikTeslimGunu** — *kural*: "Müftü salı ve cuma, kesim 1 gün önce 18:00"
- **TeslimTakvimi** — *somut gün*: "3 Ekim Cuma, kapasite 45, durum açık, kesim 2 Ekim 18:00"

**Kural ile takvim neden ayrı?** Hayat kuralı bozar: bayram olur, araç arızalanır, kapasite dolar.
Takvim kaydı sayesinde tek bir gün kapatılabilir veya kapasitesi değiştirilebilir; haftalık kural
bozulmaz. **Siparişler `TeslimTakvimi`'ne bağlanacak**, mahalleye değil.

`TeslimTakvimi.kural_uret()` bir kuraldan ileriye dönük takvim üretir; var olana dokunmaz.

---

## 6. Kod yazım kuralları

- **Model, alan ve değişken adları Türkçe.** `Magaza`, `teslim_gunleri`, `kesim_zamani`.
  Türkçe karakter kullanılmaz (ş, ğ, ı yerine s, g, i). `verbose_name` değerleri düzgün Türkçe olur.
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
haritası yazıldı, ana sayfa ve teslim günü akışı tasarlandı, yatırımcı dokümanı hazırlandı.

**Tamamlandı (30 Eylül 2026):** Adım 1 (kurulum) ve Adım 2 (`core` uygulaması, dört model,
yönetim paneli, örnek veri). Veritabanı `bostanhane.sqlite3` (eski boş `db.sqlite3` kullanılmıyor).
`TeslimTakvimi.not_` alanı Django kuralı gereği `aciklama` olarak yeniden adlandırıldı.
YAPILACAKLAR.md Aşama A (yerel kurulum, yakında sayfası, `IlgiKaydi`, yerel yönetici `bostanci`)
ve Aşama B (kod GitHub'da: github.com/asargeweb/bostanhane, gizli depo) tamam.
Sırada Aşama C (Railway) ve D (bostanhane.com bağlama); bunları kullanıcı kendi panelinden yapıyor.

**Sonraki adımlar:**
1. Adım 3: `hesaplar` — kullanıcı, roller, mağaza bağlantısı, üye adresi
2. Adım 4: `katalog` — kategori, ürün, birim, tartılı mı, kanal bayrakları, fiyat, stok
3. Adım 5: `siparis` — sepet, sipariş, kesim işlemi, alım listesi

**Henüz karar verilmedi:** sunucu (Railway mi kendi sunucu mu), ödeme sağlayıcısı
(iyzico / PayTR), kurumsal e-posta sağlayıcısı, tedarikçi rolünün sisteme girip girmeyeceği.
