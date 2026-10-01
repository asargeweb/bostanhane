"""
Her sayfanın şablonuna giden ortak bilgiler (context processor).

Üst menüdeki sepet sayısı, test modu şeridi, kesim geri sayımı ve alt bilgideki
minimum sepet / ücretsiz teslimat eşiği her sayfada lazım; her görünüm bunları
ayrı ayrı hesaplamasın diye burada.
"""


def site_baglami(request):
    # Yönetim paneli bu bilgileri kullanmıyor; oradaki her sayfada boşuna sorgu atmayalım.
    if request.path.startswith("/yonetim/"):
        return {}

    from core.models import SatisAyarlari
    from siparis.vitrin_araclari import aktif_magaza, kesim_bilgisi, sepet_bul

    magaza = aktif_magaza(request)
    if magaza is None:
        return {}
    ayarlar = SatisAyarlari.getir(magaza)
    sepet = sepet_bul(request, magaza)
    return {
        "site_magaza": magaza,
        "site_ayarlar": ayarlar,
        "test_modu": ayarlar.test_modunda_mi,
        "vitrin_gorunur": ayarlar.vitrin_gorunur_mu(request.user),
        "sepet_adet": sepet.kalem_sayisi if sepet else 0,
        "sepet_tutar": sepet.ara_toplam if sepet and not sepet.bos_mu else None,
        "site_kesim": kesim_bilgisi(request, sepet),
    }
