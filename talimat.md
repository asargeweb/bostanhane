# TALİMAT — Claude Code için

> **Bu dosya nasıl çalışıyor**
>
> Ersin iki asistanla çalışıyor: **Cowork** (tarayıcıdaki Claude — planlar, araştırır,
> hazır dosya yazar) ve **Claude Code** (VS Code'daki Claude — komut çalıştırır, kodu
> kurar, canlıya alır).
>
> İkisi bu iki dosyayla konuşur:
>
> | Dosya | Kim yazar | Kim okur |
> |---|---|---|
> | `talimat.md` | Cowork | Claude Code |
> | `rapor.md` | Claude Code | Cowork |
>
> Ersin "talimat oku" dediğinde Claude Code bu dosyayı okur ve **Yapılacaklar**
> bölümündeki işleri sırayla yapar. Bitince sonucu `rapor.md`'ye yazar; Ersin
> Cowork'e "rapor oku" der.
>
> **Kurallar**
> 1. Bu dosyayı Claude Code **değiştirmez**, sadece okur. Söyleyeceği her şey `rapor.md`'ye.
> 2. `hazir/` klasöründeki dosyaları Cowork yazar. Claude Code kurulu bir dosyada
>    (`core/admin.py` gibi) düzeltme yaparsa **aynı düzeltmeyi `hazir/` içindeki
>    eşine de uygular** ve `rapor.md`'de "şunu değiştirdim" diye bildirir — yoksa
>    Cowork'ün sonraki dosyası düzeltmenin üzerine yazar.
> 3. Geri alınamaz bir iş (veritabanı silme, `git push --force`, servis silme) önce
>    Ersin'e sorulur.
> 4. Ersin'in yazılım deneyimi yok. Komutları çalıştır, ona ne yaptığını sade
>    Türkçe anlat, terminale yazmasını isteme — interaktif soru (şifre gibi) çıkarsa
>    dur ve ne yazması gerektiğini söyle.
>
> Proje bağlamı: `CLAUDE.md`. Adım talimatları: `adim-*.md`.

---

# Yapılacaklar — 30 Eylül 2026, akşam

Üç iş var. Sırayla. Her birinin sonunda `rapor.md`'ye ne bulduğunu yaz.

---

## 1. Yeni `ornek_veri` kurulu değil — merkez mahalleleri eksik

**Durum:** `hazir/ornek_veri.py` güncellendi (13 merkez mahallesi aktif + 57 köy
kökenli mahalle pasif), ama `core/management/commands/ornek_veri.py` hâlâ eski
üç mahalleli sürüm (4170 bayt; yenisi 6356 bayt).

```powershell
Copy-Item hazir\ornek_veri.py core\management\commands\ornek_veri.py -Force
python manage.py ornek_veri
```

**Beklenen çıktı** — son satırlar:

```
Köy kökenli mahalleler: 57 kayıt pasif (57 yeni). Teslim günü tanımlanmadı.
Beyşehir'de 70 mahalle tanımlı: 13 aktif, 57 pasif.
```

Aktif olması gereken 13 merkez mahallesi ve rotaları:

| Rota | Günler | Mahalleler |
|---|---|---|
| 1 | Pazartesi, Perşembe | Müftü, Hamidiye, Dalyan, Esentepe, Beytepe |
| 2 | Salı, Cuma | Bahçelievler, Hacıakif, Hacıarmağan, Evsat |
| 3 | Çarşamba, Cumartesi | Yeni, İçerişehir, Avşar, Yeşilyurt |

Köy kökenli 57 mahalle **pasif kayıt** olarak duruyor: teslim günü yok, takvim yok,
sipariş almıyor. Panelden `aktif` kutucuğu işaretlenince açılacak.

`rapor.md`'ye yaz: komutun son üç satırı, `/yonetim/core/hizmetmahallesi/` sayfasında
kaç aktif kaç pasif göründüğü.

---

## 2. Canlı sitede mahalle listesi görünmüyor

**Durum:** `https://www.bostanhane.com` açılıyor ama **mahalle listesi yok** — sayfa
"Beyşehir'de kısa süre içinde başlıyoruz" diyor, altında mahalle rozetleri çıkmıyor.
Bu, canlı veritabanında mağaza veya hizmet mahallesi kaydı olmadığı anlamına gelir.

Sen de not düşmüşsün: Railway'de **Start Command** doluysa `Procfile`'ı geçersiz kılıyor
ve `roller_kur` / `ilk_yonetici` / `ilk_veri` atlanıyor. Muhtemel sebep bu.

Sırayla kontrol et:

1. Railway → web servisi → **Settings → Deploy → Start Command** **boş** mu?
   Doluysa temizle.
2. **Deploy Logs**'ta şu satırlar geçiyor mu:
   - `Applying core.0001_initial... OK`
   - `+ Mağaza Yöneticisi: ... yetki`
   - `+ Süper admin oluşturuldu: Ersin Öztürk (5330317288)`
   - `Konya / Beyşehir: 70 mahalle`
   - `+ Mağaza: Bostanhane Beyşehir (Beyşehir, Konya)`
3. `DATABASE_URL` yeni PostgreSQL servisinin adıyla eşleşiyor mu
   (`${{Postgres.DATABASE_URL}}` — servisin adı farklıysa o ad yazılmalı).
4. `YONETICI_TELEFON` = `5330317288` ve `YONETICI_AD` = `Ersin Öztürk` tanımlı mı?
   `YONETICI_KULLANICI` silinmiş mi?

**Önemli tuzak:** `ilk_veri` yalnızca **hiç mağaza yokken** `ornek_veri`'yi çağırır.
Canlıda mağaza zaten oluşmuşsa yeni 10 merkez mahallesi ve 57 pasif kayıt eklenmez.
O durumda canlıda bir kez elle `python manage.py ornek_veri` çalıştırmak gerekir
(Railway'in komut çalıştırma alanından ya da `railway run` ile).

`rapor.md`'ye yaz: Start Command doluydu mu, loglarda hangi satırlar vardı hangileri
yoktu, canlı veritabanında kaç mağaza / kaç hizmet mahallesi var.

---

## 3. Push ve canlı doğrulama

1. Kodu gönder:

```powershell
git add .
git commit -m "Adim 3B: merkez mahalleleri aktif, koy kokenli mahalleler pasif"
git push
```

2. Railway dağıtımının yeşile döndüğünü gör.
3. `https://www.bostanhane.com` → **13 mahalle ve teslim günleri** listelenmeli.
4. `https://www.bostanhane.com/yonetim/` → `5330317288` ile giriş yapılabilmeli.

Bir de şunu kontrol et: `https://bostanhane.com` (başında `www` olmadan) açılıyor mu,
adres çubuğunda kilit simgesi var mı? Squarespace'te apex → `https://www.bostanhane.com`
301 yönlendirmesi yapılacaktı; yapılmamışsa `rapor.md`'ye yaz, Ersin'e tarif edelim.

---

## Yapma

- Veritabanını yeniden silme. Gerekirse önce Ersin'e sor.
- `hazir/` dosyalarını Cowork'e haber vermeden yeniden yazma (Kural 2).
- Adım 4 (`katalog`) kodunu yazmaya başlama — ürün listesi henüz gelmedi, gerçek
  alanlar belli değil. Cowork ürün listesi taslağını hazırlıyor.
