(function () {
  function getCsrfToken() {
    var c = document.cookie.split(';').find(function (x) { return x.trim().startsWith('csrftoken='); });
    return c ? c.split('=')[1] : '';
  }

  function notify(type, message) {
    if (window.mostrarMensagem) {
      window.mostrarMensagem(type, message);
      return;
    }
    console.log(type + ': ' + message);
  }

  async function postJson(url, payload) {
    const response = await fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCsrfToken(),
      },
      body: JSON.stringify(payload || {}),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || 'Falha na requisicao.');
    }
    return data;
  }

  async function postFormData(url, formData) {
    const response = await fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCsrfToken(),
      },
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || 'Falha na requisicao.');
    }
    return data;
  }

  function normalizeUf(input) {
    if (!input) return;
    input.addEventListener('input', function () {
      this.value = (this.value || '').toUpperCase().slice(0, 2);
    });
  }

  function renderOutput(root, text) {
    const output = root.querySelector('#fiscal-regras-output');
    if (output) {
      output.textContent = text || '';
    }
  }

  function updateMetrics(root, metrics) {
    if (!metrics) return;
    ['total', 'found', 'fallback', 'duration_avg_ms'].forEach(function (key) {
      var el = root.querySelector('[data-metric="' + key + '"]');
      if (el) {
        el.textContent = String(metrics[key] == null ? 0 : metrics[key]);
      }
    });
  }

  function initFiscalRegrasForm(root) {
    const page = root.querySelector('[data-page="regra_icms_create"], [data-page="regra_icms_update"]');
    if (!page || page.dataset.regrasFormInit === '1') return;
    page.dataset.regrasFormInit = '1';

    normalizeUf(page.querySelector('input[name="uf_origem"]'));
    normalizeUf(page.querySelector('input[name="uf_destino"]'));
  }

  function initFiscalRegrasList(root) {
    const page = root.querySelector('[data-page="regra_icms_list"]');
    if (!page || page.dataset.regrasListInit === '1') return;
    page.dataset.regrasListInit = '1';

    const importBtn = page.querySelector('#btn-importar-regras');
    const validateBtn = page.querySelector('#btn-validar-regras');
    const fileInput = page.querySelector('#import-regras-file');

    if (importBtn) {
      importBtn.addEventListener('click', async function () {
        const importUrl = page.dataset.importUrl;
        if (!importUrl) return;
        if (!fileInput || !fileInput.files || !fileInput.files.length) {
          notify('warning', 'Selecione um arquivo JSON para importar.');
          return;
        }

        const fd = new FormData();
        fd.append('arquivo', fileInput.files[0]);
        importBtn.disabled = true;
        renderOutput(page, 'Importando regras...');
        try {
          const data = await postFormData(importUrl, fd);
          notify(data.success ? 'success' : 'warning', data.message || 'Importacao concluida.');
          renderOutput(page, JSON.stringify(data, null, 2));
          if (typeof loadAjaxContent === 'function') {
            loadAjaxContent(window.location.pathname);
          }
        } catch (error) {
          notify('error', error.message || 'Falha na importacao.');
          renderOutput(page, 'Falha na importacao: ' + (error.message || 'erro desconhecido'));
        } finally {
          importBtn.disabled = false;
        }
      });
    }

    if (validateBtn) {
      validateBtn.addEventListener('click', async function () {
        const validarUrl = page.dataset.validarUrl;
        if (!validarUrl) return;
        validateBtn.disabled = true;
        renderOutput(page, 'Validando regras...');
        try {
          const data = await postJson(validarUrl, {});
          notify(data.success ? 'success' : 'warning', data.message || 'Validacao concluida.');
          updateMetrics(page, data.metrics);
          renderOutput(page, JSON.stringify(data, null, 2));
        } catch (error) {
          notify('error', error.message || 'Falha na validacao.');
          renderOutput(page, 'Falha na validacao: ' + (error.message || 'erro desconhecido'));
        } finally {
          validateBtn.disabled = false;
        }
      });
    }
  }

  function bootstrap() {
    initFiscalRegrasForm(document);
    initFiscalRegrasList(document);
  }

  document.addEventListener('DOMContentLoaded', bootstrap);
  document.addEventListener('ajaxContentLoaded', bootstrap);
})();
