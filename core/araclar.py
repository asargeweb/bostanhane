"""
Bostanhane — küçük yardımcılar

Bu dosya `core/araclar.py` olarak kaydedilir.
"""

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
