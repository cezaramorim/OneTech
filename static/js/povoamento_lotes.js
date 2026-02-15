(function () {
  const PAGE_SELECTOR = '[data-page="povoamento-lotes"]';
  const SELECT2_SELECTOR = '.select2-povoamento';

  // === Helper robusto: suporta id ou pk ===
  function getObjId(obj) {
    return obj?.id ?? obj?.pk ?? null;
  }

  function readJsonScript(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    try {
      return JSON.parse(el.textContent || 'null');
    } catch (e) {
      return null;
    }
  }

  function resolveContext(page) {
    const globalContext = window.DJANGO_CONTEXT || {};

    const scriptTanques = readJsonScript('povoamento-tanques-json');
    const scriptFases = readJsonScript('povoamento-fases-json');
    const scriptLinhas = readJsonScript('povoamento-linhas-json');

    const ctx = {
      ...globalContext,
      tanques: Array.isArray(scriptTanques) ? scriptTanques : [],
      fases: Array.isArray(scriptFases) ? scriptFases : [],
      linhas: Array.isArray(scriptLinhas) ? scriptLinhas : [],
    };

    window.DJANGO_CONTEXT = ctx;
    return ctx;
  }

  function hasSelect2() {
    return Boolean(window.jQuery && window.jQuery.fn && window.jQuery.fn.select2);
  }

  function buildDropdownParent() {
    return window.jQuery('body');
  }

  function applySelect2($elements, extraConfig = {}) {
    if (!hasSelect2() || !$elements || !$elements.length) return;

    function getDropdownClasses() {
      let classes = 'select2-dropdown-custom ';
      if (document.documentElement.classList.contains('dark')) classes += 'select2-dropdown-dark';
      return classes;
    }

    const config = {
      theme: 'bootstrap-5',
      width: 'resolve',
      dropdownAutoWidth: true,
      dropdownParent: buildDropdownParent(),
      dropdownCssClass: getDropdownClasses(),
      ...extraConfig
    };

    $elements.each(function () {
      const $el = window.jQuery(this);
      $el.select2(config);
    });
  }

  // === Ajuste: atualizarChips tolerante a id/pk ===
  function atualizarChips(tanqueId) {
    console.log('[Debug] atualizarChips: Recebeu tanqueId:', tanqueId);

    const tanques = Array.isArray(window.DJANGO_CONTEXT?.tanques) ? window.DJANGO_CONTEXT.tanques : [];
    if (!tanqueId) {
      document.querySelectorAll('[data-chip]').forEach(chip => chip.textContent = '--');
      return;
    }

    const tanque = tanques.find(t => String(getObjId(t)) === String(tanqueId));
    console.log('[Debug] Tanque encontrado no contexto:', tanque);

    if (!tanque) return;

    const chipNome = document.querySelector('[data-chip="tanque-nome"]');
    if (chipNome) chipNome.textContent = tanque.nome ?? '--';

    const chipStatus = document.querySelector('[data-chip="tanque-status"]');
    if (chipStatus) chipStatus.textContent = tanque.status_nome ?? '--';

    const chipOcup = document.querySelector('[data-chip="tanque-ocupacao"]');
    if (chipOcup) chipOcup.textContent = (tanque.ocupacao_percentual ?? '--') + '%';
  }

  // === Ajuste: atualizarOpcoesTanque usando id/pk e data-role ===
  function atualizarOpcoesTanque(tipoTanqueSelect, tanqueSelect) {
    if (!tanqueSelect) return;

    const tipo = (tipoTanqueSelect?.value || '').trim(); // 'VAZIO' | 'POVOADO'
    const tanques = Array.isArray(window.DJANGO_CONTEXT?.tanques) ? window.DJANGO_CONTEXT.tanques : [];

    const filtrados = tanques.filter(t =>
      tipo === 'VAZIO' ? !t.tem_lote_ativo : !!t.tem_lote_ativo
    );

    tanqueSelect.innerHTML = [
      '<option value="">Selecione...</option>',
      ...filtrados.map(t => {
        const tid = getObjId(t);
        return `<option value="${tid}">${t.nome}</option>`;
      })
    ].join('');

    if (window.jQuery && window.jQuery(tanqueSelect).data('select2')) {
      window.jQuery(tanqueSelect).trigger('change.select2');
    }
  }

  async function verificarLoteAtivo(tanqueId) {
    if (!tanqueId) return null;
    try {
      const response = await fetchWithCreds(`/producao/api/tanque/${tanqueId}/lote-ativo/`);
      if (!response.ok) return null;
      const data = await response.json();
      return (data?.success && data.lote) ? data.lote : null;
    } catch (error) {
      return null;
    }
  }

  function validarAntesDeAdicionar(tipoTanqueSelect, curvaSelect, tanqueSelect) {
    if (!tanqueSelect?.value) {
      mostrarMensagem('warning', 'Selecione um tanque.');
      return false;
    }
    if (tipoTanqueSelect?.value === 'Tanque Vazio' && !curvaSelect?.value) {
      mostrarMensagem('warning', 'Selecione a Curva de Crescimento.');
      return false;
    }
    return true;
  }
  
  function sanitizeOrigem(tipoOrigemValor) {
    return (tipoOrigemValor || '')
      .toUpperCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^A-Z0-9]/g, '')
      .slice(0, 3) || 'OR';
  }

  function generateGrupoOrigem(tipoOrigemValor) {
    const now = new Date();
    const mes = String(now.getMonth() + 1).padStart(2, '0');
    const ano = String(now.getFullYear()).slice(-2);
    const origemPrefix = sanitizeOrigem(tipoOrigemValor);
    return `${origemPrefix}${mes}${ano}`;
  }

  async function adicionarLinha({
    tipoTanqueSelect,
    tipoOrigemSelect,
    curvaSelect,
    tanqueSelect,
    listagemBody,
    emptyState,
    totaisRefs,
  }) {
    if (!validarAntesDeAdicionar(tipoTanqueSelect, curvaSelect, tanqueSelect)) {
      return;
    }

    const now = new Date();
    const linhaId = `row-${now.getTime()}`;
    const fases = window.DJANGO_CONTEXT?.fases || [];
    const linhas = window.DJANGO_CONTEXT?.linhas || [];

    const faseOptions = fases.map((fase) => `<option value="${fase.pk}">${fase.nome}</option>`).join('');
    const linhaOptions = linhas.map((linha) => `<option value="${linha.pk}">${linha.nome}</option>`).join('');

    const isReforco = tipoTanqueSelect.options[tipoTanqueSelect.selectedIndex].value === 'POVOADO';
    const loteAtivo = isReforco ? await verificarLoteAtivo(tanqueSelect.value) : null;

    const curvaIdParaLinha = isReforco ? (loteAtivo?.curva_id || '') : (curvaSelect.value || '');
    const curvaTexto = isReforco 
        ? (loteAtivo?.curva_nome || '—') 
        : (curvaSelect.value ? curvaSelect.options[curvaSelect.selectedIndex].text : '—');

    const nomeLoteValor = loteAtivo ? loteAtivo.nome : '';
    const nomeLoteReadonly = loteAtivo ? 'readonly' : '';
    
    const faseIdSelecionada = loteAtivo ? loteAtivo.fase_id : '';
    const faseDisabled = loteAtivo ? 'disabled' : '';

    const novaLinhaHTML = `
      <tr id="${linhaId}" data-tanque-id="${tanqueSelect.value}" data-curva-id="${curvaIdParaLinha}">
        <td><button class="btn btn-sm btn-icon-no-focus" data-action="desfazer" type="button" title="Excluir linha"><i class="bi bi-trash3 text-danger"></i></button></td>
        <td>${tanqueSelect.options[tanqueSelect.selectedIndex].text}</td>
        <td>${generateGrupoOrigem(tipoOrigemSelect?.value)}</td>
        <td>${curvaTexto}</td>
        <td><input type="date" class="form-control form-control-sm" data-field="data_lancamento" value="${now.toISOString().slice(0, 10)}"></td>
        <td><input type="text" class="form-control form-control-sm" data-field="nome_lote" value="${nomeLoteValor}" ${nomeLoteReadonly}></td>
        <td><input type="number" class="form-control form-control-sm" data-field="quantidade" min="0" step="1"></td>
        <td><input type="number" class="form-control form-control-sm" data-field="peso_medio" min="0" step="0.1"></td>
        <td><div class="select2-wrapper"><select class="form-select form-select-sm select2-povoamento" data-field="fase_id" ${faseDisabled}>${faseOptions}</select></div></td>
        <td><div class="select2-wrapper"><select class="form-select form-select-sm select2-povoamento" data-field="linha_id">${linhaOptions}</select></div></td>
        <td><input type="text" class="form-control form-control-sm" placeholder="Ex.: B1, B2" data-field="tamanho"></td>
      </tr>
    `;

    listagemBody.insertAdjacentHTML('beforeend', novaLinhaHTML);
    const novaLinha = document.getElementById(linhaId);

    if (loteAtivo && faseIdSelecionada) {
        const faseSelect = novaLinha.querySelector('[data-field="fase_id"]');
        faseSelect.value = faseIdSelecionada;
    }

    if (hasSelect2()) {
      applySelect2(window.jQuery(`#${linhaId} ${SELECT2_SELECTOR}`));
    }

    atualizarEstadoListagem(listagemBody, emptyState);
    recalcularTotais(listagemBody, totaisRefs);
  }

  function validarLinhas(listagemBody, tipoTanqueAtual) {
    const erros = [];
    listagemBody.querySelectorAll('tr').forEach((linha, index) => {
      const ordem = index + 1;
      const findValue = (selector) => linha.querySelector(selector)?.value?.trim();
      const quantidade = Number(findValue('[data-field="quantidade"]')) || 0;
      const pesoMedio = Number(findValue('[data-field="peso_medio"]')) || 0;
      const fase = findValue('[data-field="fase_id"]');
      const linhaProducao = findValue('[data-field="linha_id"]');
      const curva = linha.dataset.curvaId;

      if (quantidade <= 0) erros.push(`Linha ${ordem}: quantidade inválida.`);
      if (pesoMedio <= 0) erros.push(`Linha ${ordem}: peso médio inválido.`);
      if (!fase) erros.push(`Linha ${ordem}: selecione a fase.`);
      if (!linhaProducao) erros.push(`Linha ${ordem}: selecione a linha.`);
      if (tipoTanqueAtual === 'Tanque Vazio' && !curva) erros.push(`Linha ${ordem}: curva obrigatória.`);
    });

    if (erros.length) {
      mostrarMensagem('danger', erros.join('<br>'));
    }
    return erros.length === 0;
  }

  function obterTotaisRefs(page) {
    return {
      linhas: page.querySelector('[data-total="linhas"]'),
      peixes: page.querySelector('[data-total="peixes"]'),
      peso: page.querySelector('[data-total="peso"]'),
    };
  }

  function recalcularTotais(listagemBody, totaisRefs) {
    if (!listagemBody) return;
    let linhas = 0, peixes = 0, peso = 0;

    listagemBody.querySelectorAll('tr').forEach((linha) => {
      linhas += 1;
      const quantidade = Number(linha.querySelector('[data-field="quantidade"]')?.value || 0);
      const pesoMedio = Number(linha.querySelector('[data-field="peso_medio"]')?.value || 0);
      peixes += quantidade;
      peso += (quantidade * pesoMedio) / 1000;
    });

    const { linhas: linhasEl, peixes: peixesEl, peso: pesoEl } = totaisRefs || {};
    if (linhasEl) linhasEl.textContent = String(linhas);
    if (peixesEl) peixesEl.textContent = new Intl.NumberFormat('pt-BR').format(peixes);
    if (pesoEl) pesoEl.textContent = `${peso.toFixed(1)} kg`;
  }

  function atualizarEstadoListagem(listagemBody, emptyState) {
    if (!emptyState) return;
    const hasRows = Boolean(listagemBody?.querySelector('tr'));
    emptyState.classList.toggle('d-none', hasRows);
  }

  function limparListagem(listagemBody, emptyState, totaisRefs) {
    if (!listagemBody) return;
    listagemBody.innerHTML = '';
    atualizarEstadoListagem(listagemBody, emptyState);
    recalcularTotais(listagemBody, totaisRefs);
  }

  async function processarPovoamentos({
    tipoTanqueSelect,
    listagemBody,
    processarBtn,
    emptyState,
    totaisRefs,
  }) {
    if (!listagemBody.querySelectorAll('tr').length) {
      mostrarMensagem('warning', 'Adicione pelo menos uma linha para processar.');
      return;
    }
    if (!validarLinhas(listagemBody, tipoTanqueSelect.value)) return;

    const payload = {
      povoamentos: Array.from(listagemBody.querySelectorAll('tr')).map((linha) => ({
        tipo_tanque: tipoTanqueSelect.options[tipoTanqueSelect.selectedIndex].value,
        curva_id: linha.dataset.curvaId || null,
        tanque_id: linha.dataset.tanqueId,
        grupo_origem: linha.cells[2]?.textContent?.trim() || null,
        data_lancamento: linha.querySelector('[data-field="data_lancamento"]').value || null,
        nome_lote: linha.querySelector('[data-field="nome_lote"]').value || null,
        quantidade: parseFloat(linha.querySelector('[data-field="quantidade"]').value) || null,
        peso_medio: parseFloat(linha.querySelector('[data-field="peso_medio"]').value) || null,
        fase_id: parseInt(linha.querySelector('[data-field="fase_id"]').value, 10) || null,
        tamanho: linha.querySelector('[data-field="tamanho"]').value || null,
        linha_id: parseInt(linha.querySelector('[data-field="linha_id"]').value, 10) || null,
      })),
    };

    processarBtn.disabled = true;
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
      limparListagem(listagemBody, emptyState, totaisRefs);
    } catch (error) {
      mostrarMensagem('danger', 'Ocorreu um erro de comunicação com o servidor.');
    } finally {
      processarBtn.disabled = false;
      processarBtn.innerHTML = 'Processar Povoamentos';
    }
  }
  
  function setupEventListeners(page, context) {
    const tipoTanqueSelect = page.querySelector('[data-role="tipo-tanque"]') || page.querySelector('#id_tipo_tanque');
    const tipoOrigemSelect = page.querySelector('#id_tipo_origem');
    const curvaSelect = page.querySelector('#curva');
    const tanqueSelect = page.querySelector('[data-role="tanque"]') || page.querySelector('#id_tanque');
    const curvaContainer = page.querySelector('[data-container="curva-crescimento"]');
    
    const addBtn = page.querySelector('[data-action="adicionar-linha"]');
    const processarBtn = page.querySelector('[data-action="processar"]');
    const limparBtn = page.querySelector('[data-action="limpar-linhas"]');
    const listagemBody = page.querySelector('[data-container="listagem-body"]');
    const emptyState = page.querySelector('[data-state="empty"]');
    const totaisRefs = obterTotaisRefs(page);

    if (addBtn) {
        addBtn.addEventListener('click', () => adicionarLinha({
            tipoTanqueSelect, tipoOrigemSelect, curvaSelect, tanqueSelect,
            listagemBody, emptyState, totaisRefs
        }));
    }

    if (processarBtn) {
        processarBtn.addEventListener('click', () => processarPovoamentos({
            tipoTanqueSelect, listagemBody, processarBtn, emptyState, totaisRefs
        }));
    }

    if (limparBtn) {
        limparBtn.addEventListener('click', () => limparListagem(listagemBody, emptyState, totaisRefs));
    }

    if (listagemBody) {
        listagemBody.addEventListener('click', (e) => {
            if (e.target.closest('[data-action="desfazer"]')) {
                e.target.closest('tr').remove();
                atualizarEstadoListagem(listagemBody, emptyState);
                recalcularTotais(listagemBody, totaisRefs);
            }
        });
        listagemBody.addEventListener('input', (e) => {
            if (e.target.matches('[data-field="quantidade"], [data-field="peso_medio"]')) {
                recalcularTotais(listagemBody, totaisRefs);
            }
        });
    }
    
    if (tipoTanqueSelect) {
        tipoTanqueSelect.addEventListener('change', () => {
            const povoado = (tipoTanqueSelect.value === 'POVOADO');
            if(curvaContainer) curvaContainer.style.display = povoado ? 'none' : '';
            if (povoado && curvaSelect) {
                curvaSelect.value = '';
                if (hasSelect2()) window.jQuery(curvaSelect).val(null).trigger('change');
            }
        });
    }
  }

  // === Ajuste: initPovoamentoLotes encontrando selects por data-role e fallback por id ===
  function initPovoamentoLotes() {
    const page = document.querySelector(PAGE_SELECTOR);
    if (!page) return;
    if (page.dataset.povoamentoInitialized === 'true') return;
    page.dataset.povoamentoInitialized = 'true';

    resolveContext(page);

    const tipoTanqueSelect =
      page.querySelector('[data-role="tipo-tanque"]') ||
      page.querySelector('#tipo-tanque') ||
      page.querySelector('#id_tipo_tanque');

    const tanqueSelect =
      page.querySelector('[data-role="tanque"]') ||
      page.querySelector('#tanque') ||
      page.querySelector('#id_tanque');

    if (!tipoTanqueSelect || !tanqueSelect) {
      console.warn('[povoamento] Selects não encontrados:', { tipoTanqueSelect, tanqueSelect });
      return;
    }

    atualizarOpcoesTanque(tipoTanqueSelect, tanqueSelect);

    tipoTanqueSelect.addEventListener('change', () => {
      atualizarOpcoesTanque(tipoTanqueSelect, tanqueSelect);
      atualizarChips('');
    });

    tanqueSelect.addEventListener('change', () => {
      atualizarChips(tanqueSelect.value);
    });

    if (tanqueSelect.value) {
      atualizarChips(tanqueSelect.value);
    }
    
    setupEventListeners(page);
  }

  function initializeWhenReady() {
    const page = document.querySelector(PAGE_SELECTOR);
    if (page) {
      initPovoamentoLotes();
    }
  }

  document.addEventListener('DOMContentLoaded', initializeWhenReady);
  document.addEventListener('ajaxContentLoaded', initializeWhenReady);

})();