# Adım 1 — VS Code ile sıfırdan, tıklaya tıklaya

Hiç VS Code kullanmadıysanız buradan gidin. Her satırı sırayla yapın.

> **İyi haber:** PostgreSQL'i şimdilik kurmanıza gerek yok. Veritabanı olarak SQLite ile başlıyoruz;
> bu, tek bir dosyadan ibaret, hiçbir kurulum istemeyen bir veritabanı. Canlıya çıkarken
> `.env` dosyasında tek satır değiştirip PostgreSQL'e geçeceğiz.

---

## 1) Klasörü VS Code'da açın

1. VS Code'u açın
2. Üst menüden **File → Open Folder…** (Dosya → Klasör Aç)
3. Şu klasörü seçin: `Masaüstü → bostanhane → bostanhane`
4. "Do you trust the authors?" diye sorarsa **Yes, I trust the authors** deyin

Sol tarafta klasördeki dosyaları göreceksiniz: adim-1-kurulum.md, requirements.txt, hazir klasörü…

## 2) Terminali açın

Üst menüden **Terminal → New Terminal**. Alt tarafta siyah bir pencere açılır. Komutları buraya yazacağız.

> Terminalin üstünde `powershell` veya `pwsh` yazmalı. Başka bir şey yazıyorsa, terminal penceresinin
> sağ üstündeki **+** işaretinin yanındaki oka tıklayıp **PowerShell** seçin.

## 3) Komutları tek tek çalıştırın

Her satırı yapıştırıp **Enter**'a basın. Bir komut bitmeden diğerine geçmeyin.

```powershell
python -m venv venv
```

```powershell
.\venv\Scripts\Activate.ps1
```

Satır başında `(venv)` yazmalı.

> **Hata: "betik çalıştırma devre dışı"** derse şunu çalıştırın, `E` yazıp Enter'a basın, sonra yukarıdaki komutu tekrarlayın:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

```powershell
python -m pip install --upgrade pip
```

```powershell
pip install -r requirements.txt
```

Bu biraz sürer, ekranda satırlar akar. Sonunda `Successfully installed…` yazmalı.

```powershell
django-admin startproject bostanhane .
```

Sondaki **nokta** önemli. Ekranda hiçbir şey yazmaz; sol taraftaki dosya listesinde `manage.py` ve `bostanhane` klasörü belirir.

```powershell
Copy-Item env-ornek.txt .env
```

## 4) .env dosyasını açın (VS Code'da nasıl yapılır)

1. Sol taraftaki dosya listesinde **.env** dosyasını bulun ve üzerine **tek tık** yapın
2. Sağda dosya açılır, içinde `DB_MOTOR=sqlite` satırını göreceksiniz
3. **Şimdilik hiçbir şey değiştirmenize gerek yok.** Sadece bir satırı düzeltelim:
   `DJANGO_SECRET_KEY=buraya-uzun-rastgele-bir-metin` satırındaki metni silip yerine
   klavyeden rastgele 40-50 karakter yazın (harf, rakam karışık olsun; ne yazdığınızın önemi yok)
4. **Ctrl + S** ile kaydedin

> Dosya listesinde `.env` görünmüyorsa: nokta ile başlayan dosyalar bazen gizlenir.
> Dosya listesinin boş bir yerine sağ tıklayıp **Reveal in File Explorer** diyebilir,
> ya da terminalde `notepad .env` yazıp Not Defteri'nde açabilirsiniz.

## 5) Veritabanını hazırlayın ve çalıştırın

```powershell
python manage.py migrate
```

```powershell
python manage.py runserver
```

Ekranda şuna benzer bir satır çıkar:

```
Starting development server at http://127.0.0.1:8000/
```

**Ctrl tuşuna basılı tutup** o adrese tıklayın; tarayıcıda Django'nun roket görselli karşılama sayfası açılır.

Sunucuyu durdurmak için terminale dönüp **Ctrl + C**.

---

## Bana şunu iletin

Terminalde en son ne yazdığını kopyalayıp bana gönderin. Hata varsa birlikte çözeriz — hata almak normaldir, ilk kurulumda herkes alır.

## Sonra ne olacak

`adim-2-modeller.md` dosyasındaki adımlarla mağaza, mahalle ve teslim takvimini kuracağız; yönetim panelinden Bostanhane Beyşehir'i açacaksınız.

## PostgreSQL ne zaman?

Canlı sunucuya geçerken. O gün şunu yapacağız: PostgreSQL kurulur, `.env` dosyasında `DB_MOTOR=postgres` yapılır, şifre yazılır, `python manage.py migrate` tekrar çalıştırılır. Kodun tek satırı değişmez.
