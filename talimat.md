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

## 3 Ekim 2026 (4) — Mahalle nüfusu, talep haritası ve "mahalleme de gelin" sayfası

Depoda ileri günleri bulup düzeltmen iyi oldu — prova rehberini yazarken
yakalaman tam da rehberin işe yaradığını gösteriyor. "Kurye ekranında aç"
bağlantısı da benim aklıma gelmemişti; yönetici başka günün rotasına başka
türlü ulaşamıyordu.

`PROVA.md` için teşekkürler, Ersin'e söyledim.

---

### 1. Gün düzenini Ersin panelden yapıyor — teyit ettim

Gözlemin doğruymuş, sordum: **evet, teslim günlerini panelden kendisi
düzenliyor.** Yani `ornek_veri.GUN_ROTALARI` tablosu artık canlıyla uyuşmuyor
ve uyuşmayacak.

Senin uyarın ("`--rotalari_esitle` canlıda çalıştırılmamalı") doğruydu, ama
uyarı insan hafızasına güveniyor. Komuta koruma koydum: `--rotalari_esitle`
artık tek başına çalışmıyor, `--eminim` da istiyor ve ne yapacağını önce
anlatıyor.

Ersin'in saatlerce yaptığı düzeni tek komutla geri almak, bu projede
yapılabilecek en can sıkıcı hatalardan biri olurdu.

### 2. Mahalle nüfusu — Ersin'in isteği

`Mahalle.nufus`, `nufus_yili`, `nufus_kaynagi` eklendi. Üç alan, çünkü sayının
kendisi kadar **nereden geldiği ve ne zamana ait olduğu** da önemli: nüfus her
yıl değişiyor, bu sayılar bizim ölçümümüz değil.

Veri: TÜİK ADNKS **2023**, atlasbig.com.tr üzerinden derlendi — yani TÜİK'ten
doğrudan değil, aktaran bir siteden. `core/nufus_verisi.py`'nin başında bunu
açıkça yazdım. 70 mahalleden **68'i** doldu; Yeşilyurt ve Akçabelen hiçbir
listede yoktu, **boş bıraktım, uydurmadım.** Ali Akkanat'ı başka bir kaynaktan
2025 verisiyle ekledim ve kendi yılıyla işaretledim — farklı yılları tek
tabloya karıştırıp aynıymış gibi göstermek karşılaştırmayı bozar.

Nüfus sütunu **Mahalleler** ve **Hizmet verilen mahalleler** listelerinde,
sıralanabilir. İkincisi önemli: kapasite kararı orada veriliyor, nüfusu
yanında görmek işe yarıyor.

### 3. Talep haritası — Ersin'in yeni isteği

Ersin şunu istedi: *"hizmet vermediğimiz yerlerdeki kişiler kayıt olsun,
mahallemde Bostanhane istiyorum diye talep oluştursunlar; taleplere göre
şubeleşmeye gideriz."*

Mantıklı buldum ve ona söyledim: reklam bütçesi böylece "beğeni" yerine
**isim, telefon ve konum** getiriyor; şube kararı tahminle değil listeyle
veriliyor.

Altyapı zaten vardı (`IlgiKaydi`). Eksik olan iki şey vardı, ikisini de yaptım:

**a. `IlgiKaydi.mahalle` (resmî mahalle FK).** Serbest metinle gruplamak
güvenilmez: "Müftü", "müftü mah.", "Müftü Mahallesi" üç ayrı satır olur ve
talep sayısı üçe bölünür — tam da güvenmek istediğimiz sayı. `save()` artık
yazılan adı slug'a çevirip resmî mahalleyi bulmaya çalışıyor.

**b. Talep haritası sayfası** — `/yonetim/core/ilgikaydi/harita/`,
İlgi kayıtları listesinin üstünde bağlantısı var.

| Yer | Talep | Nüfus | Binde | Durum |
|---|---|---|---|---|
| Üzümlü | 37 | 4.855 | 7,6 ‰ | hizmet yok |
| Adaköy | 6 | 319 | 18,8 ‰ | hizmet yok |
| Yeni | 14 | 10.323 | 1,4 ‰ | hizmet veriyoruz |

**Binde sütunu sayfanın asıl fikri.** Talep sayısı tek başına yanıltıcı:
10.000 kişilik mahalleden gelen 37 talep zayıf, 400 kişilikten gelen 37 talep
güçlüdür. Oran olmadan büyük mahalleler hep önde görünür ve yanlış yere şube
açılır.

Küçük sayı tuzağına da karşı önlem var: "en güçlü sinyal" özeti 200 kişiden az
mahalleleri saymıyor. 24 kişilik Gönen'den gelen 3 talep binde 125 çıkıp bütün
listeyi eziyordu.

**Bulduğum ve düzelttiğim bir açık:** `admin_site.admin_view` yalnızca "panele
girebilir mi" diye bakıyor, model yetkisine bakmıyor. Mağaza yöneticisi İlgi
kayıtları listesini göremezken **özetini görebiliyordu** — oysa aynı veriyi
taşıyor ve bilerek süper admine kısıtlamıştık. Yetki kontrolü ekledim; dört
rolle de denedim.

### 4. Kurulum

```powershell
Copy-Item hazir\core_models.py          core\models.py                             -Force
Copy-Item hazir\core_admin.py           core\admin.py                              -Force
Copy-Item hazir\core_nufus_verisi.py    core\nufus_verisi.py                       -Force
Copy-Item hazir\core_talep_haritasi.py  core\talep_haritasi.py                     -Force
Copy-Item hazir\nufus_yukle.py          core\management\commands\nufus_yukle.py    -Force
Copy-Item hazir\ornek_veri.py           core\management\commands\ornek_veri.py     -Force

New-Item -ItemType Directory -Force templates\admin\core\ilgikaydi | Out-Null
Copy-Item hazir\admin_ilgikaydi_harita.html      templates\admin\core\ilgikaydi\harita.html      -Force
Copy-Item hazir\admin_ilgikaydi_change_list.html templates\admin\core\ilgikaydi\change_list.html -Force

python manage.py makemigrations core
python manage.py migrate
python manage.py nufus_yukle --kuru      # önce bak
python manage.py nufus_yukle             # sonra yükle
```

Beklenen migration: `ilgikaydi.mahalle` + `mahalle.nufus/nufus_yili/nufus_kaynagi`.
`nufus_yukle` çıktısı: **68 mahalle güncellendi**, 2 mahalle boş (Akçabelen,
Yeşilyurt).

**Canlıda `nufus_yukle`'yi çalıştırmayı unutma** — migration alanları ekliyor
ama veriyi komut dolduruyor.

### 5. Senden — "mahalleme de gelin" sayfası

Şu an bu kayıt yalnızca adres formundan açılıyor (üye olup Beyşehir dışı ilçe
seçen kişi). Ersin'in istediği **herkese açık bir sayfa**:

| Adres | Ne |
|---|---|
| `/mahalleme-gelin/` | Herkese açık, **üyelik gerekmez** |

- İl → ilçe → mahalle (adres formundaki JSON uçlarının aynısı). Mahalle listesi
  boşsa serbest metin — o zaten var.
- Ad soyad, telefon (zorunlu), e-posta (isteğe bağlı).
- KVKK onayı zorunlu; aydınlatma metnine bağlantı. İzinsiz iletişim bilgisi
  toplanmaz.
- Kaydı `IlgiKaydi` olarak aç: `kaynak="mahalleme gelin sayfası"`,
  giriş yapmışsa `uye=request.user`.
- Aynı telefon + aynı mahalle ikinci kez gönderirse **yeni kayıt açma**, teşekkür
  mesajı göster. Talep sayısı şişmesin.

**Beklenti cümlesi şart, uydurmadan yaz:**

> Ne zaman geleceğimize söz veremeyiz. Mahallenize geldiğimizde ilk size haber vereceğiz.

Söz vermeyen ama ciddiye alan bir cümle. "Yakında geliyoruz" yazma — altı ay
sonra bir şey olmazsa marka "söz verdiler, unuttular" diye hatırlanır. Ersin'e
de bunu söyledim.

- Ana sayfada, gün kartlarının altına bir satır: *"Mahalleniz listede yok mu?"*
  → bu sayfa.
- Zaten hizmet verdiğimiz bir mahalle seçilirse kayıt açma; *"Bu mahalleye
  zaten geliyoruz!"* deyip vitrine yönlendir.
- Hizmet vermediğimiz mahallelerde `Mahalle.yerel_hizmet()` None dönüyor,
  kontrol için onu kullan.

Ana sayfadaki eski "yakında" formunu da bu sayfaya bağlayabilirsin — şu an ilçe
sormadığı için kayıtları haritada görünmüyor ("yer bilgisi yok" diye sayılıyor).

### 6. Raporda görmek istediklerim

- `Canlı: commit X, SUCCESS` satırı
- Canlıda `nufus_yukle` çıktısı
- Talep haritasının canlıda açıldığı ve **mağaza yöneticisinin açamadığı**
- `/mahalleme-gelin/` üyeliksiz çalıştığı, ikinci gönderimin yeni kayıt açmadığı
- Hizmet verilen mahalle seçilince kayıt açılmayıp vitrine yönlendirdiği
- Kesim servisinin ilk 24 saatlik maliyeti

### 7. Bunları yapma

- `--rotalari_esitle --eminim`'i canlıda çalıştırma. Ersin'in düzenini siler.
- Nüfus sayılarını elle doldurma ya da tahmin etme — boş kalsın, kaynağı belli
  olmayan sayı yanlış karar verdirir.
- `talep/`, `odeme/`, `core/talep_haritasi.py` dosyalarını değiştirme.
- Canlıda `vitrin_modu = acik`.

---

---

## 3 Ekim 2026 (3) — İki bulgunun da haklıydı, ikisini de düzelttim

Talep akışını bağlaman temiz olmuş. Özellikle iki şey:

- **Sorun bildirme hakkını teslim onayından sonra da açık bırakman.** Yasal
  metinde "onay, kusurlu ürün bildirme hakkınızı ortadan kaldırmaz" yazıyor;
  sen kodu metne uydurmuşsun. Ben talimatta bunu ayrıca söylememiştim.
- **`acik_talebi_var_mi`'yi çağrı anında içeri alman.** `talep` → `siparis`
  yönünde bağımlılık var; tersini dosya başında yazsaydık döngü olurdu.

---

### 1. Başarısız iade defterden siliniyordu — düzelttim

Bulgun aynen doğru:

> `karara_bagla` `@transaction.atomic`; iade başarısız olunca `ValidationError`
> fırlatılıyor → `iade_et`'in yazdığı başarısız `OdemeIslemi` satırı da geri
> alınıyor.

Defterin ilkesi "gönderilen her istek bir satır". Reddedilen istek de iz
bırakmalı, yoksa "neden iade edilmedi" sorusunun cevabı hiçbir yerde kalmaz.
Benim `@transaction.atomic` dekoratörüm tam da kaydı korumak için koyduğum şeyi
siliyormuş.

**Önerini uyguladım** — iade artık kendi işleminde yürüyüp kaydını bırakıyor,
talebin kapanması ayrı adım.

Ama bu düzeltme yeni bir risk doğuruyordu: para gidip kapanma adımı patlarsa,
yönetici tekrar denediğinde **ikinci kez para gider**. Kendi düzeltmemin
açtığı deliği de kapatmam gerekti:

`Talep.odeme_islemi` alanı ekledim (yeni migration). Para gittiği anda, talep
kapanmadan **önce** bağlanıyor. İkinci denemede bu alan doluysa sağlayıcıya hiç
gidilmiyor, yalnızca kapanma adımı tamamlanıyor.

Denedim: başarısız iade defterde kalıyor (hata kodu dahil), talep açık kalıyor,
ikinci deneme başarılı oluyor, defterde bir başarısız + bir başarılı satır
duruyor, ve bağlı talep ikinci kez para göndermiyor.

### 2. Çelişkili iki mesaj — düzelttim

Bu da doğruydu: `messages.error` basıp dönüyordum, Django ardından kendi
*"başarıyla değiştirildi"* mesajını ekliyordu. Yönetici "iade yapılamadı" ile
"başarıyla değiştirildi"yi yan yana görüyordu. Para işinde kabul edilemez.

`response_change`'i hata durumunda bastırdım. Denedim: artık yalnızca hata
mesajı görünüyor, talep açık kalıyor.

### 3. Kurulum

```powershell
Copy-Item hazir\talep_models.py   talep\models.py   -Force
Copy-Item hazir\talep_islemler.py talep\islemler.py -Force
Copy-Item hazir\talep_admin.py    talep\admin.py    -Force
python manage.py makemigrations talep
python manage.py migrate
```

Beklenen: `talep/migrations/0002_talep_odeme_islemi.py` — tek alan ekliyor,
veri taşımıyor.

### 4. Sırada — prova hazırlığı

Yazılım tarafında benden ya da senden bekleyen iş kalmadı. Ersin'in üç işi
(gün gruplaması, şirket bilgileri, sanal POS) ve R2 anahtarları bekliyor.

Bu arada yapılabilecek, gerçekten işe yarayacak bir şey var: **Ersin'in uçtan
uca prova yapması.** Kendine sipariş verip günü kesecek, depodan tartacak,
kuryeden teslim edecek. Yazılımın çalıştığını biliyoruz; **onun elinde**
çalıştığını bilmiyoruz.

Senden istediğim: `PROVA.md` diye bir dosya yaz. Ersin'in yazılım bilgisi yok,
adım adım ve ekran ekran olsun:

1. Hangi adresten giriş yapacak, hangi hesapla (süper admin mi, mağaza
   yöneticisi mi — her adımda hangi rol gerekiyorsa)
2. Panelden birkaç ürüne fiyat girmesi (vitrinde ürün görünmesi için şart)
3. Üye olarak sipariş vermesi — sepet, adres, teslim günü, deneme siparişi
4. Günü kesmesi (depo ekranı) — ya da kesim servisinin kesmesini beklemesi
5. Alım listesini görmesi
6. Toplama ekranından tartması, bir ürüne "bulunamadı" demesi
7. Kurye ekranından teslim etmesi
8. Müşteri olarak teslim onayı vermesi, bir de sorun bildirmesi
9. Yönetici olarak talebe karar verip iade etmesi
10. Ödeme defterinde üç satırı görmesi

Her adımda **ne görmesi gerektiğini** yaz — beklenen ekran, beklenen mesaj.
Böyle olmazsa bir hata var demektir ve rapora yazılacak.

Dosyayı `hazir/`'a değil doğrudan proje köküne koy; Ersin'in dosyası.

### 5. Raporda görmek istediklerim

- `Canlı: commit X, SUCCESS` satırı
- `0002` migration'ının temiz geçtiği
- Başarısız iadenin defterde kaldığı (canlıda değil, yerelde denemen yeterli)
- Panelde tek mesaj göründüğü
- `PROVA.md` hazır

### 6. Bunları yapma

- `talep/` ve `odeme/` dosyalarını değiştirme.
- Provayı sen çalıştırma — Ersin'in kendi eliyle yapması lazım, amaç o.
- Canlıda `vitrin_modu = acik`.

---

---

## 3 Ekim 2026 (2) — `talep` uygulaması: kusurlu ürün bildirimi

Teslim onayı iyi olmuş. Özellikle **sorun bildirilen siparişi otomatik
onaylamaman** doğru karar: müşteri cevap vermiş sayılır, mağaza karar verene
kadar sipariş açık kalmalı. Ben talimatta bunu söylememiştim, sen düşünüp koymuşsun.

Raporda yazdığın endişe de yerindeydi:

> Modelde alan olmadığından iç nottaki sabit işarete bakılıyor; `talep` modeli
> gelince ona bağlanmalı.

Haklıydın. İç not serbest metin — yönetici bir cümle eklerken işareti silerse
sipariş sessizce otomatik onaylanır ve şikâyet kaybolur. Model geldi.

### 1. Kurulum

```powershell
python manage.py startapp talep
Copy-Item hazir\talep_models.py    talep\models.py   -Force
Copy-Item hazir\talep_islemler.py  talep\islemler.py -Force
Copy-Item hazir\talep_admin.py     talep\admin.py    -Force
Copy-Item hazir\talep_apps.py      talep\apps.py     -Force
Copy-Item hazir\siparis_admin.py   siparis\admin.py  -Force
Copy-Item hazir\hesaplar_izinler.py hesaplar\izinler.py -Force
```

`BOSTANHANE_APPS`'e `"talep"` (`odeme`'den sonra), sonra:

```powershell
python manage.py makemigrations talep
python manage.py migrate
python manage.py roller_kur
```

`roller_kur` çıktısı: Mağaza Yöneticisi **50 yetki**, `! atlandı` yok.
`talep/views.py` ve `tests.py`'yi sil (startapp'in boş dosyaları).

### 2. Ne yapıyor

**`Talep`** — hangi sipariş, hangi kalem, müşteri ne diyor, mağaza ne karar verdi,
ne kadar iade edildi. **`TalepGorseli`** — müşterinin fotoğrafı.

Kalem bazında, çünkü kısmi iade kalem tutarına göre hesaplanıyor. Kalem boş
bırakılabiliyor (teslimat hiç gelmediyse).

**Korumalar — hepsini denedim:**

- Teslim edilmemiş siparişe talep açılmıyor.
- Süre `SatisAyarlari.talep_acma_suresi_saat`'ten okunuyor, koda gömülü değil.
  Süre dolunca *"Bildirim süresi doldu"*.
- Aynı kalem için ikinci açık talep açılmıyor (müşteri iki kez basarsa).
- İade, kalem tutarını aşamıyor.
- Karar verirken müşteriye açıklama yazmak zorunlu.
- **İade başarısızsa talep açık kalıyor.** "Kabul edildi" yazıp parayı
  göndermemek, hiç karar vermemekten kötü. Sırası: önce para gider, sonra talep
  kapanır; para gitmezse işlem geri alınıyor.
- Karara bağlanmış talep ikinci kez karara bağlanamıyor.

### 3. Fotoğraf — depolama yoksa hiç alınmıyor

`gorsel_yuklenebilir_mi()` nesne depolamanın yapılandırılıp yapılandırılmadığına
bakıyor. Canlıda R2 anahtarları yoksa **fotoğraf alanı hiç gösterilmeyecek**.

Sebebi: fotoğraf bir anlaşmazlığın kanıtı. Railway'in diski kalıcı değil;
anahtarsız yüklenen fotoğraf sonraki dağıtımda kaybolur. Müşteri "fotoğraf
gönderdim" der, elimizde hiçbir şey olmaz. Sessizce kaybolan kanıt, hiç
alınmamış kanıttan kötüdür.

Müşteri ekranında, kapalıyken: *"Fotoğraf eklemek şu anda kapalı; sorunu
yazıyla anlatın, mağaza sizi arayacak."* Ersin R2 anahtarlarını verince
kendiliğinden açılacak, kod değişmeyecek.

### 4. Senden

**a. `otomatik_onayla` komutunu bağla.** `SORUN_ISARETI` metin aramasını kaldır,
yerine:

```python
from talep.islemler import acik_talebi_var_mi
```

Açık talebi olan sipariş otomatik onaylanmasın. Geçici çözümün yerini kalıcısı
aldı; `siparis/teslim_onayi.py`'deki `SORUN_ISARETI` sabiti de kalkabilir.

**b. "Bir sorun var" düğmesini talebe bağla.** Şimdi iç nota yazıyor; onun yerine
`talep.islemler.talep_ac(siparis, request.user, tur, aciklama, kalem=...)`
çağırsın. Müşteri **hangi ürün** olduğunu seçebilsin (siparişin kalemleri +
"sipariş geneli" seçeneği) ve sorun türünü işaretlesin (kusurlu / eksik / yanlış
ürün / diğer).

Fotoğraf alanı yalnızca `gorsel_yuklenebilir_mi()` True ise görünsün; en fazla
3 fotoğraf, her biri en fazla 5 MB, yalnızca resim dosyası.

**c. Talep durumunu müşteriye göster.** Siparişlerim detayında: açıkken
*"Bildiriminiz mağazaya iletildi, inceleniyor."*, karara bağlanınca mağazanın
`karar_notu`'su ve iade varsa tutarı.

**d. Sipariş panelinde süzgeç hazır.** `siparis/admin.py`'ye "müşteri bildirimi"
süzgecini ekledim (açık / karara bağlanmış / bildirim yok), süzgeçlerin başında.
Açık bildirimi olan sipariş günün en acil işi, listede kaybolmasın.

### 5. Raporda görmek istediklerim

- `Canlı: commit X, SUCCESS` satırı
- Kesim servisinin 13.00 kaydı (iki `veritabanı: postgresql` satırı) ve
  ilk 24 saatlik gerçek maliyet
- Müşteri sorun bildirdi → panelde talep göründü → yönetici kabul etti →
  **para gerçekten iade edildi** (ödeme defterinde iade satırı) → müşteri
  kararı gördü
- Açık talebi olan siparişin `otomatik_onayla` tarafından **atlandığı**
- Fotoğraf alanının depolama yokken görünmediği

### 6. Bunları yapma

- `talep/` ve `odeme/` dosyalarını değiştirme — hata bulursan rapora yaz.
- Talebi panelden açılabilir yapma, şikâyet kaydını silinebilir yapma.
- `durum` ve `iade_tutari` alanlarını panelde doğrudan düzenlenebilir yapma —
  elle "kabul" yazılırsa para gönderilmeden talep kapanır.
- Canlıda `vitrin_modu = acik`.

---

---

## 3 Ekim 2026 — Sessiz SQLite tuzağına koruma; sırada teslim onayı

### 1. Ayarın okunmaması benim hatamdı

`getattr(settings, "DENEME_ODEME_HATASI")` yazdım ama `settings.py`'ye o ayarı
eklemeyi unuttum. `.env`'e yazılan değer hiç etki etmezdi — yani eklediğim hata
anahtarı hiç çalışmayacaktı. Sen kurarken fark edip ekledin. Doğru düzeltme.

`ODEME_SAGLAYICI` için de aynısı geçerliymiş; onu da yakalamışsın.

### 2. SQLite tuzağı — uyarını kalıcı korumaya çevirdim

Raporunda yazdığın şey bu turdaki en değerli bulgu:

> `DATABASE_URL` eksik kalırsa `settings.py` sessizce SQLite'a düşer, komut boş
> veritabanında "Kesilecek gün yok" deyip başarılı biter — çalışıyormuş gibi
> görünür ama hiçbir şey kesmez.

Haftalarca "her şey yolunda" sanıp hiçbir siparişin kesilmediğini fark etmemek,
bu projede olabilecek en sinsi hata. Komuta veritabanı adını bastırman iyi bir
teşhis aracı, ama **teşhis yetmez** — kimse her gün kayıtlara bakmaz.

`settings.py`'ye sert koruma ekledim (senin sürümünün üzerine):

```python
if not DEBUG and DATABASES["default"]["ENGINE"].endswith("sqlite3"):
    raise ImproperlyConfigured(...)
```

Canlıda SQLite'a düşmek artık **hata**. Servis hiç başlamıyor, Railway kırmızı
gösteriyor. Sessizce yanlış çalışmaktansa gürültüyle çökmesi iyidir.

Denedim: `DEBUG=True` etkilenmiyor, `DEBUG=False` + `DATABASE_URL` yok → net hata
mesajı, `DEBUG=False` + postgres ayarlı → geçiyor.

```powershell
Copy-Item hazir\settings.py bostanhane\settings.py -Force
```

**Kurduktan sonra bir kez doğrula:** canlıda `kesim` servisinin kaydında hâlâ
`veritabanı: postgresql` yazıyor mu. Yazıyorsa koruma hiç devreye girmeyecek
demektir, istediğimiz bu. Yazmıyorsa servis zaten çökecek ve göreceğiz.

### 3. Sistem kontrolü gürültüsü — sustur

Sormuşsun: komut her çalışmada W001/W002 uyarılarını basıyor, susturulsun mu.
**Sustur:** `requires_system_checks = []`.

Gerekçe: 15 dakikada bir, günde 96 çalışma, her birinde iki uyarı satırı.
Gerçek bir hata çıktığında bu yığının içinde kaybolur. W001 ve W002 zaten her
dağıtım kaydında görünüyor — yerleri orası. Kayıtların az ve okunabilir olması
uyarının tekrarlanmasından değerli.

### 4. Sırada — teslim onayı (Adım 6c)

`CLAUDE.md`'deki kararlardan biri henüz yazılmadı:

> Teslimde üye "eksiksiz teslim aldım" onayı verir; cevap gelmezse 24 saat sonra
> otomatik onay.

`SatisAyarlari.otomatik_teslim_onayi_saat` alanı duruyor, `Siparis.onay_zamani`
alanı duruyor, kimse doldurmuyor. İki parça:

**a. Müşteri onayı.** Siparişlerim detayında, sipariş `teslim_edildi` ve
`onay_zamani` boşsa iki düğme:
- **"Eksiksiz teslim aldım"** → `onay_zamani = şimdi`.
- **"Bir sorun var"** → şimdilik yalnızca `ic_not`'a yazsın ve mağazaya görünsün.
  **Fotoğraflı iade talebi ekranını yapma** — o ayrı bir iş (`talep` uygulaması),
  model gerekiyor, bende.

Onaylanmış siparişte düğmeler yerine *"3 Ekim 14.20'de teslim aldığınızı
onayladınız."* yazsın.

**b. Otomatik onay komutu.** `siparis/management/commands/otomatik_onayla.py`:
`teslim_edildi` olup `onay_zamani` boş ve `teslim_zamani` üzerinden
`SatisAyarlari.otomatik_teslim_onayi_saat` saat geçmiş siparişleri onaylar.
`--kuru` seçeneği olsun, `gunu_kes` gibi tekrar çalıştırılabilir olsun,
veritabanı adını bastırsın.

Kesim servisinin Start Command'ını şöyle yap:

```
python manage.py gunu_kes && python manage.py otomatik_onayla
```

Yeni servis açmaya gerek yok; ikisi de saniyeler sürüyor, aynı 15 dakikalık
turda çalışsınlar. `&&` kullan: kesim hata verirse onay çalışmasın, sebebi
kayıtlarda tek yerde kalsın.

**Not:** Otomatik onay müşterinin kanundan doğan haklarını ortadan kaldırmıyor;
yalnızca siparişi "kapanmış" sayıyor. Yasal metinlerde böyle yazılı, ekranda da
öyle anlat: *"24 saat içinde bildirmezseniz sipariş onaylanmış sayılır. Bu,
kusurlu ürün bildirme hakkınızı ortadan kaldırmaz."*

### 5. Raporda görmek istediklerim

- `Canlı: commit X, SUCCESS` satırı
- Canlıda kesim servisinin kaydında `veritabanı: postgresql` yazdığı
- Kesim servisinin ilk 24 saatlik gerçek maliyeti (tahmin $0,3/ay idi)
- Müşterinin teslim onayı verdiği ve ikinci kez veremediği
- `otomatik_onayla --kuru` çıktısı ve iki kez çalıştırıldığında hata vermediği

### 6. Bunları yapma

- Fotoğraflı iade talebi ekranı ve `talep` uygulaması — bende.
- `odeme/` dosyalarını değiştirme; hata bulursan rapora yaz (bu turda ikisi de işe yaradı).
- Gerçek sağlayıcı yazma, canlıda `ODEME_SAGLAYICI` ya da `DENEME_ODEME_HATASI` değiştirme.
- Canlıda `vitrin_modu = acik`.

---

---

## 2 Ekim 2026 (7) — İki notun da haklıydı; Railway kesim servisi onaylandı

### Önce: canlıya alma konusunda yanılan bendim

"Canlıya alma raporda yok" diye sormuştum. Cevabın net: hepsi gitmiş, beş commit,
hepsi SUCCESS. Raporlarında o satırı görmediğim için **gitmediğini varsaydım** —
varsaymak yerine sorsaydım Ersin'e de yanlış bilgi vermezdim. Ona da düzelttim.

"Bundan sonra her raporda `Canlı: commit X, SUCCESS` yazacağım" demişsin; tam da
gereken şey. Teşekkürler.

---

### 1. "Defterde üç satır" — sen haklısın, talimatım yanlıştı

Raporda yazmışsın: normal akışta defterde **iki** satır çıkıyor (provizyon + çekim),
üçüncüsü yok. Doğrusu bu. Ben talimatta "üç satır" demişim, hatalı.

Gerekçen de doğru: çekimde sağlayıcı kalan farkı kendiliğinden serbest bırakıyor,
biz ayrıca bir "bloke çözme" isteği **göndermiyoruz**. Defter gönderdiğimiz
istekleri tutar; göndermediğimiz bir isteği deftere yazmak uydurma kayıt olurdu.
Üçüncü satırı eklememekle doğru olanı yapmışsın.

**Ama senin notun bende bir hata ortaya çıkardı.** `siparis_ozeti()` açık blokeyi
hesaplarken yalnızca "bloke çözüldü" satırına bakıyordu. Çekim yapılmış bir
siparişte kartta hâlâ para bloke görünüyordu — yanlış. Düzelttim: blokeyi iki şey
kapatıyor, çekim ya da çözme. Ayrıca `cozulen_fark` ekledim; müşteriye
*"9,70 ₺ kartınızda serbest kaldı"* diyebilmek için.

### 2. Hata yolunu denemek için artık kod değiştirmen gerekmiyor

Haklısın: `provizyon_al` sıfır/negatif tutarı sağlayıcıya gitmeden reddediyor,
deneme sağlayıcının negatif dalına ulaşılmıyor. Sen sağlayıcı yanıtını geçici
değiştirerek sınamışsın — işe yaradı ama unutulup öyle kalabilecek bir yöntem.

Ayar ekledim:

```
DENEME_ODEME_HATASI=51|Yetersiz bakiye
```

Doluyken bütün istekler o hatayla başarısız dönüyor, boşken hiçbir etkisi yok.
`.env.ornek`'e de ekle, açıklamasıyla. Canlıda **boş kalacak**.

### 3. `sepete_geri_koy` — iyi yakalama, yerinde çözüm

`siparise_cevir` sepeti boşalttığı için provizyon başarısız olunca müşteri sepetini
kaybediyordu. Benim gözümden kaçmış; sen fark edip telafi eylemi yazmışsın.

Aklımdan geçen alternatifi de söyleyeyim ki aynı yoldan geçmeyelim: provizyonu
`siparise_cevir` ile aynı işleme (transaction) koyup başarısızlıkta hepsini geri
almak. **Yapmıyoruz** — çünkü veritabanı geri alınır ama sağlayıcıya giden istek
geri alınmaz. Para gerçekten bloke edilip bizde hiç kayıt kalmaması, sepetin
kaybolmasından çok daha kötü. Senin yaptığın doğru: önce kaydet, sonra telafi et.

### 4. Kurulum

```powershell
Copy-Item hazir\odeme_models.py       odeme\models.py       -Force
Copy-Item hazir\odeme_saglayicilar.py odeme\saglayicilar.py -Force
```

Migration gerekmiyor — `siparis_ozeti` ve sağlayıcı değişti, model alanı değişmedi
(`makemigrations --check` → No changes detected).

Sipariş detayındaki "Kalan blokaj serbest bırakıldı" metnini `cozulen_fark` ile
sayıya çevirebilirsin: *"Kartınızdan 547,05 ₺ çekildi, 39,70 ₺ serbest kaldı."*
Müşteri kart ekstresinde iki ayrı satır görecek; sayıyı önceden söylemek soru
gelmesini engeller.

---

### 5. Railway kesim servisi — Ersin onay verdi, kur

Bunu bir önceki talimata sonradan eklemiştim, sen okumadan önce gönderilmiş olabilir.
Tekrarlıyorum:

Senin önerdiğin düzenle kur: ayrı servis, aynı depodan, Start Command
`python manage.py gunu_kes`, Cron Schedule `*/15 * * * *`, değişkenler web
servisiyle ortak.

Sıra önemli:

1. **Önce canlıda `gunu_kes --kuru`.** Açık kalmış eski günler bir anda kesilecek;
   listeyi **Ersin'e göstermeden gerçeğini çalıştırma.** Kuru çıktıyı rapora yaz,
   onayını bekle.
2. Onay gelince gerçeğini çalıştır, sonra servisi `*/15` zamanlamasıyla aç.
3. İlk 24 saat sonunda Railway kullanım ekranından gerçek maliyete bak, rapora yaz —
   tahminin $0,3/ay idi, doğrulayalım.

Web servisinin **Start Command'ı boş kalmalı**; yalnızca yeni `kesim` servisinde
dolu olacak. 30 Eylül'deki olay bu yüzden olmuştu.

---

### 6. Raporda görmek istediklerim

- `Canlı: commit X, SUCCESS` satırı
- `gunu_kes --kuru` çıktısı (kaç gün, kaç sipariş) — **onay beklediğini yaz**
- Çekim sonrası sipariş detayında serbest kalan tutarın göründüğü
- `DENEME_ODEME_HATASI` ile başarısız ödeme akışının çalıştığı, ayar boşken normale döndüğü

### 7. Bunları yapma

- Kuru çalıştırmanın gerçeğini Ersin onaylamadan çalıştırma.
- `odeme/` içindeki dosyaları değiştirme — hata bulursan rapora yaz, bu turda iki
  bulgunun da işe yaradı.
- Gerçek sağlayıcı yazma, canlıda `ODEME_SAGLAYICI`'yı değiştirme.
- Canlıda `vitrin_modu = acik`.

---

---

## 2 Ekim 2026 (6) — `odeme` uygulaması hazır

### Önce: canlıya alma raporda yok

Talimat (5)'in 3. maddesi **"Canlıya alma — bunu rapora yaz"** idi. Raporunda
1. madde, kesim uyarısı ve Railway araştırması var; canlıya alma yok. Yaptın mı?

Tek cümle yeter: *"gitti, commit X"* ya da *"gitmedi, sebep şu"*. Bir engel
gördüysen sorun değil — bilmediğim şey sorun. Şu an bana canlının hâli belirsiz
görünüyor ve Ersin'e yanlış şey söylüyor olabilirim.

(Raporda *"Ersin depo ekranını açınca görecek"* diye yazmışsın; depo ekranı canlıda
mı, emin değilim. Oradan sorulmuş oluyor.)

### Railway kesim servisi — araştırman iyi, Ersin'e götürdüm

`*/15 * * * *` gerekçen doğru: kesim saati mahalle başına değişiyor, sabit saat
tutmaz; komut tekrar çalıştırılabilir olduğundan sık çalışmanın zararı yok, kaçan
çalıştırmayı sonraki telafi ediyor. Ayrı servis olması da doğru — web sürecinin
içine zamanlayıcı koymanın iki işçide iki kez çalışacağını fark etmen ince bir nokta.

**Ersin onay verdi — kur.** Senin önerdiğin düzenle: ayrı servis, aynı depodan,
Start Command `python manage.py gunu_kes`, Cron Schedule `*/15 * * * *`, değişkenler
web servisiyle ortak.

Sıra önemli:

1. **Önce canlıda `gunu_kes --kuru`** (railway ssh ya da geçici olarak Start Command
   ile). Açık kalmış eski günler bir anda kesilecek; listeyi **Ersin'e göstermeden
   gerçeğini çalıştırma.** Kuru çıktıyı rapora yaz, onayını bekle.
2. Onay gelince gerçeğini çalıştır, sonra servisi `*/15` zamanlamasıyla aç.
3. İlk 24 saat sonunda Railway kullanım ekranından gerçek maliyete bak ve rapora yaz —
   tahminin $0,3/ay idi, doğrulayalım.

Web servisinin **Start Command'ı boş kalmalı**; yalnızca yeni `kesim` servisinde dolu
olacak. 30 Eylül'deki olay bu yüzden oldu, tekrarlamasın.

---

### Asıl iş: ödeme

Söz verdiğim iş bitti. Sanal POS sözleşmesi olmadan **bütün para akışı çalışıyor**:
bloke et → tart → kesin tutarı çek → gerekirse iade et.

### 1. Kurulum

```powershell
python manage.py startapp odeme
Copy-Item hazir\odeme_models.py       odeme\models.py        -Force
Copy-Item hazir\odeme_saglayicilar.py odeme\saglayicilar.py  -Force
Copy-Item hazir\odeme_islemler.py     odeme\islemler.py      -Force
Copy-Item hazir\odeme_admin.py        odeme\admin.py         -Force
Copy-Item hazir\odeme_apps.py         odeme\apps.py          -Force
Copy-Item hazir\hesaplar_izinler.py   hesaplar\izinler.py    -Force
```

`BOSTANHANE_APPS`'e `"odeme"` (sıralamada `siparis`'ten sonra), sonra:

```powershell
python manage.py makemigrations odeme
python manage.py migrate
python manage.py roller_kur
```

**`roller_kur`'u atlama.** Atlarsan mağaza yöneticisi ödeme defterinde 403 alır —
bu hatayı üçüncü kez yaşıyoruz, ben de bu kez sandbox'ta yaşadım. Çıktıda
Mağaza Yöneticisi 47 yetki görünmeli, `! atlandı` satırı olmamalı.

### 2. Ne yapıyor

**`OdemeIslemi`** — her para hareketi bir satır: provizyon, çekim, iade, bloke çözme.
Siparişteki `cekilen_tutar` tek bir sayı; bu defter o sayının **nereden geldiğini**
tutuyor. Müşteri "param çekilmemiş", banka "çekilmiş" dediğinde tartışma sağlayıcı
işlem numarasıyla çözülür. Stok defterinde de aynısını yaptık.

**Çağrılacak dört işlev** (`odeme.islemler`):

| İşlev | Ne zaman |
|---|---|
| `provizyon_al(siparis, kullanici)` | Sipariş onaylandığı anda |
| `cekim_yap(siparis, kullanici)` | Tartım bitip sipariş hazırlandığında |
| `bloke_coz(siparis, kullanici, sebep)` | Sipariş iptal edildiğinde |
| `iade_et(siparis, tutar, kullanici, sebep)` | Kusurlu ürün kararından sonra |

Sağlayıcıyı doğrudan çağırma, hep bunlardan geç: deftere yazma, siparişin ödeme
durumunu güncelleme ve çift çekim koruması burada.

**Korumalar — hepsini denedim:**

- **Çift çekim.** Her işlemin bir istek anahtarı var (`BH-2026-000011-cekim-1`).
  Aynı anahtarla ikinci çağrı yeni istek göndermiyor, var olan kaydı döndürüyor.
  Ağ koparsa, kullanıcı iki kez tıklarsa, zamanlanmış görev iki kez tetiklenirse
  müşteriden iki kez para çekilmiyor.
- **Çekilen tutar blokeyi aşamaz.** Tartı tahmini çok aşarsa sessizce fazla çekmek
  yerine hata veriyor — bankadan zaten çekilemez, müşteriye sorulması gerekir.
- **Çekim sonrası bloke çözülemez**, **çözülmüş blokeden çekim yapılamaz**,
  **provizyonsuz çekim yapılamaz**.
- **Kısmi iade** birden çok kez yapılabiliyor; toplam iade çekilen tutarı aşamıyor.
  Hepsi iade edilince durum `iade`, bir kısmı iade edilince `kismi_iade`.
- **Kart bilgisi yanıttan temizleniyor.** Sağlayıcılar bazen gönderdiğimiz isteği
  yanıtta geri döndürür; kart numarası o yoldan loglara sızar. `yaniti_temizle`
  iç içe sözlük ve listelerde de kart, CVV ve son kullanma alanlarını `***` yapıyor.
  Bu bir tercih değil, PCI-DSS gereği.

### 3. `DenemeSaglayici` — bugünden çalışıyor

Sağlayıcı seçilmedi ama akış beklemesin diye gerçek para hareketi olmayan bir
sağlayıcı yazdım. Her isteği başarılı sayıp sahte işlem numarası döndürüyor
(`DENEME-PRV-a3f9…`). Vitrin test modundayken bütün zincir prova edilebiliyor.

**Kilit:** Vitrin `acik` moddayken deneme sağlayıcı kullanılamıyor — `saglayici_sec`
hata veriyor. Müşterinin "ödedim" sanıp hiç para çekilmemesi olabilecek en kötü
hatalardan biri, kod seviyesinde engelledim.

iyzico/PayTR seçilince `odeme/saglayicilar.py` içine `Saglayici`'den türeyen tek bir
sınıf yazılacak, `SAGLAYICILAR` sözlüğüne bir satır eklenecek, `ODEME_SAGLAYICI`
ayarı değişecek. Başka hiçbir yer değişmeyecek.

### 4. Senden — akışa bağlama

Şu an işlevler yazılı ama **kimse çağırmıyor**. Üç yere bağlanacak:

1. **Sipariş onayı** (`siparis/views.py`, `siparis_ver`) → `siparise_cevir`'den hemen
   sonra `provizyon_al(siparis, kullanici=request.user)`.
   **Provizyon başarısızsa sipariş iptal edilmeli** ve müşteriye "ödeme alınamadı"
   denmeli — stok da geri dönmeli (`siparis.iptal_et()` zaten yapıyor).
2. **Depo "hazır" düğmesi** (`depo/views.py`, `hazir`) → durum `HAZIRLANIYOR`
   yapıldıktan sonra `cekim_yap(siparis, kullanici=request.user)`.
   Çekim başarısızsa durumu geri alma; mesajla bildir ve `ic_not`'a yaz — mal
   hazırlanmış, para sorunu ayrı bir iş.
3. **Sipariş iptali** (`hesaplar/views.py` iptal görünümü ve panel) →
   `bloke_coz(siparis, kullanici=…, sebep="Müşteri iptal etti")`.

İade akışını **bağlama** — kusurlu ürün bildirimi ekranı henüz yok, sırası gelince.

Ekranlarda gösterilecek metin: provizyon alındıysa *"Kartınızda {tutar} bloke edildi.
Tartımdan sonra yalnızca kesin tutar çekilecek."* Çekim sonrası *"Kartınızdan {tutar}
çekildi."* Tutarları `para_yaz` ile yaz.

### 5. Raporda görmek istediklerim

- `okuduğum talimat: 2 Ekim (6)` satırı
- `roller_kur` çıktısı (47 yetki, `! atlandı` yok)
- Uçtan uca: sipariş ver → kartta bloke → tart → hazır → kesin tutar çekildi,
  defterde üç satır
- İptal edilen siparişte blokenin çözüldüğü
- Ödeme defteri sayfasının mağaza yöneticisiyle açıldığı ve **değiştirilemediği**
- Provizyon başarısız olduğunda siparişin açılmadığı ve stoğun geri döndüğü
  (deneme sağlayıcıda negatif tutar başarısız döner, onunla sınayabilirsin)

### 6. Bunları yapma

- `odeme/saglayicilar.py`'ye gerçek sağlayıcı yazma — sözleşme yok, test anahtarı yok.
- Ödeme defterini panelden yazılabilir yapma.
- İade akışını ekrana bağlama.
- Canlıda `ODEME_SAGLAYICI` ayarını değiştirme; `deneme` kalsın.
- Canlıda `vitrin_modu = acik`.

---

---

## 2 Ekim 2026 (5) — Provizyon örneği düzeltildi

Kısa talimat. Raporun iyiydi; iki bulduğun şey de yerindeydi.

### 1. Hesap hatası bendeydi — düzelttim

Ön Bilgilendirme m.4'teki örnek **54,29 ₺** diyordu. Haklısın: tampon %15, yani
49,35 × 1,15 = **56,75 ₺**. Ben %10 ile hesaplamışım. Yasal metinde yanlış sayı,
müşteri sepette başka rakam görünce "sözleşmede başka yazıyor" demesine yol açardı.

Düzelttim ve **senin sürümün üzerine uyguladım** (`extends` en üstte olan hâli korundu).
Ayrıca örneğin başına "%15 tamponla" etiketi, altına da şu cümle eklendi:

> Yukarıdaki oran örnektir. Siparişinize uygulanacak tampon oranı ve bloke edilecek
> tutar, siparişi onaylamadan önce sepet ekranında ve sipariş özetinizde kuruşu
> kuruşuna gösterilir. Bağlayıcı olan, orada gördüğünüz tutardır.

Şablona `{{ site_ayarlar.provizyon_tampon_orani }}` koymadım bilerek: oran panelden
değişince örnekteki **bütün sayılar** (49,35 → 56,75) birlikte değişmeli, yarısı
dinamik yarısı sabit bir örnek daha kötü olurdu. Onun yerine bağlayıcı tutarın
sepette gösterildiğini yazdım — hukuken yeterli, pratikte doğru.

```powershell
Copy-Item hazir\yasal_on_bilgilendirme.html templates\yasal\on_bilgilendirme.html -Force
```

### 2. İki düzeltmen de doğru

- **`extends` ilk etiket olmalı.** Benim hatam, altı şablonda birden. `hazir/` eşlerine
  de uygulaman tam kuralına göre. Bundan sonra şablonlarımda `extends`'i en üste koyacağım.
- **`builtins` ile filtre yükleme.** Şablona `{% load %}` eklemek yerine ayardan
  çözmen daha iyi: `para` ve `miktar` zaten her sayfada lazım, her şablonda tek tek
  yüklemek unutulacak bir iş. İyi karar.
- Kayıt ekranına **kullanım koşulları kutusu** eklemen de doğru — talimatta "üyelik
  kutusu" diye geçiyordu ama ekranda gerçekten yoktu, sen fark edip açmışsın.

### 3. Canlıya alma — bunu rapora yaz

Raporlarında **Adım 5'ten (commit `e1fceb0`) sonra canlıya gittiğine dair bir not yok.**
O tarihten beri yerelde biriken işler: depo ekranları, alım listesi, kurye ekranı,
kurye ataması, yasal metinler, `gunu_kes` komutu, ilgi kaydı düzeltmesi.

Hepsi yerelde denenmiş durumda. Canlıya almanın önünde bir engel görmüyorum:

- Yeni migration'lar: `core` 0004 (ilgi kaydı) ve 0005 (kurye) — ikisi de alan ekliyor,
  veri silmiyor. PostgreSQL'de sorunsuz geçmeli.
- `roller_kur` Procfile'da zaten çalışıyor; yeni uygulamalar (`depo`, `lojistik`) model
  içermediği için ek yetki gerekmiyor.
- Yasal metinlerde `xxx` var, ama sayfalar **vitrin test modunda** ve gerçek satış yok.
  W002 uyarısı dağıtım kaydında görünecek — beklenen davranış, dağıtımı durdurmaz.

Dağıtımdan sonra rapora **canlıdan** şunları yaz: `/iptal-ve-iade/` açılıyor mu,
`/depo/` mağaza yöneticisiyle açılıyor mu, dağıtım kaydında W002 görünüyor mu.
Yerelde çalışması canlıda çalıştığı anlamına gelmiyor; 30 Eylül'deki Start Command
olayı bunu gösterdi.

Bir engel görüyorsan **gönderme**, sebebini rapora yaz.

### 4. Sırada

Başka bir şey istemiyorum; `gunu_kes` komutu ve kurye ataması bitti, yasal metinler bağlandı.
Beklediğimiz iki şey Ersin'de: **gün gruplaması** ve **şirket bilgileri**.

Ben `odeme` uygulamasını yazıyorum (`OdemeIslemi`: provizyon, çekim, iade, sağlayıcı
işlem numarası). Sağlayıcıdan bağımsız model; iyzico mu PayTR mi belli olunca yalnızca
bağlantı katmanı yazılacak. Sen `odeme` uygulaması açma.

Boş kalırsan yapılabilecek, önceliksiz iki iş:

- **Zamanlanmış kesim.** `gunu_kes` komutu hazır ama kimse çağırmıyor. Railway'de nasıl
  kurulacağını araştırıp rapora yaz (cron servisi mi, ayrı worker mı, maliyeti ne) —
  **kurma**, Ersin'e soracağım.
- **Kesim uyarısı.** Kesim saati geçmiş ama hâlâ `ACIK` gün varsa depo ana sayfasında
  kırmızı şerit. Komut kurulana kadar insan gözü yedek olsun.

---

---

## 2 Ekim 2026 (4) — Kurye ataması: sorduğun kararı veriyorum

**Önce: bir üstteki talimatı (2 Ekim (3), yasal metinler) henüz okumamışsın.** Raporunda
"okuduğum talimat: 2 Ekim (2)" yazıyor. (3) sen çalışırken yazılmış olmalı. Bu talimatı
bitirince **yukarı doğru bakmayı alışkanlık edin:** son raporunda yazdığın numaradan
sonraki bütün başlıklar sende demektir. Şimdilik sırada (3) ve (4) var, ikisi de yapılacak.

Kurye ekranı iyi olmuş. İki şeyi ben söylemeden doğru yapmışsın:

- **"Yola çıktım" düğmesi.** `YOLDA`'ya geçiren tek yol paneldi, kurye panele girmiyor —
  o düğme olmadan müşteri siparişinde hiç "Yolda" görmeyecekti. Kalsın.
- **`personel_gerekli` ortak kapısı.** Depo ve kurye aynı yetki mantığını iki kez
  yazmaktan kurtuldu. `depo_gerekli` adını koruman da doğru; benim `depo/alim.py`
  dosyam o isimle içeri alıyor, kırılmadı.

---

### 1. Kurye ↔ rota ataması — karar: `TeslimTakvimi.kurye`

Raporunda yazmışsın: *"modelde kurye ↔ rota bağı olmadığından kurye, mağazasının bugünkü
bütün teslimatlarını görüyor. Birden çok kurye olunca karar gerekir."* Doğru tespit.

**Atama sipariş bazında değil, mahalle-gün bazında olacak.** Sebebi işin kendisi: kurye
bir mahalleye girip sokak sokak dolaşıyor. Aynı mahallenin siparişlerini iki kuryeye
bölmek aynı sokağa iki araba sokmak demek. `TeslimTakvimi` zaten "bir mahallenin bir
günü" demek — atamanın doğal yeri orası.

`core/models.py`'ye `TeslimTakvimi.kurye` eklendi (boş olabilir) ve bir yardımcı:

```python
TeslimTakvimi.kuryenin_rotalari(kullanici, sorgu)
```

Kural şu:

| Durum | Kurye ne görür |
|---|---|
| Rotaya kurye atanmamış | **Bütün kuryeler görür** — bugünkü davranışın aynısı |
| Rotaya kurye atanmış | Yalnızca o kurye görür |
| Yönetici / süper admin | Hepsini görür |

Atamayı boş bırakmak eski davranışı sürdürüyor; **tek kuryeyle çalışan mağaza hiçbir şey
yapmak zorunda değil.** İkinci kurye işe girdiğinde yönetici atama yapmaya başlar, o andan
sonra herkes yalnızca kendi rotasını görür. Zorunlu alan yapsaydım bugün tek kuryeli
Beyşehir'de her hafta 13 atama yapmak gerekirdi — işe yaramayan iş.

Kurye silinirse `SET_NULL`: rota kaybolmaz, ataması boşalır ve yine herkese görünür.
Sandbox'ta sekiz durumu da denedim, hepsi geçti.

```powershell
Copy-Item hazir\core_models.py core\models.py -Force
python manage.py makemigrations core
python manage.py migrate
```

Beklenen: `core/migrations/0006_teslimtakvimi_kurye.py` (yerelde 0005 çıktı, numara sende farklı olabilir).

**Senden:**

1. `lojistik/views.py` → rota sorgularını `TeslimTakvimi.kuryenin_rotalari(request.user, sorgu)`
   ile süz. Kendi `if` zincirini yazma; kural tek yerde dursun.
2. `core/admin.py` → `TeslimTakvimiAdmin`'e `kurye` sütunu, yan süzgeç ve düzenlenebilir alan.
   `limit_choices_to` zaten yalnızca kurye rolündekileri listeliyor. Mağaza yöneticisi
   **yalnızca kendi mağazasının** kuryelerini seçebilmeli — `MagazaKisitliAdmin`
   `suzulecek_modeller` listesine `kullanici` eklemen gerekebilir, ama dikkat: bu
   `uye` autocomplete'ini bozmuştu. Bozarsa `formfield_for_foreignkey` ile yalnızca
   `kurye` alanını süz.
3. Kurye ekranında, atanmamış bir rotanın başına küçük bir not: *"Bu rota kimseye
   atanmadı"*. Yönetici unuttuysa görünsün.

---

### 2. Sırada ne var

Üç ekran bitti (panel, depo, kurye), müşteri tarafı canlıda. Geriye iki şey kaldı:

**Sende — kesim saatinin kendiliğinden çalışması.** Şu an günü birinin elle kesmesi
gerekiyor. Kimse kesmezse sipariş akmaya devam eder, alım listesi hiç kesinleşmez.
Bu, işin sessizce bozulabileceği tek yer.

- `siparis/management/commands/gunu_kes.py` — kesim saati geçmiş ve hâlâ `ACIK` olan
  bütün takvimleri bulup `gunu_kes()` çağırsın. Kaç gün, kaç sipariş kesildiğini yazsın.
- `--kuru` seçeneği: ne yapacağını yazsın ama yapmasın. Canlıda ilk çalıştırmada lazım.
- Railway'de zamanlanmış görev olarak kurulacak (Ersin'e soracağım, sen kurma).
- Komut **tekrar çalıştırılabilir** olmalı: ikinci kez çalışınca kesilmiş günlere
  dokunmasın, hata vermesin. Zamanlanmış görevler iki kez tetiklenebilir.

**Bende — ödeme (`odeme` uygulaması) hazırlığı.** Sağlayıcı seçilmedi ama provizyon
akışının modeli sağlayıcıdan bağımsız: `OdemeIslemi` (provizyon, çekim, iade), sipariş
bağı, sağlayıcı işlem numarası. Yazıp `hazir/`'a koyacağım. Sen `odeme` uygulaması açma.

---

### 3. Raporda görmek istediklerim

- `okuduğum talimat: 2 Ekim (3) ve (4)` satırı
- Yasal metinlerin altısının da açıldığı ve kutuların bağlandığı (talimat (3))
- `bostanhane.W002` uyarısının çalıştığı (talimat (3))
- İki kuryeyle: her birinin yalnızca kendi rotasını, atanmamışları ikisinin de gördüğü
- `gunu_kes` komutunun `--kuru` çıktısı ve iki kez çalıştırıldığında hata vermediği

---

### 4. Bunları yapma

- `odeme` uygulaması açma, `OdemeIslemi` yazma — bende.
- `depo/alim.py`, `templates/depo/alim.html`, yasal metinlerin içeriği — bende.
- Zamanlanmış görevi Railway'de kurma — Ersin'e soracağım.
- Sipariş modeline yeni durum ekleme.
- Canlıda `vitrin_modu = acik`.

---

---

## 2 Ekim 2026 (3) — Yasal metinler hazır

Altı sayfa yazdım, `hazir/` içinde. Hepsi `{% extends "taban.html" %}` ile senin taban
şablonunu kullanıyor; içerik bloğunun adı `icerik`, farklıysa düzelt.

| Dosya | Sayfa | Adres adı (`name=`) | Nerede gösterilecek |
|---|---|---|---|
| `yasal_aydinlatma.html` | KVKK Aydınlatma Metni | `yasal_aydinlatma` | Kayıt ekranı, KVKK kutusunun bağlantısı |
| `yasal_kullanim.html` | Üyelik ve Kullanım Koşulları | `yasal_kullanim` | Kayıt ekranı, üyelik kutusunun bağlantısı |
| `yasal_gizlilik.html` | Gizlilik ve Çerez Politikası | `yasal_gizlilik` | Alt bilgi |
| `yasal_on_bilgilendirme.html` | Ön Bilgilendirme Formu | `yasal_on_bilgilendirme` | **Sepet onay ekranı**, birinci kutu |
| `yasal_mesafeli_satis.html` | Mesafeli Satış Sözleşmesi | `yasal_mesafeli_satis` | **Sepet onay ekranı**, ikinci kutu |
| `yasal_iade.html` | İptal ve İade | `yasal_iade` | Alt bilgi |

`yasal.css` → `static/css/site.css` dosyasının **sonuna** eklenecek (üzerine yazma).

```powershell
New-Item -ItemType Directory -Force templates\yasal | Out-Null
Copy-Item hazir\yasal_aydinlatma.html       templates\yasal\aydinlatma.html       -Force
Copy-Item hazir\yasal_kullanim.html         templates\yasal\kullanim.html         -Force
Copy-Item hazir\yasal_gizlilik.html         templates\yasal\gizlilik.html         -Force
Copy-Item hazir\yasal_on_bilgilendirme.html templates\yasal\on_bilgilendirme.html -Force
Copy-Item hazir\yasal_mesafeli_satis.html   templates\yasal\mesafeli_satis.html   -Force
Copy-Item hazir\yasal_iade.html             templates\yasal\iade.html             -Force
```

Görünümler basit (`TemplateView` yeter), `core/urls.py` ya da `bostanhane/urls.py`'ye
yukarıdaki `name` değerleriyle ekle. Hepsi **girişsiz açılabilmeli** — `vitrin_gerekli`
sarmalını koyma; sözleşmeyi okumak için üye olmak gerekmez.

### Bostanhane'ye özgü noktalar — bunları değiştirme

- **Provizyon maddesi** (Ön Bilgilendirme m.4) sayı sayı anlatılıyor: 1,5 kg domates →
  bloke 54,29 ₺ → tartıda 1,43 kg → çekilen 47,05 ₺. Müşteri kartında bloke görüp
  bankayı arayınca ortaya çıkacak soru bu; metin önden cevaplıyor. Kısaltma.
- **Taze üründe cayma hakkı yok** — Mesafeli Sözleşmeler Yönetmeliği m.15/1-(ç),
  çabuk bozulan mallar istisnası. Bal, bakliyat gibi dayanıklı üründe **var**.
  Kargo kanalı açılınca bu ayrım işleyecek.
- **Kesim saatinden sonra iptal yok** ve sebebi yazılı: ürün o sipariş için alınıyor.
- Yurt dışına veri aktarımı maddesi var — sunucu yurt dışındaysa (Railway ABD'de)
  KVKK m.9 gereği yazılması zorunlu. Ülke `xxx` bıraktım.

### Mesafeli Satış Sözleşmesi iki biçimde çalışıyor

Şablon `siparis` değişkenini kontrol ediyor:

- **Boş hâli** (`/mesafeli-satis-sozlesmesi/`) — herkes okur, genel ifadeler.
- **Dolu hâli** — görünüme `siparis` gönderirsen madde 1 ve 3 gerçek sipariş
  bilgileriyle (alıcı, ürün satırları, tutarlar) dolar.

Siparişlerim detay sayfasına *"Bu siparişin sözleşmesi"* bağlantısı ekle; dolu hâli
göstersin. Sebebi hukuki: müşteri hangi sözleşmeyi kabul ettiğini sonradan görebilmeli.

`{{ ...|para }}` filtresini kullanıyor, sende var.

### `xxx` koruması — bunu mutlaka yap

Metinlerde resmî bilgiler `<span class="xxx">xxx</span>` olarak duruyor; sayfada kırmızı
ve altı çizgili görünüyor, gözden kaçmaz. Ersin şirket bilgilerini verince hepsi tek
seferde doldurulacak.

**Buna bir de kod koruması ekle.** `bostanhane/checks.py` içindeki `W001` deseninin aynısı:

```python
# bostanhane.W002 — DEBUG=False iken yasal metinlerde doldurulmamış xxx varsa uyar
```

`templates/yasal/*.html` dosyalarını okusun, `class="xxx"` geçiyorsa uyarı versin.
Gerekçe: şirket bilgileri olmadan canlıya çıkarsak sözleşme hükümsüz, KVKK aydınlatması
eksik olur. İnsan hafızasına güvenmeyelim.

### Bir de şunu düşünelim (şimdi yapma, karar gerekiyor)

Sözleşme metni değişirse, müşterinin **hangi sürümü kabul ettiği** kanıtlanabilmeli.
Şu an metinler şablonda sabit; yarın bir maddeyi değiştirince dünkü siparişin hangi
metne dayandığını gösteremeyiz.

Çözüm bir `YasalMetin` modeli (ad, sürüm, içerik, yürürlük tarihi) ve `Siparis`'te
kabul edilen sürümün numarası. Ama bugün gerçek satış yok, vitrin test modunda —
acil değil. **Sanal POS açılmadan önce** yapılacak işler listesine koyuyorum, Ersin'e
de söyledim. Sen şimdi sabit şablonlarla devam et.

### Raporda görmek istediklerim

- `okuduğum talimat: 2 Ekim (3)` satırı
- Altı sayfanın da **girişsiz** açıldığı
- Kayıt ve sepet onay ekranındaki kutuların doğru sayfalara bağlandığı
- Siparişlerim detayından açılan sözleşmenin sipariş bilgileriyle **dolu** geldiği
- `bostanhane.W002` uyarısının çalıştığı (`DEBUG=False` ile `manage.py check` çıktısı)
- Telefon genişliğinde tabloların taşmadığı

### Bunları yapma

- Yasal metinlerin **içeriğini değiştirme.** Dizgi hatası görürsen rapora yaz, ben düzeltirim.
  Bu metinler avukat onayına gidecek; ikimizin ayrı ayrı düzenlemesi sürümü karıştırır.
- `xxx` yerlerini tahminle doldurma.
- Canlıda `vitrin_modu = acik` yapma — metinler hazır ama şirket bilgileri ve POS yok.

---

---

## 2 Ekim 2026 (2) — Alım listesi ekranı geldi; ilgi kaydı modeli düzeldi

Raporunu okudum. Paketleme ekranı iyi çıkmış — özellikle **kesilmemiş günde toplamayı
açmaman** doğru karar: yarım toplanmış sipariş değişirse tartım boşa giderdi, bunu
talimatta tek cümleyle geçmiştim, sen gerekçesini de yazmışsın.

Erken kesimi yöneticiye bağlaman da benim yazmadığım bir ayrım, ama doğru: kapasite
doldu diye günü erken kapatmak ticari karar, paketleme elemanının işi değil.

---

### 1. Alım listesi — hazır, bir tasarım hatamı düzelttim

**Talimatta `/depo/alim/<takvim>/` yazmıştım, yanlıştı.** `TeslimTakvimi` bir mahallenin
bir günü. Ama hale **günde bir kez** gidiliyor; o gün Avşar ve Evsat'a teslimat varsa
ikisinin talebi tek sepette toplanmalı. Mahalle başına liste, mahalle başına hal
yolculuğu demek olurdu. `alim_listesi()` işlevi de zaten tarih alıyor.

Adres tarihe bağlandı:

```powershell
Copy-Item hazir\depo_alim.py   depo\alim.py            -Force
Copy-Item hazir\depo_alim.html templates\depo\alim.html -Force
```

`static/css/depo.css` dosyasının **sonuna** `hazir/depo_alim.css` içeriğini ekle
(üzerine yazma — senin stillerin duruyor, bu ek bölüm).

`depo/urls.py`'ye iki satır:

```python
from . import alim as alim_gorunumleri
...
    path("depo/alim/<str:tarih>/", alim_gorunumleri.alim, name="depo_alim"),
    path("depo/alim/takvim/<int:pk>/", alim_gorunumleri.alim_takvimden, name="depo_alim_takvim"),
```

`depo/views.py`'ye dokunmadım; ekran ayrı dosyada (`depo/alim.py`), senin
`depo_gerekli` sarmalını kullanıyor.

**Bağlantı ekle** — ekran kurulduğunda ona giden yol olmalı:
- `depo/gunler.html` → her tarih başlığının yanına *"Alım listesi"*
  (`{% url 'depo_alim' tarih|date:'Y-m-d' %}`)
- `depo/gun.html` → kesildiyse *"Günün alım listesi"*
  (`{% url 'depo_alim_takvim' takvim.pk %}` — takvimden tarihe kendi yönlendiriyor)

**Ne yapıyor:**

| | |
|---|---|
| Gruplama | Kategoriye göre — haldeki yürüyüş sırası bu. Alfabetik liste mağazayı hal içinde ileri geri yürütürdü |
| Miktar | Sayfanın en büyük yazısı; `12,5 kg`, `1.234 adet`. Kilogramı grama çevirmiyorum — tezgâhta konuşulan birim kilogram |
| Deneme siparişleri | Listeye **girmiyor**, ama "1 deneme siparişi dahil edilmedi" diye yazıyor ki eksik sanılmasın |
| Kesilmemiş gün | Turuncu uyarı: "Bu liste henüz kesin değil, {n} mahallenin kesimi yapılmadı" + ilk kesim saati |
| Tartılı ürün | "tartılacak" rozeti + altta not: *"Hale biraz fazlasıyla gidin"* |
| İşaretleme | Satıra dokununca üstü çizilir. **localStorage**'da, sunucuya gitmiyor — alım kaydı değil, kişinin kendi işareti |
| Yazdır | `@media print` var: üst şerit, düğmeler ve bilgi kutuları kâğıda gitmiyor |
| Gezinme | Önceki/sonraki gün düğmeleri |

**Denediklerim (sandbox, hepsi geçti):** sayfa 200 · kategori gruplaması · miktar biçimi
(`2 kg`, `1,5 kg`, `2 kavanoz`, `1.234 adet`) · deneme siparişi sayılmıyor (2 sipariş
verdim, listede 1 göründü) · iptal edilen sipariş listeden düşüyor · kesimden sonra
uyarı kalkıyor · takvim adresi tarihe yönlendiriyor · **üye giremiyor** · bozuk tarih ve
teslimatı olmayan gün 404. Ayrıca 820 px ve 390 px'te ekran görüntüsüne baktım, taşma yok;
telefonda miktar ürün adının içine giriyordu, dar ekranda alta aldım.

---

### 2. `IlgiKaydi` — önerin doğruydu, modeli düzelttim

Haklıydın: `eposta` zorunluydu ama sen boş kaydediyordun (veritabanı kabul eder, panel
formu etmez) ve `__str__` e-postaya bağlıydı. "Yenişehir, Meram/Konya"yı tek metin alanına
sıkıştırman da mecburiyettendi.

```powershell
Copy-Item hazir\core_models.py core\models.py -Force
python manage.py makemigrations core
python manage.py migrate
```

Beklenen: `core/migrations/0005_…` — `uye` ve `ilce` eklenir, `eposta` artık boş olabilir.
(Yerelde 0004 çıktı; sende numara farklı olabilir, önemli değil.)

Değişenler:

- `eposta` → `blank=True`. Zorunlu tutarsak adres ekranından gelen kayıt hiç yazılamaz.
- `uye` → FK, boş olabilir. Ziyaretçide boş, üyeden gelende dolu.
- `ilce` → FK. **Listeyi ilçeye göre süzeceğiz** — "nereye talep var" sorusunun cevabı bu.
- `clean()` → e-posta, telefon ve üye'nin **üçü birden boşsa** reddediyor. Ulaşılamayan
  kayıt listeyi kalabalıklaştırır.
- `kime_ulasilir` ve `yer` özellikleri: `__str__` artık e-posta yoksa telefona, o da yoksa
  üyeye düşüyor.

**Senden:**

1. `hesaplar` içindeki `haber-ver` görünümünü güncelle: `mahalle_adi`'na yalnızca kişinin
   yazdığı mahalle adı gitsin; ilçe `ilce=` alanına, kullanıcı `uye=` alanına.
   `get_or_create` anahtarın da `(uye, ilce, mahalle_adi)` olsun.
2. `core/admin.py` → `IlgiKaydiAdmin`: sütunlara `ilce` ve `uye`, yan süzgece `ilce`.
   Dosya sende, `hazir/` eşine de uygula.

---

### 3. Sıradaki iş — kurye ekranı (Adım 6b)

Paketleme bitti, mal hazır. Sırada kapıya çıkması var. Telefon için, tek elle:

| Adres | Ne |
|---|---|
| `/kurye/` | Bugün kendisine düşen teslimatlar; mahalle başına kaç paket |
| `/kurye/rota/<takvim>/` | **Güzergâh sırasıyla** sipariş listesi — `hizmet_mahallesi.sira` zaten bu iş için |
| `/kurye/teslim/<numara>/` | Ad, telefon, adres, tarif, harita bağlantısı, tutar; **Teslim ettim** / **Ulaşılamadı** |

- Erişim: `Rol.KURYE` + mağaza yöneticisi + süper admin. Kurye `/yonetim/`'e giremez.
- Yalnızca `HAZIRLANIYOR` ve `YOLDA` durumundaki siparişler. `KESILDI` olan henüz toplanmamış.
- **Teslim ettim** → `siparis.teslim_edildi_isaretle()`. Kendi alan yazma, o işlev
  `teslim_zamani`'nı ve durumu birlikte ayarlıyor.
- **Ulaşılamadı** → durum `YOLDA` kalsın, `ic_not`'a saat ve "ulaşılamadı" yazılsın.
  Yeni durum **ekleme** — iade/yeniden deneme akışına karar vermedik.
- Tutar ekranda **görünsün** ama ödeme yok: kapıda ödeme almıyoruz, kart önceden çekiliyor.
  Kurye tutarı yalnızca müşteri sorarsa söylesin diye görüyor.
- Adres tarifi ve telefon büyük yazılsın; telefon numarası `tel:` bağlantısı olsun,
  adres `https://www.google.com/maps/search/?api=1&query=<enlem>,<boylam>` — enlem/boylam
  boşsa açık adresi arat.
- Depo ekranının `taban.html` ve `depo.css`'ini örnek al ama **ayrı** kur
  (`templates/kurye/`, `static/css/kurye.css`): depo tablet, kurye telefon.

---

### 4. Durum

**Bitti ve canlıda:** coğrafya · hizmet alanı · hesaplar · katalog (birim, fiyat, stok defteri) ·
satış ayarları + vitrin modu · sipariş motoru ve paneli · üyelik · vitrin · sepet · siparişlerim.

**Bitti, canlıya gidecek:** paketleme ekranı · alım listesi · ilgi kaydı düzeltmesi.

**Şu anda:** kurye ekranı (sende) · yasal metinler (bende, şirket bilgisi bekliyor).

**Sonra:** sanal POS · kargo kanalı · kampanya · abonelik · mobil uygulama.

**Bekleyen kararlar:** Beyşehir gün gruplaması (Ersin'de) · ödeme sağlayıcısı · Cloudflare R2 anahtarları.

---

### 5. Raporda görmek istediklerim

- `okuduğum talimat: 2 Ekim (2)` satırı
- Alım listesinin açıldığı ve gün sayfalarından bağlantının göründüğü
- `core` migration'ının temiz geçtiği, ilgi kaydının `ilce` ve `uye` ile yazıldığı
- Kurye ekranında bir siparişin teslim edildiği ve durumunun değiştiği
- "Ulaşılamadı" sonrası siparişin **kaybolmadığı** (hâlâ listede, not düşülmüş)

---

### 6. Bunları yapma

- `depo/alim.py` ve `templates/depo/alim.html` — bende. Hata bulursan rapora yaz.
- Sepet/sipariş modeline dokunma.
- Yeni `Siparis.Durum` ekleme — iade akışı konuşulmadı.
- Yasal metin yazma — bende, Ersin şirket bilgilerini veriyor.
- Canlıda `ornek_veri --rotalari_esitle` — Ersin'in gün gruplaması bekleniyor.
- Canlıda `vitrin_modu = acik`.

---

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

## Durum (2 Ekim (1) itibarıyla — güncel durum en üstteki talimatta)

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
