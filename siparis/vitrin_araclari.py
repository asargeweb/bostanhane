"""
Vitrin, sepet ve hesap ekranlarının ortak yardımcıları.

Sepet ve sipariş modellerine dokunmadan, onları ekranlara bağlayan ince katman:
hangi mağazada alışveriş yapılıyor, ziyaretçinin sepeti hangisi, vitrin bu kişiye
açık mı, sıradaki teslim günü ne.
"""

from functools import wraps

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.utils import timezone

from core.models import Magaza, SatisAyarlari, TeslimTakvimi

from .models import Sepet


def aktif_magaza(request):
    """
    Ziyaretçinin alışveriş yaptığı mağaza.

    Üyenin varsayılan adresi bir mağazanın hizmet alanındaysa o mağaza; değilse
    (ziyaretçi, adresi olmayan ya da kargo bölgesindeki üye) ilk açık mağaza.
    Şimdilik tek mağaza var, ama Karaman açıldığında sepet doğru mağazaya düşsün.
    """
    kullanici = request.user
    if kullanici.is_authenticated:
        adres = kullanici.varsayilan_adres
        if adres and adres.magaza and adres.magaza.aktif:
            return adres.magaza
    return Magaza.objects.filter(aktif=True).order_by("pk").first()


def sepet_bul(request, magaza, olustur=False):
    """
    Bu kişinin bu mağazadaki sepeti. Üyede üyeye, ziyaretçide oturuma bağlı.
    `olustur=False` iken sepet yoksa None döner — her sayfa açılışında boş
    sepet kaydı biriktirmeyelim.
    """
    if magaza is None:
        return None
    if request.user.is_authenticated:
        if olustur:
            return Sepet.objects.get_or_create(uye=request.user, magaza=magaza)[0]
        return Sepet.objects.filter(uye=request.user, magaza=magaza).first()

    anahtar = request.session.session_key
    if not anahtar:
        if not olustur:
            return None
        request.session.save()
        anahtar = request.session.session_key
    if olustur:
        return Sepet.objects.get_or_create(uye=None, oturum_anahtari=anahtar, magaza=magaza)[0]
    return Sepet.objects.filter(uye=None, oturum_anahtari=anahtar, magaza=magaza).first()


def ziyaretci_sepetini_kat(request, eski_anahtar):
    """
    Giriş ya da kayıttan sonra çağrılır: ziyaretçiyken kurulan sepet üyeninkine katılır.

    `eski_anahtar` girişten ÖNCE alınmalı: Django giriş anında oturum anahtarını
    güvenlik için değiştiriyor, sonradan bakınca eski sepet bulunamaz.
    """
    if not eski_anahtar or not request.user.is_authenticated:
        return
    for ziyaretci in Sepet.objects.filter(uye=None, oturum_anahtari=eski_anahtar):
        uye_sepeti = Sepet.objects.get_or_create(uye=request.user, magaza=ziyaretci.magaza)[0]
        try:
            uye_sepeti.birlestir(ziyaretci)
        except ValidationError as hata:
            messages.warning(request, "Sepetinizdeki bazı ürünler taşınamadı: "
                                      + " ".join(hata.messages))


def siradaki_teslimler(hizmet_mahallesi, adet=4):
    """Bu mahallenin sipariş alınabilen sıradaki teslim günleri."""
    if hizmet_mahallesi is None:
        return []
    return list(TeslimTakvimi.objects
                .filter(hizmet_mahallesi=hizmet_mahallesi, durum=TeslimTakvimi.Durum.ACIK,
                        kesim_zamani__gt=timezone.now())
                .select_related("hizmet_mahallesi__mahalle")
                .order_by("tarih")[:adet])


def kesim_bilgisi(request, sepet=None):
    """
    Kesim şeridi için: hangi mahalle, hangi teslim günü, kesim ne zaman.

    Sepette seçili gün varsa o; yoksa üyenin varsayılan adresinin sıradaki günü.
    Adres yoksa None — şerit "mahallenizi seçin" çağrısına döner.
    """
    if sepet and sepet.teslim_takvimi_id and sepet.teslim_takvimi.siparis_alinabilir:
        return sepet.teslim_takvimi
    adres = None
    if sepet and sepet.adres_id:
        adres = sepet.adres
    elif request.user.is_authenticated:
        adres = request.user.varsayilan_adres
    if adres is None:
        return None
    gunler = siradaki_teslimler(adres.hizmet_mahallesi, adet=1)
    return gunler[0] if gunler else None


def vitrin_gerekli(gorunum):
    """
    Vitrin bu kişiye açık değilse (mağazanın vitrin modu) yakında sayfasına gönderir.

    kapali → kimse · test → yalnızca giriş yapmış olan · acik → herkes.
    Karar `SatisAyarlari.vitrin_gorunur_mu`'da; burada yeniden yazılmıyor.
    """
    @wraps(gorunum)
    def sarmal(request, *args, **kwargs):
        magaza = aktif_magaza(request)
        ayarlar = SatisAyarlari.getir(magaza) if magaza else None
        if ayarlar is None or not ayarlar.vitrin_gorunur_mu(request.user):
            if ayarlar and ayarlar.test_modunda_mi:
                messages.info(request, "Vitrin şu an deneme modunda. Ürünleri görmek için "
                                       "giriş yapın ya da üye olun.")
            return redirect("ana_sayfa")
        request.magaza = magaza
        request.satis_ayarlari = ayarlar
        return gorunum(request, *args, **kwargs)
    return sarmal
