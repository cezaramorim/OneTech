// ============================================================================
// ARQUIVO scripts.js - ARQUITETURA AJAX REATORADA (COM BOTÕES DE AÇÃO)
// ============================================================================

// Aplica o tema salvo no localStorage (antes do paint)
const temaSalvo = localStorage.getItem("tema");
if (temaSalvo === "dark") {
  document.documentElement.classList.add("dark");
}
document.documentElement.classList.add("theme-ready");

// --- Funções de Utilidade Global ---

function getCSRFToken() {
  const c = document.cookie.split(';').find(x => x.trim().startsWith('csrftoken='));
  return c ? c.split('=')[1] : '';
}

function serializeFormToQuery(form) {
  return new URLSearchParams(new FormData(form)).toString();
}

function debounce(fn, delay = 350) {
  let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
}

function notify(type, msg) {
  if (window.mostrarMensagem) {
    window.mostrarMensagem(type, msg);
  } else {
    console[type === 'danger' || type === 'error' ? 'error' : 'log'](msg);
  }
}

const LOGIN_URL = document.body?.dataset?.loginUrl || '/accounts/login/';

async function fetchWithCreds(url, options = {}, acceptHeader) {
  const headers = { 'X-Requested-With': 'XMLHttpRequest', ...(options.headers || {}) };
  if (acceptHeader) headers['Accept'] = acceptHeader;
  const opts = { credentials: 'same-origin', ...options, headers };
  const method = (opts.method || 'GET').toUpperCase();
  if (method !== 'GET' && !headers['X-CSRFToken']) {
    headers['X-CSRFToken'] = getCSRFToken();
  }
  opts.headers = headers;
  const res = await fetch(url, opts);

  // Adiciona tratamento para 401 Unauthorized
  if (res.status === 401) {
    notify('error', 'Sessão expirada. Faça login novamente.');
    window.location.href = `${LOGIN_URL}?next=${encodeURIComponent(window.location.pathname)}`;
    return null; // Retorna null para interromper o fluxo
  }

  return res;
}

function isLikelyLoginHTML(html) {
  if (!html) return false;
  const s = html.toLowerCase();
  return s.includes('id="login-form"') || s.includes('data-page="login"');
}

function mostrarMensagem(type, message) {
    // Mapeia a tag 'error' do Django para a classe 'danger' do Bootstrap para estilização correta.
    if (type === 'error') {
        type = 'danger';
    }
    if (!window.Swal) { console.error("SweetAlert2 não encontrada."); return; }
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

function showFlashMessage() {
    const flashMessageData = sessionStorage.getItem('flashMessage');
    if (flashMessageData) {
        try {
            const { type, message } = JSON.parse(flashMessageData);
            mostrarMensagem(type, message);
        } catch (e) {
            console.error('Could not parse flash message:', e);
        }
        sessionStorage.removeItem('flashMessage');
    }
}

function loadNavbar() {
    fetchWithCreds('/accounts/get-navbar/', { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then(response => {
            if (!response.ok) {
                console.error(`❌ Falha ao buscar navbar. Status: ${response.status} ${response.statusText}`);
                throw new Error('Falha ao buscar navbar');
            }
            return response.text();
        })
        .then(html => {
            const navbarContainer = document.getElementById('navbar-container');
            if (navbarContainer) {
                navbarContainer.innerHTML = html;
            } else {
                // Silencioso em páginas que não têm o container, como a de login.
            }
        })
        .catch(error => {
            console.error('Erro catastrófico ao carregar o navbar:', error);
            notify('danger', 'Não foi possível carregar o menu de navegação.');
        });
}

function updateButtonStates(mainContent) {
    if (!mainContent) return;
    const identificadorTela = mainContent.querySelector("#identificador-tela");
    if (!identificadorTela) return;

    const seletorFilho = identificadorTela?.dataset.seletorCheckbox;
    if (!seletorFilho) return;

    const itemCheckboxes = mainContent.querySelectorAll(seletorFilho);
    const btnEditar = mainContent.querySelector('#btn-editar');
    const btnExcluir = mainContent.querySelector('#btn-excluir');
    const selectedItems = Array.from(itemCheckboxes).filter(cb => cb.checked);
    const hasSelection = selectedItems.length > 0;
    const hasSingleSelection = selectedItems.length === 1;

    if (btnEditar) {
        let canEdit = hasSingleSelection;
        let editId = null;
        if (hasSingleSelection) {
            editId = selectedItems[0].value;
        }

        btnEditar.disabled = !canEdit;
        btnEditar.classList.toggle('disabled', !canEdit);

        if (canEdit && editId) {
            const editUrlBase = identificadorTela.dataset.urlEditar;
            if (editUrlBase) {
                btnEditar.setAttribute('data-href', editUrlBase.replace('0', editId));
            }
        } else {
            btnEditar.removeAttribute('data-href');
        }
    }

    if (btnExcluir) {
        btnExcluir.disabled = !hasSelection;
        btnExcluir.classList.toggle('disabled', !hasSelection);
    }
    
    const seletorPai = identificadorTela.dataset.seletorPai;
    const paiCheckbox = seletorPai ? mainContent.querySelector(seletorPai) : null;
    if (paiCheckbox) {
        const total = itemCheckboxes.length;
        const marcados = selectedItems.length;
        if (marcados === 0) {
            paiCheckbox.checked = false;
            paiCheckbox.indeterminate = false;
        } else if (marcados === total && total > 0) {
            paiCheckbox.checked = true;
            paiCheckbox.indeterminate = false;
        } else {
            paiCheckbox.checked = false;
            paiCheckbox.indeterminate = true;
        }
    }
}

// --- Motor AJAX e Handlers de Resposta ---

async function submitAjaxForm(form) {
  let url = form.action || window.location.href;
  const method = (form.getAttribute('method') || 'GET').toUpperCase();

  const options = { method };
  if (method === 'GET' || method === 'HEAD') {
    const qs = serializeFormToQuery(form);
    const base = url.split('#')[0];
    url = qs ? `${base}${base.includes('?') ? '&' : '?'}${qs}` : base;
  } else {
    options.body = new FormData(form);
    options.headers = { ...(options.headers || {}), 'X-CSRFToken': getCSRFToken() };
  }

  const declaredType = (form.dataset.responseType || '').toLowerCase();
  const accept = declaredType === 'json'
    ? 'application/json, text/plain, */*'
    : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8';

  const res = await fetchWithCreds(url, options, accept);

  if (res.redirected && /\/accounts\/login\//.test(res.url)) {
    notify('error', 'Sessão expirada. Faça login novamente.');
    window.location.href = res.url;
    return null;
  }

  const ct = (res.headers.get('content-type') || '').toLowerCase();
  const isJson = declaredType === 'json' || ct.includes('application/json');

  if (!res.ok) {
    const errText = await res.text().catch(() => '');
    throw new Error(`HTTP ${res.status} ${res.statusText}: ${errText.slice(0, 300)}`);
  }

  return isJson ? res.json() : res.text();
}

function handleJsonFormResponse(form, data) {
  if (data.redirect_url) {
    window.location.assign(data.redirect_url);
    return;
  }
  if (data.html && form.dataset.targetContainer) {
    const container = document.querySelector(form.dataset.targetContainer);
    if (container) {
      container.innerHTML = data.html;
      document.dispatchEvent(new CustomEvent('ajaxContentLoaded', {
        detail: { screen: container.dataset.tela || container.dataset.page || '' }
      }));
    }
  }
  if (data.message) notify(data.success ? 'success' : 'error', data.message);
  if (data.reload) window.location.reload();
}

function handleHtmlFormResponse(form, html) {
  const targetSel = form.dataset.targetContainer || '#main-content';
  const container = document.querySelector(targetSel);
  if (container) {
    container.innerHTML = html;
    document.dispatchEvent(new CustomEvent('ajaxContentLoaded', {
      detail: { screen: container.dataset.tela || container.dataset.page || '' }
    }));
  } else {
    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    window.location.assign(url);
  }
}

function loadAjaxContent(url) {
  const mainContent = document.getElementById("main-content");
  if (!mainContent) {
    window.location.href = url;
    return;
  }

  fetchWithCreds(url, {}, 'text/html')
    .then(async (response) => {
      if (response === null) { // Check if fetchWithCreds already handled a redirect (e.g., 401)
        return null;
      }
      if (response.redirected && /\/accounts\/login\//.test(response.url)) {
        notify('error', 'Sessão expirada. Faça login novamente.');
        window.location.href = response.url;
        return null;
      }
      const html = await response.text();
      if (isLikelyLoginHTML(html)) {
        window.location.href = `${LOGIN_URL}?next=${encodeURIComponent(url)}`;
        return null;
      }
      return html;
    })
    .then((html) => {
      if (html == null) return;
      mainContent.innerHTML = html;
      history.pushState({ ajaxUrl: url }, "", url);
      document.dispatchEvent(new CustomEvent("ajaxContentLoaded", { detail: { url } }));
    })
    .catch(error => {
      console.error("❌ Falha ao carregar conteúdo via AJAX:", error);
      notify("danger", "Erro ao carregar a página.");
    });
}

// --- Listeners Globais ---

document.body.addEventListener('submit', async (e) => {
  const form = e.target.closest('form.ajax-form');
  if (!form || form.dataset.skipGlobal === '1') return;
  
  console.log('[DEBUG] Interceptado envio de form.ajax-form:', form);
  e.preventDefault();

  try {
    console.log('[DEBUG] Chamando submitAjaxForm...');
    const result = await submitAjaxForm(form);
    console.log('[DEBUG] Resultado de submitAjaxForm:', result);

    if (result == null) {
      console.log('[DEBUG] Resultado é nulo, encerrando.');
      return;
    }

    const declaredType = (form.dataset.responseType || '').toLowerCase();
    const isJson = declaredType === 'json' || (typeof result === 'object' && result !== null && !result.nodeType);
    console.log(`[DEBUG] Resposta é JSON? ${isJson}`);

    if (isJson) {
      console.log('[DEBUG] Chamando handleJsonFormResponse...');
      handleJsonFormResponse(form, result);
    } else {
      console.log('[DEBUG] Chamando handleHtmlFormResponse...');
      handleHtmlFormResponse(form, result);
    }

    if ((form.getAttribute('method') || 'GET').toUpperCase() === 'GET' && form.dataset.pushState !== 'false') {
      const qs = serializeFormToQuery(form);
      const base = (form.action || window.location.pathname).split('#')[0];
      const nextUrl = qs ? `${base}?${qs}` : base;
      history.pushState({}, '', nextUrl);
    }
  } catch (err) {
    console.error('❌ [DEBUG] Erro CAPTURADO na submissão do formulário AJAX:', err);
    notify('error', 'Falha ao processar a requisição. Verifique o console.');
  }
});

document.body.addEventListener('click', async (e) => {
  // Handler para paginação/ordenação
  const ajaxTargetLink = e.target.closest('a[data-ajax-target]');
  if (ajaxTargetLink) {
    e.preventDefault();
    const targetSel = ajaxTargetLink.dataset.ajaxTarget;
    const container = document.querySelector(targetSel);
    if (!container) return;

    try {
      const res = await fetchWithCreds(ajaxTargetLink.href, { method: 'GET' }, 'text/html');
      if (res.redirected && /\/accounts\/login\//.test(res.url)) {
        window.location = res.url; return;
      }
      const html = await res.text();
      container.innerHTML = html;
      document.dispatchEvent(new CustomEvent('ajaxContentLoaded', { detail: { screen: container.dataset.tela || '' }}));
      history.pushState({}, '', ajaxTargetLink.href);
    } catch (err) {
      console.error('❌ AJAX link error:', err);
      notify('error', 'Falha ao carregar a página.');
    }
    return;
  }

  // Handler para links AJAX genéricos
  const ajaxLink = e.target.closest(".ajax-link");
  if (ajaxLink && !ajaxLink.hasAttribute('data-bs-toggle')) {
      e.preventDefault();
      loadAjaxContent(ajaxLink.href);
      return;
  }
  
  // Handler para o botão Editar genérico
  const btnEditar = e.target.closest('#btn-editar');
  if (btnEditar && !btnEditar.disabled) {
      e.preventDefault();
      const href = btnEditar.getAttribute('data-href');
      if (href) {
          loadAjaxContent(href);
      }
      return;
  }

  // Handler para o botão de alternar tema
  const themeToggle = e.target.closest('#btn-alternar-tema-superior');
  if (themeToggle) {
      e.preventDefault();
      const isDark = document.documentElement.classList.toggle('dark');
      localStorage.setItem('tema', isDark ? 'dark' : 'light');
      return;
  }

  // Adicionar outros handlers de clique aqui (ex: #btn-excluir)
});

document.body.addEventListener('change', function(e) {
    const mainContent = document.getElementById('main-content');
    if (!mainContent || !e.target.matches('input[type="checkbox"]')) return;

    const identificadorTela = mainContent.querySelector("#identificador-tela");
    if (!identificadorTela) return;

    const seletorPai = identificadorTela.dataset.seletorPai;
    const seletorFilho = identificadorTela.dataset.seletorCheckbox;

    if (!seletorFilho) return;

    const paiCheckbox = seletorPai ? mainContent.querySelector(seletorPai) : null;
    const filhosCheckboxes = mainContent.querySelectorAll(seletorFilho);

    let isCheckboxRelevante = false;
    if ((paiCheckbox && e.target === paiCheckbox) || (filhosCheckboxes && Array.from(filhosCheckboxes).includes(e.target))) {
        isCheckboxRelevante = true;
    }
    
    if (isCheckboxRelevante) {
        updateButtonStates(mainContent);
    }
});

window.addEventListener('popstate', async () => {
  const activeWrapper = document.querySelector('[data-ajax-root="true"]'); 
  if (!activeWrapper) {
      if (location.href !== window.lastAjaxUrl) {
          window.location.reload();
      }
      return;
  }

  const url = window.location.href;
  try {
    const res = await fetchWithCreds(url, { method: 'GET' }, 'text/html');
    const html = await res.text();
    activeWrapper.innerHTML = html;
    document.dispatchEvent(new CustomEvent('ajaxContentLoaded', { detail: { screen: activeWrapper.dataset.tela || '' }}));
  } catch (_) {}
});


// --- Módulos de Página Específicos ---

function initListaEmpresas() {
  const form = document.getElementById('filtro-empresas-avancadas');
  if (!form || form.dataset.debounced === 'true') return;
  form.dataset.debounced = 'true';

  const handler = debounce(() => {
    form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
  }, 400);

  form.addEventListener('input', (e) => {
    if (e.target.matches('input, select, textarea')) handler();
  });
}

// --- Inicialização ---

function runInitializers() {
    showFlashMessage();
    // Lógica global que roda em todas as cargas de página/ajax
    if (document.getElementById('navbar-container')) {
        loadNavbar();
    }
    const mainContent = document.getElementById("main-content");
    if (mainContent && typeof updateButtonStates === 'function') {
        updateButtonStates(mainContent);
    }

    // Módulos específicos de página
    const initializers = [
        initListaEmpresas,
        () => {
            if (window.OneTech && window.OneTech.GerenciarCurvas) {
                const root = document.querySelector(OneTech.GerenciarCurvas.SELECTOR_ROOT);
                if (root) OneTech.GerenciarCurvas.init(root);
            }
        },
        () => {
            if (window.OneTech && window.OneTech.GerenciarTanques) {
                const root = document.querySelector(OneTech.GerenciarTanques.SELECTOR_ROOT);
                if (root) OneTech.GerenciarTanques.init(root);
            }
        },
        () => {
            if (window.OneTech && window.OneTech.GerenciarEventos) {
                const root = document.querySelector(OneTech.GerenciarEventos.SELECTOR_ROOT);
                if (root) OneTech.GerenciarEventos.init(root);
            }
        },
        () => {
            if (window.OneTech && window.OneTech.ArracoamentoDiario) {
                const root = document.querySelector(OneTech.ArracoamentoDiario.SELECTOR_ROOT);
                if (root) OneTech.ArracoamentoDiario.init(root);
            }
        },
        () => {
            if (window.OneTech && window.OneTech.NotaFiscalEntradas) {
                const root = document.querySelector(OneTech.NotaFiscalEntradas.SELECTOR_ROOT);
                if (root) OneTech.NotaFiscalEntradas.init(root);
            }
        },
        () => {
            if (window.OneTech && window.OneTech.NotasEntradas) {
                const root = document.querySelector(OneTech.NotasEntradas.SELECTOR_ROOT);
                if (root) OneTech.NotasEntradas.init(root);
            }
        },
        () => {
            if (window.OneTech && window.OneTech.PovoamentoLotes) {
                const root = document.querySelector(OneTech.PovoamentoLotes.SELECTOR_ROOT);
                if (root) OneTech.PovoamentoLotes.init(root);
            }
        },
        () => {
            if (window.OneTech && window.OneTech.EmpresaForm) {
                const root = document.querySelector(OneTech.EmpresaForm.SELECTOR_ROOT);
                if (root) OneTech.EmpresaForm.init(root);
            }
        },
        () => {
            if (window.OneTech && window.OneTech.Permissions) {
                const root = document.querySelector(OneTech.Permissions.SELECTOR_ROOT);
                if (root) OneTech.Permissions.init(root);
            }
        },
        () => {
            if (window.OneTech && window.OneTech.LancarNotaManual) {
                const root = document.querySelector(OneTech.LancarNotaManual.SELECTOR_ROOT);
                if (root) OneTech.LancarNotaManual.init(root);
            }
        },
        () => {
            if (window.OneTech && window.OneTech.CriarUsuario) {
                const root = document.querySelector(OneTech.CriarUsuario.SELECTOR_ROOT);
                if (root) OneTech.CriarUsuario.init(root);
            }
        }
    ];
    initializers.forEach(init => {
        if (typeof init === 'function') {
            init();
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ DOM completamente carregado. Iniciando scripts.");
    runInitializers();
});

document.addEventListener("ajaxContentLoaded", (event) => {
    console.log("✅ Conteúdo AJAX carregado. Re-inicializando scripts.");
    runInitializers();
});
