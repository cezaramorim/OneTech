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

// URL de login (pode vir do <body data-login-url="...") ou cai no padrão)
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
  var raiz = document.querySelector('#gerenciar-tanques[data-page="gerenciar-tanques"]');
  if (!raiz || raiz.dataset.bound === '1') return;
  raiz.dataset.bound = '1';

  var endpointBase = (raiz.dataset.endpointBase || '/producao/api/tanque/').replace(/\/+$/, '/');
  var form = raiz.querySelector('#form-tanque');
  var inputId = raiz.querySelector('#tanque-id');
  var lista = raiz.querySelector('#lista-tanques');
  var salvarBtn = raiz.querySelector('#btn-salvar-tanque') || raiz.querySelector('[data-action="salvar-tanque"]') || (form ? form.querySelector('[type="submit"]') : null);

  var toast = function(t, m) { if (window.mostrarMensagem) mostrarMensagem(t, m); else console.log('[' + t + '] ' + m); };
  var setDisabled = function(el, d) { if (el) el.disabled = !!d; };

  // a) Helpers para formatação BR e data
  function formatBR(n, dec) {
    const v = (Number.isFinite(n) ? n : 0).toFixed(dec ?? 2);
    return v.replace('.', ','); // apenas vírgula na UI
  }

  // "2025-08-01 23:35:53.738408" -> Date local -> "dd/mm/aaaa HH:mm:ss"
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

  // --- util fetch com credenciais (from original) ---
  function apiFetch(url, opts) {
    opts = opts || {};
    var headers = new Headers(opts.headers || {});
    if (!headers.has('X-Requested-With')) headers.set('X-Requested-With', 'XMLHttpRequest');
    if ((opts.method || 'GET').toUpperCase() !== 'GET' && !headers.has('X-CSRFToken') && typeof getCSRFToken === 'function') {
      headers.set('X-CSRFToken', getCSRFToken());
    }
    opts.headers = headers;
    opts.credentials = 'same-origin';
    return fetch(url, opts).then(function(resp) {
      if (resp.status === 401) {
        return resp.json().catch(function() { return {}; }).then(function(data) {
          var login = (window.LOGIN_URL || '/accounts/login/') + '?next=' + encodeURIComponent(window.location.pathname);
          window.location.href = data.redirect_url || login;
          throw new Error('401');
        });
      }
      if (resp.redirected) {
        window.location.href = resp.url;
        throw new Error('redirect');
      }
      if (resp.status === 403) {
        toast('danger', 'Você não tem permissão para executar esta ação.');
        throw new Error('403');
      }
      return resp;
    });
  }

  // --- tenta /<id>/ e /<id>/atualizar/ para editar; / para criar (from original) ---
  function postTanqueSmart(id, fd) {
    var urls = id ? [endpointBase + id + '/atualizar/', endpointBase + id + '/'] : [endpointBase];
    var i = 0;
    function tentar() {
      var url = urls[i];
      return apiFetch(url, { method: 'POST', body: fd }).then(function(resp) {
        var ct = (resp.headers.get('content-type') || '').toLowerCase();
        var isJson = ct.indexOf('application/json') !== -1;
        if (resp.ok && isJson) {
          return { resp: resp, urlTried: url };
        }
        if ((resp.status === 405 || resp.status === 404 || !isJson) && i < urls.length - 1) {
          i++;
          return tentar();
        }
        return { resp: resp, urlTried: url };
      });
    }
    return tentar();
  }

  // ====== START OF USER PATCH ======

  // ====== CAMPOS CALCULADOS: Área (m²), Volume (m³), Hectares (ha) ======
  function pickField(selectors) {
    for (var i = 0; i < selectors.length; i++) {
      var el = form.querySelector(selectors[i]);
      if (el) return el;
    }
    return null;
  }

  // b) Pegar referências dos campos (ID/Data/Dimensões/Calculados)
  var elIdVis       = pickField(['#id_id', '#id_pk', '#tanque-id-display']);
  var elDataCriacao = pickField(['#id_data_criacao', '#id_criado_em']);

  var elLarg = pickField(['#id_largura', '#id_largura_m', '#id_largura_metros']);
  var elComp = pickField(['#id_comprimento', '#id_comprimento_m', '#id_comprimento_metros']);
  var elProf = pickField(['#id_profundidade', '#id_profundidade_m', '#id_profundidade_metros']);

  var elArea   = pickField(['#id_metro_quadrado', '#id_area_m2', '#id_area']);
  var elVolume = pickField(['#id_metro_cubico',   '#id_volume_m3', '#id_volume']);
  var elHa     = pickField(['#id_ha',             '#id_hectares_ha', '#id_hectares']);

  function toNumLocale(v) {
    if (v == null) return 0;
    v = String(v).trim();
    if (!v) return 0;

    // mantém apenas dígitos, vírgula, ponto e sinal
    v = v.replace(/[^\d,.\-]/g, '');

    const lastComma = v.lastIndexOf(',');
    const lastDot   = v.lastIndexOf('.');
    let decSep = null;

    if (lastComma === -1 && lastDot === -1) {
      decSep = null; // inteiro puro
    } else if (lastComma > lastDot) {
      decSep = ',';  // vírgula é o decimal
    } else {
      decSep = '.';  // ponto é o decimal
    }

    if (decSep) {
      const thouSep = decSep === ',' ? '.' : ',';
      // remove separadores de milhar
      v = v.split(thouSep).join('');
      // normaliza decimal para ponto
      v = v.replace(decSep, '.');
    }

    const n = parseFloat(v);
    return Number.isFinite(n) ? n : 0;
  }

  function format(v, dec) {
    var num = isFinite(v) ? v : 0;
    return num.toFixed(dec);
  }
  function computeFromInputs() {
    const L = toNumLocale(elLarg && elLarg.value);
    const C = toNumLocale(elComp && elComp.value);
    const P = toNumLocale(elProf && elProf.value);
    const area = L * C;        // m²
    const volume = area * P;   // m³
    const ha = area / 10000;   // ha
    return { L, C, P, area, volume, ha };
  }
  function recalcDimensoes() {
    if (!form) return;
    var r = computeFromInputs();
    if (elArea)   elArea.value   = formatBR(r.area,   2);
    if (elVolume) elVolume.value = formatBR(r.volume, 3);
    if (elHa)     elHa.value     = formatBR(r.ha,     4);
  }

  [elLarg, elComp, elProf].forEach(function(el) {
    if (!el) return;
    el.addEventListener('input', recalcDimensoes);
    el.addEventListener('change', recalcDimensoes);
  });

  // Helper para post (from user patch)
  function _postTanqueComFD(fd) {
    var id = (inputId && inputId.value ? inputId.value : '').trim();
    setDisabled(salvarBtn, true);
    return postTanqueSmart(id, fd).then(function(result) {
      var resp = result.resp;
      var ct = (resp.headers.get('content-type') || '').toLowerCase();
      if (resp.ok && ct.indexOf('application/json') !== -1) {
        return resp.json().then(function(data) {
          // --- success logic from original salvarTanque ---
          var nomeEl = form.querySelector('#id_nome');
          var nome = (nomeEl && nomeEl.value) ? nomeEl.value : 'Sem nome';
          if (!id && (data.id || data.pk)) {
            var novoId = String(data.id || data.pk);
            if (inputId) inputId.value = novoId;
            if (lista) {
              var li = document.createElement('li');
              li.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
              li.setAttribute('data-id', novoId);
              li.setAttribute('data-name', nome);
              li.innerHTML = '<span class="texto-truncado">' + nome + '</span><i class="fas fa-chevron-right small text-muted"></i>';
              lista.appendChild(li);
            }
          } else if (id && lista) {
            var liExist = lista.querySelector('li[data-id="' + id + '"]');
            if (liExist) {
              liExist.setAttribute('data-name', nome);
              var txt = liExist.querySelector('.texto-truncado');
              if (txt) txt.textContent = nome;
            }
          }
          // --- end of success logic ---
          toast('success', data.message || 'Salvo com sucesso.');
          setDisabled(salvarBtn, false);
          return data;
        });
      }
      return resp.text().then(function(txt) {
        console.error('DEBUG: Não-JSON ao salvar:', { url: result.urlTried, status: resp.status, body: txt.slice(0, 300) });
        toast('danger', 'Servidor retornou HTML em vez de JSON ao salvar.');
        setDisabled(salvarBtn, false);
        throw new Error('save-non-json');
      });
    }).catch(function(err) {
      setDisabled(salvarBtn, false);
      if (err && err.message !== 'save-non-json') toast('danger', err.message || 'Erro ao salvar.');
      throw err;
    });
  }

  // ====== AJUSTE NO salvarTanque: garantir que os 3 campos vão no FormData ======
  function salvarTanque() {
    if (!form) return;
    recalcDimensoes(); // Garante que a UI está com os valores calculados mais recentes

    const fd = new FormData(form);
    const r = computeFromInputs(); // Pega os valores puros (numéricos) dos inputs

    // Sobrepõe os valores de dimensão e calculados no FormData,
    // garantindo que eles usem PONTO como separador decimal para o backend.
    fd.set((elLarg?.name || 'largura'), r.L.toFixed(2));
    fd.set((elComp?.name || 'comprimento'), r.C.toFixed(2));
    fd.set((elProf?.name || 'profundidade'), r.P.toFixed(2));
    
    fd.set((elArea?.name   || 'metro_quadrado'), r.area.toFixed(2));
    fd.set((elVolume?.name || 'metro_cubico'),   r.volume.toFixed(3));
    fd.set((elHa?.name     || 'ha'),             r.ha.toFixed(4));

    // Garante que os aliases (nomes alternativos) também estão corretos
    fd.set('area_m2', r.area.toFixed(2));
    fd.set('volume_m3', r.volume.toFixed(3));
    fd.set('hectares_ha', r.ha.toFixed(4));

    // Remove campos visuais que não devem ser enviados
    fd.delete('id');
    fd.delete('data_criacao');

    return _postTanqueComFD(fd);
  }

  // ====== AJUSTE NO mapTanqueToForm: preencher e já recalcular ======
  function mapTanqueToForm(d) {
    if (!form || !d) return;

    // Etapa 1: Mapeamento direto da API para os campos do formulário.
    // Isso garante que todos os dados, incluindo largura, comprimento e profundidade, sejam populados.
    var mapa = {
      'id_nome': d.nome,
      'id_tag_tanque': d.tag_tanque,
      'id_sequencia': d.sequencia,
      'id_unidade': d.unidade,
      'id_linha_producao': d.linha_producao,
      'id_fase': d.fase,
      'id_tipo_tanque': d.tipo_tanque,
      'id_status_tanque': d.status_tanque,
      'id_malha': d.malha,
      'id_tipo_tela': d.tipo_tela,
      'id_largura': d.largura,           // Restaurado
      'id_comprimento': d.comprimento, // Restaurado
      'id_profundidade': d.profundidade // Restaurado
    };

    Object.keys(mapa).forEach(function(id) {
      var el = form.querySelector('#' + id);
      if (!el) return;
      var val = mapa[id];
      if (el.tagName === 'SELECT') {
        el.value = (val == null ? '' : String(val));
      } else {
        el.value = (val == null ? '' : val);
      }
    });

    var ativoEl = form.querySelector('#id_ativo');
    if (ativoEl) {
      if (ativoEl.type === 'checkbox') { ativoEl.checked = !!d.ativo; }
      else { ativoEl.value = d.ativo ? 'True' : 'False'; }
    }

    // Etapa 2: Popula os campos somente leitura de ID e Data de Criação.
    if (elIdVis) {
      elIdVis.value = (d.id != null ? String(d.id) : '');
      elIdVis.readOnly = true; elIdVis.disabled = true;
    }
    if (elDataCriacao) {
      // Popula o campo de data de criação usando o campo correto da API.
      elDataCriacao.value = formatDateTimeBRsql(d.data_criacao);
      elDataCriacao.readOnly = true; elDataCriacao.disabled = true;
    }

    // Etapa 3: Re-formata os campos de dimensão para exibir com vírgula (BR).
    function setBR(el, val, dec) {
      if (!el) return;
      if (val == null || val === '') { el.value = ''; return; }
      const num = toNumLocale(val);
      el.value = formatBR(Number.isFinite(num) ? num : toNumLocale(String(val)), dec);
    }
    setBR(elLarg, d.largura, 2);
    setBR(elComp, d.comprimento, 2);
    setBR(elProf, d.profundidade, 2);

    // Etapa 4: Calcula e exibe os campos derivados (Área, Volume, Hectares) com vírgula.
    const r = computeFromInputs();
    if (elArea)   elArea.value   = r.area   > 0 ? formatBR(r.area,   2) : formatBR(toNumLocale(d.metro_quadrado ?? d.area_m2 ?? d.area), 2);
    if (elVolume) elVolume.value = r.volume > 0 ? formatBR(r.volume, 3) : formatBR(toNumLocale(d.metro_cubico   ?? d.volume_m3 ?? d.volume), 3);
    if (elHa)     elHa.value     = r.ha     > 0 ? formatBR(r.ha,     4) : formatBR(toNumLocale(d.ha             ?? d.hectares_ha ?? d.hectares), 4);
  };

  // ====== END OF USER PATCH INTEGRATION ======

  // --- Submit do form (sem optional chaining) ---
  if (form) {
    form.addEventListener('submit', function(ev) {
      ev.preventDefault();
      salvarTanque();
    });
  }

  // --- Click do botão Salvar (fallback robusto) ---
  if (salvarBtn) {
    salvarBtn.addEventListener('click', function(ev) {
      ev.preventDefault();
      salvarTanque();
    });
  }

  // === busca dados do tanque e preenche o formulário ===
  function carregarTanque(id) {
    if (!id) return;
    return apiFetch(endpointBase + id + '/', { method: 'GET' })
      .then(function(resp) {
        if (!resp.ok) throw new Error('Falha ao carregar o tanque.');
        return resp.json();
      })
      .then(function(data) {
        if (inputId) inputId.value = String(data.id || id);
        mapTanqueToForm(data); // This now calls the patched version
        toast('success', 'Tanque carregado.');
      })
      .catch(function(err) {
        toast('danger', err.message || 'Erro ao carregar o tanque.');
      });
  }

  // === clique na lista: seleciona o item e carrega o form ===
  if (lista) {
    lista.addEventListener('click', function(e) {
      var li = e.target.closest('li.list-group-item[data-id]');
      if (!li) return;
      Array.prototype.forEach.call(lista.querySelectorAll('li.list-group-item'), function(x) {
        x.classList.remove('active');
      });
      li.classList.add('active');
      carregarTanque(li.getAttribute('data-id'));
    });
  }

  // === busca dinâmica da lista (#search-tanque) sem recarregar ===
  (function bindBuscaTanques() {
    var search = raiz.querySelector('#search-tanque');
    if (!search || !lista) return;

    function filtrar() {
      var filtro = (search.value || '').trim().toUpperCase();
      Array.prototype.forEach.call(lista.querySelectorAll('li.list-group-item'), function(li) {
        var txt = ((li.getAttribute('data-name') || li.textContent) || '').toUpperCase();
        li.style.display = txt.indexOf(filtro) !== -1 ? '' : 'none';
      });
    }

    search.addEventListener('input', filtrar);
    search.addEventListener('keydown', function(e) { if (e.key === 'Enter') e.preventDefault(); });
    filtrar();
  })();
}

// liga em carga inicial e via AJAX (igual às curvas)
document.addEventListener("DOMContentLoaded", initGerenciarTanques);
document.addEventListener("ajaxContentLoaded", initGerenciarTanques);