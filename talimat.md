# TALİMAT — Claude Code için

> | Dosya | Kim yazar | Kim okur |
> |---|---|---|
> | `talimat.md` | Cowork | Claude Code |
> | `rapor.md` | Claude Code | Cowork |
>
> **Kurallar**
> 1. Bu dosyayı değiştirmezsin, sadece okursun. Söyleyeceğin her şey `rapor.md`'ye.
> 2. Kurulu bir dosyada düzeltme yaparsan **aynı düzeltmeyi `hazir/` eşine de uygula**
>    ve rapora yaz.
> 3. Geri alınamaz iş önce Ersin'e sorulur.
> 4. Ersin'in yazılım deneyimi yok. Ne yaptığını sade Türkçe anlat.
>
> Proje bağlamı: `CLAUDE.md`. Ersin'in listesi: `YAPILACAKLAR.md`.

---

# Ersin ne istedi

> *"site kısmımızda ürünler yayınlansın. şu an sanki canlı satış yapıyor gibi hareket
> edelim. stok yönetimi vs hepsini aynı anda canlı sitede de görelim. üyelik kısmı vs
> aktifleşsin"*

Yani: vitrin + sepet + üyelik + stok, canlıda çalışır halde. Bu **Adım 5, 6 ve 7'nin
tamamı** — birkaç oturumluk iş. Sırayı ve iş bölümünü aşağıda kurdum.

Fiyat ekranı işini (satışta kutucuğu + düzenleme modu) Ersin sana ayrıca söyledi;
o bitince buraya geç.

---

## İş bölümü — çakışmayı önlemek için

| Kim | Ne |
|---|---|
| **Cowork (ben)** | `siparis` modülünün **modelleri**: Sepet, Siparis, SiparisKalemi, kesim, alım listesi. Göç gerektiren her şey bende. Ayrıca `MagazaUrun`'a stok alanları. |
| **Claude Code (sen)** | **Üyelik** (kayıt, giriş, çıkış, adres yönetimi) ve **vitrin iskeleti** (şablonlar, taban şablon, marka stilleri). Bunlar yeni model gerektirmiyor. |

Niye böyle: üyelik `Kullanici` ve `Adres` modellerini kullanıyor, ikisi de **var**.
Yani sen hiç `makemigrations` çalıştırmadan ilerleyebilirsin. Ben modelleri bitirip
`hazir/`'a koyunca sepet ve sipariş ekranlarını üstüne kurarsın.

**Sen `siparis` uygulamasını oluşturmayacaksın.** Modelleri ben yazıyorum.

---

# Ersin'in bekleyen iki kararı — verdim

Projeyi bekletmemek için karar verdim. İkisi de `.env`/panel ayarı değil, akış kararı;
değiştirmek isterse söyler.

### Karar 1 — Kesim saatinden sonra sipariş değiştirilemez

Kesim saatine kadar müşteri sepetini değiştirebilir, siparişini iptal edebilir.
Kesim saatinden sonra **kilitlenir**.

Sebebi: kesim saatinin varlık sebebi alım listesini dondurmak. Kesimden sonra değişikliğe
izin vermek, mağaza hale gittikten sonra listenin değişmesi demek — işin temelini bozar.

### Karar 2 — Tükenen ürün: eksik teslim + o kalemin parası çekilmez

Provizyon mimarisi bu sorunu kendiliğinden çözüyor. Sipariş anında para **çekilmiyor**,
bloke ediliyor. Teslimat sabahı ürün bulunamazsa o kalem siparişten düşülür ve
**çekilen tutara girmez**. Müşteriye bildirim gider: *"Maydanoz bugün bulunamadı,
tutarınızdan düşüldü."*

Yani iptal de yok, benzer ürün dayatması da yok. Sepetin geri kalanı gelir.

Bunun için sipariş kaleminde iki alan olacak: `siparis_miktari` (müşterinin istediği)
ve `teslim_miktari` (gerçekte giden). Tartılı üründe ikisi zaten farklı olacak —
aynı mekanizma hem tartı farkını hem bulunamayan ürünü taşıyor. Tek kavram, iki iş.

---

# Stok yönetimi — burada klasik stok YOK, ve bu bilinçli

Bunu doğru kurmak önemli, yoksa yanlış şeyi inşa ederiz.

Bostanhane'nin modeli **"önce talep, sonra alım"**. Yani taze ürün için depoda stok
tutulmuyor; kesim saatinde ne satıldıysa o kadar alınıyor. Klasik "elimde 40 kg domates
var, düştükçe azalt" mantığı bu işte **yanlış** olur.

Taze üründe yönetilen üç şey var, üçü de zaten modelde:

| Alan | Ne işe yarar |
|---|---|
| `MagazaUrun.durum` | Satışta · Tükendi · Mevsim dışı — günlük bulunabilirlik |
| `MagazaUrun.gunluk_limit` | Bir teslim gününde en fazla kaç birim satılsın |
| `TeslimTakvimi.kapasite` | O gün kaç siparişe kadar alınsın |

**Ama bir istisna var: kargo kanalı.** Bal, pekmez, Akçabelen fasulyesi, bakliyat —
bunlar dayanıklı, depoda duruyor ve **gerçekten stoğu var**. 20 kavanoz bal varsa
21'inci satılmamalı.

Bu yüzden `MagazaUrun`'a iki alan ekleyeceğim:

- `stok_takibi` (bool) — bu üründe adet sayılsın mı
- `stok_adedi` (int, null) — takip açıksa eldeki miktar

Taze ürünlerde `stok_takibi=False` kalır, `durum` ve `gunluk_limit` çalışır.
Kargo ürünlerinde `True` olur, sipariş verildikçe düşer, sıfırlanınca `durum`
kendiliğinden `Tükendi` olur.

Panelde iki ayrı ekran olacak: **günlük bulunabilirlik** (taze — sadece durum
değiştirme, hızlı) ve **stok** (kargo ürünleri — sayı girme). Bunları modeller
geldikten sonra kuracaksın.

---

# Canlı satış — bir uyarı ve bir çözüm

Ersin "sanki canlı satış yapıyor gibi" dedi. Tamam, ama şunu açıkça kurmamız gerekiyor:

**Şu an gerçek sipariş alınamaz.** Sanal POS yok, yasal metinler yok (mesafeli satış
sözleşmesi, ön bilgilendirme, KVKK, cayma politikası). Bu haliyle siteyi herkese açıp
sipariş almak hem parasız sipariş hem mevzuata aykırı satış demek.

Çözüm: **vitrin modu**. Site üç durumdan birinde olacak:

| Mod | Davranış |
|---|---|
| `kapali` | Şu anki "yakında" sayfası |
| `test` | Vitrin ve sepet çalışır, ama **yalnızca giriş yapmış kullanıcılara**. Ziyaretçi "yakında" sayfasını görür. Verilen siparişler `test_siparisi=True` damgalanır. |
| `acik` | Herkese açık gerçek satış |

Varsayılan **`test`**. Ersin ve ortağı giriş yapıp uçtan uca denerler, gerçek müşteri
göremez, biriken deneme siparişleri raporları kirletmez ve sonra temizlenebilir.

`acik` moduna geçiş, sanal POS + yasal metinler tamamlanınca tek ayar değişikliğiyle
olacak. `noindex` satırı da o zaman kalkacak.

Bu ayarı `SatisAyarlari`'na ekleyeceğim (`vitrin_modu`). **Modeli ben yazıyorum**, sen
şablon tarafında `vitrin_modu` değerine bakacaksın.

---

# Yapılacaklar — sırayla

## 1. Üyelik — kayıt, giriş, çıkış

Yeni model yok. `hesaplar` uygulamasına görünümler ve şablonlar.

### Sayfalar

| Adres | Ne |
|---|---|
| `/kayit/` | Telefon, ad soyad, şifre (iki kez), KVKK onayı |
| `/giris/` | Telefon + şifre |
| `/cikis/` | Çıkış, ana sayfaya döner |
| `/hesabim/` | Ad soyad ve e-posta düzenleme, şifre değiştirme bağlantısı |
| `/hesabim/adresler/` | Adres listesi, ekleme, düzenleme, varsayılan yapma |

### Kurallar

- **Giriş anahtarı telefon.** `hesaplar.models.telefon_duzelt` ve `telefon_dogrula`
  **zaten var**, onları kullan — `0532 111 22 33` da `+90...` da kabul edilsin,
  kaydederken tek biçime insin. Yeniden yazma.
- Kayıt olan kullanıcı `rol=Rol.UYE` olur. `magaza` boş kalır (model bunu zorunlu
  kılıyor, `clean()`'e bak).
- **KVKK onayı kutucuğu zorunlu.** İşaretlenince `kvkk_onayi = timezone.now()`.
  Metnin kendisi henüz yok (hukukçuda) — şimdilik bir yer tutucu sayfaya bağla ve
  `rapor.md`'ye "metin bekliyor" diye yaz.
- **Kampanya izni ayrı ve işaretsiz gelsin** (`duyuru_izni`). KVKK onayıyla aynı
  kutuya koymak açık rıza kuralına aykırı; ikisi ayrı olmak zorunda.
- `telefon_dogrulandi` **False** kalsın. SMS sağlayıcısı seçilmedi; doğrulama sonra
  eklenecek. Üyelik bunu beklemesin.
- Şifre sıfırlama: **şimdilik yapma.** E-posta zorunlu değil, SMS yok. Ersin panelden
  şifre verebiliyor. Sağlayıcı seçilince eklenecek.
- Adres formunda **mahalle seçimi**: önce il/ilçe, sonra mahalle. Beyşehir dışında da
  adres girilebilmeli (kargo kanalı). Mahalleye hizmet verilmiyorsa form bunu bir
  bilgi notuyla söylesin: *"Bu mahalleye şu an kurye gitmiyor; kargo ile
  gönderilebilir."* `Mahalle.yerel_hizmet()` bunu söylüyor.
- `Adres.save()` ilk adresi kendiliğinden varsayılan yapıyor, varsayılanı tek tutuyor.
  Formda ayrıca uğraşma.

### Şablonlar

Taban şablon gerekiyor: `templates/taban.html` — üst menü (logo, kategoriler, sepet,
hesabım/giriş), alt bilgi, marka renkleri ve tipografi.

- Renkler ve yazı tipleri `CLAUDE.md` bölüm 7'de. Mevcut `ana_sayfa.html` aynı
  paleti kullanıyor, oradan devam et.
- Logo: `..\logo\svg\` klasöründe. Küçük olanı satır içine gömebilirsin
  (`ana_sayfa.html`'de örneği var).
- **Mobil önce.** Müşterilerin çoğu telefondan girecek.
- **Tasarım hazır, uydurmana gerek yok.** İki dosya var:
  - `..\tasarim\bostanhane-tasarim.html` — ana sayfa, teslim günü akışı, sepet (1. tur)
  - `..\tasarim\bostanhane-tasarim-2.html` — **kayıt, giriş, hesabım, siparişlerim,
    vitrin, ürün sayfası, adreslerim, test modu şeridi** (2. tur, bugün çizdim)

  İkincisi senin şu an yapacağın ekranların tamamını kapsıyor. HTML'i aç, sınıf
  adlarını ve yapıyı oradan al — `.kart`, `.adet`, `.kesim`, `.test-serit`, `.alan`,
  `.onay`, `.adres-k` hepsi tanımlı. Mockup'lar sabit marka renkleriyle `.m` kapsamı
  içinde; gerçek şablonda CSS değişkenlerine çevir.

  Her bölümün altında **neden öyle tasarlandığını** anlatan notlar var. Onları oku;
  bazıları iş kuralı (örneğin KVKK ve kampanya izninin ayrı kutular olması zorunlu).

## 2. Vitrin iskeleti — ürünleri göster

Sepet **henüz yok** (modeli yazıyorum), ama ürünleri listeleyebilirsin.

| Adres | Ne |
|---|---|
| `/urunler/` | Kategorilere göre ürün listesi, kart görünümü |
| `/urunler/<kategori-slug>/` | Kategori sayfası |
| `/urun/<urun-slug>/` | Ürün sayfası |

### Ürün kartında ne yazacak

- Ad, görsel (yoksa marka renginde yer tutucu)
- Fiyat: **tutardan sonra para birimi** → `32,90 ₺`
- `urun.satis_adimi_metni` → *"kilogram · 500 g'dan itibaren"*
- Tartılı üründe bir not: *"Tartıya göre kesinleşir"*
- `uyari_metni` doluysa göster
- Tükendi / mevsim dışı ise rozet, sepete ekleme kapalı

### Hangi ürünler görünecek

Yalnızca `MagazaUrun.satista_mi` **True** olanlar. O özellik şunların hepsine bakıyor:
`aktif` ve fiyat var ve `durum == SATISTA` ve `urun.aktif`. Kendi koşulunu yazma, onu kullan.

Mağaza seçimi: şimdilik ilk aktif mağaza. Müşterinin mahallesine göre mağaza seçimi
sepetle birlikte gelecek.

### Vitrin modu

`SatisAyarlari.vitrin_modu` alanını **ben ekleyeceğim**. Sen şimdilik şöyle yaz:

```python
mod = getattr(ayarlar, "vitrin_modu", "test")
```

`getattr` ile, çünkü alan henüz yok — böylece kodun şimdi de çalışır, model gelince
kendiliğinden doğru değeri okur. Model gelince `getattr`'ı kaldırırsın.

Davranış: `kapali` → "yakında" sayfası · `test` → giriş yapmışsa vitrin, yapmamışsa
"yakında" · `acik` → herkese vitrin.

## 2b. Teslim günü düzeni değişti — vitrinde buna göre göster

Ersin'in isteği: *"günler ve altında haritaya göre mahalleler olsun. şimdilik her
mahalle yalnızca 1 gün olsun; sonrasında komşu mahalleler için gerekirse 2 gün olabilir."*

Yaptım. **Her mahalleye haftada bir gün** gidiliyor artık, 13 mahalle altı güne dağıldı:

| Gün | Mahalleler (güzergâh sırası) |
|---|---|
| Pazartesi | İçerişehir · Müftü · Hamidiye |
| Salı | Bahçelievler · Esentepe |
| Çarşamba | Yeni · Beytepe |
| Perşembe | Hacıakif · Hacıarmağan |
| Cuma | Avşar · Evsat |
| Cumartesi | Dalyan · Yeşilyurt |

⚠ **Bu gruplama coğrafi değil, taslak.** Hangi mahallenin hangisine komşu olduğunu
bilmiyorum; Ersin düzeltecek. `ornek_veri.py` içindeki `GUN_ROTALARI` tablosundan ya da
panelden değişiyor.

Değişen dosyalar (`hazir/` içinde hazır): `ornek_veri.py`, `core_views.py`, `ana_sayfa.html`.

```powershell
Copy-Item hazir\ornek_veri.py core\management\commands\ornek_veri.py -Force
Copy-Item hazir\core_views.py core\views.py -Force
Copy-Item hazir\ana_sayfa.html templates\core\ana_sayfa.html -Force
python manage.py ornek_veri --rotalari_esitle
```

Eşitleme çıktısında 20 fazla teslim günü ve ~155 takvim kaydının silindiğini, ayrıca
güzergâh sıralarının düzeltildiğini göreceksin (`~ İçerişehir: güzergâh sırası 11 → 1`).

### Sende ne değişiyor

- **Ana sayfa artık gün başlıklı kartlar gösteriyor** — ben yazdım, hazır.
  `core_views.gun_gun_mahalleler(magaza)` yardımcısı günlere göre gruplanmış liste
  döndürüyor; vitrin ve sepet ekranlarında da aynı yardımcıyı kullan.
- **Mahalle artık tek günlü**, yani `teslim_gunleri_metni()` tek gün döndürüyor.
  Arayüzde "Salı ve Cuma" değil "Salı" yazacak. Ama **çoğul yapıyı bozma**: model
  hâlâ birden fazla gün tutabiliyor, Ersin komşu mahallelere ikinci gün ekleyebilir.
  Şablonlarda tek gün varsayımı yapma, listeyi dön.
- `HizmetMahallesi.sira` artık **kurye güzergâhı**: `gün × 10 + güzergâhtaki sıra`.
  Yani sıralama hem günü hem gün içindeki durağı taşıyor. Listelerde `sira`'ya göre
  dizmeye devam et.
- Ana sayfanın alt bilgisinde `{{ magaza.ilce }}, {{ magaza.il }}` "Beyşehir / Konya,
  Konya" diye çıkıyordu (çünkü `Ilce.__str__` zaten ili içeriyor). `{{ magaza.konum }}`
  olarak düzelttim — aynı hatayı yeni şablonlarda yapma, `konum` özelliği var.

---

## 3. Bunları yapma

- **`siparis` uygulamasını oluşturma, sepet modeli yazma.** Bende.
- `MagazaUrun`'a stok alanı ekleme. Bende.
- `SatisAyarlari`'na `vitrin_modu` ekleme. Bende.
- Ödeme ekranı yapma — sanal POS seçilmedi.
- SMS doğrulama ekleme — sağlayıcı seçilmedi.

## 4. Raporda görmek istediklerim

- Hangi sayfalar çalışıyor, hangi adreslerde
- Kayıt → giriş → adres ekleme akışını uçtan uca denediğini (test istemcisiyle olur)
- Beyşehir dışı bir adres eklemeyi denediğini ve "kurye gitmiyor" notunun çıktığını
- Taban şablonun telefon genişliğinde bozulmadığını
- `hesaplar` içindeki telefon yardımcılarını yeniden yazmadığını

---

## Durum özeti

**Bitti:** coğrafya · hizmet alanı · hesaplar (modeller) · katalog · satış ayarları ·
görsel depolama (anahtar bekliyor).

**Şu anda:** fiyat ekranı (sende) → üyelik ve vitrin iskeleti (sende) ·
`siparis` modelleri (bende).

**Sonra:** sepet ve sipariş ekranları · kesim işlemi ve alım listesi · paketleme ve
kurye ekranları · ödeme (POS bekliyor).
