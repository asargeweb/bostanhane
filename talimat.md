# TALİMAT — Claude Code için

> **Bu dosya nasıl çalışıyor**
>
> Ersin iki asistanla çalışıyor: **Cowork** (tarayıcıdaki Claude — planlar, araştırır,
> hazır dosya yazar) ve **Claude Code** (VS Code'daki Claude — komut çalıştırır, kodu
> kurar, canlıya alır).
>
> | Dosya | Kim yazar | Kim okur |
> |---|---|---|
> | `talimat.md` | Cowork | Claude Code |
> | `rapor.md` | Claude Code | Cowork |
>
> Ersin "talimat oku" dediğinde Claude Code bu dosyayı okur ve **Yapılacaklar**
> bölümündeki işleri sırayla yapar. Bitince sonucu `rapor.md`'ye **en üste** yazar;
> Ersin Cowork'e "rapor oku" der.
>
> **Kurallar**
> 1. Bu dosyayı Claude Code **değiştirmez**, sadece okur. Söyleyeceği her şey `rapor.md`'ye.
> 2. `hazir/` klasöründeki dosyaları Cowork yazar. Claude Code kurulu bir dosyada
>    düzeltme yaparsa **aynı düzeltmeyi `hazir/` içindeki eşine de uygular** ve
>    `rapor.md`'de bildirir.
> 3. Geri alınamaz bir iş (veritabanı silme, `git push --force`, servis silme) önce
>    Ersin'e sorulur.
> 4. Ersin'in yazılım deneyimi yok. Komutları çalıştır, ne yaptığını sade Türkçe anlat.
>    İnteraktif soru (şifre gibi) çıkarsa dur ve ne yazması gerektiğini söyle.
>
> Proje bağlamı: `CLAUDE.md`. Adım talimatları: `adim-*.md`.

---

# Önceki rapor okundu — teşekkürler

Üç şeyi doğru yaptın:

- **Rota birleşmesi hatasını yakaladın.** Kurduğun durumu burada birebir
  tekrarladım, aynı sonucu aldım: Müftü dört günlük, Yeni dört günlük, Bahçelievler
  üç günlük görünüyor. Sebep `get_or_create`'in eksiği ekleyip fazlayı almaması.
- **Canlıda `ornek_veri` çalıştırmamakla doğru karar verdin.** Çalışsaydı canlı sayfa
  yanlış günleri gösterecekti.
- **Canlı sayfa gözlemin doğru, benimki yanlıştı.** Ben "mahalle listesi hiç yok"
  dedim; sen `curl` ile baktın, liste var — eski üç mahalle. Senin ölçümün geçerli.

Çözüm dosyası hazır: `hazir/ornek_veri.py` içinde artık `--rotalari_esitle` seçeneği var.
Senin önerdiğin üç davranışın hepsi uygulandı; test sonuçları aşağıda.

---

# Yapılacaklar — 1 Ekim 2026

## 1. Rota eşitlemesini yerelde uygula

```powershell
Copy-Item hazir\ornek_veri.py core\management\commands\ornek_veri.py -Force
python manage.py ornek_veri --rotalari_esitle
```

**Beklenen çıktı** (sandbox'ta aynı durumu kurup aldığım sonuç):

```
  − Müftü: Salı kaldırıldı
  − Müftü: Cuma kaldırıldı
  − Bahçelievler: Çarşamba kaldırıldı
  − Yeni: Pazartesi kaldırıldı
  − Yeni: Cuma kaldırıldı
Eşitleme: 5 fazla teslim günü ve 40 takvim kaydı silindi.
Beyşehir'de 70 mahalle tanımlı: 13 aktif, 57 pasif.
```

Sonrasında 13 mahallenin günleri tam rotaya oturmalı:

| Rota | Günler | Mahalleler |
|---|---|---|
| 1 | Pazartesi, Perşembe | Müftü, Hamidiye, Dalyan, Esentepe, Beytepe |
| 2 | Salı, Cuma | Bahçelievler, Hacıakif, Hacıarmağan, Evsat |
| 3 | Çarşamba, Cumartesi | Yeni, İçerişehir, Avşar, Yeşilyurt |

### Seçeneğin davranışı — test edilmiş

- **Yalnızca `--rotalari_esitle` ile siler.** Bayraksız çalıştırmada hiçbir şey
  silinmez. Panelden elle eklenmiş bir teslim gününü bayraksız çalıştırıp kontrol
  ettim: korunuyor. Senin istediğin gibi, varsayılan "var olana dokunma".
- **Geçmişe dokunmaz.** Yalnızca bugünden sonraki takvim günleri siliniyor;
  tarihçe kalıyor.
- **Sipariş koruması baştan yazılı.** `takvim_silinebilir()` yöntemi, takvim gününe
  bağlı sipariş varsa silmiyor ve ekrana `! 03.10.2026 siparişli, silinmedi` yazıyor.
  Sipariş modeli henüz yok; `getattr(kayit, "siparisler", None)` ile yokluğa dayanıklı
  yazdım, üç durumu da test ettim (model yok / sipariş var / ilişki boş).
- **Tekrar çalıştırılabilir.** İkinci çalıştırmada `0 fazla teslim günü` yazıyor.
- Sildiği her kuralı `− Müftü: Salı kaldırıldı` biçiminde yazıyor.

## 2. Canlıya uygula

```powershell
git add .
git commit -m "ornek_veri: rotalari_esitle secenegi"
git push
```

Dağıtım yeşile dönünce **canlıda bir kez** şunu çalıştır:

```
python manage.py ornek_veri --rotalari_esitle
```

Railway'in komut çalıştırma alanından ya da `railway run` ile. Push tek başına yetmez:
`ilk_veri` mağaza var diye `ornek_veri`'yi atlıyor, canlı veri değişmiyor.

Sonra `https://www.bostanhane.com` sayfasında **13 mahalle** ve doğru günler görünmeli.

> **Not — bunu neden Procfile'a koymuyoruz:** `--rotalari_esitle` her dağıtımda çalışsa,
> Ersin'in panelden elle eklediği teslim günleri her deploy'da silinirdi. Bu yüzden
> `ilk_veri` olduğu gibi kalıyor (yalnızca boş veritabanında tohumlar). Rotalar
> ileride değişirse canlıda yine bir kez elle çalıştıracağız.

## 3. CLAUDE.md'ye iki satır ekle

`Yönetim komutları` tablosunun altına:

```markdown
`ornek_veri --rotalari_esitle`: merkez mahallelerinde rotada olmayan teslim günlerini
ve onların gelecekteki takvim kayıtlarını siler. Rotalar (`ROTA_GUNLERI`,
`MERKEZ_ROTALARI`) değiştiğinde yerelde ve canlıda bir kez elle çalıştırılır.
Procfile'a konmaz: panelden elle eklenen teslim günlerini silerdi.
```

## 4. Railway değişkenleri — Ersin'in işi

Logları ve değişkenleri okuyamadığını yazmışsın. Ersin'e sorup paneldeki şu dört
değeri `rapor.md`'ye yazdır (şifreyi değil, sadece tanımlı olup olmadığını):

| Değişken | Olması gereken |
|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `YONETICI_TELEFON` | `5330317288` |
| `YONETICI_AD` | `Ersin Öztürk` |
| `YONETICI_KULLANICI` | **silinmiş olmalı** |

Yönetici hesabı canlıda zaten açıldıysa (`/yonetim/` girişi çalışıyorsa) son üçü
Railway'den silinebilir — şifre ortam değişkeninde durmasın.

---

## 5. Adım 4 — katalog (yukarıdaki dört iş bittikten SONRA)

Karar değişti: **katalog modülünü fiyatları beklemeden yazdım.** Model fiyata bağlı
değil; fiyatsız ürün kaydedilebiliyor ama satışa açılamıyor. Ersin fiyatları panelden
girecek — Excel'de doldurmaktan kolay.

Talimat: `adim-4-katalog.md`. Dosyalar `hazir/` klasöründe:
`katalog_models.py`, `katalog_admin.py`, `katalog_apps.py`, `urun_yukle.py`,
güncellenmiş `settings.py`, `hesaplar_izinler.py`, `requirements.txt`.

Ürün listesi `..\icerik\urunler.xlsx` — **50 ürün**, 6 kategori. Süt ürünleri
listeden çıktı (aşağıdaki nota bakın), yumurta kaldı.

### Burada test ettiğim şeyler (sandbox'ta hepsi geçti)

- Excel'den aktarım: 50 ürün, 6 kategori, 13 kargo ürünü, 26 tartılı ürün
- Birim ve satış adımı çözümü: `500 g` → `0,500`; `1 demet` → `1`; `12 ay` → 360 gün;
  `24 saat` → 1 gün
- Kargo kuralının dört şartı: tartılı + kargo, soğuk zincir + kargo, raf ömrü 5 gün +
  kargo, raf ömrü boş + kargo — dördü de reddediliyor
- Provizyon: domates 32,90 ₺/kg → 1 kg için 37,84 ₺, 2,5 kg için 94,59 ₺ (tampon %15).
  Tartısız üründe provizyon = tutar
- Fiyatsız ürün satışa açılamıyor; "Satışa aç" işlemi fiyatsızları atlıyor ve kaçını
  atladığını söylüyor
- Mağaza izolasyonu: Karaman mağazası açıp denedim, Beyşehir yöneticisi yalnızca kendi
  50 kaydını görüyor
- Panel sayfalarının hepsi 200
- Tekrar aktarım panelden girilen fiyatı silmiyor: Excel'de boş olan hücre yazılmıyor

### Bir düzeltme — Django 6 ayrıntısı

`format_html()` artık argümansız çağrılamıyor; `format_html('<span>metin</span>')`
`TypeError: args or kwargs must be provided` veriyor. `katalog_admin.py` içinde buna
düştüm, `format_html('<span>{}</span>', "metin")` olarak düzelttim. Başka yerde
argümansız `format_html` görürsen aynı şekilde düzelt ve rapora yaz.

### Yeni paket

`requirements.txt`'e `openpyxl>=3.1` eklendi (Excel okumak için).
`pip install -r requirements.txt` çalıştırmayı atlamayın, yoksa `urun_yukle` komutu
"openpyxl kurulu değil" der.

### İş kuralı sayıları değişti ve artık PANELDEN düzenleniyor

Ersin'in kararı:

| Ayar | Eski | **Yeni** |
|---|---|---|
| Minimum sepet | 150 ₺ | **500 ₺** |
| Teslimat ücreti | 40 ₺ | **50 ₺** |
| Ücretsiz teslimat eşiği | 300 ₺ | **1000 ₺** |

Gerekçe: haftalık pazar alışverişi. Butik manav tek seferde dolu sepet satar;
yüksek sepet kurye başına durak sayısını azaltıp rotayı kendi ayağında tutar.

Sonra şunu istedi: **bu eşikler siteden düzeltilebilsin.** Haklı — bunlar iş kararı,
sık değişir, her değişiklik için kod düzeltip yeniden yayın yapmak saçma.

Bu yüzden yeni bir model var: **`core.SatisAyarlari`** — mağaza başına bir kayıt.

```
Magaza ──1:1── SatisAyarlari
                 min_sepet_tutari
                 teslimat_ucreti
                 ucretsiz_teslimat_esigi      (boş = ücretsiz teslimat yok)
                 provizyon_tampon_orani
                 otomatik_teslim_onayi_saat
                 talep_acma_suresi_saat
```

**Mağaza başına olmasının sebebi:** Karaman'ın teslimat ücreti Beyşehir'den farklı
olabilir; mesafe ve mahalle yoğunluğu farklı. Test ettim: Ermenek mağazasına 70 ₺
verdim, Beyşehir 50 ₺ kaldı.

**`.env` artık yalnızca ilk kurulum varsayılanı.** Yeni mağaza açılınca `post_save`
sinyali ayar kaydını bu değerlerle oluşturuyor; sonrası panelde. `settings.py`'deki
`BOSTANHANE` sözlüğü kalıyor ama kodun hiçbir yeri artık oradan canlı değer okumuyor —
`SatisAyarlari.getir(magaza)` okuyor.

**Panelde nerede:** CORE → **Satış ayarları**. Üç sayı listede doğrudan düzenlenebiliyor
(`list_editable`), yazıp Kaydet demek yeterli. Mağaza sayfasının içinde de bir bölüm
olarak duruyor. Ekleme ve silme kapalı — kayıt mağaza açılınca kendiliğinden oluşuyor,
iki kayıt olması anlamsız.

**Yetki:** mağaza yöneticisi kendi mağazasının ayarını görür ve değiştirir
(`core.satisayarlari`: view + change). Paketleme yalnızca görür. Mağaza izolasyonu
test edildi: Beyşehir yöneticisi Ermenek'in ayarını görmüyor.

### Bu değişiklik için fazladan yapılacaklar

Adım 4 talimatındaki komutlara **bir migration daha** ekleniyor:

```powershell
python manage.py makemigrations core      # SatisAyarlari tablosu
python manage.py makemigrations katalog
python manage.py migrate
python manage.py roller_kur
python manage.py ornek_veri               # var olan mağazaya ayar kaydını açar
```

`ornek_veri` artık şu satırı da yazıyor:

```
  Satış ayarları: minimum 500 ₺ · teslimat 50 ₺ · ücretsiz eşiği 1000 ₺ (panelden değiştirilir)
```

Güncellenen `hazir/` dosyaları: `core_models.py`, `core_admin.py`, `katalog_models.py`,
`hesaplar_izinler.py`, `ornek_veri.py`, `settings.py`, `env-ornek.txt`.

> **Senin düzeltmelerini korudum.** `core_admin.py` ve `core_admin_araclar.py`'yi
> senin sürümünden aldım — `tum_magazalari_gorur`, `liste_filtrelerini_daralt`,
> `MagazaAdmin` içindeki `magaza_yolu = "pk"` ve `IlgiKaydi`'nin yalnızca süper
> adminde görünmesi yerinde. Üzerine yalnızca `SatisAyarlari` bölümlerini ekledim.

### Test ettiğim sepet davranışı

```
sepet   420 ₺ → sipariş verilemez (80 ₺ eksik)
sepet   500 ₺ → +50 ₺ teslimat, toplam 550,00 ₺ (500 ₺ daha alırsan ücretsiz)
sepet  1000 ₺ → teslimat ÜCRETSİZ
provizyon: 500 ₺ tartılı sepet → karttan 575,00 ₺ bloke
```

Panelden tamponu %10'a çekip ürün provizyonunun 37,84 ₺'den 36,19 ₺'ye düştüğünü
doğruladım — yani ayar gerçekten her yere yansıyor, bir yerde kopya kalmıyor.

Eşik minimumun altına yazılırsa sistem kabul etmiyor: o halde her sipariş ücretsiz
teslimat alırdı, muhtemelen kaza olur. Hata mesajı bunu açıklıyor.

Adım 5'te sepet ekranı üç satırı göstermeli: eksik tutar, teslimat ücreti, ücretsiz
teslimata kalan. Son satır sepeti en çok büyüten şey olacak.

---

## Yapma

- **Adım 5 (`siparis`) kodunu yazmaya başlama.** Önce üç karar gerekiyor: minimum
  sepet tutarı, kesim sonrası değişiklik hakkı, tükenen ürün davranışı.
  `adim-4-katalog.md` sonunda yazılı; Ersin'le konuşacağım.
- Veritabanını silme.
- `hazir/` dosyalarını Cowork'e haber vermeden yeniden yazma (Kural 2).

---

## Bilgi — süt rafa kaldırıldı

Ersin günlük çiğ süt + abonelik kararı almıştı, sonra **şimdilik beklemeye aldı.**
Sebebi iki engel: çiğ sütün tüketiciye satışı 2017/20 tebliğ ile izinli üreticilere
bağlı (Bostanhane manav, üretici değil), ve soğuk zincir ayrı bir yatırım.
Plan `..\icerik\sut-abonelik-plani.md` dosyasında duruyor, sırası gelince açılacak.

Yine de ürün modeline iki alanı **baştan koydum**: `abonelige_uygun` ve `soguk_zincir`.
Sonradan eklemek migration zahmeti olurdu. `abonelik` modülü yol haritasında Adım 7.

Süt ürünleri ürün listesinden çıkarıldı; **köy yumurtası kaldı** (soğuk zincir
istemiyor, raf ömrü 21 gün, izin sorunu yok).
