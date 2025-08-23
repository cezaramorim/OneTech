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

function getCSRFToken() {
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
}

// URL de login (pode vir do <body data-login-url="..."> ou cai no padrão)
const LOGIN_URL = document.body?.dataset?.loginUrl || '/accounts/login/';

// fetch com cookies + cabeçalhos padrão (AJAX)
function fetchWithCreds(url, options = {}) {
  const opts = { credentials: 'same-origin', ...options };
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
    s.includes('id="login-page"') ||           // se você colocar no <body id="login-page">
    s.includes('data-page="login"');           // ou <body data-page="login">

  // Heurística mais forte: precisa ter form com action para /accounts/login E campos username+password
  const hasLoginAction = /<form[^>]+action=["'][^"']*\/accounts\/login\/?["'][^>]*>/i.test(s);
  const hasUsername = /\bname=["']username["']/i.test(s);
  const hasPassword = /\bname=["']password["']/i.test(s);

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
    if (!identificadorTela || !identificadorTela.dataset.seletorCheckbox) return;

    const itemCheckboxes = mainContent.querySelectorAll(identificadorTela.dataset.seletorCheckbox);
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
    
    const selectAllCheckbox = mainContent.querySelector('input[type="checkbox"][id^="selecionar-todas-"]');
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
            const identificadorTela = mainContent ? mainContent.querySelector("#identificador-tela") : null;
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
        if (form) {
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

    document.body.addEventListener("change", e => {
        const mainContent = document.getElementById("main-content");
        if (e.target.type === 'checkbox' && mainContent && mainContent.querySelector("#identificador-tela[data-seletor-checkbox]")) {
            updateButtonStates(mainContent);
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
      toast('success', 'Curva carregada.');
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
      if (isNovo) {
        const novoId = (data && (data.id || data.curva_id || data.pk)) || null;
        if (!novoId) toast('warning', 'Curva criada, mas não recebi o ID. Recarregue a lista se necessário.');
        else { inputCurvaId.value = String(novoId); habilitarAbaPonto(true); toast('success', 'Curva criada. Agora adicione os períodos.'); }
      } else toast('success', (data && data.message) || 'Cabeçalho da curva salvo.');
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

  const search = q('#search-curva', raiz);
  search?.addEventListener('input', () => {
    const filtro = (search.value || '').trim().toUpperCase();
    qa('li.list-group-item', listaCurvas).forEach(li => {
      const txt = (li.dataset.name || li.textContent || '').toUpperCase();
      li.style.display = txt.includes(filtro) ? '' : 'none';
    });
  });
}

// Inicializa o módulo em ambos os cenários: carga inicial e carga via AJAX.
document.addEventListener("DOMContentLoaded", initGerenciarCurvas);
document.addEventListener("ajaxContentLoaded", initGerenciarCurvas);
