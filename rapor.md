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

### İş 4 — Railway değişkenleri
Claude Code okuyamıyor (izin yok). Ersin panelden bakıp yazacak:
`DATABASE_URL`, `YONETICI_TELEFON`, `YONETICI_AD` tanımlı mı, `YONETICI_KULLANICI` silinmiş mi.

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
