// static/js/relatorios/notas_entradas.js
window.OneTech = window.OneTech || {};

OneTech.NotasEntradas = (function () {
  const SELECTOR_ROOT = '[data-page="notas-entradas"]';
  const API_URL = '/relatorios/api/v1/notas-entradas/';

  function debounce(fn, delay = 350) {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), delay);
    };
  }

  function getCSRFToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
  }

  function formatarDataBR(valor) {
    if (!valor) return '-';
    const [ano, mes, dia] = valor.split('-');
    return `${dia}/${mes}/${ano}`;
  }

  function formatarValorBR(valor) {
    if (valor == null) return '-';
    const numero = Number.parseFloat(valor);
    if (Number.isNaN(numero)) return '-';
    return numero.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  }

  function buildParams(form) {
    const params = new FormData(form);
    const entries = Object.fromEntries(params.entries());
    Object.keys(entries).forEach((key) => {
      if (!entries[key]) delete entries[key];
    });
    return entries;
  }

  function renderNotas(root, notas) {
    const tbody = root.querySelector('#notas-entradas-table tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    if (!Array.isArray(notas) || notas.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Nenhuma nota encontrada.</td></tr>';
      return;
    }

    notas.forEach((nota) => {
      const tr = document.createElement('tr');
      tr.dataset.id = nota.id;
      tr.innerHTML = `
        <td><input type="checkbox" class="form-check-input check-linha"></td>
        <td>${nota.numero || '-'}</td>
        <td>${nota.fornecedor || '-'}</td>
        <td>${formatarDataBR(nota.data_emissao)}</td>
        <td>${formatarDataBR(nota.data_saida)}</td>
        <td>${formatarValorBR(nota.valor_total)}</td>
        <td>
          <a href="/relatorios/entradas/${nota.id}/editar/" class="btn btn-sm btn-outline-primary ajax-link">
            Editar
          </a>
        </td>`;
      tbody.appendChild(tr);
    });
  }

  async function fetchNotas(root, filtros = {}) {
    const tbody = root.querySelector('#notas-entradas-table tbody');
    if (tbody) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center"><span class="spinner-border spinner-border-sm"></span> Carregando...</td></tr>';
    }

    try {
      const qs = new URLSearchParams(filtros).toString();
      const url = qs ? `${API_URL}?${qs}` : API_URL;
      const response = await fetchWithCreds(url, { method: 'GET' }, 'application/json');
      if (!response.ok) throw new Error('Não foi possível carregar as notas.');
      const data = await response.json();
      renderNotas(root, data.results || []);
    } catch (error) {
      console.error('Erro ao buscar notas:', error);
      mostrarMensagem('danger', error.message || 'Falha ao carregar notas.');
      if (tbody) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">Erro ao carregar dados.</td></tr>';
      }
    }
  }

  function bindDeleteButton(root) {
    const button = root.querySelector('#btn-excluir-selecionados');
    if (!button) return () => {};

    const handler = async () => {
      const selecionados = Array.from(root.querySelectorAll('.check-linha:checked'))
        .map((cb) => cb.closest('tr')?.dataset.id)
        .filter(Boolean);
      if (!selecionados.length) {
        mostrarMensagem('warning', 'Selecione ao menos uma nota para excluir.');
        return;
      }
      const confirma = await Swal.fire({
        icon: 'question',
        title: 'Confirmar exclusão',
        text: `Confirma excluir ${selecionados.length} nota(s)?`,
        showCancelButton: true,
        confirmButtonText: 'Sim, excluir',
        cancelButtonText: 'Cancelar',
      });
      if (!confirma.isConfirmed) return;

      try {
        const resp = await fetchWithCreds(API_URL, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
          },
          body: JSON.stringify({ ids: selecionados }),
        }, 'application/json');
        if (!resp.ok) throw new Error('Erro ao excluir notas.');
        mostrarMensagem('success', 'Notas excluídas com sucesso.');
        await fetchNotas(root, buildParams(root.querySelector('#filtro-notas')));
      } catch (error) {
        console.error('Erro ao excluir notas:', error);
        mostrarMensagem('danger', error.message || 'Falha ao excluir notas.');
      }
    };

    button.addEventListener('click', handler);
    return () => button.removeEventListener('click', handler);
  }

  function bindForm(root) {
    const form = root.querySelector('#filtro-notas');
    if (!form) return () => {};
    form.dataset.skipGlobal = '1';

    const debouncedFetch = debounce(() => fetchNotas(root, buildParams(form)), 400);

    const handleSubmit = (event) => {
      event.preventDefault();
      debouncedFetch();
    };

    form.addEventListener('submit', handleSubmit);

    const listeners = [];
    const inputs = Array.from(form.querySelectorAll('input, select, textarea'));
    inputs.forEach((input) => {
      const eventName = input.type === 'date' || input.tagName === 'SELECT' ? 'change' : 'input';
      const handler = () => debouncedFetch();
      input.addEventListener(eventName, handler);
      listeners.push({ input, eventName, handler });
    });

    return () => {
      form.removeEventListener('submit', handleSubmit);
      listeners.forEach(({ input, eventName, handler }) => {
        input.removeEventListener(eventName, handler);
      });
    };
  }

  function destroy(root) {
    if (!root) return;
    const controller = root._notasEntradasAbortController;
    if (controller) {
      controller.abort();
      delete root._notasEntradasAbortController;
    }
    delete root.dataset.bound;
    boundRoot = null;
  }

  let boundRoot = null;

  function init(rootEl) {
    const root = rootEl || document.querySelector(SELECTOR_ROOT);
    if (!root) return;

    if (boundRoot && boundRoot !== root) {
      destroy(boundRoot);
    }
    if (root.dataset.bound === '1') return;

    const controller = new AbortController();
    root._notasEntradasAbortController = controller;
    root.dataset.bound = '1';
    boundRoot = root;

    const cleanupForm = bindForm(root);
    const cleanupDelete = bindDeleteButton(root);

    fetchNotas(root, buildParams(root.querySelector('#filtro-notas')));

    controller.signal.addEventListener('abort', () => {
      cleanupForm();
      cleanupDelete();
    });
  }

  return {
    init,
    destroy,
    SELECTOR_ROOT,
  };
})();
