# RAPOR — Claude Code'dan Cowork'e

> **Bu dosya nasıl çalışıyor**
>
> Claude Code `talimat.md`'deki işleri yapar, sonucu buraya yazar. Ersin Cowork'e
> "rapor oku" der, Cowork buradan okur ve bir sonraki `talimat.md`'yi yazar.
>
> **Nasıl yazılır**
> - En yeni rapor **en üste** eklenir, eskiler altta kalır (silinmez — geçmiş lazım oluyor).
> - Her rapor tarihli bir `## ` başlıkla başlar.
> - Komut çıktısı kopyalanırken **son 10–20 satır** yeter, tamamı değil.
> - Söylenmesi gerekenler: ne yapıldı, ne çıktı, ne bozuk, ne karar bekliyor.
> - Bir dosyada Cowork'ün yazdığı bir şeyi düzelttiysen **hangi dosya, ne değişti,
>   neden** — yoksa Cowork bir sonraki sürümde üzerine yazar.
> - Tahmin ile gözlem ayrı yazılır: "log şunu diyor" ile "sanırım sebep şu" karışmasın.

---

## Şablon (kopyala, doldur, üste ekle)

```markdown
## GG Ay YYYY, saat — <kısa başlık>

### Yapıldı
- …

### Çıktılar
```
<komut çıktısının son satırları>
```

### Sorunlar
- …

### Değiştirdiğim dosyalar (Cowork'ün eşitlemesi için)
| Dosya | Ne değişti | Neden | `hazir/` eşi güncellendi mi |
|---|---|---|---|
| | | | |

### Karar bekleyen
- …
```

---

<!-- Raporlar buradan aşağıya, en yenisi en üstte. -->

## 1 Ekim 2026, akşam — Birim tablosu + stok ve stok defteri (Ersin'in isteği)

### İstek
Ersin (Ürünler ekran görüntüsü üzerinden): "satış" sütunu yerine **birim** (kg, adet, paket,
demet, kavanoz) yazsın ve birimler **eklenebilir** olsun; fiyatın yanında **stok** girilsin,
satış oldukça düşsün; mal gelince (10 kg, 5 paket) stok yanında **ekle / çıkar** olsun.

Plan Ersin'e anlatıldı, iki karar alındı:
- **Boş stok = sınırsız (takip yok).** "Önce talep, sonra alım" ilkesi yüzünden taze ürün
  stok tutmaz; stok yalnızca depoda bekleyen ürün (bal, bakliyat, yumurta) için. 0 olunca satılmaz.
- Uygula ve canlıya gönder.

### Yapıldı
**Birim artık tablo** (`katalog.Birim`: ad, kısaltma, kesirli, sıra, aktif). Panelde
KATALOG → Birimler; yönetici ekleyebilir, silmeyi yalnızca süper admin yapar (ürünü olan
birim zaten PROTECT). `Urun.birim` → yabancı anahtar. İlk 7 birim migration'la açılıyor
(boş veritabanında da). "Tartılı ürün kilogramla satılır" kuralı "kesirli birimle satılır"
oldu; kesirli olmayan birimde satış adımı tam sayı olmalı (yeni denetim).

**Stok:** `MagazaUrun.stok` (boş = takip yok) + **`StokHareketi`** defteri (tür: mal kabul,
fire, sayım düzeltmesi, satış, iade, takip kapatıldı; miktar ±, önceki/sonraki, kim).
- `stok_degistir()` satırı kilitler (`select_for_update`), eksiye düşürmez, deftere yazar.
- **`stok_dus(miktar)` Adım 5 için hazır:** sipariş kesinleşince çağrılacak; takipsiz üründe
  hiçbir şey yapmaz. `satista_mi` artık stok yetmiyorsa False.
- `stok_takibini_kapat()` + Mağaza ürünleri'nde "Stok takibini kapat" işlemi.
- Stok panelde elle yazılamaz (readonly); her değişim defterden geçsin diye.

**Ürünler listesi:** sütunlar → ürün · kategori · **birim** · fiyat·satışta · **stok** · …
Stok hücresi: `8,5 kg [ekle / çıkar]` → tür seçimi (Mal kabul (+) / Fire (−) / Sayım
düzeltmesi (±)) + miktar. Mal kabul hep ekler, fire hep çıkarır (işaret unutulsa da);
sayım yazıldığı gibi. Kesirli olmayan birime 1,5 girilemez. Düzenle hücresi ortak
(`duzenle_hucresi`), JS genelleştirildi (`.duzenle-*`; vazgeç bütün alanları ilk değere döndürür).

**Stok hareketleri** listesi (yalnızca okunur, mağaza kısıtlı) ve Mağaza ürünü sayfasında
hareket satırları.

**Migration elle yazıldı** (`katalog/0002_birim_tablosu_stok.py`): önce tablo, eski metin
değerleri taşınıyor, eski sütun sonra kalkıyor — Django'nun kendi ürettiği sürüm birimleri
silerdi. `makemigrations --check` → No changes detected.

**Cowork'ün bekleyen sürümleri kuruldu:** `hazir/katalog_models.py` (yeni ürüne otomatik
MagazaUrun sinyali) ve `hazir/urun_yukle.py` (`veri/` öncelikli yol, `--fiyatlari_guncelle`)
önce kuruldu, benim değişikliklerim onların üstüne yapıldı — ikisi de korunuyor.
`urun_yukle` birimi artık tablodan bulur; tanımsız birim satırı hata verir ("Birimler'den ekleyin").

### Test (yerel, işlem geri alındı)
```
Migration: kg 26 · paket 8 · demet 6 · adet 4 · kavanoz 4 · kutu 2 (=50) — denetimden geçmeyen ürün: yok
2) açılmadan Kaydet: [] → hareket 0
3) mal kabul: ['2 ürünün stoğu güncellendi (Bostanhane Beyşehir).'] → 10 kg, 5 paket
4) fire 2,5 kg → 7,5
5) fazla fire: 'Kaydedilmedi — Nohut, yerli (1 kg): Stok yetmiyor: 5 var, 6 çıkarılmak istendi.'
6) kesirli demet: 'Kaydedilmedi — Maydanoz: demet kesirli girilemez, tam sayı yazın'
8) fiyat+satışta+stok tek Kaydet: '1 ürünün fiyatı kaydedildi, 1 ürün satışa açıldı, 1 ürünün stoğu güncellendi'
9) stok_dus(4) → 0, satista_mi False · 11) takipsiz üründe stok_dus → dokunmadı
Sayfalar 200: birim, birim/add, stokhareketi, magazaurun change, urun change. Yönetici: 200, ekle/çıkar görünüyor.
Önceki fiyat testleri (1–4) aynen geçiyor; urun_yukle --kuru_prova çalışıyor.
```
Roller: Mağaza Yöneticisi 40 yetki (birim: gör/ekle/değiştir, stokhareketi: gör), Paketleme 9.
Düğmelerin tıklanması gerçek tarayıcıda denenmedi.

### Değiştirdiğim dosyalar (Cowork'ün eşitlemesi için)
| Dosya | Ne değişti | `hazir/` eşi |
|---|---|---|
| `katalog/models.py` | Birim modeli, Urun.birim FK, stok + stok yöntemleri, StokHareketi | **Evet** `hazir/katalog_models.py` |
| `katalog/admin.py` | BirimAdmin, birim/stok sütunları, stok kaydı, StokHareketiAdmin | **Evet** `hazir/katalog_admin.py` |
| `katalog/static/katalog/fiyat_duzenle.js` | Genel düzenle hücresi | **Evet** `hazir/katalog_fiyat_duzenle.js` |
| `katalog/management/commands/urun_yukle.py` | `birim_bul()` tablodan | **Evet** `hazir/urun_yukle.py` |
| `hesaplar/izinler.py` | katalog.birim, katalog.stokhareketi | **Evet** `hazir/hesaplar_izinler.py` |
| `katalog/migrations/0002_birim_tablosu_stok.py` | Yeni, elle yazıldı | Kopya: `hazir/katalog_migrations_0002_birim_tablosu_stok.py` |

### Adım 5 için not
Sipariş kesinleşince (kesim saati) her satır için `magaza_urun.stok_dus(miktar, kullanici)`
çağrılmalı; sepete eklerken `stok_yeterli_mi(miktar)` sorulmalı. Tartılı üründe düşülecek
miktar tahmini mi kesin mi (tartım sonrası) — karar gerekiyor.


## 1 Ekim 2026, akşamüstü — Satışta kutucuğu + görsel depolama (Aşama B)

### İş 1 — Fiyat ekranı
**1b'de Cowork'ün tarifinden ayrıldım — Ersin'in kararıyla.** Talimat sayfa başında tek
"Fiyatları düzenle" modu (`duzenle=1`) istiyordu; bir önceki raporda yazdığım satır başına
"düzenle" düğmesi zaten canlıdaydı. İkisini Ersin'e gösterdim, **satır başına düzenle'yi seçti.**
Koruma iki katmanlı, talimattaki "hem arayüzde hem kaydetme tarafında" şartı karşılanıyor:
- Arayüz: kutular `disabled` başlıyor, yalnızca o satırın "düzenle"si açıyor; "vazgeç" geri alıp kapatıyor.
- Sunucu: kapalı alan forma hiç gönderilmez; `fiyatlari_kaydet()` yalnızca gelen **ve**
  `*_ilk_<pk>` ile karşılaştırınca değişmiş alanları yazar. Açılmamış satıra POST'la yazılamaz.

**1a yapıldı:** aynı hücrede `satista_<pk>` onay kutusu + gizli `satista_ilk_<pk>`.
Düz görünüm: `32,90 ₺ / kg · ✓ satışta [düzenle]`. Sıra: fiyat → aktif → tek `full_clean()`.
`durum` listeye girmedi. Sütun adı: "fiyat · satışta".

**1c testleri** (yerel, işlem geri alındı):
```
1) açılmadan Kaydet: [] → None False
2) fiyat+satışta birlikte: ['2 ürünün fiyatı kaydedildi, 1 ürün satışa açıldı (Bostanhane Beyşehir).']
   → Domates 32.90 True | Salatalık 18.50 False
   süzgeç korundu: /yonetim/katalog/urun/?kategori__id__exact=1&o=1
3) fiyatsız satışa açma: ['Kaydedilmedi — Patlıcan: Ürünü satışa açmak için fiyat girilmeli.'] → False
4) satıştan çekme: ['1 ürün satıştan çekildi (Bostanhane Beyşehir).'] → 32.90 False
```
(Satır başına düzenlemede sayfa değişmediği için "moda geçince süzgeç korunuyor mu" testi
"kaydettikten sonra süzgeç korunuyor mu"ya dönüştü — korunuyor.)

### İş 2 — Görsel depolama, Aşama B
B1–B2 yapıldı (django-storages kuruldu; `settings.py`, `core/apps.py`, `requirements.txt`,
`env-ornek.txt` kopyalandı). Önceki rapordaki `env-ornek.txt` yorum notu yeni sürümde düzelmiş.
```
check (DEBUG=True):  System check identified no issues (0 silenced).
makemigrations --check --dry-run:  No changes detected
check (DJANGO_DEBUG=False):
?: (bostanhane.W001) Yüklenen görseller sunucu diskine yazılıyor; bir sonraki dağıtımda silinecek.
depolama: DefaultStorage → /medya/urun/deneme.jpg
```
`.env`'de `S3_` anahtarı yok — Ersin kovayı açıp girince depolama sınaması tekrar çalıştırılacak.

### Kurmadığım `hazir/` değişiklikleri
`hazir/katalog_models.py`, `hazir/urun_yukle.py`, `hazir/ilk_veri.py` kurulu sürümlerden farklı
ama bu talimatın kopyalama listesinde yok — **kurulmadı**. (Fark: `urun_yukle` varsayılan yolu
ve fiyat yazınca `aktif=True` yapan satırlar; `ilk_veri` mağaza kontrolü.) Kurulması isteniyorsa
talimata yazın.

### İş 3 — canlı
Push `09f265c`, dağıtım **SUCCESS**. Canlı: panel 200, ana sayfada 13 mahalle, yeni betik yüklü.
Satış ayarları ve Ürünler ekranının gözle kontrolü Ersin'de. `hazir/ana_sayfa.html`, `hazir/core_views.py`,
`hazir/ornek_veri.py` da değişmiş görünüyor — talimatta olmadığı için kurulmadı.
Talimattaki "50 ürünü aktarayım mı" sorusu önceden çözüldü: Ersin onayladı, canlıda 50 ürün var.

### İş 4 — Railway değişkenleri
Önceki raporda kapandı (Ersin kontrol etti, `/yonetim/` girişi çalışıyor).
Yeni: S3 değişkenleri (altı tane) kova açılınca Railway'e eklenecek.

### Değiştirdiğim dosyalar (Cowork'ün eşitlemesi için)
| Dosya | Ne değişti | Neden | `hazir/` eşi güncellendi mi |
|---|---|---|---|
| `katalog/admin.py` | Satışta kutucuğu, `_satista` annotate, `fiyatlari_kaydet` fiyat+aktif | İş 1a | **Evet** |
| `katalog/static/katalog/fiyat_duzenle.js` | vazgeç onay kutusunu da geri alır | İş 1a | **Evet** — `hazir/katalog_fiyat_duzenle.js` |


## 1 Ekim 2026, öğleden sonra (2) — Fiyat kutusu "düzenle" düğmesiyle açılıyor

### İstek
Ersin: fiyat bu kadar kolay değişmesin, yanında "düzenle" olsun, yanlışlıkla giriş olmasın.

### Yapıldı
- Fiyat artık düz yazı: **32,90 ₺** / kg  `[düzenle]`. Fiyatsız üründe kırmızı "fiyat yok" `[fiyat gir]`.
- "düzenle" kutuyu açar, "vazgeç" eski değere döndürüp kapatır.
- Kutu `disabled` başlıyor; kapalı kutu forma gönderilmediği için düzenle'ye basılmamış
  satırın fiyatı Kaydet'le değişemez. Sunucu tarafı aynı (yalnızca gelen ve değişen kutu yazılır).
- Betik: `katalog/static/katalog/fiyat_duzenle.js` (`UrunAdmin.Media`), satır içi JS yok.

### Test (yerel, geri alındı)
```
betik sayfada: True | "fiyat gir" düğmesi: True
kapalı kutu forma gidiyor mu: False
Düzenle'siz Kaydet: [] → fiyat None
Düzenle + Kaydet: ['1 ürünün fiyatı kaydedildi (Bostanhane Beyşehir).'] → fiyat 32.90
```
Düğmelerin tıklanması gerçek tarayıcıda denenmedi (sunucu tarafı test edildi); Ersin canlıda görecek.

### Değiştirdiğim dosyalar (Cowork'ün eşitlemesi için)
| Dosya | Ne değişti | Neden | `hazir/` eşi güncellendi mi |
|---|---|---|---|
| `katalog/admin.py` | `fiyat_kutusu` düz yazı + düzenle/vazgeç; `class Media` | Ersin'in isteği | **Evet** — `hazir/katalog_admin.py` |
| `katalog/static/katalog/fiyat_duzenle.js` | Yeni | Düğme davranışı | **Evet** — `hazir/katalog_fiyat_duzenle.js` (yeni) |


## 1 Ekim 2026, öğleden sonra — Ürünler listesine birimli fiyat kutusu (Ersin'in isteği)

### İstek
Ersin, **Ürünler** listesinde (`/yonetim/katalog/urun/`) fiyatın birimiyle birlikte
görünmesini ve fiyatın oradan girilip değiştirilebilmesini istedi.

### Yapıldı
- Listeye **fiyat** sütunu: `[ 32,90 ] ₺ / kg`, `[ 15,00 ] ₺ / demet` gibi. Kaydet'e
  basınca fiyat ilgili `MagazaUrun` kaydına yazılır (kayıt yoksa açılır).
- `list_editable` yalnızca modelin kendi alanlarını kabul ettiği için kutu
  `format_html` ile çiziliyor, kayıt `changelist_view` → `fiyatlari_kaydet()` içinde.
  Fiyat listeye `Subquery` ile tek sorguda ekleniyor.
- **Hangi mağazanın fiyatı:** personel → kendi mağazası; süper admin → yeni
  "fiyat mağazası" süzgeci (ürünü süzmez, yalnızca mağaza seçer), varsayılan ilk aktif mağaza.
- Yalnızca değişen kutular yazılır (gizli `fiyat_ilk_<pk>` ile karşılaştırılıyor) — aynı
  anda "Mağaza ürünleri"nden girilen fiyatın üzerine basılmasın diye.
- `MagazaUrun.full_clean()` çağrılıyor: satıştaki ürünün fiyatı silinemiyor, eski fiyat
  kuralı korunuyor. Okunamayan değer ("abc") ürün adıyla hata mesajı veriyor.
  `32,90`, `32.90`, `1.250,50`, `32,90 ₺` hepsi okunuyor.
- `katalog.change_magazaurun` yetkisi olmayan (ör. ileride paketleme) yalnızca düz metin görür.

### Test (yerel, işlem geri alındı)
```
GET 200 kutu var: True | birim: True
POST ['1 ürünün fiyatı kaydedildi (Bostanhane Beyşehir).', 'Kaydedilmedi — Patates: “abc” fiyat olarak okunamadı']
Sil denemesi: ['Kaydedilmedi — Domates: Ürünü satışa açmak için fiyat girilmeli.'] → 32.90
demet birimi: True
magaza_yoneticisi 200 | kutu: True | mağaza süzgeci: False
```

### Değiştirdiğim dosyalar (Cowork'ün eşitlemesi için)
| Dosya | Ne değişti | Neden | `hazir/` eşi güncellendi mi |
|---|---|---|---|
| `katalog/admin.py` | `fiyat_yaz`, `fiyat_oku`, `FiyatMagazasiSuzgeci`; `UrunAdmin`'e `fiyat_kutusu`, `get_queryset`, `get_list_filter`, `changelist_view`, `fiyatlari_kaydet` | Ersin'in isteği | **Evet** — `hazir/katalog_admin.py` birebir aynı |

"Mağaza ürünleri" listesi olduğu gibi duruyor; ikisi aynı kayda yazar.

## 1 Ekim 2026, öğle — Rota eşitleme + Adım 4 (katalog) yerelde kuruldu, push edildi

### Sıra değişti — neden
Talimattaki İş 1 (`ornek_veri --rotalari_esitle`) tek başına çalışamazdı: yeni
`ornek_veri.py` `SatisAyarlari`'nı içe aktarıyor, o model ise İş 5'teki `core_models.py` ile
geliyor. Ersin'in onayıyla sıra: önce yerelde Adım 4'ün tamamı + eşitleme, sonra tek push.

### Yapıldı
- `pip install -r requirements.txt` (openpyxl), `startapp katalog`, `adim-4-katalog.md` A3'teki
  dosyalar + `core_models.py`, `core_admin.py`, `ornek_veri.py` yerine kondu.
- `makemigrations core` (`0002_satisayarlari`), `makemigrations katalog` (`0001_initial`), `migrate`, `roller_kur`.
- `ornek_veri --rotalari_esitle` iki kez (ikincisi tekrar-çalıştırma testi).
- `urun_yukle --kuru_prova`, sonra `urun_yukle`.
- CLAUDE.md: komut tablosuna `urun_yukle` satırı + `--rotalari_esitle` notu (talimattaki metin aynen).
- Argümansız `format_html(...)` araması: projede yok.
- Push: `330ef86 Adim 4: katalog, satis ayarlari ve ornek_veri --rotalari_esitle`.

### Çıktılar
```
  − Müftü: Salı kaldırıldı
  − Müftü: Cuma kaldırıldı
  − Bahçelievler: Çarşamba kaldırıldı
  − Yeni: Pazartesi kaldırıldı
  − Yeni: Cuma kaldırıldı
Beyşehir'de 70 mahalle tanımlı: 13 aktif, 57 pasif.
Eşitleme: 5 fazla teslim günü ve 39 takvim kaydı silindi.
```
İkinci çalıştırma: `Eşitleme: 0 fazla teslim günü ve 0 takvim kaydı silindi.` ve
`Satış ayarları: minimum 500 ₺ · teslimat 50 ₺ · ücretsiz eşiği 1000 ₺ (panelden değiştirilir)`.
13 mahallenin günleri tam rotada (tablodaki gibi). Yerel ana sayfada 13 mahalle rozeti.

```
50 yeni ürün, 0 güncellenen, 6 yeni kategori, 0 fiyat yazıldı.
50 ürünün fiyatı yok, bu yüzden satışa açılmadı.
```
Kayıt sayıları: Kategori 6 · Urun 50 · MagazaUrun 50 · SatisAyarlari 1.
Panel (süper admin, test istemcisi): `/yonetim/`, katalog kategori/ürün/mağaza ürünü,
`core/satisayarlari`, `core/magaza`, `core/hizmetmahallesi`, `/` → hepsi **200**.
Roller: Mağaza Yöneticisi 36, Paketleme 7, Kurye 5 yetki.

### Sorunlar / gözlemler
- **39 vs 40 takvim kaydı:** Beklenen 40, silinen 39. Bugün ve geçmiş tarihli takvim kaydı
  yok, yani "geçmişe dokunmama" kuralından değil. Tahmin: yereldeki takvim 30 Eylül'de
  üretildi, sandbox'takinden bir hafta-sonu günü kaymış. Sonuç doğru (günler rotada).
- **`env-ornek.txt` yorumu eski:** "burada değiştirip yeniden başlatmak yeter" diyor; artık
  bu değerler yalnızca yeni mağazanın ilk `SatisAyarlari` kaydını oluşturuyor, sonrası panelde.
  Cowork düzeltsin (dosyayı değiştirmedim).
- **Canlıda ürün yok:** Excel repoda değil (`..\icerik\`), canlıda `urun_yukle` çalışamaz.
  Adım 4 talimatı "panelden elle girin" diyor — 50 ürünü elle girmek uzun. Karar bekliyor (aşağıda).

### Değiştirdiğim dosyalar (Cowork'ün eşitlemesi için)
| Dosya | Ne değişti | Neden | `hazir/` eşi güncellendi mi |
|---|---|---|---|
| `CLAUDE.md` | Komut tablosuna `urun_yukle`, altına `--rotalari_esitle` notu | Talimat İş 3 | — (hazir'de eşi yok) |

Kurulan diğer bütün dosyalar `hazir/` ile birebir aynı.

### Canlı — durum
- Railway dağıtımı **SUCCESS** (08:25 UTC, commit `330ef86`). Site ve `/yonetim/login/` 200.
- Canlı ana sayfa hâlâ 3 eski mahalle — beklenen; `ornek_veri --rotalari_esitle` canlıda
  henüz çalıştırılmadı (Claude Code'un canlıda komut izni yok, Ersin'in çalıştırması bekleniyor).

- **Ürünler (Ersin'in kararı: aktar):** `..\icerik\urunler.xlsx` → `veri/urunler.xlsx` olarak
  repoya kopyalandı (commit `ba367b9`, dağıtım SUCCESS). Asıl kaynak hâlâ `..\icerik\`;
  Excel güncellenirse `veri/` kopyası da yenilenmeli.
- **Canlı eşitleme yapıldı** (Ersin çalıştırdı): yereldekiyle aynı çıktı — 5 fazla gün,
  39 takvim kaydı silindi; 10 yeni merkez + 57 pasif köy mahallesi; 203 takvim günü;
  satış ayarları kaydı açıldı. Canlı ana sayfada **13 mahalle doğru günleriyle** görünüyor.
- **Canlı ürün aktarımı yapıldı** (Ersin çalıştırdı): `50 yeni ürün, 0 güncellenen, 6 yeni
  kategori, 0 fiyat yazıldı.` Hepsi fiyatsız, satışa kapalı. Fiyatlar canlı panelden girilecek:
  `/yonetim/katalog/magazaurun/`. **Canlı tarafta bekleyen iş kalmadı.**
- Çalıştırılan iki komut (Claude Code'a canlıda komut izni verilmedi, Ersin çalıştırdı):
  `railway ssh --service web python manage.py ornek_veri --rotalari_esitle`
  `railway ssh --service web python manage.py urun_yukle --dosya veri/urunler.xlsx`

### İş 4 — Railway değişkenleri
Ersin panelden listeyi gönderdi (değerler gizli): `DATABASE_URL`, `DJANGO_ALLOWED_HOSTS`,
`DJANGO_DEBUG`, `DJANGO_SECRET_KEY`, `PORT`, `YONETICI_AD`, `YONETICI_TELEFON`.
- `YONETICI_KULLANICI` **yok** — doğru.
- `YONETICI_SIFRE` **yok.** Ya hesap açıldıktan sonra silindi (doğru), ya da hiç tanımlanmadı —
  o durumda `ilk_yonetici` "hesap oluşturulmadı" der ve canlıda süper admin yoktur.
  Ersin'in `/yonetim/` girişini denemesi bunu ayırt eder.
  **Ersin doğruladı:** hesap açıldıktan sonra silindi; canlıda `/yonetim/` girişi çalışıyor. İş 4 tamam.
- `DATABASE_URL`'in değeri (`${{Postgres.DATABASE_URL}}` mi) görülmedi; site ve panel
  çalıştığına göre bağlantı doğru (çıkarım).

### Karar bekleyen
- Canlıya 50 ürün nasıl gidecek: (a) panelden elle, (b) `urunler.xlsx`'i repoya
  (ör. `veri/urunler.xlsx`) koyup canlıda bir kez `urun_yukle --dosya veri/urunler.xlsx`.
  Claude Code (b)'yi öneriyor: fiyatlar sonra canlı panelden girilir, ayrışma olmaz.

## 1 Ekim 2026, sabah — Yeni ornek_veri yerelde kuruldu; canlıda eski 3 mahalle duruyor

### Yapıldı
- `hazir/ornek_veri.py` → `core/management/commands/ornek_veri.py` kopyalandı, yerelde çalıştırıldı.
- Railway ayarları CLI ile okundu (yalnızca durum bilgisi).
- Canlı site, `/yonetim/` ve www'suz adres dışarıdan (`curl`) kontrol edildi.
- Kod commit + push edildi (bu rapor dahil).

### Çıktılar

**İş 1 — yerel `ornek_veri` son satırları:**
```
Köy kökenli mahalleler: 57 kayıt pasif (57 yeni). Teslim günü tanımlanmadı.

Tamam. Takvime 203 teslim günü eklendi.
Beyşehir'de 70 mahalle tanımlı: 13 aktif, 57 pasif.
```
Veritabanı sorgusu: **13 aktif, 57 pasif** hizmet mahallesi (panel listesi aynı tablodan okur).

**İş 2 — canlı ortam:**
- Start Command: **boş** (`""`). Sorun bu değil.
- Servisler: `web` ve `Postgres`, ikisi de son dağıtımda SUCCESS (30 Eylül ~20:40 UTC).
- Canlı ana sayfa mahalle listesini **gösteriyor** — ama eski sürümü:
  ```
  Yeni · Pazartesi ve Cuma
  Müftü · Salı ve Cuma
  Bahçelievler · Çarşamba
  ```
  Yani canlıda mağaza var, `ilk_veri` eski `ornek_veri` ile çalışmış. Talimattaki
  "liste hiç yok" gözlemi muhtemelen sayfa önbelleği / yeniden dağıtım öncesi bir anına ait (tahmin).
- Deploy logları ve değişkenler (`DATABASE_URL`, `YONETICI_TELEFON`, `YONETICI_AD`,
  `YONETICI_KULLANICI`) **okunamadı**: canlı ortam okuması için Claude Code'a izin verilmedi.
  Ersin'in Railway panelinden bakması ya da izni açması gerekiyor.
- Canlıda kaç mağaza / hizmet mahallesi olduğu doğrudan sayılamadı; sayfaya göre 1 mağaza, 3 aktif mahalle.

**İş 3:**
- Push sonrası Railway dağıtımı: **SUCCESS** (1 Ekim 07:31 UTC). Canlı sayfa beklendiği gibi
  hâlâ eski 3 mahalleyi gösteriyor (veri değişmedi).
- `/yonetim/` → 302 (giriş sayfasına yönlendiriyor, çalışıyor). Giriş denemesi Ersin'e kaldı.
- `https://bostanhane.com` ve `http://bostanhane.com` → **301 → `https://www.bostanhane.com`**
  (Squarespace). HTTPS sertifikası geçerli. Apex yönlendirmesi **tamam**.

### Sorunlar
1. **Eski kurallar yeni kurallarla birleşiyor.** `ornek_veri` var olan `HaftalikTeslimGunu`
   kayıtlarını silmediği için eski 3 mahallede gün sayısı arttı:
   ```
   Müftü         Pazartesi, Salı, Perşembe ve Cuma   (olması gereken: Pzt + Per)
   Bahçelievler  Salı, Çarşamba ve Cuma              (olması gereken: Salı + Cuma)
   Yeni          Pazartesi, Çarşamba, Cuma, Cumartesi (olması gereken: Çar + Cmt)
   ```
   Yerelde de canlıda da aynı olur. Bu yüzden **canlıda `ornek_veri`'yi henüz çalıştırmadım**;
   çalışsa canlı sayfa bu yanlış günleri gösterecek. Push sadece kodu günceller: `ilk_veri`
   mağaza var diye atlar, canlı veri değişmez.
2. Eski kurallardan üretilmiş `TeslimTakvimi` günleri de var; kural silinince bunların da
   (sipariş bağlı olmadığı için) temizlenmesi gerekir.

### Değiştirdiğim dosyalar (Cowork'ün eşitlemesi için)
| Dosya | Ne değişti | Neden | `hazir/` eşi güncellendi mi |
|---|---|---|---|
| `core/management/commands/ornek_veri.py` | `hazir/` sürümüyle değiştirildi, içerik aynı | Talimat İş 1 | Zaten aynı |

### Karar bekleyen
- **Eski günler nasıl temizlensin?** Öneri: tek seferlik bir düzeltme — 3 eski mahallede rota
  dışındaki `HaftalikTeslimGunu` kayıtlarını ve onlardan üretilmiş gelecekteki
  `TeslimTakvimi` günlerini silmek (gerçek sipariş yok, kayıp yok). Ya `ornek_veri`'ye
  `--rotalari_esitle` gibi bir seçenek olarak (Cowork yazar), ya da Claude Code yerelde
  ve canlıda bir kez elle yapar. Bu karar verilince canlıda `ornek_veri` çalıştırılacak.
- Railway log/değişken okuması için izin (veya Ersin panelden bakıp yazsın).

### Ersin'in kararı (1 Ekim)
**Temizliği Cowork `ornek_veri`'ye eklesin.** Claude Code'un önerisi:
- Merkez mahallelerinde `ROTA_GUNLERI` dışında kalan `HaftalikTeslimGunu` kayıtlarını silen
  bir seçenek (ör. `--rotalari_esitle`). Varsayılan davranış "var olana dokunma" olarak kalsın;
  panelden yapılan elle değişiklikler yanlışlıkla silinmesin.
- Silinen kuraldan üretilmiş, **bugünden sonraki** ve siparişi olmayan `TeslimTakvimi` günleri
  de silinsin (sipariş modeli henüz yok, ama koşul şimdiden yazılırsa ileride güvenli kalır).
- Komut sildiği her kuralı ekrana yazsın ("− Müftü: Salı kaldırıldı").
- Dosya `hazir/ornek_veri.py` olarak gelince Claude Code yerelde ve canlıda bir kez
  `python manage.py ornek_veri --rotalari_esitle` çalıştırıp sonucu raporlayacak.
