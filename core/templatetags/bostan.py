"""
Şablonlarda para ve miktar yazımı.

Kural (CLAUDE.md): para birimi tutardan sonra, Türkçe ondalık virgülü — `42,90 ₺`.
Her şablon bunu kendi yazarsa bir yerde `42.9 TL` kaçar; tek filtrede duruyor.
"""

from decimal import Decimal, InvalidOperation

from django import template

from core.araclar import para_yaz

register = template.Library()


def _decimal(deger):
    if deger in (None, ""):
        return None
    try:
        return Decimal(str(deger))
    except InvalidOperation:
        return None


@register.filter
def para(deger, secenek=""):
    """
    Decimal → '1.250,50 ₺'. Boşsa '—'. Biçim tek kaynaktan: core.araclar.para_yaz.
    `{{ esik|para:"yuvarlak" }}` → tam tutarda kuruş yazılmaz: '1.000 ₺'.
    """
    return para_yaz(_decimal(deger), kurusu_gizle=secenek == "yuvarlak")


@register.filter
def sayi(deger):
    """Decimal → '2,5' · '10' — gereksiz sıfırlar olmadan."""
    miktar = _decimal(deger)
    if miktar is None:
        return ""
    return f"{miktar.normalize():f}".replace(".", ",")


@register.filter
def miktar(deger, birim):
    """
    Miktarı birimiyle yazar: (0.5, 'kg') → '500 g' · (1.5, 'kg') → '1,5 kg' · (2, 'demet') → '2 demet'.
    Kilogramın altı gramla yazılır; müşteri "0,5 kg" değil "500 g" der.
    """
    sayisal = _decimal(deger)
    if sayisal is None:
        return ""
    if birim == "kg" and 0 < sayisal < 1:
        return f"{int(sayisal * 1000)} g"
    return f"{sayi(sayisal)} {birim}"


@register.filter
def yuzde(deger):
    """0.150 → '%15'"""
    oran = _decimal(deger)
    if oran is None:
        return ""
    return f"%{sayi((oran * 100).quantize(Decimal('0.1')))}"


@register.filter
def mutlak(deger):
    """-15.00 → 15.00 · "düşüldü" cümlesinde eksi işareti olmasın."""
    sayisal = _decimal(deger)
    return abs(sayisal) if sayisal is not None else deger


@register.filter
def telefon(deger):
    """'5321112233' → '0532 111 22 33'. Biçim hesaplar.models'teki tek yardımcıdan."""
    from hesaplar.models import telefon_okunur_yaz
    return telefon_okunur_yaz(deger)
