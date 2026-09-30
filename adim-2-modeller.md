# Adım 2 — Mağaza, mahalle ve teslim takvimi

Adım 1'i (kurulum) bitirdikten sonra buradan devam edin.
Bu adımın sonunda: PostgreSQL'e bağlı, yönetim panelinden Bostanhane Beyşehir mağazasının,
üç mahallenin ve 8 haftalık teslim takviminin girildiği çalışan bir sistem olacak.

Hazır dosyaları `hazir/` klasörüne koydum. Aşağıdaki komutlar onları yerlerine kopyalar.

---

## 1) Sanal ortamı açın

```powershell
cd "$env:USERPROFILE\Desktop\bostanhane\bostanhane"
.\venv\Scripts\Activate.ps1
```

## 2) core uygulamasını oluşturun

```powershell
python manage.py startapp core
```

## 3) Hazır dosyaları yerlerine kopyalayın

```powershell
Copy-Item hazir\settings.py bostanhane\settings.py -Force
Copy-Item hazir\urls.py bostanhane\urls.py -Force
Copy-Item hazir\core_models.py core\models.py -Force
Copy-Item hazir\core_admin.py core\admin.py -Force

New-Item -ItemType Directory -Force -Path core\management\commands | Out-Null
New-Item -ItemType File -Force -Path core\management\__init__.py | Out-Null
New-Item -ItemType File -Force -Path core\management\commands\__init__.py | Out-Null
Copy-Item hazir\ornek_veri.py core\management\commands\ornek_veri.py -Force
```

## 4) Veritabanı tablolarını oluşturun

```powershell
python manage.py makemigrations core
python manage.py migrate
```

`makemigrations` çıktısında dört model görmelisiniz: Magaza, Mahalle, HaftalikTeslimGunu, TeslimTakvimi.

> **Hata alırsanız:** "password authentication failed" yazıyorsa `.env` dosyasındaki `DB_PASSWORD` yanlıştır.
> "could not connect to server" yazıyorsa PostgreSQL servisi çalışmıyordur.

## 5) Kendinize yönetici hesabı açın

```powershell
python manage.py createsuperuser
```

Kullanıcı adı, e-posta ve şifre soracak. Şifreyi yazarken ekranda görünmez, bu normaldir.

## 6) Örnek veriyi oluşturun

```powershell
python manage.py ornek_veri
```

Bu komut Beyşehir mağazasını, Yeni Mahalle / Müftü / Bahçelievler mahallelerini,
teslim günlerini ve 8 haftalık takvimi oluşturur.

## 7) Çalıştırın ve bakın

```powershell
python manage.py runserver
```

Tarayıcıda **http://127.0.0.1:8000/yonetim/** adresine gidin, az önce açtığınız hesapla girin.

Göreceğiniz ekranlar:

| Bölüm | Ne var |
|---|---|
| **Mağazalar** | Bostanhane Beyşehir. İçine girince mahalleler alt liste olarak görünür |
| **Mahalleler** | Üç mahalle, teslim günleri ve kapasiteleri |
| **Haftalık teslim günleri** | "Müftü — Salı", "Müftü — Cuma" gibi kurallar |
| **Teslim takvimi** | Tarih tarih teslim günleri, kesim zamanları ve "kesime 31 saat" gibi durum bilgisi |

---

## Bu adımda ne kurduk

**Mağaza** → şube. Her mağaza aynı zamanda butik depo.

**Mahalle** → mağazanın hizmet verdiği yer. Kapasitesi var, çünkü bir kuryenin bir günde yapabileceği teslimat sınırlı.

**Haftalık teslim günü** → *kural*. "Müftü Mahallesi salı ve cuma, kesim bir gün önce 18:00."

**Teslim takvimi** → *somut gün*. "3 Ekim Cuma, kapasite 45, durum açık, kesim 2 Ekim 18:00."

Kural ile takvimi neden ayırdık? Çünkü hayat kuralı bozar: bayram tatili olur, araç arızalanır, bir gün kapasite dolar. Takvim kaydı sayesinde tek bir günü kapatabilir, kapasitesini değiştirebilir veya not düşebilirsiniz; haftalık kural bozulmaz. Siparişler de takvime bağlanacak, böylece "3 Ekim Cuma teslimatında 28 sipariş var" demek mümkün olur.

Yönetim panelinde iki de kısayol var:

- Mahalle listesinde seçim yapıp **"8 haftalık takvim üret"** diyebilirsiniz
- Takvim listesinde seçim yapıp **"Seçili günleri kes"** diyebilirsiniz (o gün sipariş almayı kapatır)

---

## Bana iletin

1. `makemigrations` ve `migrate` çıktıları
2. `ornek_veri` çıktısı
3. Yönetim panelinde takvimi görebildiniz mi

## Sırada (Adım 3)

- Kullanıcı ve roller: süper admin, mağaza yöneticisi, paketleme, kurye, üye
- Üye adresi ve adresin hangi mahalleye düştüğü
- Ürün kataloğu: kategori, ürün, birim, tartılı mı, kanal bayrakları (yerel / kargo / kurumsal)
