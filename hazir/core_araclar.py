"""
Bostanhane — küçük yardımcılar

Bu dosya `core/araclar.py` olarak kaydedilir.
"""

from decimal import Decimal

from django.utils.text import slugify


# Django'nun slugify'ı Türkçe harfleri tanımaz: "Müftü" → "mft" olur.
# Önce harfleri karşılıklarına çeviriyoruz.
TURKCE_HARFLER = str.maketrans({
    "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ı": "i", "I": "i",
    "İ": "i", "i": "i", "ö": "o", "Ö": "o", "ş": "s", "Ş": "s",
    "ü": "u", "Ü": "u", "â": "a", "î": "i", "û": "u",
})


def turkce_slug(metin):
    """'Müftü Mahallesi' → 'muftu-mahallesi'. Adreste ve eşleştirmede kullanılır."""
    return slugify(str(metin).translate(TURKCE_HARFLER))


def para_yaz(tutar, kurusu_gizle=False):
    """
    1250.5 → '1.250,50 ₺'. Binlik nokta, kuruş virgül, para birimi sonda.

    Python'un biçimlendirmesi İngilizce yazar ("1,250.50"); müşteriye giden her
    metinde Türkçe biçim gerekiyor. Tek yerde dursun diye burada:
    modeldeki hata mesajı, panel sütunu ve şablon filtresi aynı işlevi çağırsın.

    `kurusu_gizle=True` → tam tutarlarda kuruş yazılmaz: 500 ₺, ama 499,50 ₺.
    Eşik ve minimum sepet gibi yuvarlak sayılarda kullanılır.
    """
    if tutar is None:
        return "—"
    sayi = Decimal(str(tutar)).quantize(Decimal("0.01"))
    if kurusu_gizle and sayi == sayi.to_integral_value():
        metin = f"{sayi:,.0f}".replace(",", ".")
    else:
        metin = f"{sayi:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
    return f"{metin} ₺"
