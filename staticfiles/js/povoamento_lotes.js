(function () {
  const PAGE_SELECTOR = '[data-page="povoamento-lotes"]';
  const SELECT2_BASE_CONFIG = {
    theme: 'bootstrap-5',
    width: 'style',
    dropdownAutoWidth: true,
  };

  function decodeJsonAttribute(value) {
    if (!value) return [];
    let raw = value;
    try {
      return JSON.parse(raw);
    } catch (error) {
      try {
        raw = raw.replace(/&quot;/g, '"');
        return JSON.parse(raw);
      } catch (innerError) {
        console.warn('Não foi possível interpretar JSON do dataset.', innerError);
        return [];
      }
    }
  }

  function resolveContext(page) {
    const dataset = page?.dataset || {};

    const datasetContext = {
      tanques: decodeJsonAttribute(dataset.tanques),
      fases: decodeJsonAttribute(dataset.fases),
      linhas: decodeJsonAttribute(dataset.linhas),
    };

    const globalContext = window.DJANGO_CONTEXT || {};

    const merged = {
      tanques: datasetContext.tanques.length ? datasetContext.tanques : (globalContext.tanques || []),
      fases: datasetContext.fases.length ? datasetContext.fases : (globalContext.fases || []),
      linhas: datasetContext.linhas.length ? datasetContext.linhas : (globalContext.linhas || []),
    };

    window.DJANGO_CONTEXT = { ...globalContext, ...merged };
    return merged;
  }

  function hasSelect2() {
    return Boolean(window.jQuery && window.jQuery.fn && window.jQuery.fn.select2);
  }

  function buildDropdownParent() {
    return window.jQuery('body');
  }

  function applySelect2($elements, extraConfig = {}) {
    if (!hasSelect2() || !$elements || !$elements.length) return;
    const config = {
      ...SELECT2_BASE_CONFIG,
      dropdownParent: buildDropdownParent(),
      ...extraConfig,
    };

    $elements.each(function () {
      const $el = window.jQuery(this);
      $el.off('.povoamento');
      if ($el.data('select2')) {
        $el.select2('destroy');
      }
      $el.select2(config);

      $el.on('select2:open.povoamento', () => {
        const dropdown = document.querySelector('.select2-container--open .select2-dropdown');
        if (dropdown) {
          dropdown.classList.remove('select2-dropdown--above');
          dropdown.classList.add('select2-dropdown--below');
          const elWidth = Math.ceil($el.outerWidth());
          const viewportAllowance = Math.max(window.innerWidth - 48, 240);
          const targetWidth = Math.min(Math.max(elWidth, 240), viewportAllowance);
          dropdown.style.minWidth = `${targetWidth}px`;
        }
      });

      $el.on('select2:close.povoamento', () => {
        const dropdown = document.querySelector('.select2-container--open .select2-dropdown');
        if (dropdown) {
          dropdown.style.minWidth = '';
        }
      });
    });
  }

  function generateGrupoOrigem() {
    const now = new Date();
    const mes = String(now.getMonth() + 1).padStart(2, '0');
    const ano = String(now.getFullYear()).slice(-2);
    return `LM${mes}${ano}`;
  }

  async function verificarLoteAtivo(tanqueId, linhaEl) {
    if (!tanqueId || !linhaEl) return;
    const nomeLoteInput = linhaEl.querySelector('[data-field="nome_lote"]');
    if (!nomeLoteInput) return;

    try {
      const response = await fetchWithCreds(`/producao/api/tanque/${tanqueId}/lote-ativo/`);
      if (!response.ok) {
        nomeLoteInput.value = '';
        nomeLoteInput.readOnly = false;
        return;
      }
      const data = await response.json();
      if (data?.success && data.lote) {
        nomeLoteInput.value = data.lote.nome || '';
        nomeLoteInput.readOnly = true;
      } else {
        nomeLoteInput.value = '';
        nomeLoteInput.readOnly = false;
      }
    } catch (error) {
      console.error('Erro ao buscar lote ativo:', error);
      nomeLoteInput.value = '';
      nomeLoteInput.readOnly = false;
    }
  }

  function atualizarOpcoesTanque(tipoTanqueSelect, tanqueSelect) {
    if (!window.DJANGO_CONTEXT) return;
    const tipo = tipoTanqueSelect.value;
    const tanques = window.DJANGO_CONTEXT.tanques || [];
    const filtrados = tanques.filter((tanque) => {
      if (tipo === 'Tanque Vazio') {
        const status = (tanque.status_nome || '').toLowerCase();
        return !tanque.tem_lote_ativo && (status === 'livre' || status === 'vazio' || status === 'disponível');
      }
      return Boolean(tanque.tem_lote_ativo);
    });

    const options = ['<option value="">Selecione...</option>',
      ...filtrados.map((tanque) => `<option value="${tanque.pk}">${tanque.nome}</option>`),
    ].join('');
    tanqueSelect.innerHTML = options;

    if (hasSelect2()) {
      applySelect2(window.jQuery(tanqueSelect));
    }
  }

  function adicionarLinha({
    tipoTanqueSelect,
    curvaSelect,
    tanqueSelect,
    listagemBody,
  }) {
    if (!tanqueSelect.value) {
      mostrarMensagem('warning', 'Selecione um tanque primeiro.');
      return;
    }

    const now = new Date();
    const linhaId = `row-${now.getTime()}`;
    const fases = window.DJANGO_CONTEXT?.fases || [];
    const linhas = window.DJANGO_CONTEXT?.linhas || [];

    const faseOptions = fases.map((fase) => `<option value="${fase.pk}">${fase.nome}</option>`).join('');
    const linhaOptions = linhas.map((linha) => `<option value="${linha.pk}">${linha.nome}</option>`).join('');

    const curvaTexto = curvaSelect.value
      ? curvaSelect.options[curvaSelect.selectedIndex].text
      : '—';

    const novaLinhaHTML = `
      <tr id="${linhaId}" data-tanque-id="${tanqueSelect.value}" data-curva-id="${curvaSelect.value}">
        <td><button class="btn btn-danger btn-sm" data-action="desfazer" type="button">X</button></td>
        <td>${tanqueSelect.options[tanqueSelect.selectedIndex].text}</td>
        <td>${generateGrupoOrigem()}</td>
        <td>${curvaTexto}</td>
        <td><input type="date" class="form-control form-control-sm" data-field="data_lancamento" value="${now.toISOString().slice(0, 10)}"></td>
        <td><input type="text" class="form-control form-control-sm" data-field="nome_lote"></td>
        <td><input type="number" class="form-control form-control-sm" data-field="quantidade" min="0" step="1"></td>
        <td><input type="number" class="form-control form-control-sm" data-field="peso_medio" min="0" step="0.1"></td>
        <td><select class="form-select form-select-sm select2-search-row" data-field="fase_id">${faseOptions}</select></td>
        <td><select class="form-select form-select-sm select2-search-row" data-field="linha_id">${linhaOptions}</select></td>
        <td><input type="text" class="form-control form-control-sm" placeholder="Ex.: B1, B2" data-field="tamanho"></td>
      </tr>
    `;

    listagemBody.insertAdjacentHTML('beforeend', novaLinhaHTML);
    const novaLinha = document.getElementById(linhaId);

    if (tipoTanqueSelect.value === 'Tanque Povoado') {
      verificarLoteAtivo(tanqueSelect.value, novaLinha);
    }

    if (hasSelect2()) {
      applySelect2(window.jQuery(`#${linhaId} .select2-search-row`));
    }
  }

  async function processarPovoamentos({ tipoTanqueSelect, listagemBody, processarBtn }) {
    const linhas = Array.from(listagemBody.querySelectorAll('tr'));
    if (!linhas.length) {
      mostrarMensagem('warning', 'Adicione pelo menos uma linha para processar.');
      return;
    }

    const payload = {
      povoamentos: linhas.map((linha) => ({
        tipo_tanque: tipoTanqueSelect.value,
        curva_id: linha.dataset.curvaId || null,
        tanque_id: linha.dataset.tanqueId,
        grupo_origem: linha.cells[2]?.textContent?.trim() || null,
        data_lancamento: linha.querySelector('[data-field="data_lancamento"]').value || null,
        nome_lote: linha.querySelector('[data-field="nome_lote"]').value || null,
        quantidade: linha.querySelector('[data-field="quantidade"]').value || null,
        peso_medio: linha.querySelector('[data-field="peso_medio"]').value || null,
        fase_id: linha.querySelector('[data-field="fase_id"]').value || null,
        tamanho: linha.querySelector('[data-field="tamanho"]').value || null,
        linha_id: linha.querySelector('[data-field="linha_id"]').value || null,
      })),
    };

    processarBtn.disabled = true;
    const originalLabel = processarBtn.innerHTML;
    processarBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Processando...';

    try {
      const response = await fetchWithCreds('/producao/povoamento/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const result = await response.json().catch(() => ({}));

      if (!response.ok) {
        mostrarMensagem('danger', result?.message || 'Falha ao processar os povoamentos.');
        return;
      }

      mostrarMensagem('success', result?.message || 'Povoamentos processados com sucesso.');
      listagemBody.innerHTML = '';
    } catch (error) {
      console.error('Erro ao processar povoamentos:', error);
      mostrarMensagem('danger', 'Ocorreu um erro de comunicação com o servidor.');
    } finally {
      processarBtn.disabled = false;
      processarBtn.innerHTML = originalLabel;
    }
  }

  function bindHistorico(buscarBtn, historicoBody) {
    if (!buscarBtn || !historicoBody) return;
    buscarBtn.addEventListener('click', async (event) => {
      event.preventDefault();
      const inicial = document.querySelector('[data-filter="data_inicial"]').value;
      const final = document.querySelector('[data-filter="data_final"]').value;
      const status = document.querySelector('[data-filter="status"]').value;
      const url = new URL('/producao/api/povoamento/historico/', window.location.origin);
      if (inicial) url.searchParams.append('data_inicial', inicial);
      if (final) url.searchParams.append('data_final', final);
      if (status) url.searchParams.append('status', status);

      try {
        const response = await fetchWithCreds(url.toString());
        const data = await response.json();
        historicoBody.innerHTML = data?.success
          ? data.historico.map((item) => `
              <tr>
                <td>${item.id}</td>
                <td>${item.data}</td>
                <td>${item.lote}</td>
                <td>${item.tanque}</td>
                <td>${item.quantidade}</td>
                <td>${item.peso_medio}</td>
                <td>${item.tipo_evento}</td>
              </tr>
            `).join('')
          : '';
      } catch (error) {
        console.error('Erro ao buscar histórico:', error);
        mostrarMensagem('danger', 'Não foi possível carregar o histórico.');
      }
    });
  }

  function initPovoamentoLotes() {
    const page = document.querySelector(PAGE_SELECTOR);
    if (!page) return;

    const context = resolveContext(page);
    const contextReady =
      context &&
      Array.isArray(context.tanques) &&
      Array.isArray(context.fases) &&
      Array.isArray(context.linhas) &&
      (context.tanques.length || context.fases.length || context.linhas.length);

    if (!contextReady) {
      // Aguarda o disparo de `page:ready` para inicializar com os dados corretos.
      return;
    }

    if (page.dataset.initialized === 'true') return;
    page.dataset.initialized = 'true';

    const tipoTanqueSelect = page.querySelector('[data-role="tipo-tanque"]');
    const curvaContainer = page.querySelector('[data-container="curva-crescimento"]');
    const tanqueSelect = page.querySelector('[data-role="tanque"]');
    const curvaSelect = page.querySelector('[data-role="curva-crescimento"]');
    const adicionarBtn = page.querySelector('[data-action="adicionar-linha"]');
    const processarBtn = page.querySelector('[data-action="processar"]');
    const listagemBody = page.querySelector('[data-container="listagem-body"]');
    const buscarBtn = page.querySelector('[data-action="buscar-historico"]');
    const historicoBody = page.querySelector('[data-container="historico-body"]');

    if (hasSelect2()) {
      applySelect2(window.jQuery(curvaSelect));
      applySelect2(window.jQuery(tanqueSelect));
      applySelect2(window.jQuery(page.querySelectorAll('.select2-search')));
    }

    atualizarOpcoesTanque(tipoTanqueSelect, tanqueSelect);
    bindHistorico(buscarBtn, historicoBody);

    tipoTanqueSelect.addEventListener('change', () => {
      if (tipoTanqueSelect.value === 'Tanque Povoado') {
        curvaContainer.style.display = 'none';
        if (curvaSelect) {
          curvaSelect.value = '';
          if (hasSelect2()) {
            window.jQuery(curvaSelect).val(null).trigger('change');
          }
        }
      } else {
        curvaContainer.style.display = '';
      }
      atualizarOpcoesTanque(tipoTanqueSelect, tanqueSelect);
    });

    adicionarBtn?.addEventListener('click', () => {
      adicionarLinha({
        tipoTanqueSelect,
        curvaSelect,
        tanqueSelect,
        listagemBody,
      });
    });

    processarBtn?.addEventListener('click', () => {
      processarPovoamentos({ tipoTanqueSelect, listagemBody, processarBtn });
    });

    listagemBody?.addEventListener('click', (event) => {
      if (event.target?.dataset?.action === 'desfazer') {
        event.preventDefault();
        const row = event.target.closest('tr');
        row?.remove();
      }
    });
  }

  document.addEventListener('DOMContentLoaded', initPovoamentoLotes);
  document.addEventListener('ajaxContentLoaded', initPovoamentoLotes);
  window.addEventListener('page:ready', (event) => {
    if (event?.detail?.page === 'povoamento-lotes') {
      initPovoamentoLotes();
    }
  });

  window.OneTech = window.OneTech || {};
  window.OneTech.PovoamentoLotes = {
    SELECTOR_ROOT: PAGE_SELECTOR,
    init: initPovoamentoLotes,
  };

  initPovoamentoLotes();
})();
