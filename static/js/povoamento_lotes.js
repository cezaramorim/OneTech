// ---- Atualiza KPIs (chips) com base no tanque selecionado ----
function atualizarChips(tanqueId, page) {
  console.log(`[Debug] atualizarChips: Recebeu tanqueId: '${tanqueId}'`);

  const kpiTanque   = page.querySelector('[data-kpi="tanque"] [data-value]');
  const kpiOcupacao = page.querySelector('[data-kpi="ocupacao"] [data-value]');
  const kpiFase     = page.querySelector('[data-kpi="fase"] [data-value]');

  const tanque = (window.DJANGO_CONTEXT?.tanques || [])
    .find(t => String(t.pk) === String(tanqueId));

  console.log('[Debug] Tanque encontrado no contexto:', tanque);

  if (tanque) {
    const nome = tanque.nome ?? tanque.codigo ?? 'N/A';
    const pct  = tanque.ocupacao_percentual ??
                 (typeof tanque.ocupacao === 'number' ? Math.round(tanque.ocupacao * 100) + '%' : 'N/A');
    const fase = tanque.fase_nome ?? tanque.fase ?? 'N/A';

    if (kpiTanque)   kpiTanque.textContent   = nome;
    if (kpiOcupacao) kpiOcupacao.textContent = pct;
    if (kpiFase)     kpiFase.textContent     = fase;
  } else {
    if (kpiTanque)   kpiTanque.textContent   = '—';
    if (kpiOcupacao) kpiOcupacao.textContent = '—';
    if (kpiFase)     kpiFase.textContent     = '—';
  }
}


// --- HELPER: bindTanqueChange (nativo + Select2) ---
function bindTanqueChange(tanqueSelect, page) {
  const handler = () => {
    const val = (window.jQuery && window.jQuery.fn && window.jQuery.fn.select2)
      ? window.jQuery(tanqueSelect).val()  // quando Select2 está aplicado
      : tanqueSelect.value;

    console.log(`[Debug] Evento change/select2: tanqueSelect. Novo valor: ${val}`);
    tanqueSelect.dataset.prev = val || '';
    if (typeof atualizarChips === 'function') {
      atualizarChips(val || '', page);
    }
  };

  // Limpa binds nativos anteriores e religa
  tanqueSelect.removeEventListener('change', handler);
  tanqueSelect.addEventListener('change', handler);

  // Liga eventos do Select2, se disponível (com namespace para evitar duplicidade)
  if (window.jQuery && window.jQuery.fn && window.jQuery.fn.select2) {
    const $sel = window.jQuery(tanqueSelect);
    $sel.off('select2:select.selectChips select2:clear.selectChips select2:open.selectChips');

    $sel.on('select2:select.selectChips', handler);
    $sel.on('select2:clear.selectChips', handler);

    // Ao abrir o dropdown, injeta classe para dark mode no dropdown
    $sel.on('select2:open.selectChips', () => {
      const data = $sel.data('select2');
      if (data && data.$dropdown) {
        data.$dropdown.addClass('select2-dark'); // classe nossa pro tema escuro
      }
    });
  }
}

(function () {
  const PAGE_SELECTOR = '[data-page="povoamento-lotes"]';
  const SELECT2_SELECTOR = '.select2-povoamento';
  const SELECT2_BASE_CONFIG = {
    theme: 'bootstrap-5',
    width: 'style',
    dropdownAutoWidth: true,
  };
  let select2GuardsBound = false;

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

  function bindSelect2Guards() {
    if (!hasSelect2() || select2GuardsBound) return;
    select2GuardsBound = true;
    window.jQuery(document)
      .off('mousedown.povoamento')
      .on('mousedown.povoamento', '.select2-container--open .select2-dropdown', (event) => {
        event.stopPropagation();
      });
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
    dropdownParent: buildDropdownParent(),     // usa seu helper
    dropdownCssClass: getDropdownClasses(),
    ...extraConfig
  };

  $elements.each(function () {
    const $el = window.jQuery(this);
    $el.select2(config);

    $el.off('select2:open.povoamento').on('select2:open.povoamento', () => {
      const $dd = $el.data('select2').$dropdown;
      if (!$dd || !$dd.length) return;

      // força abrir para baixo
      $dd.removeClass('select2-dropdown--above').addClass('select2-dropdown--below');

      // largura ~15% maior que o campo, com limites de viewport
      const rect = this.getBoundingClientRect();
      const vw = Math.max(document.documentElement.clientWidth, window.innerWidth || 0);

      const baseWidth  = rect.width;                 // largura do <select>
      const growWidth  = Math.round(baseWidth * 1.15); // +15%
      const spaceRight = vw - rect.left - 8;         // espaço útil até a borda direita

      // não deixa menor que o campo, nem maior do que cabe na direita
      const desired = Math.max(baseWidth, Math.min(growWidth, spaceRight));

      $dd.css({
        width:     desired + 'px',
        maxWidth:  desired + 'px',
        minWidth:  baseWidth + 'px'
      });
    });
  });
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

  async function verificarLoteAtivo(tanqueId) {
    if (!tanqueId) return null;

    try {
        const response = await fetchWithCreds(`/producao/api/tanque/${tanqueId}/lote-ativo/`);
        if (!response.ok) {
            return null;
        }
        const data = await response.json();
        if (data?.success && data.lote) {
            return data.lote; // Retorna o objeto completo do lote
        }
        return null;
    } catch (error) {
        console.error('Erro ao buscar lote ativo:', error);
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

  async function adicionarLinha({
    tipoTanqueSelect,
    tipoOrigemSelect,
    curvaSelect,
    tanqueSelect,
    listagemBody,
    emptyState,
    totaisRefs,
  }) {
    if (
      !validarAntesDeAdicionar(
        tipoTanqueSelect,
        curvaSelect,
        tanqueSelect,
      )
    ) {
      return;
    }

    const now = new Date();
    const linhaId = `row-${now.getTime()}`;
    const fases = window.DJANGO_CONTEXT?.fases || [];
    const linhas = window.DJANGO_CONTEXT?.linhas || [];

    const faseOptions = fases.map((fase) => `<option value="${fase.pk}">${fase.nome}</option>`).join('');
    const linhaOptions = linhas.map((linha) => `<option value="${linha.pk}">${linha.nome}</option>`).join('');

    // --- Lógica de Reforço vs. Novo Lote ---
    const isReforco = tipoTanqueSelect.value === 'Tanque Povoado';
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
        <td><button class="btn btn-danger btn-sm" data-action="desfazer" type="button">X</button></td>
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

    // Pré-seleciona a fase se for um reforço
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
    let linhas = 0;
    let peixes = 0;
    let peso = 0;

    listagemBody.querySelectorAll('tr').forEach((linha) => {
      linhas += 1;
      const quantidade = Number(linha.querySelector('[data-field="quantidade"]')?.value || 0);
      const pesoMedio = Number(linha.querySelector('[data-field="peso_medio"]')?.value || 0);
      peixes += quantidade;
      peso += (quantidade * pesoMedio) / 1000;
    });

    const { linhas: linhasEl, peixes: peixesEl, peso: pesoEl } = totaisRefs || {};
    const formatter = new Intl.NumberFormat('pt-BR');

    if (linhasEl) linhasEl.textContent = String(linhas);
    if (peixesEl) peixesEl.textContent = formatter.format(peixes);
    if (pesoEl) pesoEl.textContent = `${peso.toFixed(1)} kg`;

    return { linhas, peixes, pesoKg: peso };
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
    const linhas = Array.from(listagemBody.querySelectorAll('tr'));
    if (!linhas.length) {
      mostrarMensagem('warning', 'Adicione pelo menos uma linha para processar.');
      return;
    }

    if (!validarLinhas(listagemBody, tipoTanqueSelect.value)) {
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
      limparListagem(listagemBody, emptyState, totaisRefs);
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


  // Liga os eventos de mudança do select de tanque de forma resiliente (nativo + Select2)
function atualizarOpcoesTanque(tipoTanqueSelect, tanqueSelect, page) {
  if (!window.DJANGO_CONTEXT || !tanqueSelect || !page) return;

  const tipo = (tipoTanqueSelect?.value || '').trim();
  const tanques = Array.isArray(window.DJANGO_CONTEXT.tanques) ? window.DJANGO_CONTEXT.tanques : [];

  // 1) filtra por tipo (Povoado/Vazio)
  const filtrados = tanques.filter(t =>
    tipo === 'Tanque Vazio' ? !t.tem_lote_ativo : !!t.tem_lote_ativo
  );

  // 2) (re)monta opções do <select>
  const optionsHtml = [
    '<option value="">Selecione...</option>',
    ...filtrados.map(t => `<option value="${t.pk}">${t.nome}</option>`),
  ].join('');
  tanqueSelect.innerHTML = optionsHtml;

  // 3) (re)aplica Select2 somente aqui (evita instâncias duplicadas)
  const hasS2 = !!(window.jQuery && window.jQuery.fn && window.jQuery.fn.select2);
  let $sel = null;
  if (hasS2) {
    $sel = window.jQuery(tanqueSelect);
    if ($sel.data('select2')) $sel.select2('destroy'); // limpa instância antiga

    const $page = window.jQuery('[data-page="povoamento-lotes"]');
    $sel.select2({
      theme: 'bootstrap-5',              // ✅ forca a classe .select2-container--bootstrap-5
      width: '100%',
      dropdownParent: $page.length ? $page : buildDropdownParent(),
      placeholder: 'Selecione...',
      allowClear: true,
    });

    // aplica tema dark no container “fechado”
    const $s2Container = $sel.next('.select2');
    $s2Container.addClass('select2-dark');
  }

  // 4) decide seleção: prioriza a anterior; senão mantém a atual; senão 1ª válida; senão vazio
  const prev   = tanqueSelect.dataset.prev || '';
  const curr   = tanqueSelect.value || '';
  const exists = v => [...tanqueSelect.options].some(o => o.value === String(v));
  let nextVal  = '';

  if (prev && exists(prev)) {
    nextVal = String(prev);
  } else if (curr && exists(curr)) {
    nextVal = String(curr);
  } else if (filtrados.length > 0) {
    nextVal = String(filtrados[0].pk);
  } else {
    nextVal = '';
  }

  // 5) (re)liga os eventos (nativo + select2) ANTES de sincronizar valor, para capturar o trigger
  if (typeof bindTanqueChange === 'function') {
    bindTanqueChange(tanqueSelect, page);
  } else {
    console.error('[Erro] bindTanqueChange não está definido no escopo.');
  }

  // 6) sincroniza UI/valor e atualiza chips
  tanqueSelect.value = nextVal;

  if (hasS2) {
    // no Select2, o trigger dispara o handler → chips serão atualizados via bind
    $sel.val(nextVal || null).trigger('change.select2');
  } else {
    // sem Select2, atualiza chips manualmente
    if (typeof atualizarChips === 'function') {
      atualizarChips(nextVal || '', page);
    }
  }

  // 7) persiste a seleção para a próxima filtragem
  tanqueSelect.dataset.prev = nextVal || '';
}


  function initPovoamentoLotes() {
  console.log('%c[Debug] initPovoamentoLotes: Iniciando...', 'color: blue; font-weight: bold;');

  const page = document.querySelector(PAGE_SELECTOR);
  if (!page) return;

  // ✅ Anti-reentrada: evita concorrência/duplicidade entre múltiplos eventos
  if (page.dataset.initialized === 'true') {
    console.log('[Debug] initPovoamentoLotes: já inicializado, abortando.');
    return;
  }
  if (page.dataset.initializing === 'true') {
    console.log('[Debug] initPovoamentoLotes: já em inicialização, abortando.');
    return;
  }
  page.dataset.initializing = 'true';

  const context = resolveContext(page);
  console.log('[Debug] Contexto de tanques resolvido:', JSON.parse(JSON.stringify(window.DJANGO_CONTEXT.tanques)));

  const contextReady =
    context &&
    Array.isArray(context.tanques) &&
    Array.isArray(context.fases) &&
    Array.isArray(context.linhas) &&
    (context.tanques.length || context.fases.length || context.linhas.length);

  if (!contextReady) {
    // ❗ Se ainda não há contexto suficiente, libera o lock para permitir uma futura tentativa
    delete page.dataset.initializing;
    console.warn('[Debug] initPovoamentoLotes: contexto ainda não pronto. Abortando (liberado para nova tentativa).');
    return;
  }

  // ✅ Agora podemos marcar como inicializado de fato
  page.dataset.initialized = 'true';
  delete page.dataset.initializing;

  const tipoOrigemSelect = page.querySelector('[data-role="tipo-origem"]');
  const tipoTanqueSelect = page.querySelector('[data-role="tipo-tanque"]');
  const curvaContainer   = page.querySelector('[data-container="curva-crescimento"]');
  const tanqueSelect     = page.querySelector('[data-role="tanque"]');
  const curvaSelect      = page.querySelector('[data-role="curva-crescimento"]');
  const adicionarBtn     = page.querySelector('[data-action="adicionar-linha"]');
  const processarBtn     = page.querySelector('[data-action="processar"]');
  const listagemBody     = page.querySelector('[data-container="listagem-body"]');
  const buscarBtn        = page.querySelector('[data-action="buscar-historico"]');
  const historicoBody    = page.querySelector('[data-container="historico-body"]');
  const limparBtn        = page.querySelector('[data-action="limpar-linhas"]');
  const emptyState       = page.querySelector('[data-state="empty"]');
  const totaisRefs       = obterTotaisRefs(page);

  if (hasSelect2()) {
    applySelect2(window.jQuery(curvaSelect));

    // Exclui o [data-role="tanque"] do seletor genérico
    const others = Array.from(page.querySelectorAll(SELECT2_SELECTOR))
      .filter(el => el !== tanqueSelect); // ou: !el.matches('[data-role="tanque"]')
    if (others.length) applySelect2(window.jQuery(others));
  }


// Popula o combo e sincroniza chips (a função já cuida de Select2, restauração/auto-seleção e chips)
atualizarOpcoesTanque(tipoTanqueSelect, tanqueSelect, page);

// Mantém estado da listagem e histórico
atualizarEstadoListagem(listagemBody, emptyState);
recalcularTotais(listagemBody, totaisRefs);
bindHistorico(buscarBtn, historicoBody);

// Listener do tipo de tanque (sem atualizarChips manualmente)
tipoTanqueSelect.addEventListener('change', () => {
  console.log(`[Debug] Evento change: tipoTanqueSelect. Novo valor: ${tipoTanqueSelect.value}`);

  const povoado = (tipoTanqueSelect.value === 'Tanque Povoado');

  // Mostra/oculta o container de curva conforme o tipo
  curvaContainer.style.display = povoado ? 'none' : '';

  // Se for "Tanque Povoado", limpamos a curva selecionada
  if (povoado && curvaSelect) {
    curvaSelect.value = '';
    if (hasSelect2()) {
      window.jQuery(curvaSelect).val(null).trigger('change');
    }
  }

  // Reconstroi as opções do tanque e, internamente, já:
  // - (re)aplica Select2 com dropdownParent e classe dark
  // - restaura/auto-seleciona valor
  // - re-binda eventos (bindTanqueChange)
  // - atualiza os chips conforme a seleção atual
  atualizarOpcoesTanque(tipoTanqueSelect, tanqueSelect, page);

  // ❌ NÃO chame atualizarChips aqui
});

// Ações da listagem
adicionarBtn?.addEventListener('click', () => {
  adicionarLinha({
    tipoTanqueSelect,
    tipoOrigemSelect,
    curvaSelect,
    tanqueSelect,
    listagemBody,
    emptyState,
    totaisRefs,
  });
});

processarBtn?.addEventListener('click', () => {
  processarPovoamentos({
    tipoTanqueSelect,
    listagemBody,
    processarBtn,
    emptyState,
    totaisRefs,
  });
});

listagemBody?.addEventListener('click', (event) => {
  if (event.target?.dataset?.action === 'desfazer') {
    event.preventDefault();
    const row = event.target.closest('tr');
    row?.remove();
    atualizarEstadoListagem(listagemBody, emptyState);
    recalcularTotais(listagemBody, totaisRefs);
  }
});

listagemBody?.addEventListener('input', (event) => {
  if (event.target?.matches('[data-field="quantidade"], [data-field="peso_medio"]')) {
    recalcularTotais(listagemBody, totaisRefs);
  }
});

limparBtn?.addEventListener('click', () => {
  limparListagem(listagemBody, emptyState, totaisRefs);
});

// Mantém a função local de chips — ela é chamada por atualizarOpcoesTanque/binds

}



  // A inicialização foi centralizada no evento 'page:ready' para garantir que o contexto do Django esteja sempre disponível.
  // document.addEventListener('DOMContentLoaded', initPovoamentoLotes);
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

})();
