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
