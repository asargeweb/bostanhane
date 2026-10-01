// Ürünler listesindeki fiyat sütunu: "düzenle" kutuyu açar, "vazgeç" eski
// değere döndürüp kapatır. Kapalı kutu forma gönderilmediği için yalnızca
// bilerek açılan fiyatlar kaydedilir.
document.addEventListener("click", function (olay) {
  var dugme = olay.target.closest(".fiyat-duzenle, .fiyat-vazgec");
  if (!dugme) return;
  var hucre = dugme.closest(".fiyat-hucre");
  var metin = hucre.querySelector(".fiyat-metin");
  var alan = hucre.querySelector(".fiyat-alan");
  var kutu = alan.querySelector("input");
  var ac = dugme.classList.contains("fiyat-duzenle");

  if (!ac) {
    kutu.value = hucre.querySelector('input[name^="fiyat_ilk_"]').value;
  }
  metin.hidden = ac;
  alan.hidden = !ac;
  kutu.disabled = !ac;
  if (ac) {
    kutu.focus();
    kutu.select();
  }
});
