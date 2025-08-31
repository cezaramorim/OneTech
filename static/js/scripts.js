// ============================================================================
// ARQUIVO scripts.js - VERSÃO COM FETCH HELPER E CREDENCIAIS
// ============================================================================

// 🌙 Aplica o tema salvo no localStorage (antes do paint)
const temaSalvo = localStorage.getItem("tema");
const isDarkInit = temaSalvo === "dark";
if (isDarkInit) {
  document.documentElement.classList.add("dark");
}

// ✅ Libera a exibição da tela (importante!)
document.documentElement.classList.add("theme-ready");

// ── Ajusta o navbar logo de cara ──
const navbarInicial = document.querySelector(".navbar-superior");
if (navbarInicial) {
  navbarInicial.classList.add(isDarkInit ? "navbar-dark" : "navbar-light");
}

// --- Funções de Utilidade Global ---

// Detecta separador decimal e devolve Number seguro (aceita “1.234,56” e “1,234.56”)
function toNumLocale(v) {
  if (v == null) return 0;
  v = String(v).trim();
  if (!v) return 0;
  v = v.replace(/[^\d,.\-]/g, '');
  const lastComma = v.lastIndexOf(',');
  const lastDot   = v.lastIndexOf('.');
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

// Formata sempre com vírgula para a UI
function formatBR(n, dec) {
  const v = (Number.isFinite(n) ? n : 0).toFixed(dec ?? 2);
  return v.replace('.', ',');
}

function parseSqlDatetime(s) {
  if (!s) return null;
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?/);
  if (!m) return null;
  return new Date(+m[1], +m[2]-1, +m[3], +m[4], +m[5], +(m[6]||0));
}
function formatDateTimeBRsql(s) {
  const d = parseSqlDatetime(s);
  return d && !isNaN(d) ? d.toLocaleString('pt-BR') : (s || '');
}

function getCSRFToken() {
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
}

// URL de login (pode vir do <body data-login-url=\"...\") ou cai no padrão)
const LOGIN_URL = document.body?.dataset?.loginUrl || '/accounts/login/';

// fetch com cookies + cabeçalhos padrão (AJAX)
function fetchWithCreds(url, options = {}) {
  const opts = { credentials: 'include', ...options }; // Ensure credentials: 'include'
  const headers = new Headers(opts.headers || {});
  if (!headers.has('X-Requested-With')) headers.set('X-Requested-With', 'XMLHttpRequest');
  if ((opts.method || 'GET').toUpperCase() !== 'GET' && !headers.has('X-CSRFToken')) {
    headers.set('X-CSRFToken', getCSRFToken());
  }
  opts.headers = headers;
  return fetch(url, opts);
}

// Heurística simples para detectar HTML de login devolvido no lugar do conteúdo pedido
function isLikelyLoginHTML(html) {
  if (!html) return false;
  const s = html.toLowerCase();

  // Marcadores explícitos (recomendado: adicione isso no template do login)
  const hasExplicitMarker =
    s.includes('id="login-form"') ||
    s.includes('id="login-page"') ||           // se você colocar no <body id=\"login-page\">
    s.includes('data-page="login"');           // ou <body data-page=\"login\">

  // Heurística mais forte: precisa ter form com action para /accounts/login E campos username+password
  const hasLoginAction = /<form[^>]+action=[\"'][^\"']*\/accounts\/login\/?['\"][^>]*>/i.test(s);
  const hasUsername = /\bname=[\"']username[\"']/i.test(s);
  const hasPassword = /\bname=[\"']password[\"']/i.test(s);

  return hasExplicitMarker || (hasLoginAction && hasUsername && hasPassword);
}

function mostrarMensagem(type, message) {
    if (!window.Swal) {
        console.error("Biblioteca Swal (SweetAlert2) não encontrada.");
        return;
    }
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.id = 'toast-container';
        container.style.zIndex = '1090';
        document.body.appendChild(container);
    }
    const toastId = `toast-${Date.now()}`;
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', toastHTML);
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
    toast.show();
    toastElement.addEventListener('hidden.bs.toast', () => toastElement.remove());
}

function loadAjaxContent(url) {
  console.log(" loadAjaxContent: Carregando URL:", url);
  const mainContent = document.getElementById("main-content");
  if (!mainContent) {
    console.error("❌ #main-content não encontrado. Recarregando a página.");
    window.location.href = url;
    return;
  }

  fetchWithCreds(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
    .then(async (response) => {
      if (response.status === 401) {
        let data = null; try { data = await response.json(); } catch {}
        window.location.href = data?.redirect_url || `${LOGIN_URL}?next=${encodeURIComponent(url)}`;
        return null;
      }
      if (response.redirected) { // servidor respondeu 302 → login
        window.location.href = response.url;
        return null;
      }
      if (response.status === 403) {
        if (typeof mostrarMensagem === 'function') {
          mostrarMensagem('danger', 'Você não tem permissão para acessar esta página.');
        } else {
          alert('Você não tem permissão para acessar esta página.');
        }
        return null; // não troca o main-content
      }
      const ct = response.headers.get('content-type') || '';
      if (ct.includes('application/json')) {
        const data = await response.json();
        if (data?.redirect_url) { window.location.href = data.redirect_url; return null; }
        throw new Error('JSON inesperado em loadAjaxContent.');
      }
      const html = await response.text();
      if (isLikelyLoginHTML(html)) { // HTML da tela de login veio “embedado”
        window.location.href = `${LOGIN_URL}?next=${encodeURIComponent(url)}`;
        return null;
      }
      return html;
    })
    .then((html) => {
      if (html == null) return; // já redirecionou
      mainContent.innerHTML = html;

      // reexecuta scripts embutidos (mantendo seu skip do scripts.js)
      Array.from(mainContent.querySelectorAll("script")).forEach(oldScript => {
        if (oldScript.src && oldScript.src.includes('scripts.js')) return;
        const newScript = document.createElement("script");
        Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
        newScript.appendChild(document.createTextNode(oldScript.innerHTML));
        oldScript.parentNode.replaceChild(newScript, oldScript);
      });

      history.pushState({ ajaxUrl: url }, "", url);
      document.dispatchEvent(new CustomEvent("ajaxContentLoaded", { detail: { url } }));
      console.log("✅ Conteúdo do #main-content atualizado e scripts executados.");
    })
    .catch(error => {
      console.error("❌ Falha ao carregar conteúdo via AJAX:", error);
      mostrarMensagem("danger", "Erro ao carregar a página.");
    });
}

function updateButtonStates(mainContent) {
    if (!mainContent) return;
    const identificadorTela = mainContent.querySelector("#identificador-tela");
    const seletorFilho = identificadorTela?.dataset.seletorFilho || identificadorTela?.dataset.seletorCheckbox;

    if (!identificadorTela || !seletorFilho) return;

    const itemCheckboxes = mainContent.querySelectorAll(seletorFilho);
    const btnEditar = mainContent.querySelector('#btn-editar');
    const btnExcluir = mainContent.querySelector('#btn-excluir');
    const selectedItems = Array.from(itemCheckboxes).filter(cb => cb.checked);
    const hasSelection = selectedItems.length > 0;
    const hasSingleSelection = selectedItems.length === 1;

    if (btnEditar) {
        btnEditar.disabled = !hasSingleSelection;
        btnEditar.classList.toggle('disabled', !hasSingleSelection);
        if (hasSingleSelection) {
            const editUrlBase = identificadorTela.dataset.urlEditar;
            if (editUrlBase) {
                const itemId = selectedItems[0].value;
                btnEditar.setAttribute('data-href', editUrlBase.replace('0', itemId));
            } else {
                btnEditar.disabled = true;
                btnEditar.classList.add('disabled');
            }
        } else {
            btnEditar.removeAttribute('data-href');
        }
    }

    if (btnExcluir) {
        btnExcluir.disabled = !hasSelection;
        btnExcluir.classList.toggle('disabled', !hasSelection);
    }
    
    const selectAllCheckbox = mainContent.querySelector('input[type="checkbox"][id^="select-all-"]');
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = itemCheckboxes.length > 0 && selectedItems.length === itemCheckboxes.length;
    }
}

function loadNavbar() {
    fetchWithCreds('/accounts/get-navbar/', { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then(response => {
            if (!response.ok) {
                // Log detalhado do erro
                console.error(`❌ Falha ao buscar navbar. Status: ${response.status} ${response.statusText}`);
                throw new Error('Falha ao buscar navbar');
            }
            return response.text();
        })
        .then(html => {
            const navbarContainer = document.getElementById('navbar-container');
            if (navbarContainer) {
                navbarContainer.innerHTML = html;
                console.log("✅ Navbar carregado e inserido no DOM.");
            } else {
                console.error("❌ Elemento #navbar-container não encontrado no DOM.");
            }
        })
        .catch(error => {
            console.error('Erro catastrófico ao carregar o navbar:', error);
            mostrarMensagem('danger', 'Não foi possível carregar o menu de navegação.');
        });
}

function alternarTema() {
    const isDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('tema', isDark ? 'dark' : 'light');
    console.log(`DEBUG: Tema alterado para: ${isDark ? 'dark' : 'light'}`);
    const navbar = document.querySelector('.navbar-superior');
    if (navbar) {
        navbar.classList.toggle('navbar-dark', isDark);
        navbar.classList.toggle('navbar-light', !isDark);
    }
}

function adjustMainContentPadding() {
    const navbarSuperior = document.querySelector('.navbar-superior');
    const mainContent = document.getElementById('main-content');
    if (navbarSuperior && mainContent) {
        mainContent.style.paddingTop = `${navbarSuperior.offsetHeight}px`;
    }
}

// --- Lógica de Inicialização e Bind de Eventos ---
document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ DOM completamente carregado. Iniciando scripts.");

    if (document.getElementById('navbar-container')) {
        loadNavbar();
    }

    adjustMainContentPadding();
    const mainContentInitial = document.getElementById("main-content");
    if (mainContentInitial) {
        updateButtonStates(mainContentInitial);
    }

    document.body.addEventListener("click", async (e) => {
        const logoutLink = e.target.closest('#logout-link-superior');
        if (logoutLink) {
            e.preventDefault();
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = logoutLink.href;
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = getCSRFToken();
            form.appendChild(csrfInput);
            document.body.appendChild(form);
            form.submit();
            return;
        }

        const themeButton = e.target.closest('#btn-alternar-tema-superior');
        if (themeButton) {
            e.preventDefault();
            alternarTema();
            return;
        }

        const ajaxLink = e.target.closest(".ajax-link");
        if (ajaxLink && !ajaxLink.hasAttribute('data-bs-toggle')) {
            e.preventDefault();
            loadAjaxContent(ajaxLink.href);
        }

        const btnEditar = e.target.closest('#btn-editar');
        if (btnEditar && !btnEditar.disabled) {
            e.preventDefault();
            const href = btnEditar.getAttribute('data-href');
            if(href) loadAjaxContent(href);
        }

        const btnExcluir = e.target.closest('#btn-excluir');
        if (btnExcluir && !btnExcluir.disabled) {
            e.preventDefault();
            const mainContent = document.getElementById("main-content");
            const identificadorTela = mainContent ? mainContent.querySelector("#identificador-tela[data-seletor-checkbox]") : null;
            if (!identificadorTela) return;
            
            const selectedItems = Array.from(mainContent.querySelectorAll(identificadorTela.dataset.seletorCheckbox)).filter(cb => cb.checked);
            if (selectedItems.length === 0) return;

            const entidadeSingular = identificadorTela.dataset.entidadeSingular || 'item';
            const entidadePlural = identificadorTela.dataset.entidadePlural || 'itens';

            const result = await Swal.fire({
                title: 'Tem certeza?',
                text: `Você realmente deseja excluir ${selectedItems.length} ${selectedItems.length > 1 ? entidadePlural : entidadeSingular} selecionado(s)?`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Sim, excluir!',
                cancelButtonText: 'Cancelar'
            });

            if (result.isConfirmed) {
                const ids = selectedItems.map(cb => cb.value);
                const url = identificadorTela.dataset.urlExcluir;
                fetchWithCreds(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ids: ids })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.sucesso || data.success) {
                        mostrarMensagem('success', data.mensagem || data.message);
                        loadAjaxContent(window.location.pathname);
                    } else {
                        mostrarMensagem('danger', data.mensagem || data.message || 'Erro desconhecido.');
                    }
                })
                .catch(error => {
                    console.error('Erro na exclusão:', error);
                    mostrarMensagem('danger', 'Erro de comunicação ao tentar excluir.');
                });
            }
        }
    });

    document.body.addEventListener("submit", e => {
        const form = e.target.closest(".ajax-form");
        if (!form || form.dataset.skipGlobal === '1') return; // ⟵ ignore this form
        if (form) { // This 'if (form)' is now redundant but kept for minimal change
            e.preventDefault();
            const apiUrl = form.getAttribute("data-api-url") || form.action;
            const method = form.method;
            const formData = new FormData(form);

            fetchWithCreds(apiUrl, { method, body: formData })
                .then(async (response) => {
                    if (response.status === 401) {
                        const data = await response.json().catch(() => ({}));
                        window.location.href = data.redirect_url || `${LOGIN_URL}?next=${encodeURIComponent(window.location.pathname)}`;
                        throw new Error('Sessão expirada.');
                    }
                    if (response.redirected) {
                        window.location.href = response.url;
                        throw new Error('Redirecionado para login.');
                    }
                    const ct = response.headers.get('content-type') || '';
                    if (ct.includes('text/html')) {
                        const html = await response.text();
                        if (isLikelyLoginHTML(html)) {
                            window.location.href = `${LOGIN_URL}?next=${encodeURIComponent(window.location.pathname)}`;
                            throw new Error('Login requerido.');
                        }
                        throw new Error('HTML inesperado.');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        document.dispatchEvent(new CustomEvent("ajaxFormSuccess", { detail: { form, responseJson: data } }));
                    }
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    } else if (data.message || data.mensagem) {
                        const messageText = data.message || data.mensagem;
                        const messageType = data.success ? "success" : "danger";
                        mostrarMensagem(messageType, messageText);
                    }
                })
                .catch(error => {
                    if (error.message !== 'Sessão expirada.' && error.message !== 'Redirecionado para login.' && error.message !== 'Login requerido.') {
                        console.error("❌ Erro na submissão do formulário AJAX:", error);
                        mostrarMensagem("danger", error.message || "Ocorreu um erro de comunicação.");
                    }
                });
        }
    });

    window.addEventListener("popstate", e => {
        if (e.state && e.state.ajaxUrl) {
            loadAjaxContent(e.state.ajaxUrl);
        }
    });

    

    document.addEventListener("ajaxContentLoaded", (event) => {
        adjustMainContentPadding();
        const mainContent = document.getElementById("main-content");
        if (mainContent) {
            updateButtonStates(mainContent);
        }
    });
});

// === GERENCIAR CURVAS: bootstrap da página ===
function initGerenciarCurvas() {
  const raiz = document.querySelector('#gerenciar-curvas[data-page="gerenciar-curvas"]');
  if (!raiz || raiz.dataset.bound === '1') return;
  raiz.dataset.bound = '1';

  const q = (sel, ctx = document) => ctx.querySelector(sel);
  const qa = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));
  const toast = (type, text) => {
    if (typeof window.mostrarMensagem === 'function') window.mostrarMensagem(type, text);
    else console.log(`[${type.toUpperCase()}] ${text}`);
  };
  const toJSONorText = async (resp) => {
    const ct = resp.headers.get('content-type') || '';
    if (ct.includes('application/json')) return resp.json();
    return resp.text();
  };
  const setDisabled = (el, disabled = true) => { if (el) el.disabled = disabled; };

  const endpointBaseCurva = raiz.dataset.endpointCurvaBase || '/producao/api/curva/';
  const endpointSufixoDet = raiz.dataset.endpointDetalheSufixo || 'detalhes/';

  const listaCurvas = q('#lista-curvas', raiz);
  const formCurva = q('#form-curva', raiz);
  const formDetalhe = q('#form-ponto-crescimento', raiz);
  const inputCurvaId = q('#curva-id', raiz);
  const inputDetalheId = q('#detalhe-id', raiz);
  const tabBtnPonto = q('#ponto-crescimento-tab', raiz);
  const tabelaBody = q('#tabela-detalhes-body', raiz);
  const btnNovaCurva = q('#btn-nova-curva', raiz);
  const btnLimparCurva = q('[data-action="limpar-curva"]', formCurva);
  const btnLimparDetalhe = q('[data-action="limpar-detalhe"]', formDetalhe);

  function habilitarAbaPonto(habilitar = true) {
    if (!tabBtnPonto) return;
    tabBtnPonto.disabled = !habilitar;
    tabBtnPonto.classList.toggle('disabled', !habilitar);
    tabBtnPonto.setAttribute('aria-disabled', (!habilitar).toString());
  }
  function abrirAbaPonto() {
    if (!tabBtnPonto) return;
    new bootstrap.Tab(tabBtnPonto).show();
  }

  function limparTabela() {
    tabelaBody.innerHTML = `<tr data-empty="true"><td colspan="8" class="text-center text-muted">Selecione uma curva para ver ou adicionar detalhes.</td></tr>`;
  }
  function limparFormCurva(keepId = false) {
    if (!formCurva) return;
    if (!keepId) inputCurvaId.value = '';
    qa('input, select, textarea', formCurva).forEach(el => {
      if (el === inputCurvaId) return;
      if (el.type === 'checkbox' || el.type === 'radio') el.checked = false;
      else if (el.tagName === 'SELECT') el.selectedIndex = 0;
      else el.value = '';
    });
  }
  function limparFormDetalhe(keepId = false) {
    if (!formDetalhe) return;
    if (!keepId) inputDetalheId.value = '';
    qa('input, select, textarea', formDetalhe).forEach(el => {
      if (el === inputDetalheId) return;
      if (el.type === 'checkbox' || el.type === 'radio') el.checked = false;
      else if (el.tagName === 'SELECT') el.selectedIndex = 0;
      else el.value = '';
    });
  }

  function renderLinhaDetalheJSON(d) {
    const tr = document.createElement('tr');
    tr.setAttribute('data-id', d.id);
    tr.innerHTML = `
      <td>${d.periodo_semana ?? ''}</td>
      <td>${d.peso_inicial ?? ''}</td>
      <td>${d.peso_final ?? ''}</td>
      <td>${d.ganho_de_peso ?? ''}</td>
      <td>${d.racao_nome ?? d.racao ?? ''}</td>
      <td>${d.numero_tratos ?? ''}</td>
      <td>${d.gpd ?? ''}</td>
      <td>${d.tca ?? ''}</td>
    `;
    return tr;
  }

  function popularTelaComCurva(payload) {
    const c = payload.curva || {};
    inputCurvaId.value = c.id ?? '';
    const map = {
      'id_nome': c.nome, 'id_especie': c.especie, 'id_rendimento_perc': c.rendimento_perc,
      'id_trato_perc_curva': c.trato_perc_curva, 'id_peso_pretendido': c.peso_pretendido,
      'id_trato_sabados_perc': c.trato_sabados_perc, 'id_trato_domingos_perc': c.trato_domingos_perc,
      'id_trato_feriados_perc': c.trato_feriados_perc,
    };
    Object.entries(map).forEach(([id, val]) => { if (q(`#${id}`, formCurva)) q(`#${id}`, formCurva).value = (val ?? ''); });
    habilitarAbaPonto(true);
    const detalhes = Array.isArray(payload.detalhes) ? payload.detalhes : [];
    tabelaBody.innerHTML = '';
    if (!detalhes.length) {
      limparTabela();
    } else {
      const frag = document.createDocumentFragment();
      detalhes.forEach(d => frag.appendChild(renderLinhaDetalheJSON(d)));
      tabelaBody.appendChild(frag);
    }
    limparFormDetalhe(false);
  }

  async function carregarCurva(curvaId) {
    if (!curvaId) return;
    try {
      const url = `${endpointBaseCurva}${curvaId}/${endpointSufixoDet}`;
      const resp = await fetchWithCreds(url, { method: 'GET' });
      if (!resp.ok) throw new Error('Falha ao carregar a curva.');
      const data = await resp.json();
      popularTelaComCurva(data);
      toast('success', `Curva '${data.curva.nome}' carregada.`);
    } catch (err) {
      toast('danger', err.message || 'Erro ao carregar a curva.');
      limparTabela();
    }
  }

  if (listaCurvas) {
    listaCurvas.addEventListener('click', (ev) => {
      const li = ev.target.closest('li.list-group-item[data-id]');
      if (!li) return;
      qa('li.list-group-item', listaCurvas).forEach(x => x.classList.remove('active'));
      li.classList.add('active');
      carregarCurva(li.dataset.id);
    });
  }

  if (btnNovaCurva) {
    btnNovaCurva.addEventListener('click', () => {
      qa('li.list-group-item', listaCurvas).forEach(x => x.classList.remove('active'));
      limparFormCurva(false); limparFormDetalhe(false); limparTabela(); habilitarAbaPonto(false);
      toast('info', 'Preencha o cabeçalho e salve para liberar os períodos.');
    });
  }

  if (btnLimparCurva) btnLimparCurva.addEventListener('click', () => limparFormCurva(true));
  if (btnLimparDetalhe) btnLimparDetalhe.addEventListener('click', () => limparFormDetalhe(false));

  formCurva?.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const curvaId = inputCurvaId.value?.trim();
    const isNovo = !curvaId;
    const url = isNovo ? endpointBaseCurva : `${endpointBaseCurva}${curvaId}/`;
    const fd = new FormData(formCurva);
    try {
      setDisabled(formCurva.querySelector('[type="submit"]'), true);
      const resp = await fetchWithCreds(url, { method: 'POST', body: fd });
      const data = await toJSONorText(resp);
      if (!resp.ok || (data && data.success === false)) throw new Error((data && (data.message || data.error)) || 'Erro ao salvar a curva.');
      if (isNovo) { // Branch for new curve creation
        const novoId = (data && (data.id || data.curva_id || data.pk)) || null;
        if (!novoId) { // If ID not received
          toast('warning', 'Curva criada, mas não recebi o ID. Recarregue a lista se necessário.');
        } else { // If ID received, add to list
          inputCurvaId.value = String(novoId);
          habilitarAbaPonto(true);
          toast('success', 'Curva criada. Agora adicione os períodos.');

          // Adiciona o novo item à lista lateral
          const li = document.createElement('li');
          li.className =
            'list-group-item list-group-item-action d-flex align-items-center justify-content-between';
          li.dataset.id = String(novoId);
          li.dataset.name = data.curva_nome || 'Sem nome';
          li.style.cursor = 'pointer';
          li.innerHTML =
            `<span class="texto-truncado">${li.dataset.name}</span>` +
            `<i class="fas fa-chevron-right small text-muted"></i>`;
          document.querySelector('#lista-curvas')?.appendChild(li);
        }
      } else { // This is the ELSE branch for if (isNovo) - meaning it's an update
        toast('success', (data && data.message) || 'Cabeçalho da curva salvo.');
        // Atualiza o nome na lista lateral
        const li = listaCurvas.querySelector(`li[data-id="${curvaId}"]`);
        if (li && data.curva_nome) {
          li.dataset.name = data.curva_nome;
          li.innerHTML =
            `<span class="texto-truncado">${data.curva_nome}</span>` +
            `<i class="fas fa-chevron-right small text-muted"></i>`;
        }
      }
    } catch (err) { toast('danger', err.message || 'Falha ao salvar a curva.');
    } finally { setDisabled(formCurva.querySelector('[type="submit"]'), false); }
  });

  tabelaBody?.addEventListener('click', async (ev) => {
    const tr = ev.target.closest('tr[data-id]');
    if (!tr) return;
    const curvaId = inputCurvaId.value?.trim();
    const detalheId = tr.getAttribute('data-id');
    if (!curvaId || !detalheId) return;
    try {
      const url = `${endpointBaseCurva}${curvaId}/${endpointSufixoDet}${detalheId}/`;
      const resp = await fetchWithCreds(url, { method: 'GET' });
      if (!resp.ok) throw new Error('Falha ao carregar o detalhe.');
      const d = await resp.json();
      inputDetalheId.value = d.id ?? detalheId;
      const map = {
        'id_periodo_semana': d.periodo_semana, 'id_periodo_dias': d.periodo_dias, 'id_peso_inicial': d.peso_inicial,
        'id_peso_final': d.peso_final, 'id_ganho_de_peso': d.ganho_de_peso, 'id_numero_tratos': d.numero_tratos,
        'id_hora_inicio': d.hora_inicio, 'id_arracoamento_biomassa_perc': d.arracoamento_biomassa_perc,
        'id_mortalidade_presumida_perc': d.mortalidade_presumida_perc, 'id_racao': d.racao, 'id_gpd': d.gpd, 'id_tca': d.tca
      };
      Object.entries(map).forEach(([id, val]) => { if (q(`#${id}`, formDetalhe)) q(`#${id}`, formDetalhe).value = (val ?? ''); });
      abrirAbaPonto();
    } catch (err) { toast('danger', err.message || 'Erro ao carregar o detalhe.'); }
  });

  formDetalhe?.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const curvaId = inputCurvaId.value?.trim();
    const detalheId = inputDetalheId.value?.trim();
    if (!curvaId) { toast('warning', 'Salve o cabeçalho da curva antes.'); return; }
    const isNovo = !detalheId;
    const url = isNovo ? `${endpointBaseCurva}${curvaId}/${endpointSufixoDet}` : `${endpointBaseCurva}${curvaId}/${endpointSufixoDet}${detalheId}/`;
    const fd = new FormData(formDetalhe);
    try {
      setDisabled(formDetalhe.querySelector('[type="submit"]'), true);
      const resp = await fetchWithCreds(url, { method: 'POST', body: fd });
      const data = await toJSONorText(resp);
      if (!resp.ok || (data && data.success === false)) throw new Error((data && (data.message || data.error)) || 'Erro ao salvar o detalhe.');
      if (data && data.periodo) {
        const d = data.periodo;
        const trNova = renderLinhaDetalheJSON(d);
        if (!isNovo) {
          const alvo = tabelaBody.querySelector(`tr[data-id="${d.id || detalheId}"]`);
          if (alvo) alvo.replaceWith(trNova);
        } else {
          const empty = tabelaBody.querySelector('tr[data-empty="true"]');
          if (empty) empty.remove();
          tabelaBody.appendChild(trNova);
        }
      }
      if (isNovo) { limparFormDetalhe(false); toast('success', (data && data.message) || 'Período adicionado.');
      } else toast('success', (data && data.message) || 'Período atualizado.');
    } catch (err) { toast('danger', err.message || 'Falha ao salvar o detalhe.');
    } finally { setDisabled(formDetalhe.querySelector('[type="submit"]'), false); }
  });

  //  Busca dinâmica robusta (delegação + sem recarregar ao pressionar Enter)
  (function bindBuscaDinamica() {
    const listaCurvas = raiz.querySelector('#lista-curvas');
    if (!listaCurvas) return;

    function filtrar() {
      const search = raiz.querySelector('#search-curva');
      const filtro = (search?.value || '').trim().toUpperCase();
      Array.from(listaCurvas.querySelectorAll('li.list-group-item')).forEach(li => {
        const txt = ((li.dataset.name || li.textContent) || '').toUpperCase();
        li.style.display = txt.includes(filtro) ? '' : 'none';
      });
    }

    // Delegação: reage a qualquer #search-curva que estiver no DOM
    raiz.addEventListener('input', (e) => {
      if (e.target && e.target.id === 'search-curva') filtrar();
    });

    // Evita submit/reload ao apertar Enter dentro do campo de busca
    raiz.addEventListener('keydown', (e) => {
      if (e.target && e.target.id === 'search-curva' && e.key === 'Enter') {
        e.preventDefault();
      }
    });

    // Primeiro filtro (caso haja valor vindo de autofill)
    filtrar();
  })();
}

// Inicializa o módulo em ambos os cenários: carga inicial e carga via AJAX.
document.addEventListener("DOMContentLoaded", initGerenciarCurvas);
document.addEventListener("ajaxContentLoaded", initGerenciarCurvas);

// === GERENCIAR TANQUES ===
function initGerenciarTanques() {
  const raiz  = document.querySelector('#gerenciar-tanques[data-page="gerenciar-tanques"]');
  if (!raiz) return;

  const form  = raiz.querySelector('#form-tanque');
  const lista = raiz.querySelector('#lista-tanques');

  const inputId = raiz.querySelector('#tanque-id'); // hidden (real id p/ POST)

  // campos de exibição somente-leitura
  const elIdVis       = raiz.querySelector('#id_id');
  const elDataCriacao = raiz.querySelector('#id_data_criacao');

  // dimensões (editáveis)
  const elLarg = raiz.querySelector('#id_largura');
  const elComp = raiz.querySelector('#id_comprimento');
  const elProf = raiz.querySelector('#id_profundidade');

  // calculados (readonly na UI)
  const elArea   = raiz.querySelector('#id_metro_quadrado');
  const elVolume = raiz.querySelector('#id_metro_cubico');
  const elHa     = raiz.querySelector('#id_ha');

  // busca e botões
  const search = raiz.querySelector('#search-tanque, [data-role="busca-tanque"]');
  const btnNovo = raiz.querySelector('#btn-novo-tanque,[data-action="novo-tanque"]');
  const btnSalvar = raiz.querySelector('[data-action="salvar-tanque"]');

  // endpoints
  const API_BASE = '/producao/api/tanques/';

  // ---------- helpers ----------
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
    if (elArea)   elArea.value   = formatBR(r.area,   2);
    if (elVolume) elVolume.value = formatBR(r.volume, 3);
    if (elHa)     elHa.value     = formatBR(r.ha,     4);
  }

  function setBR(el, val, dec) {
    if (!el) return;
    if (val == null || val === '') { el.value = ''; return; }
    el.value = formatBR(toNumLocale(val), dec);
  }

  function resetFormTanque(clearId=true) {
    if (!form) return;
    if (clearId && inputId) inputId.value = '';

    Array.from(form.querySelectorAll('input,select,textarea')).forEach(el=>{
      // preserva somente-leitura/disabled
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
    const url = `${API_BASE}${id}/`;
    const resp = await fetchWithCreds(url);
    if (!resp.ok) { alert('Falha ao carregar tanque'); return; }
    const d = await resp.json();

    // popula hidden real
    if (inputId) inputId.value = d.id;

    // somente leitura de exibição
    if (elIdVis)       { elIdVis.value = String(d.id || ''); elIdVis.readOnly = true; elIdVis.disabled = true; }
    if (elDataCriacao) { elDataCriacao.value = formatDateTimeBRsql(d.data_criacao); elDataCriacao.readOnly = true; elDataCriacao.disabled = true; }

    // dimensões com vírgula
    setBR(elLarg, d.largura, 2);
    setBR(elComp, d.comprimento, 2);
    setBR(elProf, d.profundidade, 2);

    // outros campos comuns
    const elNome = raiz.querySelector('#id_nome');
    if (elNome) elNome.value = d.nome || '';

    const elSeq = raiz.querySelector('#id_sequencia');
    if (elSeq) elSeq.value = (d.sequencia ?? '');

    const elTag = raiz.querySelector('#id_tag_tanque');
    if (elTag) elTag.value = d.tag_tanque || '';

    // selects (usar value por id)
    const selUnid = raiz.querySelector('#id_unidade');
    if (selUnid) selUnid.value = d.unidade_id || d.unidade || '';

    const selFase = raiz.querySelector('#id_fase');
    if (selFase) selFase.value = d.fase_id || d.fase || '';

    const selTipo = raiz.querySelector('#id_tipo_tanque');
    if (selTipo) selTipo.value = d.tipo_tanque_id || d.tipo_tanque || '';

    const selLinha = raiz.querySelector('#id_linha_producao');
    if (selLinha) selLinha.value = d.linha_producao_id || d.linha_producao || '';

    const selMalha = raiz.querySelector('#id_malha');
    if (selMalha) selMalha.value = d.malha_id || d.malha || '';

    const selStatus = raiz.querySelector('#id_status_tanque');
    if (selStatus) selStatus.value = d.status_tanque_id || d.status_tanque || '';
    const elAtivo = raiz.querySelector('#id_ativo');
    if (elAtivo) {
        elAtivo.value = (String(d.ativo) === '1' || d.ativo === true) ? 'True' : 'False';
    }

    // calculados: preferir cálculo local
    recalcDimensoes();
  }

  async function salvarTanque() {
    if (!form) return;

    // revalida e garante calculados em ponto no POST
    recalcDimensoes();
    const r = computeFromInputs();

    const fd = new FormData(form);

    // remove id/data_criacao visuais se por acaso tiverem name
    fd.delete('id');
    fd.delete('data_criacao');

    // força calculados (padrão de names – ajuste se seus names forem outros)
    fd.set( (elArea?.name   || 'metro_quadrado'), r.area.toFixed(2) );
    fd.set( (elVolume?.name || 'metro_cubico'),   r.volume.toFixed(3) );
    fd.set( (elHa?.name     || 'ha'),             r.ha.toFixed(4) );

    const id = (inputId?.value || '').trim();
    const url = id ? `${API_BASE}${id}/atualizar/` : API_BASE; // POST em ambos

    const btn = btnSalvar || form.querySelector('[type="submit"]');
    btn && (btn.disabled = true);
    try {
      const resp = await fetchWithCreds(url, { method:'POST', body: fd });
      const ct = resp.headers.get('content-type') || '';
      if (!ct.includes('json')) {
        const body = await resp.text().catch(()=> '');
        throw new Error(`Servidor retornou ${resp.status} ${resp.statusText}.`);
      }
      const data = await resp.json();
      if (!resp.ok || data.success === false) {
        throw new Error(data.message || 'Falha ao salvar.');
      }

      // atualiza/insere na lista
      const nome = form.querySelector('#id_nome')?.value || 'Sem nome';
      if (!id && (data.id || data.pk)) {
        const novoId = String(data.id || data.pk);
        if (inputId) inputId.value = novoId;

        const li = document.createElement('li');
        li.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
        li.dataset.id = novoId;
        li.dataset.name = nome;
        li.innerHTML = `<span class="texto-truncado">${nome}</span><i class="fas fa-chevron-right small text-muted"></i>`;
        lista?.appendChild(li);
      } else if (id) {
        const li = lista?.querySelector(`li[data-id="${id}"]`);
        if (li) { li.dataset.name = nome; li.querySelector('.texto-truncado')?.replaceChildren(document.createTextNode(nome)); }
      }

      mostrarMensagem('success', data.message || 'Salvo com sucesso.');
    } catch (err) {
      mostrarMensagem('danger', err.message || 'Erro ao salvar.');
    } finally {
      btn && (btn.disabled = false);
    }
  }

  // ---------- binds ----------
  // recalcular em tempo real
  [elLarg, elComp, elProf].forEach(el=>{
    el?.addEventListener('input', recalcDimensoes);
    el?.addEventListener('change', recalcDimensoes);
  });
  recalcDimensoes();

  // clique na lista
  lista?.addEventListener('click', (e)=>{
    const li = e.target.closest('li.list-group-item');
    if (!li) return;
    lista.querySelectorAll('li.list-group-item.active').forEach(x=>x.classList.remove('active'));
    li.classList.add('active');
    carregarTanque(li.dataset.id);
  });

  // busca dinâmica
  (function bindBuscaTanques(){
    if (!lista) { console.log("DEBUG: Lista de tanques não encontrada."); return; }
    if (!search) { console.log("DEBUG: Campo de busca não encontrado."); return; }
    
    console.log("DEBUG: bindBuscaTanques inicializado.");

    function filtrar(){
      const filtro = (search.value || '').trim().toUpperCase();
      console.log("DEBUG: Filtro atual:", filtro);
      lista.querySelectorAll('li.list-group-item').forEach(li=>{
        const txt = ((li.getAttribute('data-name') || li.textContent) || '').toUpperCase();
        const isVisible = txt.includes(filtro);
        li.style.display = isVisible ? '' : 'none';
        // Toggle d-flex class to ensure visibility is correctly applied
        if (isVisible) {
            li.classList.add('d-flex');
        } else {
            li.classList.remove('d-flex');
        }
        console.log("DEBUG: Item:", txt, " - Filtro:", filtro, " - isVisible:", isVisible, " - li.style.display (after set):", li.style.display, " - li.classList (after set):", li.classList.value, " - li.id:", li.id, " - li.dataset.id:", li.dataset.id);
      });
    }
    search.addEventListener('input', filtrar);
    search.addEventListener('keydown', (e)=> { if (e.key === 'Enter') e.preventDefault(); });
    filtrar(); // Initial filter in case of pre-filled search
  })();

  // botão novo
  btnNovo?.addEventListener('click', (e)=> {
    e.preventDefault();
    lista?.querySelectorAll('li.list-group-item.active').forEach(li=>li.classList.remove('active'));
    resetFormTanque(true);
  });

  // salvar
  btnSalvar?.addEventListener('click', (e)=> {
    e.preventDefault();
    salvarTanque();
  });

  // não autocarregar nada por padrão
  resetFormTanque(true);
}

// Inicializa os módulos em ambos os cenários: carga inicial e carga via AJAX.
document.addEventListener("DOMContentLoaded", () => {
    initGerenciarCurvas();
    initGerenciarTanques();
    initPovoamentoLotes();
});
document.addEventListener("ajaxContentLoaded", () => {
    initGerenciarCurvas();
    initGerenciarTanques();
    initPovoamentoLotes();
});

// === POVOAMENTO DE LOTES ===
function initPovoamentoLotes() {
    const page = document.querySelector('[data-page="povoamento-lotes"]');
    if (!page || page.dataset.initialized) return;
    page.dataset.initialized = "true";

    // --- Seletores de Elementos ---
    const tipoTanqueSelect = page.querySelector('[data-role="tipo-tanque"]');
    const curvaContainer = page.querySelector('[data-container="curva-crescimento"]');
    const tanqueSelect = page.querySelector('[data-role="tanque"]');
    const curvaSelect = page.querySelector('[data-role="curva-crescimento"]');
    const adicionarBtn = page.querySelector('[data-action="adicionar-linha"]');
    const processarBtn = page.querySelector('[data-action="processar"]');
    const listagemBody = page.querySelector('[data-container="listagem-body"]');
    const buscarBtn = page.querySelector('[data-action="buscar-historico"]');
    const historicoBody = page.querySelector('[data-container="historico-body"]');

    const DJANGO_CONTEXT = window.DJANGO_CONTEXT || {};

    // --- Funções Auxiliares ---
    const gerarGrupoOrigem = () => {
        const d = new Date();
        const mes = String(d.getMonth() + 1).padStart(2, '0');
        const ano = String(d.getFullYear()).slice(-2);
        return `LM${mes}${ano}`;
    };

    const atualizarOpcoesTanque = () => {
        const tipo = tipoTanqueSelect.value;
        const tanquesFiltrados = (DJANGO_CONTEXT.tanques || []).filter(t => {
            if (tipo === 'Tanque Vazio') {
                return !t.tem_lote_ativo && t.status_nome === 'livre';
            } else {
                return t.tem_lote_ativo;
            }
        });
        tanqueSelect.innerHTML = '<option value="">Selecione...</option>' + tanquesFiltrados.map(t => `<option value="${t.pk}">${t.nome}</option>`).join('');
        $(tanqueSelect).trigger('change');
    };

    const verificarLoteAtivo = async (tanqueId, linha) => {
        if (!tanqueId) return;
        const nomeLoteInput = linha.querySelector('[data-field="nome_lote"]');
        try {
            const response = await fetchWithCreds(`/producao/api/tanque/${tanqueId}/lote-ativo/`);
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    nomeLoteInput.value = data.lote.nome;
                    nomeLoteInput.readOnly = true;
                }
            } else {
                nomeLoteInput.value = '';
                nomeLoteInput.readOnly = false;
            }
        } catch (error) {
            console.error('Erro ao buscar lote ativo:', error);
            nomeLoteInput.value = '';
            nomeLoteInput.readOnly = false;
        }
    };

    const buscarHistorico = async () => {
        const dataInicial = page.querySelector('[data-filter="data_inicial"]').value;
        const dataFinal = page.querySelector('[data-filter="data_final"]').value;
        const url = new URL(window.location.origin + '/producao/api/povoamento/historico/');
        if (dataInicial) url.searchParams.append('data_inicial', dataInicial);
        if (dataFinal) url.searchParams.append('data_final', dataFinal);

        try {
            const response = await fetchWithCreds(url);
            const data = await response.json();
            if (data.success) {
                historicoBody.innerHTML = data.historico.map(h => `
                    <tr>
                        <td>${h.id}</td>
                        <td>${h.data}</td>
                        <td>${h.lote}</td>
                        <td>${h.tanque}</td>
                        <td>${h.quantidade}</td>
                        <td>${h.peso_medio}</td>
                        <td>${h.tipo_evento}</td>
                    </tr>
                `).join('');
            } else {
                mostrarMensagem('danger', data.message);
            }
        } catch (error) {
            mostrarMensagem('danger', 'Erro de comunicação ao buscar histórico.');
        }
    };

    // --- Lógica Principal ---
    const adicionarLinha = async () => {
        if (!tanqueSelect.value) { mostrarMensagem('warning', 'Selecione um tanque primeiro.'); return; }
        const linhaId = `row-${Date.now()}`;
        const faseOptions = (DJANGO_CONTEXT.fases || []).map(f => `<option value="${f.pk}">${f.nome}</option>`).join('');
        const linhaOptions = (DJANGO_CONTEXT.linhas || []).map(l => `<option value="${l.pk}">${l.nome}</option>`).join('');
        const novaLinhaHTML = `
            <tr id="${linhaId}" data-tanque-id="${tanqueSelect.value}" data-curva-id="${curvaSelect.value}">
                <td><button class="btn btn-danger btn-sm" data-action="desfazer">X</button></td>
                <td>${tanqueSelect.options[tanqueSelect.selectedIndex].text}</td>
                <td>${gerarGrupoOrigem()}</td>
                <td>${curvaSelect.options[curvaSelect.selectedIndex].text}</td>
                <td><input type="date" class="form-control form-control-sm" data-field="data_lancamento" value="${new Date().toISOString().slice(0,10)}"></td>
                <td><input type="text" class="form-control form-control-sm" data-field="nome_lote"></td>
                <td><input type="number" class="form-control form-control-sm" data-field="quantidade" step="0.01"></td>
                <td><input type="number" class="form-control form-control-sm" data-field="peso_medio" step="0.01"></td>
                <td><select class="form-select form-select-sm select2-search-row" data-field="fase_id">${faseOptions}</select></td>
                <td><input type="text" class="form-control form-control-sm" data-field="tamanho"></td>
                <td><select class="form-select form-select-sm select2-search-row" data-field="linha_id">${linhaOptions}</select></td>
            </tr>
        `;
        listagemBody.insertAdjacentHTML('beforeend', novaLinhaHTML);
        const novaLinha = document.getElementById(linhaId);
        if (tipoTanqueSelect.value === 'Tanque Povoado') {
            await verificarLoteAtivo(tanqueSelect.value, novaLinha);
        }
        $(`#${linhaId} .select2-search-row`).select2();
    };

    const processarPovoamentos = async () => {
        const linhas = listagemBody.querySelectorAll('tr');
        if (linhas.length === 0) { mostrarMensagem('warning', 'Adicione pelo menos uma linha para processar.'); return; }
        const payload = {
            povoamentos: Array.from(linhas).map(linha => ({
                tipo_tanque: tipoTanqueSelect.value,
                curva_id: linha.dataset.curvaId,
                tanque_id: linha.dataset.tanqueId,
                grupo_origem: linha.cells[2].textContent,
                data_lancamento: linha.querySelector('[data-field="data_lancamento"]').value,
                nome_lote: linha.querySelector('[data-field="nome_lote"]').value,
                quantidade: linha.querySelector('[data-field="quantidade"]').value,
                peso_medio: linha.querySelector('[data-field="peso_medio"]').value,
                fase_id: linha.querySelector('[data-field="fase_id"]').value,
                tamanho: linha.querySelector('[data-field="tamanho"]').value,
                linha_id: linha.querySelector('[data-field="linha_id"]').value,
            }))
        };
        processarBtn.disabled = true;
        processarBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Processando...';
        try {
            const response = await fetchWithCreds('/producao/povoamento/', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            mostrarMensagem(response.ok ? 'success' : 'danger', result.message);
            if (response.ok) {
                listagemBody.innerHTML = '';
            }
        } catch (error) {
            mostrarMensagem('danger', 'Ocorreu um erro de comunicação com o servidor.');
        } finally {
            processarBtn.disabled = false;
            processarBtn.innerHTML = 'Processar Povoamentos';
        }
    };

    // --- Event Listeners ---
    tipoTanqueSelect.addEventListener('change', () => {
        curvaContainer.style.display = tipoTanqueSelect.value === 'Tanque Povoado' ? 'none' : '';
        atualizarOpcoesTanque();
    });
    adicionarBtn.addEventListener('click', adicionarLinha);
    processarBtn.addEventListener('click', processarPovoamentos);
    if(buscarBtn) buscarBtn.addEventListener('click', buscarHistorico);
    listagemBody.addEventListener('click', (e) => {
        if (e.target.dataset.action === 'desfazer') {
            e.target.closest('tr').remove();
        }
    });

    // --- Inicialização ---
    atualizarOpcoesTanque();
    $('.select2-search').select2();
}
document.addEventListener("ajaxContentLoaded", initGerenciarTanques);


// === POVOAMENTO DE LOTES ===
window.init_povoamento_lotes = function(DJANGO_CONTEXT) {
    const page = document.querySelector('[data-page="povoamento-lotes"]');
    if (!page || page.dataset.initialized) return;
    page.dataset.initialized = "true";

    // --- Seletores de Elementos ---
    const tipoTanqueSelect = page.querySelector('[data-role="tipo-tanque"]');
    const curvaContainer = page.querySelector('[data-container="curva-crescimento"]');
    const tanqueSelect = page.querySelector('[data-role="tanque"]');
    const curvaSelect = page.querySelector('[data-role="curva-crescimento"]');
    const adicionarBtn = page.querySelector('[data-action="adicionar-linha"]');
    const processarBtn = page.querySelector('[data-action="processar"]');
    const listagemBody = page.querySelector('[data-container="listagem-body"]');
    const buscarBtn = page.querySelector('[data-action="buscar-historico"]');
    const historicoBody = page.querySelector('[data-container="historico-body"]');

    // --- Funções Auxiliares ---
    const gerarGrupoOrigem = () => {
        const d = new Date();
        const mes = String(d.getMonth() + 1).padStart(2, '0');
        const ano = String(d.getFullYear()).slice(-2);
        return `LM${mes}${ano}`;
    };

    const atualizarOpcoesTanque = () => {
        const tipo = tipoTanqueSelect.value;
        const tanquesFiltrados = (DJANGO_CONTEXT.tanques || []).filter(t => {
            if (tipo === 'Tanque Vazio') {
                return !t.tem_lote_ativo && t.status_nome === 'livre';
            } else {
                return t.tem_lote_ativo;
            }
        });
        tanqueSelect.innerHTML = '<option value="">Selecione...</option>' + tanquesFiltrados.map(t => `<option value="${t.pk}">${t.nome}</option>`).join('');
        $(tanqueSelect).trigger('change');
    };

    const verificarLoteAtivo = async (tanqueId, linha) => {
        if (!tanqueId) return;
        const nomeLoteInput = linha.querySelector('[data-field="nome_lote"]');
        try {
            const response = await fetchWithCreds(`/producao/api/tanque/${tanqueId}/lote-ativo/`);
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    nomeLoteInput.value = data.lote.nome;
                    nomeLoteInput.readOnly = true;
                }
            } else {
                nomeLoteInput.value = '';
                nomeLoteInput.readOnly = false;
            }
        } catch (error) {
            console.error('Erro ao buscar lote ativo:', error);
            nomeLoteInput.value = '';
            nomeLoteInput.readOnly = false;
        }
    };

    const buscarHistorico = async () => {
        const dataInicial = page.querySelector('[data-filter="data_inicial"]').value;
        const dataFinal = page.querySelector('[data-filter="data_final"]').value;
        const url = new URL(window.location.origin + '/producao/api/povoamento/historico/');
        if (dataInicial) url.searchParams.append('data_inicial', dataInicial);
        if (dataFinal) url.searchParams.append('data_final', dataFinal);

        try {
            const response = await fetchWithCreds(url);
            const data = await response.json();
            if (data.success) {
                historicoBody.innerHTML = data.historico.map(h => `
                    <tr>
                        <td>${h.id}</td>
                        <td>${h.data}</td>
                        <td>${h.lote}</td>
                        <td>${h.tanque}</td>
                        <td>${h.quantidade}</td>
                        <td>${h.peso_medio}</td>
                        <td>${h.tipo_evento}</td>
                    </tr>
                `).join('');
            } else {
                mostrarMensagem('danger', data.message);
            }
        } catch (error) {
            mostrarMensagem('danger', 'Erro de comunicação ao buscar histórico.');
        }
    };

    // --- Lógica Principal ---
    const adicionarLinha = async () => {
        if (!tanqueSelect.value) { mostrarMensagem('warning', 'Selecione um tanque primeiro.'); return; }
        const linhaId = `row-${Date.now()}`;
        const faseOptions = (DJANGO_CONTEXT.fases || []).map(f => `<option value="${f.pk}">${f.nome}</option>`).join('');
        const linhaOptions = (DJANGO_CONTEXT.linhas || []).map(l => `<option value="${l.pk}">${l.nome}</option>`).join('');
        const novaLinhaHTML = `
            <tr id="${linhaId}" data-tanque-id="${tanqueSelect.value}" data-curva-id="${curvaSelect.value}">
                <td><button class="btn btn-danger btn-sm" data-action="desfazer">X</button></td>
                <td>${tanqueSelect.options[tanqueSelect.selectedIndex].text}</td>
                <td>${gerarGrupoOrigem()}</td>
                <td>${curvaSelect.options[curvaSelect.selectedIndex].text}</td>
                <td><input type="date" class="form-control form-control-sm" data-field="data_lancamento" value="${new Date().toISOString().slice(0,10)}"></td>
                <td><input type="text" class="form-control form-control-sm" data-field="nome_lote"></td>
                <td><input type="number" class="form-control form-control-sm" data-field="quantidade" step="0.01"></td>
                <td><input type="number" class="form-control form-control-sm" data-field="peso_medio" step="0.01"></td>
                <td><select class="form-select form-select-sm select2-search-row" data-field="fase_id">${faseOptions}</select></td>
                <td><input type="text" class="form-control form-control-sm" data-field="tamanho"></td>
                <td><select class="form-select form-select-sm select2-search-row" data-field="linha_id">${linhaOptions}</select></td>
            </tr>
        `;
        listagemBody.insertAdjacentHTML('beforeend', novaLinhaHTML);
        const novaLinha = document.getElementById(linhaId);
        if (tipoTanqueSelect.value === 'Tanque Povoado') {
            await verificarLoteAtivo(tanqueSelect.value, novaLinha);
        }
        $(`#${linhaId} .select2-search-row`).select2();
    };

    const processarPovoamentos = async () => {
        const linhas = listagemBody.querySelectorAll('tr');
        if (linhas.length === 0) { mostrarMensagem('warning', 'Adicione pelo menos uma linha para processar.'); return; }
        const payload = {
            povoamentos: Array.from(linhas).map(linha => ({
                tipo_tanque: tipoTanqueSelect.value,
                curva_id: linha.dataset.curvaId,
                tanque_id: linha.dataset.tanqueId,
                grupo_origem: linha.cells[2].textContent,
                data_lancamento: linha.querySelector('[data-field="data_lancamento"]').value,
                nome_lote: linha.querySelector('[data-field="nome_lote"]').value,
                quantidade: linha.querySelector('[data-field="quantidade"]').value,
                peso_medio: linha.querySelector('[data-field="peso_medio"]').value,
                fase_id: linha.querySelector('[data-field="fase_id"]').value,
                tamanho: linha.querySelector('[data-field="tamanho"]').value,
                linha_id: linha.querySelector('[data-field="linha_id"]').value,
            }))
        };
        processarBtn.disabled = true;
        processarBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Processando...';
        try {
            const response = await fetchWithCreds('/producao/povoamento/', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            mostrarMensagem(response.ok ? 'success' : 'danger', result.message);
            if (response.ok) {
                listagemBody.innerHTML = '';
            }
        } catch (error) {
            mostrarMensagem('danger', 'Ocorreu um erro de comunicação com o servidor.');
        } finally {
            processarBtn.disabled = false;
            processarBtn.innerHTML = 'Processar Povoamentos';
        }
    };

    // --- Event Listeners ---
    tipoTanqueSelect.addEventListener('change', () => {
        curvaContainer.style.display = tipoTanqueSelect.value === 'Tanque Povoado' ? 'none' : '';
        atualizarOpcoesTanque();
    });
    adicionarBtn.addEventListener('click', adicionarLinha);
    processarBtn.addEventListener('click', processarPovoamentos);
    if(buscarBtn) buscarBtn.addEventListener('click', buscarHistorico);
    listagemBody.addEventListener('click', (e) => {
        if (e.target.dataset.action === 'desfazer') {
            e.target.closest('tr').remove();
        }
    });

    // --- Inicialização ---
    $(function() {
        atualizarOpcoesTanque();
        $('.select2-search').select2();
    });
}

// Inicializa os módulos em ambos os cenários: carga inicial e carga via AJAX.
document.addEventListener("DOMContentLoaded", () => {
    initGerenciarCurvas();
    initGerenciarTanques();
});
document.addEventListener("ajaxContentLoaded", () => {
    initGerenciarCurvas();
    initGerenciarTanques();
});

// Listener de delegação de eventos unificado para checkboxes
document.body.addEventListener('change', function(e) {
    const mainContent = document.getElementById('main-content');
    // Apenas continua se o alvo for um checkbox dentro do conteúdo principal
    if (!mainContent || !e.target.matches('input[type="checkbox"]')) return;

    const identificadorTela = mainContent.querySelector("#identificador-tela");
    if (!identificadorTela) return;

    const seletorPai = identificadorTela.dataset.seletorPai;
    const seletorFilho = identificadorTela.dataset.seletorCheckbox;

    // Se não houver seletores de checkbox nesta tela, não faz nada.
    if (!seletorFilho) return;

    const paiCheckbox = seletorPai ? mainContent.querySelector(seletorPai) : null;
    const filhosCheckboxes = mainContent.querySelectorAll(seletorFilho);

    let isCheckboxRelevante = false;

    // Lógica 1: O clique foi no checkbox "Pai"?
    if (paiCheckbox && e.target === paiCheckbox) {
        isCheckboxRelevante = true;
        filhosCheckboxes.forEach(filho => {
            filho.checked = paiCheckbox.checked;
        });
    }

    // Lógica 2: O clique foi em um checkbox "Filho"?
    if (filhosCheckboxes && Array.from(filhosCheckboxes).includes(e.target)) {
        isCheckboxRelevante = true;
        if (paiCheckbox) {
            const total = filhosCheckboxes.length;
            const marcados = mainContent.querySelectorAll(`${seletorFilho}:checked`).length;

            if (marcados === 0) {
                paiCheckbox.checked = false;
                paiCheckbox.indeterminate = false;
            } else if (marcados === total) {
                paiCheckbox.checked = true;
                paiCheckbox.indeterminate = false;
            } else {
                paiCheckbox.checked = false;
                paiCheckbox.indeterminate = true;
            }
        }
    }
    
    // Lógica 3: Atualizar sempre o estado dos botões se um checkbox relevante foi alterado
    if (isCheckboxRelevante) {
        updateButtonStates(mainContent);
    }
});