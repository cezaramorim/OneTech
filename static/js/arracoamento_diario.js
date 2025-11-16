// static/js/arracoamento_diario.js
window.OneTech = window.OneTech || {};

OneTech.ArracoamentoDiario = (function () {
  const SELECTOR_ROOT = '[data-page="arracoamento-diario"]';
  let boundRoot = null;

  function toNumLocale(value) {
    if (value == null) return 0;
    let v = String(value).trim();
    if (!v) return 0;
    v = v.replace(/[^\d,\.\-]/g, '');
    const lastComma = v.lastIndexOf(',');
    const lastDot = v.lastIndexOf('.');
    let decSep = null;
    if (lastComma === -1 && lastDot === -1) decSep = null;
    else if (lastComma > lastDot) decSep = ',';
    else decSep = '.';
    if (decSep) {
      const thouSep = decSep === ',' ? '.' : ',';
      v = v.split(thouSep).join('');
      v = v.replace(decSep, '.');
    }
    const n = parseFloat(v);
    return Number.isFinite(n) ? n : 0;
  }

  function formatBR(n, dec = 2) {
    const value = Number.isFinite(n) ? n : 0;
    return value.toFixed(dec).replace('.', ',');
  }

  function destroy(root) {
    if (!root) return;
    const controller = root._arracoamentoAbortController;
    if (controller) {
      controller.abort();
      delete root._arracoamentoAbortController;
    }
    delete root.dataset.bound;
    if (boundRoot === root) boundRoot = null;
  }

  function init(rootEl) {
    const root = rootEl || document.querySelector(SELECTOR_ROOT);
    if (!root) return;

    if (boundRoot && boundRoot !== root) {
      destroy(boundRoot);
    }
    if (root.dataset.bound === '1') return;

    const controller = new AbortController();
    const { signal } = controller;
    root._arracoamentoAbortController = controller;
    root.dataset.bound = '1';
    boundRoot = root;

    root.dataset.disableAllRows = root.dataset.disableAllRows || '0';

    const dataInput = root.querySelector('#data-arraçoamento');
    const aprovarBtn = root.querySelector('#btn-aprovar-selecionados');
    const tabelaBody = root.querySelector('#corpo-tabela-sugestoes');
    const loadingSpinner = root.querySelector('#loading-spinner');
    const selecionarTodosCheckbox = root.querySelector('#selecionar-todos-sugestoes');
    const totalSugeridoEl = root.querySelector('#total-sugerido');
    const totalRealEl = root.querySelector('#total-real');
    const filtroLinhaProducaoSelect = root.querySelector('#filtro-linha-producao');

    if (!dataInput || !aprovarBtn || !tabelaBody || !loadingSpinner || !selecionarTodosCheckbox) {
      return;
    }

    const API_URL_SUGESTOES = '/producao/api/arracoamento/sugestoes/';
    const API_URL_APROVAR = '/producao/api/arracoamento/aprovar/';
    const API_URL_LINHAS_PRODUCAO = '/producao/api/linhas-producao/';
    const API_URL_PRODUTOS_RACAO = '/produtos/api/racoes/';

    let produtosRacaoCache = null;

    async function inicializarSeletoresDeRacao(container) {
      if (!container) return;
      if (!produtosRacaoCache) {
        try {
          const response = await fetchWithCreds(API_URL_PRODUTOS_RACAO);
          produtosRacaoCache = await response.json();
        } catch (error) {
          console.error('Erro ao buscar produtos de ração:', error);
          mostrarMensagem('danger', 'Não foi possível carregar as opções de ração.');
          return;
        }
      }

      container.querySelectorAll('.racao-realizada-select').forEach((select) => {
        while (select.options.length > 1) select.remove(1);
        produtosRacaoCache.forEach((produto) => {
          const option = new Option(produto.nome, produto.id);
          select.add(option);
        });

        // *** NOVA LÓGICA DE SELEÇÃO ***
        const racaoRealizadaId = select.dataset.racaoRealizadaId;
        if (racaoRealizadaId) {
          select.value = racaoRealizadaId;
        }
      });
    }

    async function popularFiltroLinhaProducao() {
      if (!filtroLinhaProducaoSelect) return;
      try {
        const response = await fetchWithCreds(API_URL_LINHAS_PRODUCAO);
        const linhas = await response.json();
        linhas.forEach((linha) => {
          const option = document.createElement('option');
          option.value = linha.id;
          option.textContent = linha.nome;
          filtroLinhaProducaoSelect.appendChild(option);
        });
      } catch (error) {
        console.error('Erro ao popular filtro de linha de produção:', error);
        mostrarMensagem('danger', 'Erro ao carregar linhas de produção.');
      }
    }

    function updateTotais() {
      let totalSugerido = 0;
      let totalReal = 0;
      tabelaBody.querySelectorAll('tr').forEach((row) => {
        // Fonte de verdade consistente para o valor sugerido, vindo do dataset corrigido.
        const sugerida = parseFloat(row.dataset.qtdSugerida) || 0;
        totalSugerido += sugerida;

        // Para o total real, a fonte de verdade é o input do usuário.
        const qtdRealInput = row.querySelector('.qtd-real-input');
        if (qtdRealInput) {
          // Se o input tiver um valor, use-o. Senão, o valor real é 0 para a soma.
          const valorReal = qtdRealInput.value.trim();
          totalReal += valorReal ? toNumLocale(valorReal) : 0;
        }
      });

      // Exibe os totais formatados com 3 casas decimais para representar kg
      if (totalSugeridoEl) totalSugeridoEl.textContent = totalSugerido.toFixed(3);
      if (totalRealEl) totalRealEl.textContent = totalReal.toFixed(3);
    }

    async function buscarSugestoes() {
      root.dataset.disableAllRows = '0';
      const data = dataInput.value;
      const linhaProducaoId = filtroLinhaProducaoSelect?.value || '';

      if (!data) {
        tabelaBody.innerHTML = '<tr><td colspan="12" class="text-center text-muted">Selecione uma data para ver as sugestões.</td></tr>';
        updateTotais();
        return;
      }

      const dataAlvo = new Date(data);
      const hoje = new Date();
      hoje.setHours(0, 0, 0, 0);
      const isDataFutura = dataAlvo > hoje;

      loadingSpinner.style.display = 'block';
      tabelaBody.innerHTML = '';
      aprovarBtn.disabled = true;

      try {
        const params = new URLSearchParams({ data });
        if (linhaProducaoId) params.append('linha_producao_id', linhaProducaoId);
        const response = await fetchWithCreds(`${API_URL_SUGESTOES}?${params.toString()}`);
        const result = await response.json();

        const shouldDisableAll = isDataFutura || !!result.has_pending_previous_approvals;
        root.dataset.disableAllRows = shouldDisableAll ? '1' : '0';

        if (result.success) {
          if (result.has_pending_previous_approvals) {
            const dates = (result.pending_previous_approval_dates || []).join(', ');
            await Swal.fire({
              icon: 'warning',
              title: 'Atenção!',
              html: `Existem arraçoamentos pendentes para datas anteriores: <strong>${dates}</strong>.`,
              confirmButtonText: 'Entendi'
            });
          }

          if (Array.isArray(result.sugestoes) && result.sugestoes.length > 0) {
            tabelaBody.innerHTML = result.sugestoes.map((s) => {
              const statusLower = String(s.status || '').toLowerCase();
              const isPendente = statusLower === 'pendente';
              const qtdSugerida = parseFloat(s.quantidade_kg ?? s.quantidade_sugerida_kg ?? 0).toFixed(3);
              const qtdReal = s.quantidade_realizada_kg ? parseFloat(s.quantidade_realizada_kg).toFixed(3) : '';
              const disableRow = shouldDisableAll || !isPendente;
              return `
                <tr data-sugestao-id="${s.sugestao_id ?? s.id}" data-qtd-sugerida="${s.quantidade_kg ?? s.quantidade_sugerida_kg ?? 0}">
                  <td class="text-center" style="width: 40px;">
                    <input type="checkbox" class="form-check-input sugestao-checkbox" value="${s.sugestao_id ?? s.id}" ${disableRow ? 'disabled' : ''}>
                  </td>
                  <td>${s.lote_nome || ''}</td>
                  <td>${s.tanque_nome || ''}</td>
                  <td>${s.lote_quantidade_atual || ''}</td>
                  <td>${s.lote_peso_medio_atual || ''}</td>
                  <td>${s.lote_linha_producao || ''}</td>
                  <td>${s.lote_sequencia || ''}</td>
                  <td>${s.produto_racao_nome || ''}</td>
                  <td style="width: 150px;">
                    <select class="form-select form-select-sm racao-realizada-select" data-racao-realizada-id="${s.racao_realizada_id || ''}" ${disableRow ? 'disabled' : ''}>
                      <option value="">Padrão</option>
                    </select>
                  </td>
                  <td class="text-center">${qtdSugerida}</td>
                  <td><input type="text" class="form-control form-control-sm qtd-real-input" value="${qtdReal}" ${disableRow ? 'disabled' : ''} style="max-width: 80px;"></td>
                  <td><span class="badge bg-${isPendente ? 'warning' : 'success'}">${s.status}</span></td>
                </tr>`;
            }).join('');
          } else {
            tabelaBody.innerHTML = '<tr><td colspan="12" class="text-center">Nenhuma sugestão encontrada para esta data.</td></tr>';
          }

          if (result.erros && result.erros.length > 0) {
            mostrarMensagem('warning', `Erros encontrados: ${result.erros.join('; ')}`);
          }
        } else {
          mostrarMensagem('danger', result.message || 'Erro ao buscar sugestões.');
          tabelaBody.innerHTML = '<tr><td colspan="12" class="text-center text-danger">Falha ao carregar dados.</td></tr>';
        }
      } catch (error) {
        console.error('Erro na busca de sugestões:', error);
        mostrarMensagem('danger', 'Erro de comunicação com o servidor.');
      } finally {
        loadingSpinner.style.display = 'none';
        updateAprovarBtnState();
        updateTotais();
        inicializarSeletoresDeRacao(tabelaBody);
      }
    }

    function updateAprovarBtnState() {
      const disableAll = root.dataset.disableAllRows === '1';
      const selecionados = root.querySelectorAll('.sugestao-checkbox:checked:not(:disabled)');
      aprovarBtn.disabled = disableAll || selecionados.length === 0;
    }
function updateAprovarBtnState(disableAll = false) {
      const selecionados = root.querySelectorAll('.sugestao-checkbox:checked:not(:disabled)');
      aprovarBtn.disabled = disableAll || selecionados.length === 0;
    }

    async function aprovarSugestoes() {
      const selecionados = root.querySelectorAll('.sugestao-checkbox:checked:not(:disabled)');
      if (selecionados.length === 0) {
        mostrarMensagem('warning', 'Selecione pelo menos uma sugestão pendente para aprovar.');
        return;
      }

      aprovarBtn.disabled = true;
      const total = selecionados.length;
      let concluidos = 0;
      const erros = [];

      for (const cb of selecionados) {
        concluidos += 1;
        aprovarBtn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Aprovando (${concluidos}/${total})...`;

        const row = cb.closest('tr');
        const sugerida = parseFloat(row.dataset.qtdSugerida) || 0;
        const realInput = row.querySelector('.qtd-real-input');
        const real = realInput?.value.trim() ? toNumLocale(realInput.value) : sugerida;
        const racaoSelect = row.querySelector('.racao-realizada-select');

        const payload = {
          sugestao_id: cb.value,
          quantidade_real_kg: real,
          racao_realizada_id: racaoSelect ? racaoSelect.value : null,
        };

        try {
          const response = await fetchWithCreds(API_URL_APROVAR, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          });
          const data = await response.json();
          if (!response.ok || data.success === false) {
            erros.push(data.message || 'Erro desconhecido');
          }
        } catch (error) {
          console.error('Erro na requisição de aprovação:', error);
          erros.push('Erro de comunicação');
        }
      }

      if (erros.length === 0) {
        mostrarMensagem('success', `${total} arraçoamento(s) aprovado(s) com sucesso.`);
      } else {
        mostrarMensagem('danger', `Falha ao aprovar ${erros.length} item(ns): ${erros.join('; ')}`);
      }

      aprovarBtn.disabled = false;
      aprovarBtn.innerHTML = '<i class="fas fa-check me-2"></i>Aprovar Selecionados';
      buscarSugestoes();
    }

    aprovarBtn.addEventListener('click', aprovarSugestoes, { signal });

    selecionarTodosCheckbox.addEventListener('change', (event) => {
      tabelaBody.querySelectorAll('.sugestao-checkbox:not(:disabled)').forEach((cb) => {
        cb.checked = event.target.checked;
      });
      const data = dataInput.value;
      const isFuture = data ? new Date(data) > new Date().setHours(0, 0, 0, 0) : false;
      updateAprovarBtnState(isFuture);
    }, { signal });

    tabelaBody.addEventListener('change', (event) => {
      if (event.target.classList.contains('sugestao-checkbox')) {
        const data = dataInput.value;
        const isFuture = data ? new Date(data) > new Date().setHours(0, 0, 0, 0) : false;
        updateAprovarBtnState(isFuture);
      }
    }, { signal });

    tabelaBody.addEventListener('input', (event) => {
      if (event.target.classList.contains('qtd-real-input')) {
        updateTotais();
      }
    }, { signal });

    tabelaBody.addEventListener('keydown', (event) => {
      if (event.key !== 'Tab') return;
      const currentInput = event.target;
      if (!currentInput.classList.contains('qtd-real-input')) return;

      event.preventDefault();
      const inputs = Array.from(tabelaBody.querySelectorAll('.qtd-real-input:not([disabled])'));
      const currentIndex = inputs.indexOf(currentInput);
      if (currentIndex === -1) return;

      let nextIndex;
      if (event.shiftKey) {
        nextIndex = currentIndex - 1;
        if (nextIndex < 0) nextIndex = inputs.length - 1;
      } else {
        nextIndex = currentIndex + 1;
        if (nextIndex >= inputs.length) nextIndex = 0;
      }

      const nextInput = inputs[nextIndex];
      nextInput.focus();
      nextInput.select();
    }, { signal });

    filtroLinhaProducaoSelect?.addEventListener('change', buscarSugestoes, { signal });
    dataInput.addEventListener('change', buscarSugestoes, { signal });

    const modalEdicao = document.getElementById('modalEdicao');
    const formEdicao = document.getElementById('formEdicao');
    const editIdInput = document.getElementById('edit-id');
    const editLoteNomeInput = document.getElementById('edit-lote-nome');
    const editProdutoRacaoNomeInput = document.getElementById('edit-produto-racao-nome');
    const editQuantidadeKgInput = document.getElementById('edit-quantidade-kg');
    const editObservacoesInput = document.getElementById('edit-observacoes');

    if (modalEdicao && formEdicao) {
      modalEdicao.addEventListener('show.bs.modal', async (event) => {
        const button = event.relatedTarget;
        const url = button?.dataset?.href;
        if (!url) {
          console.error('O botão de edição não possui um data-href.');
          event.preventDefault();
          return;
        }
        try {
          const response = await fetchWithCreds(url);
          const result = await response.json();
          if (result.success) {
            const data = result.data;
            if (editIdInput) editIdInput.value = data.id;
            if (editLoteNomeInput) editLoteNomeInput.value = data.lote_nome;
            if (editProdutoRacaoNomeInput) editProdutoRacaoNomeInput.value = data.produto_racao_nome;
            if (editQuantidadeKgInput) editQuantidadeKgInput.value = data.quantidade_kg;
            if (editObservacoesInput) editObservacoesInput.value = data.observacoes;
            formEdicao.dataset.apiUrl = `/producao/api/arracoamento/realizado/${data.id}/update/`;
          } else {
            mostrarMensagem('danger', result.message || 'Erro ao carregar dados para edição.');
            bootstrap.Modal.getInstance(modalEdicao)?.hide();
          }
        } catch (error) {
          console.error('Erro ao carregar dados para edição:', error);
          mostrarMensagem('danger', 'Erro de comunicação ao carregar dados para edição.');
          bootstrap.Modal.getInstance(modalEdicao)?.hide();
        }
      }, { signal });

      formEdicao.addEventListener('submit', async (event) => {
        event.preventDefault();
        const apiUrl = formEdicao.dataset.apiUrl;
        if (!apiUrl) return;
        const payload = {
          quantidade_kg: parseFloat(editQuantidadeKgInput?.value) || 0,
          observacoes: editObservacoesInput?.value || '',
        };
        try {
          const response = await fetchWithCreds(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          });
          const result = await response.json();
          if (result.success) {
            mostrarMensagem('success', result.message);
            bootstrap.Modal.getInstance(modalEdicao)?.hide();
            buscarSugestoes();
          } else {
            mostrarMensagem('danger', result.message || 'Erro ao salvar alterações.');
          }
        } catch (error) {
          console.error('Erro ao salvar alterações:', error);
          mostrarMensagem('danger', 'Erro de comunicação ao salvar alterações.');
        }
      }, { signal });
    }

    popularFiltroLinhaProducao();
  }

  return {
    init,
    destroy,
    SELECTOR_ROOT,
  };
})();
