// Bostanhane — site betikleri. Betik çalışmasa da sayfalar iş görür:
// miktar kutusu varsayılan değerle gönderilir, geri sayım sabit yazıyla kalır.
(function () {
  "use strict";

  function sayiYaz(n, basamak) {
    return n.toLocaleString("tr-TR", { minimumFractionDigits: basamak, maximumFractionDigits: basamak });
  }
  function miktarYaz(n, birim) {
    if (birim === "kg" && n < 1) return Math.round(n * 1000) + " g";
    return n.toLocaleString("tr-TR", { maximumFractionDigits: 3 }) + " " + birim;
  }
  function paraYaz(n) { return sayiYaz(n, 2) + " ₺"; }

  // -- miktar seçici: satış adımı kadar artar/azalır ----------------------
  document.querySelectorAll(".adet[data-adim]").forEach(function (kutu) {
    var adim = parseFloat(kutu.dataset.adim);
    var birim = kutu.dataset.birim;
    var girdi = kutu.parentElement.querySelector("input[name=miktar]");
    var yazi = kutu.querySelector("span");
    function guncelle(deger) {
      // Kayan nokta artığını at: 0.1 + 0.2 sorunu miktarı 0,30000001 yapmasın.
      deger = Math.round(deger * 1000) / 1000;
      girdi.value = deger;
      yazi.textContent = miktarYaz(deger, birim);
      kutu.dispatchEvent(new CustomEvent("miktar", { detail: deger, bubbles: true }));
    }
    kutu.querySelector("[data-azalt]").addEventListener("click", function () {
      var deger = parseFloat(girdi.value) - adim;
      if (deger >= adim - 1e-9) guncelle(deger);
    });
    kutu.querySelector("[data-arttir]").addEventListener("click", function () {
      guncelle(parseFloat(girdi.value) + adim);
    });
  });

  // Sepet satırında miktar değişince formu kendiliğinden gönder.
  document.addEventListener("miktar", function (olay) {
    var form = olay.target.closest("form[data-otomatik]");
    if (form) {
      clearTimeout(form._zamanlayici);
      form._zamanlayici = setTimeout(function () { form.submit(); }, 600);
    }
  });

  // -- ürün sayfası: tahmini tutar ve blokaj --------------------------------
  var hesap = document.querySelector("[data-fiyat]");
  if (hesap) {
    var fiyat = parseFloat(hesap.dataset.fiyat);
    var tampon = parseFloat(hesap.dataset.tampon || "0");
    var hBirim = hesap.dataset.birim;
    document.addEventListener("miktar", function (olay) {
      var m = olay.detail;
      var tahmini = Math.round(fiyat * m * 100) / 100;
      document.querySelectorAll("[data-tahmini]").forEach(function (e) { e.textContent = paraYaz(tahmini); });
      document.querySelectorAll("[data-bloke]").forEach(function (e) {
        e.textContent = paraYaz(Math.round(tahmini * (1 + tampon) * 100) / 100);
      });
      document.querySelectorAll("[data-miktar-yazi]").forEach(function (e) { e.textContent = miktarYaz(m, hBirim); });
      var ornek = Math.round(m * 0.95 * 1000) / 1000;
      document.querySelectorAll("[data-ornek-miktar]").forEach(function (e) { e.textContent = miktarYaz(ornek, hBirim); });
      document.querySelectorAll("[data-ornek-tutar]").forEach(function (e) {
        e.textContent = paraYaz(Math.round(fiyat * ornek * 100) / 100);
      });
    });
  }

  // -- kesim geri sayımı -------------------------------------------------
  var sayaclar = document.querySelectorAll("[data-kesim]");
  function sayacGuncelle() {
    sayaclar.forEach(function (e) {
      var kalan = (new Date(e.dataset.kesim) - new Date()) / 60000;   // dakika
      if (kalan <= 0) { e.textContent = "sipariş saati doldu"; return; }
      var gun = Math.floor(kalan / 1440), saat = Math.floor((kalan % 1440) / 60), dk = Math.floor(kalan % 60);
      e.textContent = (gun ? gun + " gün " : "") + (gun || saat ? saat + " saat " : "") + dk + " dakika";
    });
  }
  if (sayaclar.length) { sayacGuncelle(); setInterval(sayacGuncelle, 30000); }

  // -- adres formu: il → ilçe → mahalle ve bilgi kutusu ----------------------
  var adresFormu = document.querySelector("form[data-adres]");
  if (adresFormu) {
    var il = adresFormu.querySelector("[name=il]");
    var ilce = adresFormu.querySelector("[name=ilce]");
    var mahalle = adresFormu.querySelector("[name=mahalle]");
    var bilgi = adresFormu.querySelector("[data-mahalle-bilgi]");
    var ilgi = adresFormu.querySelector("[data-ilgi]");
    var ayrinti = adresFormu.querySelector("[data-adres-ayrinti]");
    // Mahalle listesi boş ilçe: adres alanları yerine "haber verelim" daveti.
    function davetGoster(bos) {
      ilgi.hidden = !bos;
      ayrinti.hidden = bos;
    }

    function doldur(secim, adres, bos) {
      secim.innerHTML = "<option value=''>" + bos + "</option>";
      secim.disabled = true;
      return fetch(adres).then(function (c) { return c.json(); }).then(function (veri) {
        veri.secenekler.forEach(function (s) {
          var o = document.createElement("option");
          o.value = s.pk; o.textContent = s.ad; secim.appendChild(o);
        });
        secim.disabled = false;
        return veri.secenekler.length;
      });
    }
    function bilgiGoster() {
      bilgi.hidden = true;
      if (!mahalle.value) return;
      fetch(adresFormu.dataset.bilgi.replace("0", mahalle.value))
        .then(function (c) { return c.json(); })
        .then(function (v) {
          bilgi.className = v.yerel ? "bilgi" : "uyari";
          bilgi.innerHTML = "";
          var b = document.createElement("b");
          var s = document.createElement("span");
          if (v.yerel) {
            b.textContent = v.mahalle + " Mahallesi'ne kurye gidiyor. ";
            s.appendChild(b);
            s.appendChild(document.createTextNode("Teslim günü: " + v.gunler + "." +
              (v.kesim ? " Siparişler " + v.kesim + "'de kapanır." : "")));
          } else {
            b.textContent = "Bu mahalleye kurye gitmiyor. ";
            s.appendChild(b);
            s.appendChild(document.createTextNode("Adresi kaydedebilirsiniz; kargo ile gönderim açıldığında kullanılır."));
          }
          bilgi.appendChild(document.createTextNode(v.yerel ? "🌿 " : "📦 "));
          bilgi.appendChild(s);
          bilgi.hidden = false;
        });
    }
    il.addEventListener("change", function () {
      mahalle.innerHTML = "<option value=''>Mahalle seçin</option>";
      bilgi.hidden = true;
      davetGoster(false);
      if (il.value) {
        doldur(ilce, adresFormu.dataset.ilceler + "?il=" + il.value, "İlçe seçin").then(function (adet) {
          // İlçeleri de yüklü olmayan il: doğrudan davet.
          davetGoster(adet === 0);
        });
      }
    });
    ilce.addEventListener("change", function () {
      bilgi.hidden = true;
      if (ilce.value) {
        doldur(mahalle, adresFormu.dataset.mahalleler + "?ilce=" + ilce.value, "Mahalle seçin")
          .then(function (adet) { davetGoster(adet === 0); });
      }
    });
    mahalle.addEventListener("change", bilgiGoster);
    if (mahalle.value) bilgiGoster();

    var baskasi = adresFormu.querySelector("[name=baskasi_alacak]");
    var kisi = adresFormu.querySelector("[data-baskasi]");
    function kisiGoster() { kisi.hidden = !baskasi.checked; }
    baskasi.addEventListener("change", kisiGoster);
    kisiGoster();
  }

  // -- mahallemize de gelin: il → ilçe → mahalle -----------------------------
  var gelin = document.querySelector("form[data-gelin]");
  if (gelin) {
    var gIl = gelin.querySelector("[name=il]");
    var gIlce = gelin.querySelector("[name=ilce]");
    var gMahalle = gelin.querySelector("[name=mahalle]");
    var gSec = gelin.querySelector("[data-mahalle-sec]");
    var gYaz = gelin.querySelector("[data-mahalle-yaz]");
    var gZaten = gelin.querySelector("[data-zaten]");
    var gGun = gelin.querySelector("[data-zaten-gun]");

    function gListe(secim, adres, bos) {
      secim.innerHTML = "<option value=''>" + bos + "</option>";
      return fetch(adres).then(function (c) { return c.json(); }).then(function (veri) {
        veri.secenekler.forEach(function (s) {
          var o = document.createElement("option");
          o.value = s.pk; o.textContent = s.ad; secim.appendChild(o);
        });
        return veri.secenekler.length;
      });
    }
    // Listesi olmayan ilçede mahalle adı elle yazılır.
    function gMod(listeVar) { gSec.hidden = !listeVar; gYaz.hidden = listeVar; }
    // Zaten gittiğimiz mahalle seçilirse göndermeden söyleyelim.
    function gZatenMi() {
      gZaten.hidden = true;
      if (!gMahalle.value || gSec.hidden) return;
      fetch(gelin.dataset.bilgi.replace("0", gMahalle.value))
        .then(function (c) { return c.json(); })
        .then(function (v) {
          if (!v.yerel) return;
          gGun.textContent = "Teslim günü: " + v.gunler + ".";
          gZaten.hidden = false;
        });
    }
    gIl.addEventListener("change", function () {
      gMahalle.innerHTML = "<option value=''>Mahalle seçin</option>";
      gZaten.hidden = true;
      gIlce.innerHTML = "<option value=''>İlçe seçin</option>";
      if (!gIl.value) return;
      gListe(gIlce, gelin.dataset.ilceler + "?il=" + gIl.value, "İlçe seçin");
    });
    gIlce.addEventListener("change", function () {
      gZaten.hidden = true;
      if (!gIlce.value) return;
      gListe(gMahalle, gelin.dataset.mahalleler + "?ilce=" + gIlce.value, "Mahalle seçin")
        .then(function (adet) { gMod(adet > 0); });
    });
    gMahalle.addEventListener("change", gZatenMi);
    gZatenMi();
  }

  // Sepette adres/gün seçimi değişince kaydet.
  document.querySelectorAll("form[data-secim] input[type=radio]").forEach(function (r) {
    r.addEventListener("change", function () { r.form.submit(); });
  });
})();
