window.OneTech = window.OneTech || {};

OneTech.ComercialCondicaoPagamento = (function () {
  const SELECTOR_ROOT = '[data-page="condicao_pagamento_list"]';

  function buildEditUrl(editUrlBase, id) {
    const base = (editUrlBase || '').trim();
    if (!base || !id) return '';

    if (base.includes('/0/')) {
      return base.replace('/0/', `/${id}/`);
    }

    return base.endsWith('/') ? `${base}${id}/` : `${base}/${id}/`;
  }

  function navigate(url) {
    if (!url) return;
    if (typeof loadAjaxContent === 'function') {
      loadAjaxContent(url);
      return;
    }
    window.location.assign(url);
  }

  function init(rootEl) {
    if (!rootEl || rootEl.dataset.initialized === 'true') return;
    rootEl.dataset.initialized = 'true';

    const selectAllCheckbox = rootEl.querySelector('#select-all-checkbox');
    const btnEditarSelecionado = rootEl.querySelector('#btn-editar-selecionado');
    const btnExcluirSelecionados = rootEl.querySelector('#btn-excluir-selecionados');
    const searchInput = rootEl.querySelector('#search-input');
    const clearButton = rootEl.querySelector('#btn-limpar-busca');

    const rowCheckboxes = () => Array.from(rootEl.querySelectorAll('.row-checkbox'));

    function updateButtonStates() {
      const checkedCheckboxes = rowCheckboxes().filter((cb) => cb.checked);
      const selectedCount = checkedCheckboxes.length;

      if (btnEditarSelecionado) btnEditarSelecionado.disabled = selectedCount !== 1;
      if (btnExcluirSelecionados) btnExcluirSelecionados.disabled = selectedCount === 0;

      if (selectAllCheckbox) {
        const total = rowCheckboxes().length;
        selectAllCheckbox.checked = total > 0 && selectedCount === total;
        selectAllCheckbox.indeterminate = selectedCount > 0 && selectedCount < total;
      }
    }

    if (selectAllCheckbox) {
      selectAllCheckbox.addEventListener('change', function () {
        rowCheckboxes().forEach((checkbox) => {
          checkbox.checked = this.checked;
        });
        updateButtonStates();
      });
    }

    rowCheckboxes().forEach((checkbox) => checkbox.addEventListener('change', updateButtonStates));

    if (btnEditarSelecionado) {
      btnEditarSelecionado.addEventListener('click', function (event) {
        event.preventDefault();
        const checkedCheckboxes = rowCheckboxes().filter((cb) => cb.checked);
        if (checkedCheckboxes.length !== 1) return;

        const id = String(checkedCheckboxes[0].value || '').trim();
        const editUrlBase = btnEditarSelecionado.dataset.editUrlBase || '';
        const editUrl = buildEditUrl(editUrlBase, id);
        navigate(editUrl);
      });
    }

    if (btnExcluirSelecionados) {
      btnExcluirSelecionados.addEventListener('click', function () {
        const ids = rowCheckboxes().filter((cb) => cb.checked).map((cb) => cb.value);
        if (!ids.length || !window.Swal) return;

        Swal.fire({
          title: 'Tem certeza?',
          text: `Voce realmente deseja excluir ${ids.length} item(ns)? Esta acao e irreversivel.`,
          icon: 'warning',
          showCancelButton: true,
          confirmButtonColor: '#d33',
          cancelButtonColor: '#3085d6',
          confirmButtonText: 'Sim, excluir',
          cancelButtonText: 'Cancelar'
        }).then((result) => {
          if (!result.isConfirmed) return;

          fetch(btnExcluirSelecionados.dataset.deleteUrl || '', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': typeof getCSRFToken === 'function' ? getCSRFToken() : ''
            },
            body: JSON.stringify({ ids })
          })
            .then((response) => response.json())
            .then((data) => {
              if (data.success) {
                Swal.fire('Excluido', data.message, 'success').then(() => {
                  navigate(window.location.pathname + window.location.search);
                });
              } else {
                Swal.fire('Erro', data.message || 'Erro ao excluir registros.', 'error');
              }
            })
            .catch(() => Swal.fire('Erro', 'Falha na comunicacao com o servidor.', 'error'));
        });
      });
    }

    if (searchInput) {
      const runSearch = (window.debounce || ((fn) => fn))(function (value) {
        const currentUrl = new URL(window.location.href);
        const normalized = (value || '').trim();
        if (normalized) currentUrl.searchParams.set('busca', normalized);
        else currentUrl.searchParams.delete('busca');
        currentUrl.searchParams.delete('ordenacao');
        navigate(`${currentUrl.pathname}${currentUrl.search}`);
      }, 350);

      searchInput.addEventListener('input', function () {
        runSearch(this.value);
      });

      searchInput.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
          event.preventDefault();
          runSearch(this.value);
        }
        if (event.key === 'Escape') {
          this.value = '';
          runSearch('');
        }
      });
    }

    if (clearButton) {
      clearButton.addEventListener('click', function () {
        if (searchInput) {
          searchInput.value = '';
          searchInput.focus();
        }
        const currentUrl = new URL(window.location.href);
        currentUrl.searchParams.delete('busca');
        currentUrl.searchParams.delete('ordenacao');
        navigate(`${currentUrl.pathname}${currentUrl.search}`);
      });
    }

    updateButtonStates();
  }

  return { init, SELECTOR_ROOT };
})();
