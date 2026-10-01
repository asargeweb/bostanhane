// Ürünler listesindeki fiyat sütunu: "düzenle" fiyat kutusunu ve satışta
// kutucuğunu açar, "vazgeç" ikisini eski değere döndürüp kapatır. Kapalı
// alanlar forma gönderilmediği için yalnızca bilerek açılan satırlar kaydedilir.
document.addEventListener("click", function (olay) {
  var dugme = olay.target.closest(".fiyat-duzenle, .fiyat-vazgec");
  if (!dugme) return;
  var hucre = dugme.closest(".fiyat-hucre");
  var metin = hucre.querySelector(".fiyat-metin");
  var alan = hucre.querySelector(".fiyat-alan");
  var kutu = alan.querySelector('input[name^="fiyat_"]');
  var satista = alan.querySelector('input[name^="satista_"]');
  var ac = dugme.classList.contains("fiyat-duzenle");

  if (!ac) {
    kutu.value = hucre.querySelector('input[name^="fiyat_ilk_"]').value;
    satista.checked = hucre.querySelector('input[name^="satista_ilk_"]').value === "1";
  }
  metin.hidden = ac;
  alan.hidden = !ac;
  kutu.disabled = !ac;
  satista.disabled = !ac;
  if (ac) {
    kutu.focus();
    kutu.select();
  }
});
