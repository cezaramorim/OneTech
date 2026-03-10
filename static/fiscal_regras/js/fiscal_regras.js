(function () {
  function normalizeUf(input) {
    if (!input) return;
    input.addEventListener('input', function () {
      this.value = (this.value || '').toUpperCase().slice(0, 2);
    });
  }

  function initFiscalRegrasForm(root) {
    const page = root.querySelector('[data-page="regra_icms_create"], [data-page="regra_icms_update"]');
    if (!page || page.dataset.regrasInit === '1') return;
    page.dataset.regrasInit = '1';

    normalizeUf(page.querySelector('input[name="uf_origem"]'));
    normalizeUf(page.querySelector('input[name="uf_destino"]'));
  }

  document.addEventListener('DOMContentLoaded', function () {
    initFiscalRegrasForm(document);
  });

  document.addEventListener('ajaxContentLoaded', function () {
    initFiscalRegrasForm(document);
  });
})();
