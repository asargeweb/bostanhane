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
> 5. **Yeni:** Her talimat tarihli başlıkla **en üste** eklenir, eskiler altta kalır.
>    Raporunun ilk satırına *"okuduğum talimat: 2 Ekim (1)"* yaz — hangisini okuduğun belli olsun.
>
> Bağlam: `CLAUDE.md` · Tasarım: `..\tasarim\bostanhane-tasarim-2.html` · Ersin: `YAPILACAKLAR.md`

---

## 2 Ekim 2026 (1) — Kayıp talimat benim hatam; para biçimi düzeltildi

### Önce: haklısın, hata bende

"Aradaki talimat ben okumadan üzerine yazılmış olmalı" dedin — aynen öyle olmuş.
Ben `talimat.md`'yi her seferinde **baştan yazıyordum**. Sen bir talimatı okumaya
yetişemeden ben üzerine yenisini yazdım, o talimat kayboldu. Sonra da "rapor yazmamışsın"
diye seni suçladım; rapor yerindeydi, eksik olan benim tarafımdaydı. Ersin'e de söyledim.

Bu yüzden yukarıdaki **5. kural** geldi: talimat da artık rapor gibi birikiyor, en yenisi
en üstte, eskisi silinmiyor. Raporunun başına hangi talimatı okuduğunu yaz; biri atlanırsa
ikimiz de görürüz.

**Deneme siparişi düğmen doğru karar.** Talimat "ödeme ekranı yapma" diyordu, sen ödeme
yapmadın; `siparise_cevir`'i çağırıp test siparişi açtın. Ersin'in "sanki canlı satış
yapıyor gibi" isteği ancak böyle görünür hale geliyor. Kalsın.

Yazdıklarını okudum: üyelik, vitrin, sepet, siparişlerim, adres akışı, 390 px'te dokuz sayfa.
Ziyaretçi sepetini girişten **önce** alıp sonra birleştirmen ince bir ayrıntı — Django girişte
oturum anahtarını değiştiriyor, bunu kaçırsaydın müşteri giriş yapınca sepetini kaybederdi.

---

### 1. Para biçimi — senin bulduğun hata, benim kodumda

Haklıydın: `siparise_hazir_mi` *"450.65 ₺ daha eklemelisiniz"* diyordu. Noktalı.
Sende `bostan.para` filtresi doğru yazıyordu ama model metni kapalı düğmenin altında
İngilizce biçimde kalıyordu.

Üç yerde ayrı ayrı biçimleme vardı (senin filtren, benim panel yardımcım, model metni).
**Tek kaynağa indirdim:** `core/araclar.py` içinde `para_yaz()`.

```python
para_yaz("1250.5")                      # '1.250,50 ₺'
para_yaz("500", kurusu_gizle=True)      # '500 ₺'      (yuvarlak eşiklerde)
para_yaz("499.5", kurusu_gizle=True)    # '499,50 ₺'   (yuvarlak değilse kuruş görünür)
para_yaz(None)                          # '—'
```

Kurulum:

```powershell
Copy-Item hazir\core_araclar.py   core\araclar.py    -Force
Copy-Item hazir\siparis_models.py siparis\models.py  -Force
Copy-Item hazir\siparis_admin.py  siparis\admin.py   -Force
```

Migration gerekmez — alan değişmedi, yalnızca metin.

Yeni sepet uyarısı: **"Minimum sepet tutarı 500 ₺. 450,65 ₺ daha eklemelisiniz."**

**Senden iki küçük iş:**

1. `core/templatetags/bostan.py` içindeki `para` filtresi artık `para_yaz`'ı çağırsın,
   kendi biçimlemesini tutmasın. İki yerde iki biçim kalırsa bir gün ayrışırlar.
   (`miktar`, `yuzde`, `mutlak` filtrelerine dokunma, onlar başka iş.)
2. Panelde iki yerde `:.0f` kalmış, bin ayırıcısı yok — `1000 ₺` yerine `1.000 ₺` olmalı:
   - `core/admin.py` → satış ayarları özet satırı ("… üstü ücretsiz")
   - `katalog/admin.py` → fiyat sütunu, kendi biçimlemesini yapıyorsa
   Bu iki dosya artık senin elinde (benim kopyam eski), onun için bende düzeltmedim.
   Düzeltirsen `hazir/` eşlerine de uygula.

---

### 2. Beyşehir dışı adres — kararı veriyorum

Sorunu doğru koymuşsun: veritabanında yalnızca Beyşehir'in 70 mahallesi var, başka ilçe
seçilince *"Bu bölgenin listesi henüz yüklü değil"* çıkıyor.

**Türkiye'nin bütün mahallelerini yüklemiyoruz.** Elle yazılacak veri değil, hazır bir
kaynak gerekir ve bugün kimse Beyşehir dışına sipariş veremiyor — kargo kanalı kapalı.
Yüklesek de ölü veri olurdu.

Ama **çıkmaz sokak da bırakmıyoruz.** Müşteri başka ilçeyi seçtiğinde hata değil, davet
görsün. Şöyle yap:

- Mahalle listesi boş dönen ilçede: *"Buraya henüz kargo göndermiyoruz. Açıldığında haber
  vermemiz için mahallenizi yazın."*
- Altına **tek satır serbest metin alanı** + e-posta/telefon zaten hesabında var.
- Kaydet'e basınca `core.IlgiKaydi` kaydı aç (model zaten var, ana sayfadaki "yakında"
  formu da onu kullanıyor): ilçe + yazdığı mahalle + kullanıcı.
- Adres **oluşturulmaz** — mahallesiz adres kurye için anlamsız. Mesaj: *"Teşekkürler,
  haber vereceğiz."*

Böylece "nereye talep var" sorusunun cevabı kendiliğinden birikiyor. Karaman ve Konya
merkez sırası gelince hangi mahallelerin verisi gerektiğini bu listeden okuyacağız.

---

### 3. Canlı gün düzeni — Ersin'e sordum, bekliyoruz

`ornek_veri --rotalari_esitle` canlıda **henüz çalıştırılmayacak.** Sebep: benim gün
gruplaması coğrafi değil, taslak. Canlıda şu an eski iki günlü düzen görünüyor
(Pazartesi: Müftü · Dalyan · Esentepe; Çarşamba: Yeni · İçerişehir · Avşar · Yeşilyurt).
Yanlış bir düzeni başka bir yanlış düzenle değiştirmenin anlamı yok.

Ersin'den doğru gruplamayı istedim. Geldiğinde `ornek_veri.GUN_ROTALARI` tablosunu
güncelleyip sana vereceğim; o zaman tek seferde canlıya uygularız. Senden bir şey istemiyorum,
sadece bilmen için — raporunda "neden çalıştırmadım" diye yazma, karar bu.

---

### 4. Aydınlatma metni — bende

Kayıtta *"(Metin hazırlanıyor.)"* yazıyor. KVKK aydınlatma metnini, gizlilik politikasını
ve mesafeli satış sözleşmesini ben yazıyorum. İkisi için Ersin'den şirket bilgisi
(unvan, vergi no, adres) lazım, istedim.

Gelince `hazir/` içine düz metin olarak koyacağım, sen şablona bağlarsın. Sen yazmaya
kalkma — yasal metin uydurulmaz.

---

### 5. Sıradaki iş

**Sende — paketleme ekranı (Adım 6a).** Sipariş motoru ve vitrin bitti; sıra malın
toplanmasına geldi. Tablet için, Django panelinden ayrı, sade:

| Adres | Ne |
|---|---|
| `/depo/` | Bugünün ve yarının teslim günleri, her birinde kaç sipariş, kesildi mi |
| `/depo/alim/<takvim>/` | **Alım listesi** — ürün ürün toplam miktar (bu ekranı ben yazıyorum, aşağıda) |
| `/depo/toplama/<siparis>/` | Tek siparişin satırları; her satırda tartım kutusu, "bulunamadı" düğmesi |

- Giriş: `Rol.PAKETLEME` **ve** `Rol.MAGAZA_YONETICISI`. Paketleme elemanı `/yonetim/`'e
  giremez (`is_staff` False) — bu ekranlar normal görünüm, panel değil.
- Tartımı kendin hesaplama: `kalem.tartim_gir(miktar, kullanici=request.user)`.
  "Bulunamadı" = `tartim_gir(0)`.
- Yalnızca kendi mağazasının siparişleri. Sorguda `magaza=request.user.magaza`.
- Parmakla kullanılacak: büyük düğmeler, büyük yazı, tek elle erişilebilir. Tasarım
  dosyasında bu ekranlar yok, marka renkleriyle sade kur.
- **Kesilmemiş günde toplama ekranı açılmasın** — sipariş hâlâ değişebilir.

**Bende — alım listesi ekranı.** `alim_listesi(magaza, tarih)` işlevi hazır, ekranı ben
yazıp `hazir/` içine koyacağım. `/depo/alim/<takvim>/` adresini bana bırak, çakışmasın.

---

### 6. Raporda görmek istediklerim

- `okuduğum talimat: 2 Ekim (1)` satırı
- Sepet uyarısının yeni hali ("450,65 ₺")
- `bostan.para` filtresinin `para_yaz`'a bağlandığı
- Beyşehir dışı ilçede ilgi kaydının açıldığı, adresin açılmadığı
- Paketleme ekranında bir siparişin tartılıp bitirildiği, tutarın düzeldiği
- Kesilmemiş günde toplama ekranının açılmadığı

---

### 7. Bunları yapma

- Sepet/sipariş modeline dokunma, alım listesi ekranını yazma — bende.
- Yasal metin yazma — bende.
- Canlıda `ornek_veri --rotalari_esitle` çalıştırma — Ersin'in gruplaması bekliyor.
- Canlıda `vitrin_modu = acik` yapma — POS ve yasal metinler yok.
- Kurye ekranı (Adım 6b) — paketleme bitince.

---

## Durum

**Bitti:** coğrafya · hizmet alanı · hesaplar · katalog (birim, fiyat, stok defteri) ·
satış ayarları + vitrin modu · sipariş motoru ve paneli · üyelik · vitrin · sepet ·
siparişlerim — **canlıda**.

**Şu anda:** paketleme ekranı (sende) · alım listesi ekranı + yasal metinler (bende).

**Sonra:** kurye ekranı · sanal POS · kargo kanalı · kampanya · abonelik.

---
---

## 1 Ekim 2026 (2) — Adım 5 `siparis` + üyelik/vitrin talimatı

> Bu talimat uygulandı, raporu geldi. Geçmiş için bırakıldı; kurulum sırası ve
> sipariş motorunun nasıl çağrıldığı burada anlatılıyor.

### Sipariş motoru — çağrı noktaları (hâlâ geçerli referans)

- `sepet.ekle(magaza_urun, miktar)` — var olan satıra **ekler**, üzerine yazmaz.
- `sepet.birlestir(kaynak_sepet)` — ziyaretçi sepetini üyeye katar.
- `sepet.siparise_hazir_mi()` → `(True/False, sebep)`. Sebep kullanıcıya gösterilmeye hazır.
- `sepet.siparise_cevir(kullanici=..., kanal=...)` — satırları ve adresi kopyalar,
  **stoğu o anda düşer**, tutarları dondurur. Numara `BH-2026-000001`.
- `kalem.tartim_gir(miktar, kullanici=...)` — farkı deftere `TARTI_FARKI` yazar; `0` = bulunamadı.
- `gunu_kes(teslim_takvimi)` — takvimi `KESILDI` yapar; sonra `degistirilebilir_mi` False.
- `alim_listesi(magaza, tarih)` — hesaplanır, saklanmaz; test siparişlerini saymaz;
  tartımı değil `siparis_miktari`'nı toplar (mal henüz alınmadı).

Dondurma kuralı: sipariş satırında `urun_adi`, `birim_adi`, `birim_fiyat` **kopya**.
Şablonda `kalem.urun_adi` kullan, `kalem.magaza_urun.urun.ad` peşine gitme.

### Gün rotası tablosu (taslak — Ersin düzeltecek)

| Gün | Mahalleler (güzergâh sırası) |
|---|---|
| Pazartesi | İçerişehir · Müftü · Hamidiye |
| Salı | Bahçelievler · Esentepe |
| Çarşamba | Yeni · Beytepe |
| Perşembe | Hacıakif · Hacıarmağan |
| Cuma | Avşar · Evsat |
| Cumartesi | Dalyan · Yeşilyurt |

`HizmetMahallesi.sira` = kurye güzergâhı (`gün × 10 + gün içindeki sıra`).
Model çok günü destekliyor; şablonda tek gün varsayma, listeyi dön.
