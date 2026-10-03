"""
Bostanhane — mahalle nüfusları

Bu dosya `core/nufus_verisi.py` olarak kaydedilir.

### Bu sayılar nereden geldi

Kaynak: TÜİK ADNKS **2023** verileri, atlasbig.com.tr üzerinden derlenmiş liste
(https://atlasbig.com.tr/konya-beysehirin-mahalleleri). Yani **TÜİK'ten
doğrudan değil, aktaran bir siteden** alındı.

Bunu açıkça yazıyorum çünkü fark eder:

- Sayılar 2023'e ait; nüfus her yıl değişiyor.
- Aktaran siteler arasında küçük farklar olabiliyor (örnek: Üzümlü için bir
  başka sitede 2026 verisi olarak 4.966 görünüyor, burada 2023 için 4.855).
- Listede **67 mahalle** var; veritabanında 70 kayıtlı. Eksik üçü aşağıda.

Bu yüzden sayılar **yön göstermek için** yeterli ("Yeni, İçerişehir'in on beş
katı"), ama bir yatırım hesabına ya da resmî bir belgeye girecekse TÜİK'in
kendi yayınından doğrulanmalı. Doğru sayılar elde edilince bu dosya
güncellenip `nufus_yukle` yeniden çalıştırılır.

Eşleştirme mahalle adının Türkçe slug'ı ile yapılıyor; listede olmayan mahalle
atlanıyor, uydurulmuyor.
"""

# TÜİK ADNKS 2023 — Beyşehir / Konya
KAYNAK = "TÜİK ADNKS 2023 (atlasbig.com.tr üzerinden)"
YIL = 2023

BEYSEHIR_NUFUS = {
    "Yeni": 10323,
    "Müftü": 8074,
    "Üzümlü": 4855,
    "Bahçelievler": 4499,
    "Hamidiye": 4372,
    "Hacıakif": 3183,
    "Beytepe": 2768,
    "Huğlu": 2711,
    "Karaali": 2285,
    "Esentepe": 2085,
    "Evsat": 2002,
    "Dalyan": 1704,
    "Doğanbey": 1611,
    "Sadıkhacı": 1604,
    "Avşar": 1457,
    "Esence": 1355,
    "Yeşildağ": 1345,
    "Hacıarmağan": 1049,
    "Yenidoğan": 945,
    "Bademli": 831,
    "Kurucuova": 769,
    "Çetmi": 737,
    "Sevindik": 724,
    "Bayavşar": 672,
    "Gökçimen": 594,
    "İçerişehir": 577,
    "Gölyaka": 567,
    "Çiçekler": 537,
    "Üstünler": 530,
    "Emen": 472,
    "Üçpınar": 452,
    "Bayındır": 417,
    "Akburun": 396,
    "Damlapınar": 395,
    "Kayabaşı": 363,
    "Göçü": 325,
    "Adaköy": 319,
    "Eğirler": 304,
    "Gölkaşı": 290,
    "Karadiken": 285,
    "Karahisar": 284,
    "Ağılönü": 270,
    "Yazyurdu": 267,
    "Avdancık": 224,
    "Sarıköy": 220,
    "Çukurağıl": 199,
    "Çiftlik": 193,
    "Eylikler": 192,
    "Fasıllar": 190,
    "Başgöze": 188,
    "Yunuslar": 185,
    "Kuşluca": 165,
    "Bekdemir": 154,
    "İsaköy": 139,
    "Dumanlı": 134,
    "Hüseyinler": 123,
    "Doğancık": 117,
    "Gökçekuyu": 116,
    "Yukarıesence": 94,
    "Mesutlar": 88,
    "Gündoğdu": 81,
    "Şamlar": 80,
    "Karabayat": 68,
    "Küçükavşar": 53,
    "Bayat": 48,
    "Çivril": 37,
    "Gönen": 24,
}

# Yukarıdaki listede olmayan, başka kaynaktan bulunan mahalleler.
# Her biri kendi yılını ve kaynağını taşıyor — farklı yılların sayılarını
# aynı tabloya karıştırıp tek yılmış gibi göstermek karşılaştırmayı bozardı.
# Model `nufus_yili` alanını mahalle başına tuttuğu için bu sorun olmuyor.
BEYSEHIR_AYRI = {
    "Ali Akkanat": (988, 2025, "TÜİK ADNKS 2025 (nufusune.com üzerinden)"),
}

# Hâlâ nüfusu bilinmeyenler — uydurmuyoruz, boş kalıyorlar:
#   Yeşilyurt (hizmet verdiğimiz mahallelerden biri), Akçabelen
# İkisi de aradığım listelerde yoktu. Ersin Beyşehir'i biliyor; TÜİK'ten ya da
# belediyeden doğru sayı gelince buraya eklenecek.

# İlçe slug'ı → nüfus tablosu. Karaman ve Konya merkez sırası gelince eklenir.
NUFUSLAR = {
    "beysehir": (KAYNAK, YIL, BEYSEHIR_NUFUS, BEYSEHIR_AYRI),
}
