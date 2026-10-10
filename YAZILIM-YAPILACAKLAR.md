# Bostanhane — Yazılımda kalanlar

> 9 Ekim 2026. Yazılımın şu ana kadarki hâli **canlıda çalışıyor**: müşteri sipariş
> verebiliyor, depo tartabiliyor, kurye teslim edebiliyor, para akışı (deneme modunda)
> işliyor, kusurlu ürün iadesi yapılabiliyor.
>
> Bu dosya **bundan sonra ne kaldığını** gösterir. Resmî işler (şirket, POS başvurusu,
> İYS) ayrı; burada yalnızca yazılım var.
>
> Kim: **C** = Cowork · **CC** = Claude Code · **E** = Ersin

---

## A — Pilot açılmadan tamamlanması gerekenler

### A1. Test şeridi yanlış sayfalarda · CC · küçük
`/mahalleme-gelin/` ve altı yasal sayfanın üstünde *"⚠ Deneme modundasınız — siparişler
gerçek değildir"* yazıyor. Talep sayfasında sipariş yok; kişinin bıraktığı kayıt gerçekten
tutuluyor. Reklamla gelen kişinin okuduğu ilk cümle bu olmamalı. Mesafeli satış
sözleşmesinin başında "gerçek değildir" yazması ayrıca sözleşmeyi şüpheli gösteriyor.

Şerit yalnızca sipariş akışında kalsın: vitrin, ürün, sepet, siparişlerim, hesabım.

**Durum:** talimat yazıldı, CC henüz okumadı.

### A2. Bildirimler — müşteri hiçbir şey duymuyor · C + CC · orta
Bugün müşteri sipariş veriyor ve **kapı çalana kadar sessizlik**. Gönderilmesi gerekenler:

| Ne zaman | Mesaj |
|---|---|
| Sipariş alındı | "Siparişiniz alındı. Kartınızda {tutar} bloke edildi." |
| Kesime 2 saat kala | "Bugün 18.00'de kapanıyor, eklemek istediğiniz var mı?" |
| Gün kesildi | "Siparişiniz kesinleşti, yarın {mahalle} teslimatındasınız." |
| Ürün bulunamadı | "{ürün} bulunamadı, {tutar} düşüldü." |
| Kurye yola çıktı | "Siparişiniz yola çıktı." |
| Teslim edildi | "Teslim edildi. Kesin tutar {tutar} çekildi." |

Kesim uyarısı doğrudan ciroya dokunuyor: "iki saat sonra kapanıyor" mesajı sepete ürün
ekletir.

**Yapı:** ödemede işe yarayan düzenin aynısı — sağlayıcıdan bağımsız katman, bugünden
çalışan "deneme" göndericisi (mesajı yollamaz, kaydeder). SMS firması seçilince tek
bağlantı sınıfı yazılır.

**Durum (10 Ekim): altyapı yazıldı, denendi, CC'ye teslim edildi.** Sekiz mesaj türü
(yukarıdaki altısı + sipariş iptali + talep kararı), defteri panelde salt okunur,
her mesajın kaç SMS parçası ettiği görünüyor, çift gönderim koruması var, SMS firması
çökse bile sipariş akışı bozulmuyor. Kesim hatırlatması zamanlanmış komut olarak hazır.
71 kontrolle denendi. Kalan: CC'nin uygulamayı kurup akıştaki altı yere bağlaması, sonra
firma seçilince tek bağlantı sınıfı.

### A3. Sözleşme sürüm takibi · C · küçük
Yasal metinler şu an şablonda sabit. Yarın bir maddeyi değiştirince **dünkü siparişin
hangi metne dayandığını gösteremeyiz.** Gerçek satış açılmadan önce yapılmalı:
`YasalMetin` kaydı (ad, sürüm, içerik, yürürlük tarihi) ve siparişte kabul edilen sürüm.

### A4. Gerçek sanal POS bağlantısı · C · orta
Sağlayıcı (iyzico / PayTR) seçilince. Model ve akış hazır; yazılacak tek şey
`odeme/saglayicilar.py` içine bir sınıf. **Test anahtarları gerekiyor**, onsuz yazılamaz.

### A5. Prova · E · yarım gün
`PROVA.md` hazır bekliyor. Sistemi bugüne kadar hiçbir insan uçtan uca kullanmadı — ben ve
CC kod yazarak test ettik. İlk gerçek müşteride ekranı ilk kez görmek kötü olur.

---

## B — Pilot dönmeye başlayınca lazım olacaklar

### B1. Satış raporları · C · orta
Şu an sadece alım listesi var. Birkaç hafta sonra sorulacak sorular: ne sattım, hangi
mahalle ne getirdi, en çok satan ürün, ortalama sepet, fire oranı, iade oranı.

### B2. Görsel küçültme · CC · küçük
R2 anahtarları gelince. Telefonla çekilen 5 MB'lık fotoğraf olduğu gibi yüklenirse hem
depolama hem sayfa hızı bozulur.

### B3. Paketleme etiketi · CC · küçük
Toplanan siparişin üzerine yapıştırılacak etiket: müşteri adı, sipariş no, mahalle,
kalem sayısı. Kurye poşetleri karıştırmasın.

### B4. Fire ve stok sayımı ekranı · CC · küçük
Panelden yapılabiliyor ama depo ekranında yok. Bozulan ürünü tablet başındayken
işaretlemek, akşam panele oturup hatırlamaya çalışmaktan iyidir.

### B5. Mağaza → müşteri mesajı · C · küçük
Yönetici bir siparişle ilgili müşteriye not yazabilsin (A2 altyapısı üzerinden).

---

## C — Büyürken

### C1. Kargo kanalı · C + CC · büyük
Veri modeli destekliyor (`Urun` kanal bayrakları, `Siparis.Kanal.KARGO`) ama akış yok:
kargo firması entegrasyonu, takip numarası, kargo ücreti, 14 gün cayma süreci.
Ayrıca **Beyşehir dışı mahalle verisi** gerekiyor — şu an yalnızca Beyşehir yüklü.

### C2. Kampanya ve indirim kodu · C · orta
Hiç yok. `MagazaUrun.eski_fiyat` üstü çizili fiyat için duruyor, arkasında motor yok.

### C3. Abonelik · C · orta
Haftalık düzenli sipariş. Süt işi bununla birlikte gelir (`icerik/sut-abonelik-plani.md`).

### C4. Kurumsal (B2B) · C · büyük
Kafe, pansiyon, yurt. Ayrı fiyat listesi, düzenli sipariş şablonu, fatura akışı.

### C5. API + mobil uygulama · C + CC · büyük
DRF kurulu ama uç nokta yok. Mobil (React Native) hiç başlamadı.

### C6. İkinci mağaza · E + C · orta
Yazılım çok mağazayı baştan destekliyor (mağaza izolasyonu sorgu seviyesinde). Karaman
açılırken yapılacak iş: mahalle verisi, mağaza kaydı, yönetici hesabı, teslim günleri.
Talep haritası nereye açılacağını gösterecek.

---

## SMS firması — seçmeden önce bilinmesi gereken

**Önemli uyarı:** SMS başlığı (gönderen adı) **marka/unvan belgesine bağlı** olarak
tahsis ediliyor. Anlaşma seçmennediyor'un şirketi üzerinden yapılırsa, mesajlar o
şirketin başlığıyla gider. Müşteri **"BOSTANHANE"** değil başka bir isimden mesaj alır —
sipariş bildiriminde bu güven kırar, hatta spam sanılır.

Aynı hesap altında ikinci bir başlık açılabilir ama "BOSTANHANE" adını kullanma hakkını
belgelemek gerekir. **Marka başvurusu bu yüzden önem kazanıyor.** Operatöre ne
sunulacağını önceden sor.

**İkinci önemli nokta:** Sipariş bildirimleri **ticari elektronik ileti değildir** —
hizmetin ifasına ilişkin bilgilendirmedir, İYS onayı gerektirmez. Yalnızca kampanya
duyuruları İYS'ye tabi. Firmayla konuşurken bu ayrımı netleştir; bazı firmalar her şeyi
İYS'ye sokmaya çalışıyor, gereksiz onay kaybına yol açar.

**Firmada aranacaklar:** BTK lisansı · REST API ve test ortamı · teslim raporu ·
ulaşmayan SMS'in iade edilmesi · İYS entegrasyonu (kampanya için) · paket zorunluluğu
olmadan kullandıkça ödeme.

Bakılabilecekler: iletiMerkezi (eMarka, BTK lisanslı, API + test ortamı + SDK),
Netgsm, Verimor, Mutlucell. Fiyatlar paket büyüklüğüne göre değişiyor; pilotta aylık
birkaç yüz SMS olacağı için **en ucuz birim fiyat değil, en küçük paket ve API kalitesi**
belirleyici olmalı.

---

## Sıra önerim

1. **A1** (CC) — reklamdan önce şart, hâlâ bekliyor
2. ~~**A2 bildirim altyapısı**~~ — yazıldı, CC kurulumu bekliyor (10 Ekim)
3. **A5 prova** (E) — hiçbir şeye bağlı değil, bugün yapılabilir · en çok ihmal edilen madde
4. SMS firması seçilince A2'nin bağlantısı · POS seçilince A4 · ikisi de kısa iş
5. **A3** gerçek satıştan önce
6. B grubu pilot dönerken
