// static/js/gerenciar_eventos.js
window.OneTech = window.OneTech || {};

OneTech.GerenciarEventos = (function () {
  const SELECTOR_ROOT = '#gerenciar-eventos[data-page="gerenciar-eventos"]';
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
    const controller = root._gerenciarEventosAbortController;
    if (controller) {
      controller.abort();
      delete root._gerenciarEventosAbortController;
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
    root._gerenciarEventosAbortController = controller;
    root.dataset.bound = '1';
    boundRoot = root;

    const q = (selector, ctx = root) => (ctx || root).querySelector(selector);
    const qa = (selector, ctx = root) => Array.from((ctx || root).querySelectorAll(selector));

    const visaoInicial = q('#visao-inicial-eventos');
    const conteudoAbas = q('#conteudo-abas-eventos');
    const selectAba = q('#aba-evento-select');
    const btnMostrarMais = q('#btn-mostrar-mais-eventos');
    const tabelaUltimosEventosBody = q('#tabela-ultimos-eventos-body');

    const filtroBusca = q('#filtro-busca');
    const filtroUnidade = q('#filtro-unidade');
    const filtroLinha = q('#filtro-linha');
    const filtroFase = q('#filtro-fase');
    const filtroData = q('#filtro-data');

    function debounce(fn, delay = 350) {
      let timeout;
      return (...args) => {
        if (timeout) clearTimeout(timeout);
        timeout = setTimeout(() => fn(...args), delay);
      };
    }

    function toggleView(showAbas) {
      if (visaoInicial) visaoInicial.classList.toggle('d-none', showAbas);
      if (conteudoAbas) conteudoAbas.classList.toggle('d-none', !showAbas);
    }

    function showTabBySlug(slug) {
      if (!slug) {
        toggleView(false);
        return;
      }
      const btn = q(`[data-bs-toggle="tab"][data-bs-target="#pane-${slug}"]`);
      if (btn && window.bootstrap?.Tab) {
        toggleView(true);
        new bootstrap.Tab(btn).show();
      }
    }

    function activePaneSlug() {
      const active = q('#conteudo-abas-eventos .tab-pane.active');
      return active ? active.id.replace('pane-', '') : null;
    }

  function loadActivePane(reset = false) {
    const slug = activePaneSlug();
    if (!slug) {
      carregarUltimosEventos(reset);
      return;
    }
    if (slug === 'mortalidade') {
      carregarMortalidade();
    }
  }

    async function carregarUltimosEventos(reset = false) {
      if (!btnMostrarMais || !tabelaUltimosEventosBody) return;
      const offset = reset ? 0 : parseInt(btnMostrarMais.dataset.offset || '0', 10);
      const params = new URLSearchParams({
        offset,
        termo: filtroBusca?.value.trim() || '',
        unidade: filtroUnidade?.value || '',
        linha_producao: filtroLinha?.value || '',
        fase: filtroFase?.value || '',
        data: filtroData?.value || '',
      });

      btnMostrarMais.disabled = true;
      btnMostrarMais.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Carregando...';

      if (reset) {
        tabelaUltimosEventosBody.innerHTML = `<tr><td colspan="8" class="text-center"><span class="spinner-border spinner-border-sm"></span> Buscando...</td></tr>`;
      }

      try {
        const url = `/producao/api/ultimos-eventos/?${params.toString()}`;
        const response = await (window.fetchWithCreds || fetch)(url);
        const data = await response.json();

        if (reset) {
          tabelaUltimosEventosBody.innerHTML = '';
        }

        if (data.success && Array.isArray(data.eventos) && data.eventos.length > 0) {
          const newRows = data.eventos.map((evento) => `
            <tr>
              <td>${evento.data_evento}</td>
              <td>${evento.tipo_evento}</td>
              <td>${evento.lote}</td>
              <td>${evento.tanque_origem}</td>
              <td>${evento.tanque_destino}</td>
              <td class="text-end">${evento.quantidade}</td>
              <td class="text-end">${evento.peso_medio}</td>
              <td>${evento.observacoes}</td>
            </tr>
          `).join('');
          tabelaUltimosEventosBody.insertAdjacentHTML('beforeend', newRows);
          btnMostrarMais.dataset.offset = offset + data.eventos.length;

          if (data.eventos.length < 20) btnMostrarMais.classList.add('d-none');
          else btnMostrarMais.classList.remove('d-none');
        } else {
          btnMostrarMais.classList.add('d-none');
          if (reset) {
            tabelaUltimosEventosBody.innerHTML = '<tr><td colspan="8" class="text-center">Nenhum evento encontrado para a busca.</td></tr>';
          }
          if (!data.success) {
            mostrarMensagem('danger', data.message || 'Erro ao carregar eventos.');
          }
        }
      } catch (error) {
        console.error('Erro ao carregar eventos:', error);
        mostrarMensagem('danger', 'Erro de comunicação ao buscar eventos.');
      } finally {
        btnMostrarMais.disabled = false;
        btnMostrarMais.innerHTML = 'Mostrar mais...';
      }
    }

    async function carregarMortalidade() {
      const tbody = q('#tabela-mortalidade tbody');
      if (!tbody) return;

      tbody.innerHTML = '<tr><td colspan="99" class="text-center"><span class="badge bg-primary">Carregando dados...</span></td></tr>';

      try {
        const params = new URLSearchParams({
          unidade: filtroUnidade?.value || '',
          linha_producao: filtroLinha?.value || '',
          fase: filtroFase?.value || '',
          termo: filtroBusca?.value.trim() || '',
          data: filtroData?.value || '',
        });
        const url = `/producao/api/eventos/mortalidade/?${params.toString()}`;
        const response = await (window.fetchWithCreds || fetch)(url);
        const data = await response.json();

        if (Array.isArray(data.results) && data.results.length > 0) {
          tbody.innerHTML = data.results.map((item) => `
            <tr data-lote="${item.lote_id}">
              <td>${item.tanque}</td>
              <td>${item.lote}</td>
              <td>${item.data_inicio}</td>
              <td class="text-end">${item.qtd_atual}</td>
              <td class="text-end">${item.peso_medio_g}</td>
              <td class="text-end">${item.biomassa_kg}</td>
              <td class="text-end"><input type="text" pattern="[0-9]*" inputmode="numeric" class="form-control form-control-sm input-mort" value="${item.qtd_mortalidade || ''}" data-peso-medio="${item.peso_medio_g}"></td>
              <td class="text-end" data-biomassa-retirada>${formatBR((item.qtd_mortalidade * item.peso_medio_g) / 1000, 2)}</td>
            </tr>
          `).join('');
        } else {
          tbody.innerHTML = '<tr><td colspan="99" class="text-center">Nenhum lote ativo encontrado para os filtros selecionados.</td></tr>';
        }

        qa('.input-mort', tbody).forEach((input) => {
          input.addEventListener('input', (event) => {
            const row = event.target.closest('tr');
            const qtd = parseFloat(event.target.value) || 0;
            const pesoMedioG = parseFloat(event.target.dataset.pesoMedio) || 0;
            const biomassaRetiradaKg = (qtd * pesoMedioG) / 1000;
            const target = row.querySelector('[data-biomassa-retirada]');
            if (target) target.textContent = formatBR(biomassaRetiradaKg, 2);
            updateTotaisMortalidade();
          }, { signal });
        });
        updateTotaisMortalidade();
      } catch (error) {
        console.error('Erro ao carregar mortalidade:', error);
        tbody.innerHTML = '<tr><td colspan="99" class="text-center"><span class="badge bg-danger">Erro ao carregar dados</span></td></tr>';
      }
    }

    function updateTotaisMortalidade() {
      const tbody = q('#tabela-mortalidade tbody');
      if (!tbody) return;

      let totalQtd = 0;
      let totalBiomassa = 0;

      tbody.querySelectorAll('tr').forEach((row) => {
        const inputQtd = row.querySelector('.input-mort');
        if (!inputQtd) return;
        const qtd = toNumLocale(inputQtd.value) || 0;
        const biomassa = toNumLocale(row.querySelector('[data-biomassa-retirada]')?.textContent) || 0;
        totalQtd += qtd;
        totalBiomassa += biomassa;
      });

      const totalQtdElement = q('#total-mortalidade-qtd', root) || q('#total-mortalidade-qtd');
      const totalBiomassaElement = q('#total-mortalidade-biomassa', root) || q('#total-mortalidade-biomassa');
      if (totalQtdElement) totalQtdElement.textContent = formatBR(totalQtd, 0);
      if (totalBiomassaElement) totalBiomassaElement.textContent = formatBR(totalBiomassa, 2);
    }

    const debouncedLoad = debounce(() => loadActivePane(true), 400);

    selectAba?.addEventListener('change', (event) => {
      showTabBySlug(event.target.value);
      loadActivePane(true);
    }, { signal });

    btnMostrarMais?.addEventListener('click', () => carregarUltimosEventos(false), { signal });

    [filtroBusca, filtroUnidade, filtroLinha, filtroFase, filtroData].forEach((filtro) => {
      if (!filtro) return;
      filtro.addEventListener('input', (event) => {
        if (event.target.type === 'date' && event.type === 'input') return;
        debouncedLoad();
      }, { signal });
      if (filtro.type === 'date') {
        filtro.addEventListener('change', debouncedLoad, { signal });
      }
    });

    qa('[data-bs-toggle="tab"]').forEach((el) => {
      el.addEventListener('shown.bs.tab', () => loadActivePane(true), { signal });
    });

    const btnProcessarMortalidade = q('#btn-processar-mortalidade');
    if (btnProcessarMortalidade) {
      btnProcessarMortalidade.addEventListener('click', async () => {
        const tabela = q('#tabela-mortalidade tbody');
        if (!tabela) return;

        const dataEvento = filtroData?.value;
        if (!dataEvento) {
          mostrarMensagem('warning', 'Por favor, selecione uma data de lançamento.');
          return;
        }

        const lancamentos = [];
        tabela.querySelectorAll('tr').forEach((row) => {
          const checkbox = row.querySelector('.input-mort');
          if (!checkbox) return;
          const loteId = row.dataset.lote;
          const qtdMortalidade = toNumLocale(row.querySelector('.input-mort')?.value);
          const biomassaRetirada = toNumLocale(row.querySelector('[data-biomassa-retirada]')?.textContent);
          if (qtdMortalidade > 0) {
            lancamentos.push({ lote_id: loteId, quantidade_mortalidade: qtdMortalidade, biomassa_retirada: biomassaRetirada });
          }
        });

        if (lancamentos.length === 0) {
          mostrarMensagem('warning', 'Nenhum lançamento de mortalidade para processar.');
          return;
        }

        btnProcessarMortalidade.disabled = true;
        btnProcessarMortalidade.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Processando...';

        try {
          const response = await fetchWithCreds('/producao/api/eventos/mortalidade/processar/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lancamentos, data_evento: dataEvento }),
          });
          const result = await response.json();

          if (result.success) {
            mostrarMensagem('success', result.message);
            
            // Limpa os filtros e reseta a UI para a visão inicial
            if (filtroData) filtroData.value = '';
            if (filtroUnidade) filtroUnidade.value = '';
            if (filtroLinha) filtroLinha.value = '';
            if (filtroFase) filtroFase.value = '';
            if (filtroBusca) filtroBusca.value = '';
            if (selectAba) selectAba.value = '';
            toggleView(false);

            // Recarrega a lista principal (agora sem filtros) para mostrar o novo evento
            carregarUltimosEventos(true);
          } else {
            mostrarMensagem('danger', result.message || 'Erro ao processar mortalidade.');
          }
        } catch (error) {
          console.error('Erro ao processar mortalidade:', error);
          mostrarMensagem('danger', 'Erro de comunicação ao processar mortalidade.');
        } finally {
          btnProcessarMortalidade.disabled = false;
          btnProcessarMortalidade.innerHTML = 'Processar Lançamentos';
        }
      }, { signal });
    }

    toggleView(false);
    carregarUltimosEventos(true);
  }

  return {
    init,
    destroy,
    SELECTOR_ROOT,
  };
})();
