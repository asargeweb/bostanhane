// Ürünler listesindeki fiyat ve stok hücreleri: "düzenle" / "ekle / çıkar"
// alanları açar, "vazgeç" hepsini sayfanın ilk açıldığı değere döndürüp kapatır.
// Kapalı alanlar forma gönderilmediği için yalnızca bilerek açılan satırlar kaydedilir.
document.addEventListener("click", function (olay) {
  var dugme = olay.target.closest(".duzenle-ac, .duzenle-vazgec");
  if (!dugme) return;
  var hucre = dugme.closest(".duzenle-hucre");
  var metin = hucre.querySelector(".duzenle-metin");
  var alan = hucre.querySelector(".duzenle-alan");
  var ac = dugme.classList.contains("duzenle-ac");
  var alanlar = alan.querySelectorAll("input:not([type=hidden]), select");

  alanlar.forEach(function (girdi) {
    if (!ac) {
      if (girdi.type === "checkbox") {
        girdi.checked = girdi.defaultChecked;
      } else if (girdi.tagName === "SELECT") {
        girdi.selectedIndex = 0;
      } else {
        girdi.value = girdi.defaultValue;
      }
    }
    girdi.disabled = !ac;
  });
  metin.hidden = ac;
  alan.hidden = !ac;
  if (ac) {
    var ilk = alan.querySelector("input[type=text]");
    if (ilk) {
      ilk.focus();
      ilk.select();
    }
  }
});
