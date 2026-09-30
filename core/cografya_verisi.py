"""
Bostanhane — coğrafya verisi

Bu dosya `core/cografya_verisi.py` olarak kaydedilir.
`cografya_yukle` komutu buradaki listeleri veritabanına yazar.

Kaynaklar: PTT posta kodu kayıtları ve nüfus istatistik siteleri (Eylül 2026).
Yeni il/ilçe eklemek için sadece bu dosyaya satır ekleyip
`python manage.py cografya_yukle` çalıştırmak yeterli.

6360 sayılı kanun notu: Konya büyükşehir olduğu için Beyşehir'de köy yok;
eski köyler mahalleye dönüştü. Bu yüzden listede hem merkez mahalleleri hem
köy kökenli mahalleler var, `tip` ile ayrılıyorlar.
"""

# --------------------------------------------------------------------------
# 81 il — (plaka kodu, ad)
# --------------------------------------------------------------------------
ILLER = [
    (1, "Adana"), (2, "Adıyaman"), (3, "Afyonkarahisar"), (4, "Ağrı"), (5, "Amasya"),
    (6, "Ankara"), (7, "Antalya"), (8, "Artvin"), (9, "Aydın"), (10, "Balıkesir"),
    (11, "Bilecik"), (12, "Bingöl"), (13, "Bitlis"), (14, "Bolu"), (15, "Burdur"),
    (16, "Bursa"), (17, "Çanakkale"), (18, "Çankırı"), (19, "Çorum"), (20, "Denizli"),
    (21, "Diyarbakır"), (22, "Edirne"), (23, "Elazığ"), (24, "Erzincan"), (25, "Erzurum"),
    (26, "Eskişehir"), (27, "Gaziantep"), (28, "Giresun"), (29, "Gümüşhane"), (30, "Hakkari"),
    (31, "Hatay"), (32, "Isparta"), (33, "Mersin"), (34, "İstanbul"), (35, "İzmir"),
    (36, "Kars"), (37, "Kastamonu"), (38, "Kayseri"), (39, "Kırklareli"), (40, "Kırşehir"),
    (41, "Kocaeli"), (42, "Konya"), (43, "Kütahya"), (44, "Malatya"), (45, "Manisa"),
    (46, "Kahramanmaraş"), (47, "Mardin"), (48, "Muğla"), (49, "Muş"), (50, "Nevşehir"),
    (51, "Niğde"), (52, "Ordu"), (53, "Rize"), (54, "Sakarya"), (55, "Samsun"),
    (56, "Siirt"), (57, "Sinop"), (58, "Sivas"), (59, "Tekirdağ"), (60, "Tokat"),
    (61, "Trabzon"), (62, "Tunceli"), (63, "Şanlıurfa"), (64, "Uşak"), (65, "Van"),
    (66, "Yozgat"), (67, "Zonguldak"), (68, "Aksaray"), (69, "Bayburt"), (70, "Karaman"),
    (71, "Kırıkkale"), (72, "Batman"), (73, "Şırnak"), (74, "Bartın"), (75, "Ardahan"),
    (76, "Iğdır"), (77, "Yalova"), (78, "Karabük"), (79, "Kilis"), (80, "Osmaniye"),
    (81, "Düzce"),
]

# --------------------------------------------------------------------------
# İlçeler — şimdilik iş planındaki iki il
# --------------------------------------------------------------------------
ILCELER = {
    "Konya": [
        "Ahırlı", "Akören", "Akşehir", "Altınekin", "Beyşehir", "Bozkır", "Cihanbeyli",
        "Çeltik", "Çumra", "Derbent", "Derebucak", "Doğanhisar", "Emirgazi", "Ereğli",
        "Güneysınır", "Hadim", "Halkapınar", "Hüyük", "Ilgın", "Kadınhanı", "Karapınar",
        "Karatay", "Kulu", "Meram", "Sarayönü", "Selçuklu", "Seydişehir", "Taşkent",
        "Tuzlukçu", "Yalıhüyük", "Yunak",
    ],
    "Karaman": [
        "Karaman", "Ayrancı", "Başyayla", "Ermenek", "Kazımkarabekir", "Sarıveliler",
    ],
}

# --------------------------------------------------------------------------
# Beyşehir mahalleleri
#
# MERKEZ: Beyşehir kent merkezi. Pilot burada başlıyor.
# KIRSAL: 6360 ile mahalleye dönüşen eski köyler ve beldeler.
# --------------------------------------------------------------------------
BEYSEHIR_MERKEZ = [
    "Avşar", "Bahçelievler", "Beytepe", "Dalyan", "Esentepe", "Evsat",
    "Hacıakif", "Hacıarmağan", "Hamidiye", "İçerişehir", "Müftü", "Yeni", "Yeşilyurt",
]

BEYSEHIR_KIRSAL = [
    "Adaköy", "Ağılönü", "Akburun", "Akçabelen", "Ali Akkanat", "Avdancık", "Bademli",
    "Başgöze", "Bayat", "Bayavşar", "Bayındır", "Bekdemir", "Çetmi", "Çiçekler",
    "Çiftlik", "Çivril", "Çukurağıl", "Damlapınar", "Doğanbey", "Doğancık", "Dumanlı",
    "Eğirler", "Emen", "Esence", "Eylikler", "Fasıllar", "Göçü", "Gökçekuyu",
    "Gökçimen", "Gölkaşı", "Gölyaka", "Gönen", "Gündoğdu", "Huğlu", "Hüseyinler",
    "İsaköy", "Karaali", "Karabayat", "Karadiken", "Karahisar", "Kayabaşı",
    "Kurucuova", "Kuşluca", "Küçükavşar", "Mesutlar", "Sadıkhacı", "Sarıköy",
    "Sevindik", "Şamlar", "Üçpınar", "Üstünler", "Üzümlü", "Yazyurdu", "Yenidoğan",
    "Yeşildağ", "Yukarıesence", "Yunuslar",
]

# İlçe bazında mahalle listesi: "Il / Ilce" → {"merkez": [...], "kirsal": [...]}
MAHALLELER = {
    "Konya / Beyşehir": {
        "merkez": BEYSEHIR_MERKEZ,
        "kirsal": BEYSEHIR_KIRSAL,
        "posta_kodu": "42700",
    },
}
