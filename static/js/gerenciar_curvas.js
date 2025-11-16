// static/js/gerenciar_curvas.js
window.OneTech = window.OneTech || {};

OneTech.GerenciarCurvas = (function () {
  const SELECTOR_ROOT = '#gerenciar-curvas[data-page="gerenciar-curvas"]';
  const SELECTORS = {
    listaCurvas: '#lista-curvas',
    formCurva: '#form-curva',
    formDetalhe: '#form-ponto-crescimento',
    inputCurvaId: '#curva-id',
    inputDetalheId: '#detalhe-id',
    tabPonto: '#ponto-crescimento-tab',
    tabelaBody: '#tabela-detalhes-body',
    btnNovaCurva: '#btn-nova-curva',
    btnLimparCurva: '[data-action="limpar-curva"]',
    btnLimparDetalhe: '[data-action="limpar-detalhe"]',
    searchCurva: '#search-curva'
  };

  let boundRoot = null;

  function toast(type, text) {
    if (typeof window.mostrarMensagem === 'function') {
      window.mostrarMensagem(type, text);
    } else {
      console.log(`[${type?.toUpperCase?.() || 'INFO'}] ${text}`);
    }
  }

  async function toJSONorText(response) {
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      return response.json();
    }
    return response.text();
  }

  function setDisabled(element, disabled = true) {
    if (!element) return;
    element.disabled = disabled;
  }

  function renderLinhaDetalheJSON(detalhe) {
    const tr = document.createElement('tr');
    tr.setAttribute('data-id', detalhe.id);
    tr.innerHTML = `
      <td>${detalhe.periodo_semana ?? ''}</td>
      <td>${detalhe.peso_inicial ?? ''}</td>
      <td>${detalhe.peso_final ?? ''}</td>
      <td>${detalhe.ganho_de_peso ?? ''}</td>
      <td>${detalhe.racao_nome ?? detalhe.racao ?? ''}</td>
      <td>${detalhe.numero_tratos ?? ''}</td>
      <td>${detalhe.gpd ?? ''}</td>
      <td>${detalhe.tca ?? ''}</td>
    `;
    return tr;
  }

  function bindBuscaDinamica(raiz, signal) {
    const lista = raiz.querySelector(SELECTORS.listaCurvas);
    if (!lista) return;

    const filtrar = () => {
      const search = raiz.querySelector(SELECTORS.searchCurva);
      const filtro = (search?.value || '').trim().toUpperCase();
      Array.from(lista.querySelectorAll('li.list-group-item')).forEach(li => {
        const texto = ((li.dataset.name || li.textContent) || '').toUpperCase();
        li.style.display = texto.includes(filtro) ? '' : 'none';
      });
    };

    raiz.addEventListener('input', (event) => {
      if (event.target && event.target.matches(SELECTORS.searchCurva)) filtrar();
    }, { signal });

    raiz.addEventListener('keydown', (event) => {
      if (event.target && event.target.matches(SELECTORS.searchCurva) && event.key === 'Enter') {
        event.preventDefault();
      }
    }, { signal });

    filtrar();
  }

  function destroy() {
    if (!boundRoot) return;
    const controller = boundRoot._gerenciarCurvasAbortController;
    if (controller) {
      controller.abort();
      delete boundRoot._gerenciarCurvasAbortController;
    }
    delete boundRoot.dataset.bound;
    boundRoot = null;
  }

  function init(rootEl) {
    const raiz = rootEl || document.querySelector(SELECTOR_ROOT);
    if (!raiz) return;

    if (boundRoot && boundRoot !== raiz) {
      destroy();
    }

    if (raiz.dataset.bound === '1') return;

    const controller = new AbortController();
    const { signal } = controller;
    raiz._gerenciarCurvasAbortController = controller;
    raiz.dataset.bound = '1';
    boundRoot = raiz;

    const q = (selector) => raiz.querySelector(selector);
    const qa = (selector, ctx = raiz) => Array.from((ctx || raiz).querySelectorAll(selector));

    const endpointBaseCurva = raiz.dataset.endpointCurvaBase || '/producao/api/curva/';
    const endpointSufixoDet = raiz.dataset.endpointDetalheSufixo || 'detalhes/';

    const listaCurvas = q(SELECTORS.listaCurvas);
    const formCurva = q(SELECTORS.formCurva);
    const formDetalhe = q(SELECTORS.formDetalhe);
    const inputCurvaId = q(SELECTORS.inputCurvaId);
    const inputDetalheId = q(SELECTORS.inputDetalheId);
    const tabBtnPonto = q(SELECTORS.tabPonto);
    const tabelaBody = q(SELECTORS.tabelaBody);
    const btnNovaCurva = q(SELECTORS.btnNovaCurva);
    const btnLimparCurva = formCurva?.querySelector(SELECTORS.btnLimparCurva);
    const btnLimparDetalhe = formDetalhe?.querySelector(SELECTORS.btnLimparDetalhe);

    function habilitarAbaPonto(habilitar = true) {
      if (!tabBtnPonto) return;
      tabBtnPonto.disabled = !habilitar;
      tabBtnPonto.classList.toggle('disabled', !habilitar);
      tabBtnPonto.setAttribute('aria-disabled', (!habilitar).toString());
    }

    function abrirAbaPonto() {
      if (!tabBtnPonto) return;
      const tab = new bootstrap.Tab(tabBtnPonto);
      tab.show();
    }

    function limparTabela() {
      if (!tabelaBody) return;
      tabelaBody.innerHTML = `
        <tr data-empty="true">
          <td colspan="8" class="text-center text-muted">Selecione uma curva para ver ou adicionar detalhes.</td>
        </tr>
      `;
    }

    function limparFormCurva(keepId = false) {
      if (!formCurva) return;
      if (!keepId && inputCurvaId) inputCurvaId.value = '';
      Array.from(formCurva.querySelectorAll('input, select, textarea')).forEach(el => {
        if (keepId && el === inputCurvaId) return;
        if (el.type === 'checkbox' || el.type === 'radio') {
          el.checked = false;
        } else if (el.tagName === 'SELECT') {
          el.selectedIndex = 0;
        } else {
          el.value = '';
        }
      });
    }

    function limparFormDetalhe(keepId = false) {
      if (!formDetalhe) return;
      if (!keepId && inputDetalheId) inputDetalheId.value = '';
      Array.from(formDetalhe.querySelectorAll('input, select, textarea')).forEach(el => {
        if (keepId && el === inputDetalheId) return;
        if (el.type === 'checkbox' || el.type === 'radio') {
          el.checked = false;
        } else if (el.tagName === 'SELECT') {
          el.selectedIndex = 0;
        } else {
          el.value = '';
        }
      });
    }

    function popularTelaComCurva(payload) {
      if (!formCurva || !tabelaBody) return;
      const curva = payload.curva || {};
      if (inputCurvaId) inputCurvaId.value = curva.id ?? '';
      const map = {
        'id_nome': curva.nome,
        'id_especie': curva.especie,
        'id_rendimento_perc': curva.rendimento_perc,
        'id_trato_perc_curva': curva.trato_perc_curva,
        'id_peso_pretendido': curva.peso_pretendido,
        'id_trato_sabados_perc': curva.trato_sabados_perc,
        'id_trato_domingos_perc': curva.trato_domingos_perc,
        'id_trato_feriados_perc': curva.trato_feriados_perc
      };
      Object.entries(map).forEach(([id, val]) => {
        const field = formCurva.querySelector(`#${id}`);
        if (field) field.value = val ?? '';
      });

      const detalhes = Array.isArray(payload.detalhes) ? payload.detalhes : [];
      tabelaBody.innerHTML = '';
      if (!detalhes.length) {
        limparTabela();
      } else {
        const fragment = document.createDocumentFragment();
        detalhes.forEach(item => fragment.appendChild(renderLinhaDetalheJSON(item)));
        tabelaBody.appendChild(fragment);
      }

      limparFormDetalhe(false);
    }

    async function carregarCurva(curvaId) {
      if (!curvaId) return;
      try {
        const url = `${endpointBaseCurva}${curvaId}/${endpointSufixoDet}`;
        const response = await fetchWithCreds(url, { method: 'GET' });
        if (!response.ok) throw new Error('Falha ao carregar a curva.');
        const data = await response.json();
        popularTelaComCurva(data);
        habilitarAbaPonto(true);
        toast('success', `Curva '${data.curva?.nome || ''}' carregada.`);
      } catch (error) {
        toast('danger', error.message || 'Erro ao carregar a curva.');
        limparTabela();
      }
    }

    listaCurvas?.addEventListener('click', (event) => {
      const item = event.target.closest('li.list-group-item');
      if (!item) return;
      qa('li.list-group-item', listaCurvas).forEach(li => li.classList.remove('active'));
      item.classList.add('active');
      const curvaId = item.dataset.id || item.dataset.curvaId;
      if (curvaId) carregarCurva(curvaId);
    }, { signal });

    btnNovaCurva?.addEventListener('click', (event) => {
      event.preventDefault();
      if (listaCurvas) {
        qa('li.list-group-item', listaCurvas).forEach(li => li.classList.remove('active'));
      }
      limparFormCurva(false);
      limparFormDetalhe(false);
      limparTabela();
      habilitarAbaPonto(false);
      toast('info', 'Preencha o cabeçalho e salve para liberar os períodos.');
    }, { signal });

    btnLimparCurva?.addEventListener('click', (event) => {
      event.preventDefault();
      limparFormCurva(true);
    }, { signal });

    btnLimparDetalhe?.addEventListener('click', (event) => {
      event.preventDefault();
      limparFormDetalhe(false);
    }, { signal });

    formCurva?.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (!formCurva) return;
      const curvaId = inputCurvaId?.value?.trim();
      const isNovo = !curvaId;
      const url = isNovo ? endpointBaseCurva : `${endpointBaseCurva}${curvaId}/`;
      const formData = new FormData(formCurva);

      try {
        setDisabled(formCurva.querySelector('[type="submit"]'), true);
        const response = await fetchWithCreds(url, { method: 'POST', body: formData });
        const data = await toJSONorText(response);
        if (!response.ok || (data && data.success === false)) {
          throw new Error((data && (data.message || data.error)) || 'Erro ao salvar a curva.');
        }

        if (isNovo) {
          const novoId = (data && (data.id || data.curva_id || data.pk)) || '';
          if (inputCurvaId) inputCurvaId.value = String(novoId || '');
          habilitarAbaPonto(true);
          toast('success', 'Curva criada. Agora adicione os períodos.');
          if (novoId && listaCurvas) {
            const li = document.createElement('li');
            li.className = 'list-group-item list-group-item-action d-flex align-items-center justify-content-between';
            li.dataset.id = String(novoId);
            li.dataset.name = data.curva_nome || data.nome || 'Sem nome';
            li.style.cursor = 'pointer';
            li.innerHTML = `
              <span class="texto-truncado">${li.dataset.name}</span>
              <i class="fas fa-chevron-right small text-muted"></i>
            `;
            listaCurvas.appendChild(li);
          }
        } else {
          toast('success', (data && data.message) || 'Cabeçalho da curva salvo.');
          if (listaCurvas && curvaId) {
            const li = listaCurvas.querySelector(`li[data-id="${curvaId}"]`);
            if (li && data.curva_nome) {
              li.dataset.name = data.curva_nome;
              li.innerHTML = `
                <span class="texto-truncado">${data.curva_nome}</span>
                <i class="fas fa-chevron-right small text-muted"></i>
              `;
            }
          }
        }
      } catch (error) {
        toast('danger', error.message || 'Falha ao salvar a curva.');
      } finally {
        setDisabled(formCurva.querySelector('[type="submit"]'), false);
      }
    }, { signal });

    tabelaBody?.addEventListener('click', async (event) => {
      const linha = event.target.closest('tr[data-id]');
      if (!linha || !formDetalhe) return;
      const curvaId = inputCurvaId?.value?.trim();
      const detalheId = linha.getAttribute('data-id');
      if (!curvaId || !detalheId) return;
      try {
        const url = `${endpointBaseCurva}${curvaId}/${endpointSufixoDet}${detalheId}/`;
        const response = await fetchWithCreds(url, { method: 'GET' });
        if (!response.ok) throw new Error('Falha ao carregar o detalhe.');
        const detalhes = await response.json();
        if (inputDetalheId) inputDetalheId.value = detalhes.id ?? detalheId;
        const map = {
          'id_periodo_semana': detalhes.periodo_semana,
          'id_periodo_dias': detalhes.periodo_dias,
          'id_peso_inicial': detalhes.peso_inicial,
          'id_peso_final': detalhes.peso_final,
          'id_ganho_de_peso': detalhes.ganho_de_peso,
          'id_numero_tratos': detalhes.numero_tratos,
          'id_hora_inicio': detalhes.hora_inicio,
          'id_arracoamento_biomassa_perc': detalhes.arracoamento_biomassa_perc,
          'id_mortalidade_presumida_perc': detalhes.mortalidade_presumida_perc,
          'id_racao': detalhes.racao,
          'id_gpd': detalhes.gpd,
          'id_tca': detalhes.tca
        };
        Object.entries(map).forEach(([id, val]) => {
          const field = formDetalhe.querySelector(`#${id}`);
          if (field) field.value = val ?? '';
        });
        abrirAbaPonto();
      } catch (error) {
        toast('danger', error.message || 'Erro ao carregar o detalhe.');
      }
    }, { signal });

    formDetalhe?.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (!formDetalhe) return;
      const curvaId = inputCurvaId?.value?.trim();
      if (!curvaId) {
        toast('warning', 'Salve o cabeçalho da curva antes.');
        return;
      }
      const detalheId = inputDetalheId?.value?.trim();
      const isNovo = !detalheId;
      const url = isNovo
        ? `${endpointBaseCurva}${curvaId}/${endpointSufixoDet}criar/`
        : `${endpointBaseCurva}${curvaId}/${endpointSufixoDet}${detalheId}/atualizar/`;
      const formData = new FormData(formDetalhe);
      try {
        setDisabled(formDetalhe.querySelector('[type="submit"]'), true);
        const response = await fetchWithCreds(url, { method: 'POST', body: formData });
        const data = await toJSONorText(response);
        if (!response.ok || (data && data.success === false)) {
          throw new Error((data && (data.message || data.error)) || 'Erro ao salvar o detalhe.');
        }

        if (data && data.periodo) {
          const detalheAtualizado = data.periodo;
          const novaLinha = renderLinhaDetalheJSON(detalheAtualizado);
          if (!isNovo) {
            const alvo = tabelaBody?.querySelector(`tr[data-id="${detalheAtualizado.id || detalheId}"]`);
            if (alvo) alvo.replaceWith(novaLinha);
          } else {
            const placeholder = tabelaBody?.querySelector('tr[data-empty="true"]');
            if (placeholder) placeholder.remove();
            tabelaBody?.appendChild(novaLinha);
          }
        }

        if (isNovo) {
          limparFormDetalhe(false);
          toast('success', (data && data.message) || 'Período adicionado.');
        } else {
          toast('success', (data && data.message) || 'Período atualizado.');
        }
      } catch (error) {
        toast('danger', error.message || 'Falha ao salvar o detalhe.');
      } finally {
        setDisabled(formDetalhe.querySelector('[type="submit"]'), false);
      }
    }, { signal });

    bindBuscaDinamica(raiz, signal);
  }

  return {
    init,
    destroy,
    SELECTOR_ROOT
  };
})();
