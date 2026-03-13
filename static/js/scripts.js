// ============================================================================
// ARQUIVO scripts.js - ARQUITETURA AJAX REATORADA (COM BOTOES DE ACAO)
// ============================================================================

// Aplica o tema salvo no localStorage (antes do paint)
const temaSalvo = localStorage.getItem("tema");
if (temaSalvo && temaSalvo !== "light") { // 'light' ÃƒÂ© o tema padrÃƒÂ£o sem classe
  document.documentElement.classList.add(temaSalvo);
}
document.documentElement.classList.add("theme-ready");

// Temas disponÃƒÂ­veis
const availableThemes = ['light', 'dark', 'azul'];

// FunÃƒÂ§ÃƒÂ£o para obter o prÃƒÂ³ximo tema
function getNextTheme(currentTheme) {
  const currentIndex = availableThemes.indexOf(currentTheme);
  const nextIndex = (currentIndex + 1) % availableThemes.length;
  return availableThemes[nextIndex];
}

// FunÃƒÂ§ÃƒÂ£o para aplicar o tema
function applyTheme(theme) {
  document.documentElement.classList.remove('light', 'dark', 'azul'); // Remove todos os temas
  if (theme !== 'light') { // 'light' ÃƒÂ© o tema padrÃƒÂ£o sem classe
    document.documentElement.classList.add(theme);
  }
  localStorage.setItem('tema', theme);
}

// --- FunÃƒÂ§ÃƒÂµes de Utilidade Global ---

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
    notify('error', 'SessÃƒÂ£o expirada. FaÃƒÂ§a login novamente.');
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

function syncMainContentMetadata(container) {
  const mainContent = document.getElementById('main-content');
  if (!mainContent || !container || container !== mainContent) return;

  const activeRoot = mainContent.querySelector('[data-page], [data-tela]');
  if (!activeRoot) {
    delete mainContent.dataset.page;
    delete mainContent.dataset.tela;
    return;
  }

  const page = activeRoot.dataset.page || '';
  const tela = activeRoot.dataset.tela || '';

  if (page) {
    mainContent.dataset.page = page;
  } else {
    delete mainContent.dataset.page;
  }

  if (tela) {
    mainContent.dataset.tela = tela;
  } else {
    delete mainContent.dataset.tela;
  }
}

function mostrarMensagem(type, message) {
    if (type === 'error') {
        type = 'danger';
    }
    if (!window.Swal) {
        console.error('SweetAlert2 nao encontrada.');
        return;
    }
    let container = document.getElementById('toast-container');
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
    if (!flashMessageData) return;

    try {
        const { type, message } = JSON.parse(flashMessageData);
        mostrarMensagem(type, message);
    } catch (error) {
        console.error('Could not parse flash message:', error);
    }

    sessionStorage.removeItem('flashMessage');
}

function syncNavbarOffset() {}

function logLayoutDiagnostics() {}


function ensureNavbarReady() {
    const navbarContainer = document.getElementById('navbar-container');
    if (!navbarContainer) return;

    const navbar = navbarContainer.querySelector('.navbar-superior');
    if (navbar) {
        initNestedNavbarSubmenus(navbarContainer);
        syncNavbarOffset(navbarContainer);
        return;
    }

    return;
}


let navbarSyncInFlight = null;
function syncNavbarWithServerIfNeeded(force = false) {
  const body = document.body;
  if (!body || !body.classList.contains('logged-in')) return;

  const navbarContainer = document.getElementById('navbar-container');
  if (!navbarContainer) return;

  const currentNavbar = navbarContainer.querySelector('.navbar-superior');
  if (!force && currentNavbar) return;
  if (navbarSyncInFlight) return;

  const navbarUrl = '/accounts/get-navbar/';
  navbarSyncInFlight = fetchWithCreds(navbarUrl, { method: 'GET' }, 'text/html')
    .then(async (response) => {
      if (!response || !response.ok) return;
      const html = await response.text();
      if (!html) return;

      const temp = document.createElement('div');
      temp.innerHTML = html;
      const freshNavbar = temp.querySelector('.navbar-superior');
      if (!freshNavbar) return;

      navbarContainer.innerHTML = '';
      navbarContainer.appendChild(freshNavbar);
      initNestedNavbarSubmenus(navbarContainer);
      syncNavbarOffset(navbarContainer);
    })
    .catch((error) => {
      console.error('Falha ao sincronizar navbar:', error);
    })
    .finally(() => {
      navbarSyncInFlight = null;
    });
}

// --- Motor AJAX e Handlers de Resposta ---

async function submitAjaxForm(form) {
  let url = form.action || window.location.href;
  const method = (form.getAttribute('method') || 'GET').toUpperCase();

  const options = { method };
  if (method === 'GET' || method === 'HEAD') {
    const qs = serializeFormToQuery(form);
    const parsedUrl = new URL(url, window.location.origin);
    parsedUrl.search = qs;
    parsedUrl.hash = '';
    url = `${parsedUrl.pathname}${parsedUrl.search}`;
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
    notify('error', 'SessÃƒÂ£o expirada. FaÃƒÂ§a login novamente.');
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
  if (data.message) notify(data.success ? 'success' : 'error', data.message);

  if (data.redirect_url) {
    const redirectDelayMs = data.message ? 1400 : 0;
    const forceFullRedirect = form && form.dataset && form.dataset.fullRedirectOnSuccess === '1';
    setTimeout(() => {
      if (forceFullRedirect) {
        window.location.assign(data.redirect_url);
      } else if (typeof loadAjaxContent === 'function') {
        loadAjaxContent(data.redirect_url);
      } else {
        window.location.assign(data.redirect_url);
      }
    }, redirectDelayMs);
    return;
  }
  if (data.html && form.dataset.targetContainer) {
    const container = document.querySelector(form.dataset.targetContainer);
    if (container) {
      container.innerHTML = data.html;
      syncMainContentMetadata(container);
      document.dispatchEvent(new CustomEvent('ajaxContentLoaded', {
        detail: { screen: container.dataset.tela || container.dataset.page || '' }
      }));
    }
  }
  if (data.reload) window.location.reload();

  // Dispara um evento global para que mÃ³dulos especÃ­ficos possam reagir Ã  resposta.
  document.dispatchEvent(new CustomEvent("ajaxForm:jsonResponse", {
    detail: { form, data }
  }));
}

function extractAjaxFragment(html, targetSelector = '#main-content') {
  if (!html || typeof html !== 'string') return html;

  const trimmed = html.trimStart();
  if (!/^<(?:!doctype|html|head|body|meta|title|link|script)\b/i.test(trimmed)) {
    return html;
  }

  const parser = new DOMParser();
  const doc = parser.parseFromString(html, 'text/html');

  if (targetSelector && targetSelector !== '#main-content') {
    const target = doc.querySelector(targetSelector);
    if (target) return target.innerHTML;
  }

  const main = doc.getElementById('main-content');
  if (main) return main.innerHTML;

  return doc.body ? doc.body.innerHTML : html;
}

function handleHtmlFormResponse(form, html) {
  const targetSel = form.dataset.targetContainer || '#main-content';
  const container = document.querySelector(targetSel);
  if (container) {
    container.innerHTML = extractAjaxFragment(html, targetSel);
    executeScriptsInContainer(container);
    syncMainContentMetadata(container);
    document.dispatchEvent(new CustomEvent('ajaxContentLoaded', {
      detail: { screen: container.dataset.tela || container.dataset.page || '' }
    }));
  } else {
    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    window.location.assign(url);
  }
}

function executeScriptsInContainer(container) {
  if (!container) return;
  const scripts = Array.from(container.querySelectorAll('script'));
  scripts.forEach((oldScript) => {
    const newScript = document.createElement('script');
    Array.from(oldScript.attributes).forEach((attr) => {
      newScript.setAttribute(attr.name, attr.value);
    });
    if (oldScript.textContent) {
      newScript.textContent = oldScript.textContent;
    }
    oldScript.replaceWith(newScript);
  });
}


function closeOpenNavbarDropdowns() {
  document.querySelectorAll('.navbar-superior .nav-item.dropdown.show .dropdown-toggle').forEach(toggle => {
    try {
      const instance = bootstrap.Dropdown.getInstance(toggle) || new bootstrap.Dropdown(toggle);
      instance.hide();
    } catch (_) {}
    toggle.setAttribute('aria-expanded', 'false');
  });

  document.querySelectorAll('.navbar-superior .dropdown.show').forEach(dropdown => {
    dropdown.classList.remove('show');
  });

  document.querySelectorAll('.navbar-superior .dropdown-menu.show').forEach(menu => {
    menu.classList.remove('show');
  });

  document.querySelectorAll('.navbar-superior .nested-submenu-collapse.show').forEach(submenu => {
    try {
      const instance = bootstrap.Collapse.getInstance(submenu) || new bootstrap.Collapse(submenu, { toggle: false });
      instance.hide();
    } catch (_) {}
    submenu.classList.remove('show');
  });
}


let currentAjaxNavigationUrl = null;
let ajaxNavigationSeq = 0;

function resetPageScroll() {
  try {
    window.scrollTo(0, 0);
  } catch (_) {}

  const mainContent = document.getElementById('main-content');
  if (mainContent) {
    mainContent.scrollTop = 0;
  }
}

function loadAjaxContent(url) {
  const mainContent = document.getElementById("main-content");
  const requestSeq = ++ajaxNavigationSeq;
  if (!mainContent) {
    window.location.href = url;
    return;
  }

  if (currentAjaxNavigationUrl === url) {
    return;
  }
  currentAjaxNavigationUrl = url;
  closeOpenNavbarDropdowns();

  fetchWithCreds(url, {}, 'text/html')
    .then(async (response) => {
      if (response === null) { // Check if fetchWithCreds already handled a redirect (e.g., 401)
        return null;
      }
      if (response.redirected && /\/accounts\/login\//.test(response.url)) {
        notify('error', 'SessÃƒÂ£o expirada. FaÃƒÂ§a login novamente.');
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
      if (requestSeq !== ajaxNavigationSeq) return;
      mainContent.innerHTML = extractAjaxFragment(html, '#main-content');
      executeScriptsInContainer(mainContent);
      syncMainContentMetadata(mainContent);
      resetPageScroll();
      closeOpenNavbarDropdowns();
      history.pushState({ ajaxUrl: url }, "", url);
      document.dispatchEvent(new CustomEvent("ajaxContentLoaded", { detail: { url } }));
    })
    .catch(error => {
      console.error("Ã¢ÂÅ’ Falha ao carregar conteÃƒÂºdo via AJAX:", error);
      notify("danger", "Erro ao carregar a pÃƒÂ¡gina.");
    });
}

// --- Listeners Globais ---

document.body.addEventListener('submit', async (e) => {
  const form = e.target.closest('form.ajax-form');
  if (!form || form.dataset.skipGlobal === '1') return;

  e.preventDefault();

  const loadingMessage = (form.dataset.loadingMessage || '').trim();
  const shouldShowLoading = Boolean(loadingMessage) && window.Swal && typeof Swal.fire === 'function';

  if (shouldShowLoading) {
    Swal.fire({
      title: loadingMessage,
      text: 'Por favor, aguarde...',
      allowOutsideClick: false,
      didOpen: () => Swal.showLoading(),
    });
  }

  try {
    const result = await submitAjaxForm(form);

    if (result == null) {
      console.log('[DEBUG] Resultado ÃƒÂ© nulo, encerrando.');
      return;
    }

    const declaredType = (form.dataset.responseType || '').toLowerCase();
    const isJson = declaredType === 'json' || (typeof result === 'object' && result !== null && !result.nodeType);
    if (isJson) {
      handleJsonFormResponse(form, result);
    } else {
      handleHtmlFormResponse(form, result);
    }

    if ((form.getAttribute('method') || 'GET').toUpperCase() === 'GET' && form.dataset.pushState !== 'false') {
      const qs = serializeFormToQuery(form);
      const parsedUrl = new URL(form.action || window.location.href, window.location.origin);
      parsedUrl.search = qs;
      parsedUrl.hash = '';
      history.pushState({}, '', `${parsedUrl.pathname}${parsedUrl.search}`);
    }
  } catch (err) {
    console.error('Ã¢ÂÅ’ [DEBUG] Erro CAPTURADO na submissÃƒÂ£o do formulÃƒÂ¡rio AJAX:', err);
    notify('error', 'Falha ao processar a requisiÃƒÂ§ÃƒÂ£o. Verifique o console.');
  } finally {
    if (shouldShowLoading && window.Swal && Swal.isVisible()) {
      Swal.close();
    }
  }
});
document.body.addEventListener('click', async (e) => {
  // Handler para paginaÃƒÂ§ÃƒÂ£o/ordenaÃƒÂ§ÃƒÂ£o
  const ajaxTargetLink = e.target.closest('a[data-ajax-target]');
  if (ajaxTargetLink) {
    e.preventDefault();
    const targetSel = ajaxTargetLink.dataset.ajaxTarget;
    const container = document.querySelector(targetSel);
    if (!container) return;

    try {
      closeOpenNavbarDropdowns();
      const res = await fetchWithCreds(ajaxTargetLink.href, { method: 'GET' }, 'text/html');
      if (res.redirected && /\/accounts\/login\//.test(res.url)) {
        window.location = res.url; return;
      }
      const html = await res.text();
      container.innerHTML = extractAjaxFragment(html, targetSel);
      executeScriptsInContainer(container);
      resetPageScroll();
      closeOpenNavbarDropdowns();
      document.dispatchEvent(new CustomEvent('ajaxContentLoaded', { detail: { screen: container.dataset.tela || '' }}));
      history.pushState({}, '', ajaxTargetLink.href);
    } catch (err) {
      console.error('Ã¢ÂÅ’ AJAX link error:', err);
      notify('error', 'Falha ao carregar a pÃƒÂ¡gina.');
    }
    return;
  }

  // Handler para links AJAX genÃƒÂ©ricos
  const ajaxLink = e.target.closest(".ajax-link");
  if (ajaxLink && !ajaxLink.hasAttribute('data-bs-toggle')) {
      e.preventDefault();
      closeOpenNavbarDropdowns();
      loadAjaxContent(ajaxLink.href);
      return;
  }
  // Handler para os links de tema no menu de perfil
  const themeOption = e.target.closest('.theme-option');
  if (themeOption) {
      e.preventDefault();
      const selectedTheme = themeOption.dataset.theme;
      applyTheme(selectedTheme);
      return;
  }

  // Adicionar outros handlers de clique aqui (ex: #btn-excluir)
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


// --- MÃƒÂ³dulos de PÃƒÂ¡gina EspecÃƒÂ­ficos ---

function setupAutocomplete(inputId, apiUrl, displayField = 'text', valueField = 'id', options = {}) {
  const inputElement = document.getElementById(inputId);
  if (!inputElement || inputElement.dataset.autocompleteBound === '1') return;
  inputElement.dataset.autocompleteBound = '1';

  const minLength = Number(options.minLength || 2);
  const queryParam = options.queryParam || 'search';
  const limit = Number(options.limit || 0);
  const onSelect = typeof options.onSelect === 'function' ? options.onSelect : null;
  const selectedDisplayField = options.selectedDisplayField || displayField;
  const hiddenTargetSelector = options.hiddenTargetSelector || null;
  const hiddenValueField = options.hiddenValueField || valueField;
  let currentDropdown = null;
  let currentNextUrl = null;
  let activeSearchToken = 0;
  let suppressFetchUntil = 0;

  const removeDropdown = () => {
    if (currentDropdown) {
      currentDropdown.remove();
      currentDropdown = null;
    }
  };

  const ensureDropdown = () => {
    if (currentDropdown) return currentDropdown;
    currentDropdown = document.createElement('div');
    currentDropdown.className = 'autocomplete-ncm-list';
    currentDropdown.style.position = 'absolute';
    currentDropdown.style.zIndex = '1080';
    currentDropdown.style.top = 'calc(100% + 4px)';
    currentDropdown.style.left = '0';
    currentDropdown.style.width = '100%';
    inputElement.parentNode.style.position = 'relative';
    inputElement.parentNode.appendChild(currentDropdown);
    return currentDropdown;
  };

  const renderAutocompleteLabel = (rawValue) => {
    const value = String(rawValue || '');
    const escaped = value
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');

    // Permite somente a tag <i> para exibir nomenclatura cientifica de NCM.
    return escaped
      .replace(/&lt;i&gt;/gi, '<i>')
      .replace(/&lt;\/i&gt;/gi, '</i>');
  };

  const selectSuggestion = (item) => {
    // Invalida buscas pendentes para evitar reabertura do dropdown apos selecionar.
    activeSearchToken += 1;
    suppressFetchUntil = Date.now() + 250;
    currentNextUrl = null;
    const chosenValue = item[valueField] || item[displayField] || '';
    const displayValue = item[selectedDisplayField] || item[displayField] || chosenValue;
    inputElement.value = displayValue;
    inputElement.dataset.selectedValue = item.id || chosenValue;

    let hiddenField = null;
    if (hiddenTargetSelector && !hiddenTargetSelector.includes('{{')) {
      try {
        hiddenField = document.querySelector(hiddenTargetSelector);
      } catch (_) {
        hiddenField = null;
      }
    }
    if (!hiddenField) {
      hiddenField = inputElement.parentElement.querySelector('select.d-none, input[type="hidden"]');
    }
    const hiddenValue = item[hiddenValueField] || chosenValue;
    if (hiddenField) {
      if (hiddenField.tagName === 'SELECT') {
        let matchingOption = Array.from(hiddenField.options).find(option => option.value === String(hiddenValue));
        if (!matchingOption) {
          matchingOption = new Option(displayValue, hiddenValue, true, true);
          hiddenField.add(matchingOption);
        }
        hiddenField.value = hiddenValue;
      } else {
        hiddenField.value = hiddenValue;
      }
      hiddenField.dispatchEvent(new Event('change', { bubbles: true }));
    }

    removeDropdown();
    inputElement.blur();
    inputElement.dispatchEvent(new Event('change', { bubbles: true }));
    if (onSelect) onSelect(item, inputElement);
  };

  const renderSuggestions = (suggestions, append = false) => {
    if (!Array.isArray(suggestions)) suggestions = [];

    if (!append) {
      removeDropdown();
      if (suggestions.length === 0 && !currentNextUrl) return;
    } else if (!currentDropdown && suggestions.length === 0) {
      return;
    }

    const dropdown = ensureDropdown();
    if (!append) dropdown.innerHTML = '';

    suggestions.forEach(item => {
      const suggestionItem = document.createElement('button');
      suggestionItem.type = 'button';
      suggestionItem.className = 'autocomplete-ncm-item';
      suggestionItem.innerHTML = renderAutocompleteLabel(
        item[displayField] || item.text || item[valueField] || ''
      );
      suggestionItem.addEventListener('mousedown', (event) => {
        event.preventDefault();
        selectSuggestion(item);
      });
      suggestionItem.addEventListener('click', (event) => {
        event.preventDefault();
        selectSuggestion(item);
      });
      dropdown.appendChild(suggestionItem);
    });

    const existingLoadMore = dropdown.querySelector('.autocomplete-load-more');
    if (existingLoadMore) existingLoadMore.remove();

    if (currentNextUrl) {
      const loadMoreButton = document.createElement('button');
      loadMoreButton.type = 'button';
      loadMoreButton.className = 'autocomplete-ncm-item autocomplete-load-more';
      loadMoreButton.textContent = 'Carregar mais';
      loadMoreButton.addEventListener('mousedown', (event) => {
        event.preventDefault();
      });
      loadMoreButton.addEventListener('click', async (event) => {
        event.preventDefault();
        await fetchData(inputElement.value, true, currentNextUrl);
      });
      dropdown.appendChild(loadMoreButton);
    } else if (dropdown.children.length === 0) {
      removeDropdown();
    }
  };

  const fetchData = async (searchTerm, append = false, nextUrl = null) => {
    const term = (searchTerm || '').trim();
    if (!append && Date.now() < suppressFetchUntil) {
      return;
    }
    if (!append && term.length < minLength) {
      removeDropdown();
      currentNextUrl = null;
      return;
    }

    const searchToken = ++activeSearchToken;

    try {
      const url = nextUrl ? new URL(nextUrl, window.location.origin) : new URL(apiUrl, window.location.origin);
      if (!nextUrl) {
        url.searchParams.set(queryParam, term);
        if (limit > 0) {
          url.searchParams.set('limit', String(limit));
        }
      }

      const response = await fetchWithCreds(url.toString(), { method: 'GET' }, 'application/json, text/plain, */*');
      if (!response || !response.ok) throw new Error('Erro ao buscar dados da API');
      const data = await response.json();
      if (searchToken !== activeSearchToken) return;

      const paginatedResults = Array.isArray(data.results) ? data.results : null;
      const results = Array.isArray(data) ? data : (paginatedResults || []);
      currentNextUrl = paginatedResults ? (data.next || null) : null;
      renderSuggestions(results, append);
    } catch (error) {
      console.error('Erro no autocompletar:', error);
      removeDropdown();
      currentNextUrl = null;
    }
  };

  const debouncedFetchData = debounce(fetchData, Number(options.delay || 250));

  inputElement.addEventListener('input', (event) => {
    inputElement.dataset.selectedValue = '';
    currentNextUrl = null;
    debouncedFetchData(event.target.value);
  });

  inputElement.addEventListener('focus', (event) => {
    debouncedFetchData(event.target.value);
  });

  inputElement.addEventListener('blur', () => {
    setTimeout(removeDropdown, 180);
  });
}

window.setupAutocomplete = setupAutocomplete;

function initGenericAutocomplete(root = document) {
  root.querySelectorAll('[data-autocomplete-url]').forEach(input => {
    if (!input.id) return;

    setupAutocomplete(
      input.id,
      input.dataset.autocompleteUrl,
      input.dataset.autocompleteDisplayField || 'text',
      input.dataset.autocompleteValueField || 'id',
      {
        minLength: input.dataset.autocompleteMinLength || 2,
        limit: input.dataset.autocompleteLimit || 0,
        queryParam: input.dataset.autocompleteQueryParam || 'search',
        selectedDisplayField: input.dataset.autocompleteSelectedDisplayField || input.dataset.autocompleteDisplayField || 'text',
        hiddenTargetSelector: input.dataset.autocompleteHiddenTarget || null,
        hiddenValueField: input.dataset.autocompleteHiddenValueField || input.dataset.autocompleteValueField || 'id',
        onSelect: (item, inputElement) => {
          const formSelector = input.dataset.autocompleteSubmitTargetForm;
          const shouldSubmit = input.dataset.autocompleteSubmitOnSelect === 'true';
          if (!shouldSubmit) return;
          const form = formSelector ? document.querySelector(formSelector) : inputElement.closest('form');
          if (form) {
            form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
          }
        }
      }
    );
  });
}

function initFiscalList(root = document) {
  const selector = '[data-list-controller="unified-list"]';
  const pageRoot = root.querySelector(selector) || document.querySelector(selector);
  if (!pageRoot) return;

  const rowCheckboxes = Array.from(pageRoot.querySelectorAll('.row-checkbox'));
  const selectAllCheckbox = pageRoot.querySelector('#select-all-checkbox');
  const btnEditarSelecionado = pageRoot.querySelector('#btn-editar-selecionado');
  const btnExcluirSelecionados = pageRoot.querySelector('#btn-excluir-selecionados');

  const selectedCount = rowCheckboxes.filter(cb => cb.checked).length;
  if (btnEditarSelecionado) btnEditarSelecionado.disabled = selectedCount !== 1;
  if (btnExcluirSelecionados) btnExcluirSelecionados.disabled = selectedCount === 0;
  if (selectAllCheckbox) {
    const total = rowCheckboxes.length;
    selectAllCheckbox.checked = total > 0 && selectedCount === total;
    selectAllCheckbox.indeterminate = selectedCount > 0 && selectedCount < total;
  }
}

let fiscalListDelegationBound = false;
function initFiscalListDelegation() {
  if (fiscalListDelegationBound) return;
  fiscalListDelegationBound = true;

  const selector = '[data-list-controller="unified-list"]';
  const debounceTimers = new WeakMap();

  const getPageRoot = (el) => (el && el.closest) ? el.closest(selector) : null;

  const buildListUrl = (pageRoot, value) => {
    const base = pageRoot.dataset.listUrl || window.location.pathname;
    const url = new URL(base, window.location.origin);
    const normalized = String(value || '').trim();
    const searchParam = pageRoot.dataset.searchParam || 'busca';
    if (normalized) url.searchParams.set(searchParam, normalized);
    else url.searchParams.delete(searchParam);
    url.searchParams.delete('ordenacao');
    return `${url.pathname}${url.search}`;
  };

  const updateState = (pageRoot) => {
    if (!pageRoot) return;
    const rows = Array.from(pageRoot.querySelectorAll('.row-checkbox'));
    const selected = rows.filter(cb => cb.checked).length;
    const btnEdit = pageRoot.querySelector('#btn-editar-selecionado');
    const btnDelete = pageRoot.querySelector('#btn-excluir-selecionados');
    const selectAll = pageRoot.querySelector('#select-all-checkbox');

    if (btnEdit) btnEdit.disabled = selected !== 1;
    if (btnDelete) btnDelete.disabled = selected === 0;
    if (selectAll) {
      const total = rows.length;
      selectAll.checked = total > 0 && selected === total;
      selectAll.indeterminate = selected > 0 && selected < total;
    }
  };

  const setPendingSearchFocus = (pageRoot, inputEl) => {
    if (!pageRoot || !inputEl) return;
    window.__unifiedListSearchFocus = {
      page: pageRoot.dataset.page || '',
      cursor: Number.isInteger(inputEl.selectionStart) ? inputEl.selectionStart : String(inputEl.value || '').length,
    };
  };

  const restorePendingSearchFocus = () => {
    const pending = window.__unifiedListSearchFocus;
    if (!pending || !pending.page) return;

    const nextPageRoot = document.querySelector(`[data-page="${pending.page}"]`);
    if (!nextPageRoot) return;

    const nextInput = nextPageRoot.querySelector('#search-input');
    if (!nextInput) return;

    nextInput.focus({ preventScroll: true });
    const len = String(nextInput.value || '').length;
    const cursor = Math.max(0, Math.min(Number(pending.cursor || len), len));
    try {
      nextInput.setSelectionRange(cursor, cursor);
    } catch (error) {
      // browsers podem rejeitar setSelectionRange em tipos nao text
    }

    window.__unifiedListSearchFocus = null;
  };

  const runSearch = (pageRoot, value, immediate = false, inputEl = null) => {
    const existing = debounceTimers.get(pageRoot);
    if (existing) {
      clearTimeout(existing);
      debounceTimers.delete(pageRoot);
    }

    const exec = () => {
      if (inputEl) {
        setPendingSearchFocus(pageRoot, inputEl);
      }
      const url = buildListUrl(pageRoot, value);
      loadAjaxContent(url);
    };

    if (immediate) {
      exec();
      return;
    }

    const t = setTimeout(exec, 350);
    debounceTimers.set(pageRoot, t);
  };

  document.addEventListener('ajaxContentLoaded', restorePendingSearchFocus);

  const resolveSearchInput = (target) => {
    if (!target) return null;
    if (target.id === 'search-input') return target;
    if (target.closest) return target.closest('#search-input');
    return null;
  };

  document.body.addEventListener('input', (event) => {
    const searchInput = resolveSearchInput(event.target);
    if (!searchInput) return;
    const pageRoot = getPageRoot(searchInput);
    if (!pageRoot) return;
    runSearch(pageRoot, searchInput.value, false, searchInput);
  });

  document.body.addEventListener('change', (event) => {
    const searchInput = resolveSearchInput(event.target);
    if (!searchInput) return;
    const pageRoot = getPageRoot(searchInput);
    if (!pageRoot) return;
    runSearch(pageRoot, searchInput.value, true, searchInput);
  });

  document.body.addEventListener('keydown', (event) => {
    const searchInput = resolveSearchInput(event.target);
    if (!searchInput) return;
    const pageRoot = getPageRoot(searchInput);
    if (!pageRoot) return;

    if (event.key === 'Enter') {
      event.preventDefault();
      runSearch(pageRoot, searchInput.value, true, searchInput);
    } else if (event.key === 'Escape') {
      searchInput.value = '';
      runSearch(pageRoot, '', true, searchInput);
    }
  });

  document.body.addEventListener('keyup', (event) => {
    const searchInput = resolveSearchInput(event.target);
    if (!searchInput) return;
    if (event.key === 'Enter' || event.key === 'Escape' || event.key === 'Tab') return;
    const pageRoot = getPageRoot(searchInput);
    if (!pageRoot) return;
    runSearch(pageRoot, searchInput.value, false, searchInput);
  });

  document.body.addEventListener('click', (event) => {
    const clearBtn = event.target.closest ? event.target.closest('#btn-limpar-busca') : null;
    if (clearBtn) {
      const pageRoot = getPageRoot(clearBtn);
      if (!pageRoot) return;
      const search = pageRoot.querySelector('#search-input');
      if (search) {
        search.value = '';
        search.focus();
      }
      runSearch(pageRoot, '', true, search);
      return;
    }

    const editBtn = event.target.closest ? event.target.closest('#btn-editar-selecionado') : null;
    if (editBtn) {
      const pageRoot = getPageRoot(editBtn);
      if (!pageRoot || editBtn.disabled) return;
      const checked = Array.from(pageRoot.querySelectorAll('.row-checkbox')).filter(cb => cb.checked);
      if (checked.length !== 1) return;
      const editUrlBase = editBtn.dataset.editUrlBase || '';
      if (!editUrlBase) return;
      const buildEditUrl = (baseUrl, selectedId) => {
        if (!baseUrl) return '';
        if (baseUrl.includes('/0/')) return baseUrl.replace('/0/', `/${selectedId}/`);
        if (baseUrl.endsWith('/0')) return `${baseUrl.slice(0, -2)}/${selectedId}`;
        return baseUrl.replace(/0\/?$/, `${selectedId}/`);
      };
      const editUrl = buildEditUrl(editUrlBase, checked[0].value);
      loadAjaxContent(editUrl);
      return;
    }

    const deleteBtn = event.target.closest ? event.target.closest('#btn-excluir-selecionados') : null;
    if (deleteBtn) {
      const pageRoot = getPageRoot(deleteBtn);
      if (!pageRoot || deleteBtn.disabled) return;

      const checked = Array.from(pageRoot.querySelectorAll('.row-checkbox')).filter(cb => cb.checked);
      const selectedIds = checked.map(cb => cb.value);
      if (!selectedIds.length) return;

      const entityPlural = deleteBtn.dataset.entityLabelPlural || 'itens';
      const entitySingular = deleteBtn.dataset.entityLabelSingular || 'item';
      const actionVerb = deleteBtn.dataset.actionVerb || 'excluir';
      const actionWarning = deleteBtn.dataset.actionWarning || 'Esta acao nao pode ser desfeita.';
      const deleteUrl = deleteBtn.dataset.deleteUrl || '';
      const itemType = deleteBtn.dataset.itemType || '';
      if (!deleteUrl) return;

      Swal.fire({
        title: 'Voce tem certeza?',
        text: `Voce esta prestes a ${actionVerb} ${selectedIds.length} ${selectedIds.length === 1 ? entitySingular : entityPlural}. ${actionWarning}`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: `Sim, ${actionVerb}!`,
        cancelButtonText: 'Cancelar'
      }).then(async (result) => {
        if (!result.isConfirmed) return;

        const payload = { ids: selectedIds };
        if (itemType) payload.item_type = itemType;

        try {
          const response = await fetchWithCreds(deleteUrl, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(payload)
          });
          if (!response) return;

          const data = await response.json();
          if (!response.ok || data.success === false) {
            mostrarMensagem('danger', data.message || 'Ocorreu um erro ao processar os itens.');
            return;
          }

          if (data.message) mostrarMensagem('success', data.message);
          if (data.redirect_url) {
            loadAjaxContent(data.redirect_url);
          } else {
            const searchInput = pageRoot.querySelector('#search-input');
            const currentValue = searchInput ? searchInput.value : '';
            runSearch(pageRoot, currentValue, true);
          }
        } catch (error) {
          console.error('Erro ao excluir selecionados:', error);
          mostrarMensagem('danger', 'Erro de comunicacao com o servidor.');
        }
      });
      return;
    }
  });

  document.body.addEventListener('change', (event) => {
    const pageRoot = getPageRoot(event.target);
    if (!pageRoot) return;

    if (event.target.matches && event.target.matches('#select-all-checkbox')) {
      const rows = Array.from(pageRoot.querySelectorAll('.row-checkbox'));
      rows.forEach((cb) => {
        cb.checked = event.target.checked;
      });
      updateState(pageRoot);
      return;
    }

    if (event.target.matches && event.target.matches('.row-checkbox')) {
      updateState(pageRoot);
    }
  });
}

function initNcmMaintenance() {

  const form = document.getElementById('ncm-search-form');
  if (!form || form.dataset.debounced === 'true') return;
  form.dataset.debounced = 'true';

  const pageRoot = document.querySelector('[data-page="manutencao-ncm"]');
  const refreshUrl = pageRoot?.dataset.refreshUrl || form.action;
  const input = form.querySelector('input[name="term"]');
  if (!input) return;

  const clearButton = document.getElementById('btn-limpar-ncm');
  const atualizarBaseButton = document.getElementById('btn-atualizar-base-ncm');
  const importarLocalButton = document.getElementById('btn-importar-ncm-local');
  const consolidarButton = document.getElementById('btn-consolidar-ncm');

  const refreshPage = () => {
    const currentTerm = (input.value || '').trim();
    const url = currentTerm ? `${refreshUrl}?term=${encodeURIComponent(currentTerm)}` : refreshUrl;
    loadAjaxContent(url);
  };

  const submitDebounced = debounce(() => {
    form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
  }, 250);

  const postNcmAction = async (button, payload = {}, loadingText = 'Processando base NCM...') => {
    if (!button || !button.dataset.url) throw new Error('Botao de acao NCM sem URL configurada.');
    const originalDisabled = button.disabled;
    const shouldShowLoading = Boolean(window.Swal);
    button.disabled = true;

    if (shouldShowLoading) {
      Swal.fire({
        title: 'Aguarde',
        text: loadingText,
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
          Swal.showLoading();
        }
      });
    }

    try {
      const response = await fetchWithCreds(button.dataset.url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(payload)
      }, 'application/json, text/plain, */*');

      if (!response) throw new Error('Falha de autenticacao ao executar a acao de NCM.');
      const data = await response.json();
      if (!response.ok || data.success === false) {
        throw new Error(data.message || 'Falha ao executar a acao de NCM.');
      }
      return data;
    } finally {
      if (shouldShowLoading) {
        Swal.close();
      }
      button.disabled = originalDisabled;
    }
  };

  const formatDuplicateSummary = (summary) => {
    if (!summary || !summary.group_count) return 'Nenhuma duplicidade encontrada.';
    const preview = (summary.groups || []).slice(0, 3).map(group => `${group.normalized_code} (${group.duplicate_count})`).join(', ');
    return `${summary.group_count} grupo(s) e ${summary.duplicate_count} duplicidade(s). ${preview ? `Ex.: ${preview}.` : ''}`;
  };

  input.addEventListener('input', () => {
    submitDebounced();
  });

  input.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      input.value = '';
      form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    }
  });

  if (clearButton && clearButton.dataset.bound !== '1') {
    clearButton.dataset.bound = '1';
    clearButton.addEventListener('click', () => {
      input.value = '';
      input.dataset.selectedValue = '';
      form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
      input.focus();
    });
  }

  if (atualizarBaseButton && atualizarBaseButton.dataset.bound !== '1') {
    atualizarBaseButton.dataset.bound = '1';
    atualizarBaseButton.addEventListener('click', async () => {
      try {
        const data = await postNcmAction(atualizarBaseButton, {}, 'Atualizando o arquivo local com a base oficial...');
        notify('success', data.message);
        refreshPage();
      } catch (error) {
        notify('error', error.message);
      }
    });
  }

  if (importarLocalButton && importarLocalButton.dataset.bound !== '1') {
    importarLocalButton.dataset.bound = '1';
    importarLocalButton.addEventListener('click', async () => {
      try {
        const data = await postNcmAction(importarLocalButton, {}, 'Importando a base local para o banco. Isso pode levar alguns segundos...');
        const summary = data.duplicate_summary || {};
        if (window.Swal && summary.group_count > 0) {
          const result = await Swal.fire({
            icon: 'success',
            title: 'Importacao concluida',
            html: `${data.message}<br><br><strong>Normalizacao sugerida:</strong> ${formatDuplicateSummary(summary)}`,
            showCancelButton: true,
            confirmButtonText: 'Consolidar agora',
            cancelButtonText: 'Depois'
          });
          if (result.isConfirmed && consolidarButton) {
            const consolidateData = await postNcmAction(consolidarButton, { apply: true }, 'Consolidando e normalizando os registros NCM...');
            notify('success', consolidateData.message);
          } else {
            notify('success', data.message);
          }
        } else {
          notify('success', data.message);
        }
        refreshPage();
      } catch (error) {
        notify('error', error.message);
      }
    });
  }

  if (consolidarButton && consolidarButton.dataset.bound !== '1') {
    consolidarButton.dataset.bound = '1';
    consolidarButton.addEventListener('click', async () => {
      try {
        const inspectData = await postNcmAction(consolidarButton, {}, 'Verificando se existem NCMs duplicados ou inconsistentes...');
        const summary = inspectData.duplicate_summary || {};
        if (!summary.group_count) {
          notify('success', inspectData.message);
          return;
        }

        if (window.Swal) {
          const result = await Swal.fire({
            icon: 'warning',
            title: 'Consolidar NCM',
            html: `Foram encontrados registros para consolidacao.<br><br>${formatDuplicateSummary(summary)}`,
            showCancelButton: true,
            confirmButtonText: 'Aplicar consolidacao',
            cancelButtonText: 'Cancelar'
          });
          if (!result.isConfirmed) return;
        }

        const applyData = await postNcmAction(consolidarButton, { apply: true }, 'Aplicando consolidacao e normalizacao da base NCM...');
        notify('success', applyData.message);
        refreshPage();
      } catch (error) {
        notify('error', error.message);
      }
    });
  }
}

function initMigrationTenantSelect(root = document) {
    if (!(window.jQuery && window.jQuery.fn && window.jQuery.fn.select2)) return;

    root.querySelectorAll('.migration-tenant-select').forEach(el => {
        const $el = window.jQuery(el);
        if ($el.data('select2')) {
            $el.off('.migrationSelectSummary');
            $el.select2('destroy');
        }

        let dropdownCssClass = 'select2-dropdown-custom migration-select2-dropdown';
        if (document.documentElement.classList.contains('dark')) dropdownCssClass += ' select2-dropdown-dark';

        const $dropdownParent = $el.closest('.migration-status-panel').length
            ? $el.closest('.migration-status-panel')
            : ($el.closest('.card-body').length ? $el.closest('.card-body') : window.jQuery('body'));

        $el.select2({
            theme: 'bootstrap-5',
            width: 'style',
            placeholder: el.dataset.placeholder || 'Selecione tenants',
            closeOnSelect: false,
            selectionCssClass: 'migration-select2-selection',
            dropdownParent: $dropdownParent,
            dropdownCssClass,
        });

        const updateSummary = () => {
            const selectedCount = Array.isArray($el.val()) ? $el.val().length : 0;
            const summary = selectedCount === 0
                ? (el.dataset.placeholder || 'Selecione tenants')
                : selectedCount === 1
                    ? '1 tenant selecionado'
                    : `${selectedCount} tenants selecionados`;
            const $selection = $el.next('.select2-container').find('.select2-selection');
            $selection.attr('data-summary', summary);
            $selection.toggleClass('has-selection', selectedCount > 0);
        };

        $el.on('change.migrationSelectSummary select2:select.migrationSelectSummary select2:unselect.migrationSelectSummary', updateSummary);
        updateSummary();
    });
}

function initTooltips(root = document) {
    if (!window.bootstrap || !bootstrap.Tooltip) return;

    root.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
        const existing = bootstrap.Tooltip.getInstance(el);
        if (existing) existing.dispose();
        new bootstrap.Tooltip(el, {
            trigger: 'hover focus',
            container: 'body'
        });
    });
}

function initNestedNavbarSubmenus(root = document) {
    root.querySelectorAll('.nested-submenu-toggle').forEach(el => {
        if (el.dataset.navbarNestedBound === '1') return;
        el.dataset.navbarNestedBound = '1';
        el.addEventListener('click', (event) => {
            event.stopPropagation();
        });
    });

    root.querySelectorAll('.navbar-superior .nav-item.dropdown').forEach(dropdown => {
        if (dropdown.dataset.navbarDropdownBound === '1') return;
        dropdown.dataset.navbarDropdownBound = '1';
        dropdown.addEventListener('hidden.bs.dropdown', () => {
            dropdown.querySelectorAll('.nested-submenu-collapse.show').forEach(submenu => {
                const instance = bootstrap.Collapse.getInstance(submenu) || new bootstrap.Collapse(submenu, { toggle: false });
                instance.hide();
            });
        });
    });
}

function initListaEventos() {
  const form = document.getElementById('filtro-eventos-form');
  if (!form || form.dataset.debounced === 'true') return;
  form.dataset.debounced = 'true';

  const submitFilters = () => {
    form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
  };

  const debouncedSubmit = debounce(submitFilters, 250);

  form.addEventListener('change', (e) => {
    if (e.target.matches('select, input[type="date"]')) {
      submitFilters();
    }
  });

  form.addEventListener('keydown', (e) => {
    if (e.target.matches('input[type="date"]') && e.key === 'Enter') {
      e.preventDefault();
      submitFilters();
    }
  });

  const clearButton = form.querySelector('#btn-limpar-filtros-eventos');
  if (clearButton) {
    clearButton.addEventListener('click', () => {
      form.querySelectorAll('select').forEach((select) => {
        select.selectedIndex = 0;
      });
      form.querySelectorAll('input[type="date"]').forEach((input) => {
        input.value = '';
      });
      debouncedSubmit();
    });
  }
}
function initCriarNfeSaida(root = document) {
  const pageRoot = root.querySelector('[data-page="criar-nfe-saida"]');
  if (!pageRoot || pageRoot.dataset.bound === '1') return;
  pageRoot.dataset.bound = '1';

  if (!(window.jQuery && window.jQuery.fn && window.jQuery.fn.select2)) return;

  const selects = pageRoot.querySelectorAll(
    '#emitente_proprio, #destinatario, #finalidade_emissao, #tipo_operacao, #condicao_pagamento_cadastro, #id_emitente_proprio, #id_destinatario, #id_finalidade_emissao, #id_tipo_operacao, #id_condicao_pagamento_cadastro'
  );
  if (!selects.length) return;

  const $allSelects = window.jQuery(selects);
  const $destinatario = $allSelects.filter('#destinatario, #id_destinatario');

  $allSelects.not($destinatario).select2({
    theme: 'bootstrap-5'
  });

  $destinatario.select2({
    theme: 'bootstrap-5',
    matcher: function (params, data) {
      const term = (params.term || '').trim().toLowerCase();
      if (!term) return data;

      const optionText = (data.text || '').toLowerCase();
      const searchTokens = (data.element && data.element.dataset && data.element.dataset.search)
        ? data.element.dataset.search.toLowerCase()
        : '';

      if (optionText.includes(term) || searchTokens.includes(term)) {
        return data;
      }

      return null;
    }
  });

  const condicaoSelect = pageRoot.querySelector('#condicao_pagamento_cadastro, #id_condicao_pagamento_cadastro');
  const parcelasInput = pageRoot.querySelector('#quantidade_parcelas, #id_quantidade_parcelas');
  const condicaoHiddenInput = pageRoot.querySelector('#condicao_pagamento, #id_condicao_pagamento');

  const syncParcelasFromCondicao = () => {
    if (!condicaoSelect || !parcelasInput) return;
    const selectedOption = condicaoSelect.options[condicaoSelect.selectedIndex];
    if (!selectedOption) return;

    const condicaoSelecionada = String(condicaoSelect.value || '').trim() !== '';
    const parcelas = parseInt(selectedOption.dataset.parcelas || '0', 10);
    const descricao = (selectedOption.dataset.descricao || '').trim();

    if (condicaoSelecionada && parcelas > 0) {
      parcelasInput.value = String(parcelas);
    }

    if (condicaoHiddenInput && condicaoSelecionada && descricao) {
      condicaoHiddenInput.value = descricao;
    } else if (condicaoHiddenInput && !condicaoSelecionada) {
      condicaoHiddenInput.value = '';
    }

    parcelasInput.readOnly = condicaoSelecionada;
    parcelasInput.classList.toggle('bg-light', condicaoSelecionada);
  };

  if (condicaoSelect) {
    condicaoSelect.addEventListener('change', syncParcelasFromCondicao);
    window.jQuery(condicaoSelect).on('select2:select', syncParcelasFromCondicao);
    syncParcelasFromCondicao();
  }

  setupAutocomplete(
    'id_natureza_operacao',
    '/nota-fiscal/api/buscar-naturezas-operacao/',
    'text',
    'valor_gravacao',
    {
      minLength: 2,
      queryParam: 'search',
      selectedDisplayField: 'text'
    }
  );
}

function initProdutoOrigemMercadoriaSelect(root = document) {
  if (!(window.jQuery && window.jQuery.fn && window.jQuery.fn.select2)) return;

  const pageRoot = root.querySelector('[data-page="cadastrar-produto"], [data-tela="editar_produto"]');
  if (!pageRoot) return;

  pageRoot.querySelectorAll('select.select2-origem-mercadoria').forEach((select) => {
    const $select = window.jQuery(select);
    if ($select.data('select2')) {
      $select.select2('destroy');
    }
    $select.select2({
      theme: 'bootstrap-5',
      width: '100%',
      placeholder: select.dataset.placeholder || 'Selecione',
      allowClear: true,
    });
  });
}
function initEmitirNfeList(root = document) {
  const pageRoot = root.querySelector('[data-page="emitir-nfe-list"]');
  if (!pageRoot || pageRoot.dataset.bound === '1') return;
  pageRoot.dataset.bound = '1';

  const url = pageRoot.dataset.emitirUrl || '';
  const csrfToken = pageRoot.dataset.csrfToken || getCSRFToken();
  if (!url) return;

  const showLoading = (title) => {
    Swal.fire({
      title,
      text: 'Por favor, aguarde...',
      allowOutsideClick: false,
      didOpen: () => {
        Swal.showLoading();
      }
    });
  };

  pageRoot.querySelectorAll('.emit-btn').forEach((button) => {
    button.addEventListener('click', function () {
      const notaId = this.dataset.notaId;
      const notaNumero = this.dataset.notaNumero;

      Swal.fire({
        title: `Emitir a NF-e No ${notaNumero}?`,
        text: 'Esta acao enviara a nota para autorizacao. Voce nao podera edita-la apos o envio.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#0d6efd',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Sim, emitir!',
        cancelButtonText: 'Cancelar'
      }).then((result) => {
        if (!result.isConfirmed) return;

        showLoading('Enviando nota para a SEFAZ...');

        fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
          },
          body: JSON.stringify({ nota_id: notaId })
        })
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              Swal.fire({
                icon: 'success',
                title: 'Enviada!',
                text: data.message || 'A nota foi enviada para processamento.'
              });
              const row = pageRoot.querySelector(`#nota-row-${notaId}`);
              if (row) {
                row.style.transition = 'opacity 0.5s ease';
                row.style.opacity = '0';
                setTimeout(() => row.remove(), 500);
              }
            } else {
              Swal.fire({
                icon: 'error',
                title: 'Erro!',
                text: data.message || 'Ocorreu um erro ao enviar a nota.'
              });
            }
          })
          .catch((error) => {
            console.error('Erro na requisicao:', error);
            Swal.fire({
              icon: 'error',
              title: 'Erro de Rede!',
              text: 'Nao foi possivel se comunicar com o servidor.'
            });
          });
      });
    });
  });
}

// --- InicializaÃƒÂ§ÃƒÂ£o ---

function initSearchAutocompletePolicy(root = document) {
    const selectors = [
        'input[type="search"]',
        'input[id*="search"]',
        'input[name*="search"]',
        'input[id*="busca"]',
        'input[name*="busca"]',
        'input[placeholder*="Buscar"]',
        'input[placeholder*="buscar"]',
        'input[placeholder*="Search"]',
        'input[placeholder*="search"]',
        'input[name="termo"]'
    ];

    root.querySelectorAll(selectors.join(',')).forEach((input) => {
        if (input.dataset.autocompletePolicyApplied === '1') return;
        input.dataset.autocompletePolicyApplied = '1';
        input.setAttribute('autocomplete', 'off');
        input.setAttribute('autocorrect', 'off');
        input.setAttribute('autocapitalize', 'off');
        input.setAttribute('spellcheck', 'false');

        if (input.form && input.form.dataset.autocompletePolicyApplied !== '1') {
            input.form.dataset.autocompletePolicyApplied = '1';
            input.form.setAttribute('autocomplete', 'off');
        }
    });
}

function releaseBootingState() {
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            document.documentElement.classList.remove('booting');
        });
    });
}

function runInitializers() {
    showFlashMessage();
    // LÃƒÂ³gica global que roda em todas as cargas de pÃƒÂ¡gina/ajax
    initTooltips(document);
    if (!window.__navbarSyncedOnce) {
        window.__navbarSyncedOnce = true;
        syncNavbarWithServerIfNeeded(true);
    }
    initMigrationTenantSelect(document);
    initNestedNavbarSubmenus(document);
    initSearchAutocompletePolicy(document);
    initGenericAutocomplete(document);
    initNcmMaintenance();
    initFiscalListDelegation();
    initFiscalList(document);
    initProdutoOrigemMercadoriaSelect(document);

    // MÃƒÂ³dulos especÃƒÂ­ficos de pÃƒÂ¡gina
    const initializers = [
        initListaEventos,
        () => {
            if (typeof initReprocessarLotes === 'function') {
                initReprocessarLotes();
            }
        },
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
            // A inicializaÃƒÂ§ÃƒÂ£o de PovoamentoLotes foi movida para o prÃƒÂ³prio arquivo (povoamento_lotes.js)
            // para garantir a execuÃƒÂ§ÃƒÂ£o correta e eliminar condiÃƒÂ§ÃƒÂµes de corrida.
        },
        () => {
            const empresaModule = window.OneTech && window.OneTech.EmpresaForm;
            if (empresaModule) {
                const root = document.querySelector(empresaModule.SELECTOR_ROOT);
                if (root) empresaModule.init(root);
            }
        },
        () => {
            if (window.OneTech && window.OneTech.Permissions) {
                const mainContent = document.getElementById('main-content');
                const root = (mainContent && mainContent.querySelector(OneTech.Permissions.SELECTOR_ROOT))
                    || document.querySelector(OneTech.Permissions.SELECTOR_ROOT);
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
        },
        () => {
            if (window.OneTech && window.OneTech.ReprocessarLotes) {
                const root = document.querySelector(window.OneTech.ReprocessarLotes.SELECTOR_ROOT);
                if (root) window.OneTech.ReprocessarLotes.init(root);
            }
        },
        () => {
            initEmitirNfeList(document);
        },
        () => {
            initCriarNfeSaida(document);
        }
    ];
    initializers.forEach(init => {
        if (typeof init === 'function') {
            init();
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    releaseBootingState();
    runInitializers();
});

document.addEventListener("ajaxContentLoaded", () => {
    runInitializers();
});





















































