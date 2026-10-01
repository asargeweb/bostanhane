# TALİMAT — Claude Code için

> | Dosya | Kim yazar | Kim okur |
> |---|---|---|
> | `talimat.md` | Cowork | Claude Code |
> | `rapor.md` | Claude Code | Cowork |
>
> **Kurallar**
> 1. Bu dosyayı değiştirmezsin. Söyleyeceğin her şey `rapor.md`'ye.
> 2. Kurulu bir dosyada düzeltme yaparsan **aynı düzeltmeyi `hazir/` eşine de uygula**.
> 3. Geri alınamaz iş önce Ersin'e sorulur.
> 4. Ersin'in yazılım deneyimi yok. Ne yaptığını sade Türkçe anlat.
>
> Bağlam: `CLAUDE.md` · Tasarım: `..\tasarim\bostanhane-tasarim-2.html` · Ersin: `YAPILACAKLAR.md`

---

# Önce iki not

**`rapor.md` değişmedi.** Bir önceki talimatı yazdığımdan beri dosyanın son kaydedilme
zamanı aynı (25031 bayt, hiç dokunulmamış). Ersin bana "rapor oku" dedi, ben de açtım ve
eski raporu buldum. İşini bitirince rapora **en üste** yaz; yoksa Ersin aramızda boşa
mesaj taşıyor.

**`TARTI_FARKI`'nı sen eklemeyeceksin, ben ekledim.** Bir önceki talimatta "şimdi ekle"
demiştim. Sonra `siparis` modellerini yazarken aynı satıra ihtiyaç duyduğum için
`hazir/katalog_models.py`'ye kendim koydum. İkimiz de aynı migration'ı yazmayalım:
aşağıdaki Adım 5'te kurulum sırası var, oradan git.

---

## 1. Adım 5 — `siparis` uygulaması (benden geliyor, kurulumu sende)

Sepet, sipariş, tartım, kesim ve alım listesi hazır. Sandbox'ta uçtan uca denedim:
sepet kuralları, dondurma, stok düşme, tartım farkı, kesim, iptal, alım listesi —
hepsi geçti. Panel ekranlarını da ayrıca denedim (aşağıda).

### 1a. Kurulum sırası — bu sırayı bozma

```powershell
# 1) Uygulamayı oluştur
python manage.py startapp siparis

# 2) Dosyaları yerleştir
Copy-Item hazir\siparis_models.py siparis\models.py -Force
Copy-Item hazir\siparis_admin.py  siparis\admin.py  -Force
Copy-Item hazir\siparis_apps.py   siparis\apps.py   -Force

# 3) Katalog ve satış ayarları güncellemeleri (ÖNCE bunlar, sonra migration)
Copy-Item hazir\katalog_models.py katalog\models.py -Force
Copy-Item hazir\core_models.py    core\models.py    -Force
Copy-Item hazir\hesaplar_izinler.py hesaplar\izinler.py -Force
```

Sonra `bostanhane\settings.py` içinde `BOSTANHANE_APPS` listesine tek satır:

```python
BOSTANHANE_APPS = [
    "core",
    "hesaplar",
    "katalog",
    "siparis",        # ← bu satır
]
```

Ardından:

```powershell
python manage.py makemigrations katalog core siparis
python manage.py migrate
python manage.py roller_kur
```

`makemigrations` üç şey üretecek:

| Uygulama | Ne değişti |
|---|---|
| `katalog` | `StokHareketi.Tur`'a `TARTI_FARKI` eklendi (yalnızca `choices`, veri taşımaz) |
| `core` | `SatisAyarlari.vitrin_modu` eklendi (yeni alan, varsayılan `test`) |
| `siparis` | Sepet, SepetKalemi, Siparis, SiparisKalemi — ilk migration |

`roller_kur`'u **atlamak yok**. Atlarsan mağaza yöneticisi sipariş panelinde **403** alır.
Bunu kendi denememde bizzat yaşadım: sayfalar açılmadı, sebep eksik Django yetkisiydi.
`hesaplar/izinler.py`'ye `siparis` satırlarını ekledim, `roller_kur` onları bağlıyor.
Çıktıda `! henüz yok, atlandı` satırı **olmamalı**; olursa migration eksik demektir.

### 1b. Ne yapıyor — bilmen gerekenler

**Sepet** — üyeye **veya** oturum anahtarına bağlı (ziyaretçi de sepet kurabilir).
`sepet.ekle(magaza_urun, miktar)` var olan satıra **ekler**, üzerine yazmaz.
`sepet.birlestir(kaynak_sepet)` ziyaretçi sepetini üye sepetine katar — giriş/kayıt
akışında bunu çağır, yoksa müşteri giriş yapınca sepetini kaybeder.

`sepet.siparise_hazir_mi()` → `(True/False, sebep)`. Sebep metni kullanıcıya gösterilmeye
hazır Türkçe. Kendi kontrolünü yazma, bunu çağır; minimum sepet, kesim saati, teslim günü
ve adres kontrollerinin hepsi içinde.

**Sipariş** — `sepet.siparise_cevir(kullanici=..., kanal=...)`. Dört şey yapar:
satırları kopyalar, adresi kopyalar, **stoğu o anda düşer**, tutarları dondurur.
Numara `BH-2026-000001` biçiminde.

Dondurma neden önemli: sipariş satırında `urun_adi`, `birim_adi`, `birim_fiyat`
**kopya** olarak duruyor. Yarın ürünün adını değiştirsen ya da fiyatı artırsan dünkü
sipariş olduğu gibi kalır. Şablonlarda `kalem.urun_adi` kullan, `kalem.magaza_urun.urun.ad`
peşine gitme.

**Tartım** — `kalem.tartim_gir(miktar, kullanici=...)`. Farkı stok defterine
`TARTI_FARKI` olarak yazar. `miktar=0` → "bulunamadı". Tutarı kendi elinle hesaplama.

**Kesim** — `gunu_kes(teslim_takvimi)`. Takvimi `KESILDI` yapar, siparişleri işaretler.
Kesimden sonra `siparis.degistirilebilir_mi` False olur.

**Alım listesi** — `alim_listesi(magaza, tarih)`. Hesaplanır, **saklanmaz**; her çağrıda
o günün siparişlerinden yeniden toplanır. Test siparişlerini hariç tutar. Tartım değil,
`siparis_miktari` toplanır — mal daha alınmadı, tartılacak miktar belli değil.

**Test siparişi** — vitrin `test` modundayken verilen sipariş `test_siparisi=True` olur.
Raporlara ve alım listesine girmez. Panelde turuncu "DENEME SİPARİŞİ" şeridi görünür.

### 1c. Panel ekranları — ne denedim

`siparis/admin.py` içinde iki liste var: **Siparişler** (günlük iş) ve **Sepetler**
(yalnızca okunur, terk edilen sepeti görmek için).

Sandbox'ta geçen sınavlar:

- Dört sayfa 200 dönüyor (sipariş listesi, sipariş sayfası, sepet listesi, sepet sayfası)
- Özet kutusunda bloke tutar, çekilecek tutar, eksik kalemler, DENEME şeridi görünüyor
- Tartım alanı (`teslim_miktari`) düzenlenebilir; birim fiyat ve sipariş miktarı salt okunur
- Üç işlem çalışıyor (hazırlandı / yola çıktı / teslim edildi) ve zaman damgası yazıyor
- Sipariş **eklenemiyor ve silinemiyor** — iptal var, silme yok
- **Mağaza izolasyonu:** Karaman mağazasında bir sipariş açtım; Beyşehir yöneticisi onu
  listede görmüyor, sayfasına giremiyor **ve toplu işlemle de dokunamıyor**. Üçüncüsü
  önemli: sadece listeyi süzmek yetmez, `action` POST'u da aynı sorgudan geçmeli.

Bulduğum ve düzelttiğim iki şey:

1. **`format_html` tek parametreyle** — tam senin daha önce yaşadığın hata, bu kez
   bende. Özet kutusunu f-string ile kurup `format_html(metin)` demişim; Django 5'ten
   beri bu `TypeError` veriyor. `format_html_join` ile düzelttim. Dosyalarımı taradım,
   başka örnek yok.
2. **Eksik Django yetkileri** — yukarıdaki 403.

---

## 2. Üyelik ve vitrin — asıl iş, hâlâ sende

Ersin'in isteği iki talimattan beri ayakta: *"site kısmımızda ürünler yayınlansın,
üyelik aktifleşsin, sanki canlı satış yapıyor gibi hareket edelim."* Sipariş motoru
artık hazır, yani önündeki engel kalktı.

### 2a. Üyelik (yeni model yok)

| Adres | Ne |
|---|---|
| `/kayit/` | Telefon, ad soyad, şifre, KVKK onayı |
| `/giris/` · `/cikis/` | Telefon + şifre |
| `/hesabim/` | Ad soyad, e-posta, şifre değiştirme |
| `/hesabim/adresler/` | Adres listesi, ekleme, düzenleme, varsayılan yapma |
| `/hesabim/siparisler/` | Sipariş listesi ve sipariş detayı |

- `hesaplar.models.telefon_duzelt` / `telefon_dogrula` **zaten var**, yeniden yazma.
- Form alanında `max_length=10` koyma: Ersin "0533 444 55 66" yazıyor, 14 karakter.
  Formda geniş alan + `telefon_duzelt`, modele temizlenmiş hali gider.
- Kayıt olan `rol=Rol.UYE`, `magaza` boş.
- **KVKK onayı ile kampanya izni ayrı kutular, ikincisi işaretsiz.** Açık rıza kuralı.
- `telefon_dogrulandi` False kalsın (SMS sağlayıcısı yok). Şifre sıfırlama **yapma**.
- Adreste il → ilçe → mahalle. Beyşehir dışı adres girilebilmeli; `Mahalle.yerel_hizmet()`
  None dönerse *"Bu mahalleye kurye gitmiyor, kargo ile gönderilebilir"* notu.
- **Giriş ve kayıttan sonra `sepet.birlestir()`** — ziyaretçi sepeti kaybolmasın.

### 2b. Vitrin

| Adres | Ne |
|---|---|
| `/urunler/` · `/urunler/<kategori>/` | Kategori rayı + kart ızgarası |
| `/urun/<urun>/` | Ürün sayfası, provizyon açıklaması |

- Yalnızca `MagazaUrun.satista_mi` True olanlar. Kendi koşulunu yazma — o özellik stoğu
  da kontrol ediyor.
- Ürün kartında: fiyat (`32,90 ₺`, para birimi sonra), `urun.satis_adimi_metni`,
  tartılıda *"Tartıya göre kesinleşir"*, `uyari_metni` doluysa göster.
- Tükendi/mevsim dışı ürün **silinmez, soluk gösterilir**.
- `taban.html` gerekiyor: üst menü, alt bilgi, marka renkleri, **mobil önce**.
- Gün listesi için `core_views.gun_gun_mahalleler(magaza)` kullan, kendi gruplamanı yazma.

### 2c. Vitrin modu — artık alan var

`SatisAyarlari.vitrin_modu` geldi (`kapali` / `test` / `acik`). `getattr` numarasını
kaldır, doğrudan oku. Karar için `ayarlar.vitrin_gorunur_mu(request.user)` çağır:

| Mod | Davranış |
|---|---|
| `kapali` | Herkese yakında sayfası |
| `test` | Giriş yapmışsa vitrin, yapmamışsa yakında — **varsayılan** |
| `acik` | Herkese satış |

Test modunda üst tarafta `.test-serit` şeridi görünsün (tasarım dosyasında var):
*"Deneme modundasınız — siparişler gerçek değildir."* Varsayılan `test`, çünkü sanal POS
ve yasal metinler yok.

### 2d. Tasarım hazır — uydurmana gerek yok

`..\tasarim\bostanhane-tasarim-2.html` — kayıt, giriş, hesabım, siparişlerim, vitrin,
ürün sayfası, adreslerim, test modu şeridi. Sınıf adları ve yapı orada
(`.kart`, `.adet`, `.kesim`, `.test-serit`, `.alan`, `.onay`, `.adres-k`).
Her bölümün altındaki notlar **neden öyle** olduğunu anlatıyor; bazıları iş kuralı.
JPG'ler `..\tasarim\jpg\` altında.

---

## 3. Kurulmayı bekleyen eski `hazir/` dosyaları

Bir önceki talimatta vardı, raporda görmedim — kurulmadıysa bunlar da:

```powershell
Copy-Item hazir\ornek_veri.py core\management\commands\ornek_veri.py -Force
Copy-Item hazir\core_views.py core\views.py -Force
Copy-Item hazir\ana_sayfa.html templates\core\ana_sayfa.html -Force
Copy-Item hazir\ilk_veri.py core\management\commands\ilk_veri.py -Force
python manage.py ornek_veri --rotalari_esitle
```

Her mahalle **tek gün**, 13 mahalle altı güne dağıldı:

| Gün | Mahalleler (güzergâh sırası) |
|---|---|
| Pazartesi | İçerişehir · Müftü · Hamidiye |
| Salı | Bahçelievler · Esentepe |
| Çarşamba | Yeni · Beytepe |
| Perşembe | Hacıakif · Hacıarmağan |
| Cuma | Avşar · Evsat |
| Cumartesi | Dalyan · Yeşilyurt |

- `HizmetMahallesi.sira` artık **kurye güzergâhı**: `gün × 10 + gün içindeki sıra`.
- Model çok günü destekliyor; şablonlarda tek gün varsayma, listeyi dön.
- ⚠ Gün gruplaması **coğrafi değil, taslak** — Ersin `ornek_veri.GUN_ROTALARI`'ndan düzeltecek.
- `ana_sayfa.html`'de alt bilgi `{{ magaza.konum }}` oldu; `{{ magaza.ilce }}, {{ magaza.il }}`
  canlıda "Beyşehir / Konya, Konya" yazıyordu.

---

## 4. Bunları yapma

- **Sepet ve sipariş modeline dokunma.** Bende; değişiklik gerekirse rapora yaz.
- Ödeme ekranı, SMS doğrulama — sağlayıcılar seçilmedi.
- Paketleme ve kurye ekranları — Adım 6, sırası gelmedi.
- Canlıya `vitrin_modu = acik` yapma. Yasal metinler ve POS yok.

---

## 5. Raporda görmek istediklerim

- `makemigrations` çıktısı: üç uygulamada kaç migration, `roller_kur`'da `! atlandı` var mı
- Mağaza yöneticisi hesabıyla `/yonetim/siparis/siparis/` sayfasının açıldığı
- `ornek_veri --rotalari_esitle` çıktısı ve ana sayfanın gün kartlarıyla göründüğü
- Kayıt → giriş → adres ekleme → sepete ürün atma akışını uçtan uca denediğin
- Beyşehir dışı adreste "kurye gitmiyor" notunun çıktığı
- Taban şablonun telefon genişliğinde bozulmadığı
- Canlıda (Railway) migration'ların sorunsuz geçtiği — **PostgreSQL'de ilk kez çalışacak**

---

## Durum

**Bitti:** coğrafya · hizmet alanı (tek günlü rota) · hesaplar (modeller) · katalog
(birim tablosu, fiyat ekranı, stok defteri) · satış ayarları + vitrin modu ·
**sipariş motoru ve paneli** · görsel depolama (anahtar bekliyor).

**Şu anda:** üyelik + vitrin ekranları (sende) · alım listesi ekranı (bende).

**Sonra:** sepet ve ödeme ekranları · paketleme ve kurye ekranları · sanal POS.
