// static/js/gerenciar_tanques.js
window.OneTech = window.OneTech || {};

OneTech.GerenciarTanques = (function () {
  const SELECTOR_ROOT = '#gerenciar-tanques[data-page="gerenciar-tanques"]';

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

  function parseSqlDatetime(value) {
    if (!value) return null;
    const match = value.match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?/);
    if (!match) return null;
    return new Date(+match[1], +match[2] - 1, +match[3], +match[4], +match[5], +(match[6] || 0));
  }

  function formatDateTimeBRsql(value) {
    const date = parseSqlDatetime(value);
    return date && !Number.isNaN(date.getTime()) ? date.toLocaleString('pt-BR') : (value || '');
  }

  function destroy(root) {
    if (!root) return;
    const controller = root._gerenciarTanquesAbortController;
    if (controller) {
      controller.abort();
      delete root._gerenciarTanquesAbortController;
    }
    delete root.dataset.bound;
  }

  function init(rootEl) {
    const root = rootEl || document.querySelector(SELECTOR_ROOT);
    if (!root) return;

    if (root._gerenciarTanquesAbortController) {
      destroy(root);
    }

    if (root.dataset.bound === '1') return;

    const controller = new AbortController();
    const { signal } = controller;
    root._gerenciarTanquesAbortController = controller;
    root.dataset.bound = '1';

    const form = root.querySelector('#form-tanque');
    const lista = root.querySelector('#lista-tanques');
    const inputId = root.querySelector('#tanque-id');
    const elIdVis = root.querySelector('#id_id');
    const elDataCriacao = root.querySelector('#id_data_criacao');
    const elLarg = root.querySelector('#id_largura');
    const elComp = root.querySelector('#id_comprimento');
    const elProf = root.querySelector('#id_profundidade');
    const elArea = root.querySelector('#id_metro_quadrado');
    const elVolume = root.querySelector('#id_metro_cubico');
    const elHa = root.querySelector('#id_ha');
    const search = root.querySelector('#search-tanque, [data-role="busca-tanque"]');
    const btnNovo = root.querySelector('#btn-novo-tanque,[data-action="novo-tanque"]');
    const btnSalvar = root.querySelector('[data-action="salvar-tanque"]');
    const API_BASE = '/producao/api/tanques/';

    if (!form || !lista) {
      return;
    }

    function computeFromInputs() {
      const L = toNumLocale(elLarg?.value);
      const C = toNumLocale(elComp?.value);
      const P = toNumLocale(elProf?.value);
      const area = L * C;
      const volume = area * P;
      const ha = area / 10000;
      return { L, C, P, area, volume, ha };
    }

    function recalcDimensoes() {
      const r = computeFromInputs();
      if (elArea) elArea.value = formatBR(r.area, 2);
      if (elVolume) elVolume.value = formatBR(r.volume, 3);
      if (elHa) elHa.value = formatBR(r.ha, 4);
    }

    function setBRField(el, val, dec) {
      if (!el) return;
      if (val == null || val === '') {
        el.value = '';
        return;
      }
      el.value = formatBR(toNumLocale(val), dec);
    }

    function resetFormTanque(clearId = true) {
      if (!form) return;
      if (clearId && inputId) inputId.value = '';
      Array.from(form.querySelectorAll('input,select,textarea')).forEach((el) => {
        if (el.readOnly || el.disabled) return;
        if (clearId && el === inputId) return;
        if (el.type === 'checkbox' || el.type === 'radio') el.checked = false;
        else if (el.tagName === 'SELECT') el.selectedIndex = 0;
        else el.value = '';
      });
      if (elIdVis) elIdVis.value = '';
      if (elDataCriacao) elDataCriacao.value = '';
      recalcDimensoes();
      form.querySelector('#id_nome')?.focus();
    }

    async function carregarTanque(id) {
      if (!id) return;
      try {
        const resp = await fetchWithCreds(`${API_BASE}${id}/`, { method: 'GET' }, 'application/json');
        if (!resp.ok) throw new Error('Falha ao carregar tanque');
        const data = await resp.json();

        if (inputId) inputId.value = data.id;
        if (elIdVis) {
          elIdVis.value = String(data.id || '');
          elIdVis.readOnly = true;
          elIdVis.disabled = true;
        }
        if (elDataCriacao) {
          elDataCriacao.value = formatDateTimeBRsql(data.data_criacao);
          elDataCriacao.readOnly = true;
          elDataCriacao.disabled = true;
        }
        setBRField(elLarg, data.largura, 2);
        setBRField(elComp, data.comprimento, 2);
        setBRField(elProf, data.profundidade, 2);

        const elNome = form.querySelector('#id_nome');
        if (elNome) elNome.value = data.nome || '';
        const elSeq = form.querySelector('#id_sequencia');
        if (elSeq) elSeq.value = data.sequencia ?? '';
        const elTag = form.querySelector('#id_tag_tanque');
        if (elTag) elTag.value = data.tag_tanque || '';

        const selUnid = form.querySelector('#id_unidade');
        if (selUnid) selUnid.value = data.unidade_id || data.unidade || '';
        const selFase = form.querySelector('#id_fase');
        if (selFase) selFase.value = data.fase_id || data.fase || '';
        const selTipo = form.querySelector('#id_tipo_tanque');
        if (selTipo) selTipo.value = data.tipo_tanque_id || data.tipo_tanque || '';
        const selLinha = form.querySelector('#id_linha_producao');
        if (selLinha) selLinha.value = data.linha_producao_id || data.linha_producao || '';
        const selMalha = form.querySelector('#id_malha');
        if (selMalha) selMalha.value = data.malha_id || data.malha || '';
        const selStatus = form.querySelector('#id_status_tanque');
        if (selStatus) selStatus.value = data.status_tanque_id || data.status_tanque || '';
        const selTipoTela = form.querySelector('#id_tipo_tela');
        if (selTipoTela) selTipoTela.value = data.tipo_tela || '';
        const elAtivo = form.querySelector('#id_ativo');
        if (elAtivo) elAtivo.value = (String(data.ativo) === '1' || data.ativo === true) ? 'True' : 'False';

        recalcDimensoes();
      } catch (error) {
        mostrarMensagem('danger', error.message || 'Falha ao carregar tanque.');
      }
    }

    async function salvarTanque() {
      recalcDimensoes();
      const metrics = computeFromInputs();
      const fd = new FormData(form);
      fd.delete('id');
      fd.delete('data_criacao');
      fd.set((elArea?.name || 'metro_quadrado'), metrics.area.toFixed(2));
      fd.set((elVolume?.name || 'metro_cubico'), metrics.volume.toFixed(3));
      fd.set((elHa?.name || 'ha'), metrics.ha.toFixed(4));

      const id = (inputId?.value || '').trim();
      const url = id ? `${API_BASE}${id}/atualizar/` : API_BASE;
      const btn = btnSalvar || form.querySelector('[type="submit"]');
      if (btn) btn.disabled = true;

      try {
        const resp = await fetchWithCreds(url, { method: 'POST', body: fd });
        const contentType = resp.headers.get('content-type') || '';
        if (!contentType.includes('json')) {
          const body = await resp.text().catch(() => '');
          throw new Error(`Servidor retornou ${resp.status} ${resp.statusText}. ${body}`);
        }
        const result = await resp.json();
        if (!resp.ok || result.success === false) {
          throw new Error(result.message || 'Falha ao salvar.');
        }

        const nome = form.querySelector('#id_nome')?.value || 'Sem nome';
        if (!id && (result.id || result.pk)) {
          const novoId = String(result.id || result.pk);
          if (inputId) inputId.value = novoId;
          const li = document.createElement('li');
          li.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
          li.dataset.id = novoId;
          li.dataset.name = nome;
          li.innerHTML = `<span class="texto-truncado">${nome}</span><i class="fas fa-chevron-right small text-muted"></i>`;
          lista.appendChild(li);
        } else if (id) {
          const li = lista.querySelector(`li[data-id="${id}"]`);
          if (li) {
            li.dataset.name = nome;
            const label = li.querySelector('.texto-truncado');
            if (label) label.textContent = nome;
          }
        }
        mostrarMensagem('success', result.message || 'Salvo com sucesso.');
      } catch (error) {
        mostrarMensagem('danger', error.message || 'Erro ao salvar.');
      } finally {
        if (btn) btn.disabled = false;
      }
    }

    [elLarg, elComp, elProf].forEach((el) => {
      el?.addEventListener('input', recalcDimensoes, { signal });
      el?.addEventListener('change', recalcDimensoes, { signal });
    });
    recalcDimensoes();

    lista.addEventListener('click', (event) => {
      const li = event.target.closest('li.list-group-item');
      if (!li) return;
      lista.querySelectorAll('li.list-group-item.active').forEach((item) => item.classList.remove('active'));
      li.classList.add('active');
      carregarTanque(li.dataset.id);
    }, { signal });

    if (search) {
      const filtrar = () => {
        const filtro = (search.value || '').trim().toUpperCase();
        lista.querySelectorAll('li.list-group-item').forEach((li) => {
          const texto = ((li.getAttribute('data-name') || li.textContent) || '').toUpperCase();
          const visivel = texto.includes(filtro);
          li.style.display = visivel ? '' : 'none';
          if (visivel) li.classList.add('d-flex');
          else li.classList.remove('d-flex');
        });
      };
      search.addEventListener('input', filtrar, { signal });
      search.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') event.preventDefault();
      }, { signal });
      filtrar();
    }

    btnNovo?.addEventListener('click', (event) => {
      event.preventDefault();
      lista.querySelectorAll('li.list-group-item.active').forEach((li) => li.classList.remove('active'));
      resetFormTanque(true);
    }, { signal });

    btnSalvar?.addEventListener('click', (event) => {
      event.preventDefault();
      salvarTanque();
    }, { signal });

    function adjustListHeight() {
      if (!form || !lista) return;
      const formRect = form.getBoundingClientRect();
      const searchWrapper = root.querySelector('.d-flex.mb-2');
      const offset = searchWrapper ? searchWrapper.offsetHeight : 0;
      const finalHeight = form.offsetHeight - offset - 20;
      if (finalHeight > 0) {
        lista.style.maxHeight = `${finalHeight}px`;
        lista.style.overflowY = 'auto';
      }
    }

    adjustListHeight();
    window.addEventListener('resize', adjustListHeight, { signal });

    resetFormTanque(true);
  }

  return {
    init,
    destroy,
    SELECTOR_ROOT,
  };
})();
