// static/js/nota_fiscal_entradas.js
window.OneTech = window.OneTech || {};

OneTech.NotaFiscalEntradas = (function () {
  const SELECTOR_ROOT = '#identificador-tela[data-tela="entradas_nota"]';
  const FORM_SELECTOR = '#filtro-notas-form';
  const INPUT_SELECTOR = '#filtro-notas-form input[name="termo"]';
  const TABLE_SORT_SCOPE = '#tabela-notas-redimensionavel thead';

  let boundRoot = null;
  const lastFormValues = {};

  function debounce(fn, delay = 350) {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), delay);
    };
  }

  function buildUrl(form) {
    const base = form.getAttribute('action') || window.location.pathname;
    const params = new URLSearchParams();
    const formData = new FormData(form);
    formData.forEach((value, key) => {
      params.append(key, value);
      lastFormValues[key] = value;
    });
    const qs = params.toString();
    return qs ? `${base}?${qs}` : base;
  }

  function restoreValues(root) {
    Object.entries(lastFormValues).forEach(([key, value]) => {
      if (value == null) return;
      const input = root.querySelector(`[name="${key}"]`);
      if (!input) return;
      if (input.type === 'checkbox' || input.type === 'radio') return;
      input.value = value;
    });
  }

  function focusInput(root) {
    const input = root.querySelector(INPUT_SELECTOR);
    if (!input) return;
    const end = input.value.length;
    input.focus();
    if (typeof input.setSelectionRange === 'function') {
      input.setSelectionRange(end, end);
    }
  }

  function destroy(root) {
    if (!root) return;
    const controller = root._entradasNotaAbortController;
    if (controller) {
      controller.abort();
      delete root._entradasNotaAbortController;
    }
    delete root.dataset.bound;
    if (boundRoot === root) boundRoot = null;
  }

  function init(rootEl) {
    const marker = rootEl || document.querySelector(SELECTOR_ROOT);
    const root = marker ? marker.closest('main') || marker.parentElement : null;
    if (!root) return;

    if (boundRoot && boundRoot !== root) {
      destroy(boundRoot);
    }
    if (root.dataset.bound === '1') {
      destroy(root);
    }

    const form = root.querySelector(FORM_SELECTOR);
    if (!form) {
      root.dataset.bound = '0';
      return;
    }

    const controller = new AbortController();
    const { signal } = controller;
    root._entradasNotaAbortController = controller;
    root.dataset.bound = '1';
    boundRoot = root;

    restoreValues(root);
    form.dataset.skipGlobal = '1';

    const submitHandler = (event) => {
      event.preventDefault();
      const url = buildUrl(form);
      loadAjaxContent(url);
    };
    form.addEventListener('submit', submitHandler, { signal });

    const termoInput = root.querySelector(INPUT_SELECTOR);
    if (termoInput) {
      const debounced = debounce(() => {
        lastFormValues.termo = termoInput.value;
        const url = buildUrl(form);
        loadAjaxContent(url);
      }, 350);
      termoInput.addEventListener('input', debounced, { signal });
    }

    const clickHandler = (event) => {
      const link = event.target.closest('a');
      if (!link) return;
      if (link.closest(TABLE_SORT_SCOPE)) {
        event.preventDefault();
        loadAjaxContent(link.href);
        return;
      }
      if (link.closest(FORM_SELECTOR) && link.classList.contains('btn-outline-secondary')) {
        event.preventDefault();
        loadAjaxContent(link.href);
      }
    };
    root.addEventListener('click', clickHandler, { signal });

    controller.signal.addEventListener('abort', () => {
      if (form.dataset.skipGlobal === '1') delete form.dataset.skipGlobal;
    });

    focusInput(root);
  }

  return {
    init,
    destroy,
    SELECTOR_ROOT,
  };
})();
