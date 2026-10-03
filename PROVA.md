# Bostanhane — Uçtan Uca Prova

Bu provada kendine bir sipariş verip onu baştan sona yürüteceksin: fiyat gir → sipariş ver →
günü kes → tart → kuryeyle teslim et → müşteri olarak onayla ve sorun bildir → yönetici olarak
iade et. Yaklaşık **45 dakika** sürer.

**Gerçek para hareketi yok.** Site deneme modunda; kart, bloke ve iade hepsi "deneme". Verilen
sipariş "DENEME" olarak işaretlenir, raporlara ve alım listesine girmez.

Her adımın altında **"Görmen gereken"** var. Gördüğün şey farklıysa bir hata var demektir:
ekranın görüntüsünü al (Windows + Shift + S) ve Claude Code'a hangi adımda olduğunu yazıp
"son ekran" de.

---

## Hazırlık — iki pencere

İki ayrı kişi olacaksın: **yönetici** (sen) ve **müşteri**. İkisi aynı pencerede olamaz.

- **Normal Chrome penceresi = yönetici.** Burada kendi hesabınla gir.
- **Gizli pencere = müşteri.** Chrome'da `Ctrl + Shift + N`. Burada yeni bir müşteri hesabı açacaksın.

Müşteri hesabı için **senin numarandan farklı** bir cep numarası lazım (ikinci hattın, eşinin ya da
bir yakınının numarası). SMS gönderilmiyor, numaraya bir şey gitmez; sadece "bu numara kayıtlı mı"
kontrolü için farklı olmalı.

---

## 1. Yönetici girişi
**Pencere:** normal · **Hesap:** senin (süper admin)

1. `www.bostanhane.com/yonetim/` adresine git.
2. Telefon: `5330317288`, kendi şifren → **Giriş yap**.

**Görmen gereken:** "Bostanhane Yönetimi" başlıklı panel; solda CORE, KATALOG, SİPARİŞ, ÖDEME, TALEP…

---

## 2. Ürünlere fiyat gir
**Pencere:** normal (yönetici)

Vitrinde ürün görünmesi için fiyatı olmalı ve "satışta" işaretli olmalı. Üç ürün yeter:

1. **KATALOG → Ürünler**.
2. Her ürün için satırdaki **düzenle** düğmesine bas, fiyatı yaz, **satışta** kutusunu işaretle:
   | Ürün | Fiyat |
   |---|---|
   | Domates | `32,90` |
   | Süzme çiçek balı (850 g) | `450` |
   | Maydanoz | `15` |
3. Sayfanın en altındaki **Kaydet**'e bir kez bas.

**Görmen gereken:** Üstte yeşil mesaj: *"3 ürünün fiyatı kaydedildi, 3 ürün satışa açıldı (Bostanhane Beyşehir)."*
Satırlarda `32,90 ₺ / kg · ✓ satışta` gibi yazılar.

---

## 3. Müşteri olarak sipariş ver
**Pencere:** gizli (müşteri)

**3a. Üye ol**
1. `www.bostanhane.com/kayit/`
2. Telefon (farklı numara), ad soyad, şifre (iki kez). İki onay kutusunu işaretle (aydınlatma metni,
   kullanım koşulları). Kampanya kutusu isteğe bağlı. → **Üye ol**.

**Görmen gereken:** *"Hoş geldiniz, …! Teslim gününüzü görmek için bir adres ekleyin."* ve adres formu.

**3b. Adres**
1. Başlık `Ev`, İl Konya, İlçe Beyşehir, Mahalle **Müftü**.
2. Mahalleyi seçince yeşil kutu çıkmalı: *"Müftü Mahallesi'ne kurye gidiyor. Teslim günü: …"*
3. Açık adres yaz → **Adresi kaydet**.

**3c. Sepet**
1. Üst menüden **Ürünler** (telefonda alttaki 🥬).
2. Domates: miktarı **1,5 kg** yap (+ düğmesi) → **Sepete ekle**. Bal: 1 kavanoz → **Sepete ekle**.
   Maydanoz: 1 demet → **Sepete ekle**.
3. Üstten **Sepet**'e git.

**Görmen gereken (sepet):**
- Ürünler 514,35 ₺ · Teslimat 50,00 ₺ · **Toplam (tahmini) 564,35 ₺**
- Kesim şeridi en üstte: *"Müftü · teslimat {tarih} — Kesime … kaldı"*
- "Tartılı ürünlerde ödeme nasıl olur?" kutusu: **Kartta bloke edilecek 571,75 ₺**
- Adres "Ev · Müftü" ve teslim günü seçili.

**3d. Sipariş**
1. **Ön Bilgilendirme Formu'nu okudum** ve **Mesafeli Satış Sözleşmesi'ni kabul ediyorum** kutularını işaretle.
2. **Deneme siparişi ver**.

**Görmen gereken:** *"Deneme siparişiniz alındı: BH-2026-00000X. Kartınızda 571,75 ₺ bloke edildi (deneme —
gerçek para hareketi yok)…"* ve sipariş sayfası. **Sipariş numarasını not al.**

---

## 4. Günü kes
**Pencere:** normal (yönetici)

Kesim normalde teslimattan bir gün önce 18.00'de kendiliğinden yapılır (her 15 dakikada çalışan servis).
Provada beklememek için erken keseceksin.

1. `www.bostanhane.com/depo/` (ya da sitede **Hesabım → Depo ekranı**).
2. Siparişin teslim tarihinin altında **Müftü** kartı → tıkla.
3. **Erken kes (yönetici)** → onay penceresinde **Tamam**.

**Görmen gereken:** *"Gün kesildi: 1 sipariş toplamaya açıldı."* Siparişin yanında **Kesildi** etiketi.

---

## 5. Alım listesi
**Pencere:** normal · aynı gün sayfası

1. **Günün alım listesi**'ne bas.

**Görmen gereken:** Liste **boş** ve *"1 deneme siparişi bu listeye dahil edilmedi"* notu. **Bu doğru:** deneme
siparişleri hale gidecek listeye girmiyor. Gerçek siparişte burada Domates 1,5 kg, Bal 1 kavanoz,
Maydanoz 1 demet yazacak.

---

## 6. Toplama ve tartım
**Pencere:** normal · gün sayfasına geri dön

1. Siparişin satırına (müşterinin adı) tıkla → toplama ekranı.
2. **Domates** kutusuna `1,43` yaz → **Kaydet**. (Tartı 1,5 kg yerine 1,43 kg gösterdi diyelim.)
3. **Bal** kutusunda `1` yazıyor → **Kaydet**.
4. **Maydanoz** → **Bulunamadı** → onay.
5. En alttaki turuncu **Sipariş hazır**.

**Görmen gereken:**
- Tartılan satırlar yeşil, maydanoz kırmızı ("Bulunamadı — müşteriden çekilmeyecek").
- Hazırdan sonra iki mesaj: *"… hazır. Kesin tutar: 547,05 ₺"* ve *"Karttan 547,05 ₺ çekildi."*

---

## 7. Kurye teslimatı
**Pencere:** normal · gün sayfası

1. **Kurye ekranında aç**.
2. **Yola çıktım (1 paket)**.
3. Müşterinin adına tıkla.

**Görmen gereken:** Büyük telefon numarası (dokununca arar), adres, **Haritada aç**, tutar 547,05 ₺,
"Kapıda ödeme alınmaz", *"Maydanoz: bulunamadı — müşteriye söyleyin"*.

4. **✓ Teslim ettim**.

**Görmen gereken:** *"… — teslim edildi."*

---

## 8. Müşteri: teslim onayı ve sorun bildirimi
**Pencere:** gizli (müşteri)

1. **Hesabım → Siparişlerim** → siparişe tıkla.

**Görmen gereken:**
- *"Kartınızdan 547,05 ₺ çekildi, 24,70 ₺ kartınızda serbest kaldı."*
- *"Siparişinizi teslim aldınız mı?"* kutusu ve *"… bildirmezseniz sipariş onaylanmış sayılır. Bu, kusurlu ürün
  bildirme hakkınızı ortadan kaldırmaz."*
- Ürünlerde Maydanoz için *"Bulunamadı, 15,00 ₺ düşüldü"*.

2. **✓ Eksiksiz teslim aldım**.

**Görmen gereken:** *"{tarih saat}'de teslim aldığınızı onayladınız."*

3. **Bir sorun mu var?** → Hangi ürün: **Domates** · Sorun: **Ürün kusurlu / bozuk** · Ne oldu: "Domateslerin
   ikisi ezik" → **Mağazaya bildir**.

**Görmen gereken:** *"Bildiriminiz mağazaya iletildi…"* ve sipariş sayfasında *"Domates · Ürün kusurlu / bozuk —
Bildiriminiz mağazaya iletildi, inceleniyor."* Fotoğraf alanı yerine *"Fotoğraf eklemek şu anda kapalı…"*
yazması **normal** (fotoğraf deposu henüz kurulmadı).

---

## 9. Yönetici: talebe karar ver ve iade et
**Pencere:** normal (yönetici)

1. `www.bostanhane.com/yonetim/` → **SİPARİŞ → Siparişler** → sağdaki **müşteri bildirimi** süzgecinde
   **"Açık sorun bildirimi var"** → siparişin listede olduğunu gör.
2. **TALEP → Talepler** → talebe tıkla.
3. **Karar:** *Kısmen kabul et — bir kısmını iade et* · **İade edilecek tutar:** `10` ·
   **Mağazanın kararı:** "Ezik domatesler için 10 TL iade ettik." → **Kaydet**.

**Görmen gereken:** Tek bir yeşil mesaj: *"Karar kaydedildi; müşterinin kartına 10,00 ₺ iade edildi."*

4. Gizli pencerede (müşteri) sipariş sayfasını yenile.

**Görmen gereken:** *"Mağazanın kararı: Ezik domatesler için 10 TL iade ettik. 10,00 ₺ kartınıza iade edildi."*

---

## 10. Ödeme defteri
**Pencere:** normal (yönetici)

1. **ÖDEME → Ödeme işlemleri** → arama kutusuna sipariş numarası.

**Görmen gereken — üç satır, üçü de "Başarılı":**
| Tür | Tutar |
|---|---|
| Provizyon (bloke) | 571,75 ₺ |
| Çekim | 547,05 ₺ |
| İade | 10,00 ₺ |

"Bloke çözüldü" satırı **yok** — bu doğru; çekimde kalan 24,70 ₺'yi banka kendiliğinden serbest bırakır.

---

## Bitti

Bütün adımlarda "Görmen gereken" ile gördüğün aynıysa sistem senin elinde de çalışıyor. Farklı bir şey
gördüysen adım numarasıyla birlikte not al; Claude Code'a "PROVA: 6. adımda şunu gördüm" diye yaz.

**Temizlik gerekmiyor.** Deneme siparişi raporlara girmez. İstersen ürün fiyatlarını bırak — gerçek
fiyatları girerken üzerine yazarsın.
