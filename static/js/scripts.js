// ============================================================================
// ARQUIVO scripts.js - ARQUITETURA AJAX REATORADA (COM BOTOES DE ACAO)
// ============================================================================

// Aplica o tema salvo no localStorage (antes do paint)
const temaSalvo = localStorage.getItem("tema");
if (temaSalvo && temaSalvo !== "light") { // 'light' Ã© o tema padrÃ£o sem classe
  document.documentElement.classList.add(temaSalvo);
}
document.documentElement.classList.add("theme-ready");

// Temas disponÃ­veis
const availableThemes = ['light', 'dark', 'azul'];

// FunÃ§Ã£o para obter o prÃ³ximo tema
function getNextTheme(currentTheme) {
  const currentIndex = availableThemes.indexOf(currentTheme);
  const nextIndex = (currentIndex + 1) % availableThemes.length;
  return availableThemes[nextIndex];
}

// FunÃ§Ã£o para aplicar o tema
function applyTheme(theme) {
  document.documentElement.classList.remove('light', 'dark', 'azul'); // Remove todos os temas
  if (theme !== 'light') { // 'light' Ã© o tema padrÃ£o sem classe
    document.documentElement.classList.add(theme);
  }
  localStorage.setItem('tema', theme);
}

// --- FunÃ§Ãµes de Utilidade Global ---

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
    notify('error', 'SessÃ£o expirada. FaÃ§a login novamente.');
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
    // Mapeia a tag 'error' do Django para a classe 'danger' do Bootstrap para estilizaÃ§Ã£o correta.
    if (type === 'error') {
        type = 'danger';
    }
    if (!window.Swal) { console.error("SweetAlert2 nÃ£o encontrada."); return; }
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
                console.error(`âŒ Falha ao buscar navbar. Status: ${response.status} ${response.statusText}`);
                throw new Error('Falha ao buscar navbar');
            }
            return response.text();
        })
        .then(html => {
            const navbarContainer = document.getElementById('navbar-container');
            if (navbarContainer) {
                navbarContainer.innerHTML = html;
                initNestedNavbarSubmenus(navbarContainer);
            } else {
                // Silencioso em pÃ¡ginas que nÃ£o tÃªm o container, como a de login.
            }
        })
        .catch(error => {
            console.error('Erro catastrÃ³fico ao carregar o navbar:', error);
            notify('danger', 'NÃ£o foi possÃ­vel carregar o menu de navegaÃ§Ã£o.');
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
    notify('error', 'SessÃ£o expirada. FaÃ§a login novamente.');
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

  // Dispara um evento global para que mÃ³dulos especÃ­ficos possam reagir Ã  resposta.
  document.dispatchEvent(new CustomEvent("ajaxForm:jsonResponse", {
    detail: { form, data }
  }));
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
        notify('error', 'SessÃ£o expirada. FaÃ§a login novamente.');
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
      console.error("âŒ Falha ao carregar conteÃºdo via AJAX:", error);
      notify("danger", "Erro ao carregar a pÃ¡gina.");
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
      console.log('[DEBUG] Resultado Ã© nulo, encerrando.');
      return;
    }

    const declaredType = (form.dataset.responseType || '').toLowerCase();
    const isJson = declaredType === 'json' || (typeof result === 'object' && result !== null && !result.nodeType);
    console.log(`[DEBUG] Resposta Ã© JSON? ${isJson}`);

    if (isJson) {
      console.log('[DEBUG] Chamando handleJsonFormResponse...');
      handleJsonFormResponse(form, result);
    } else {
      console.log('[DEBUG] Chamando handleHtmlFormResponse...');
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
    console.error('âŒ [DEBUG] Erro CAPTURADO na submissÃ£o do formulÃ¡rio AJAX:', err);
    notify('error', 'Falha ao processar a requisiÃ§Ã£o. Verifique o console.');
  }
});

document.body.addEventListener('click', async (e) => {
  // Handler para paginaÃ§Ã£o/ordenaÃ§Ã£o
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
      console.error('âŒ AJAX link error:', err);
      notify('error', 'Falha ao carregar a pÃ¡gina.');
    }
    return;
  }

  // Handler para links AJAX genÃ©ricos
  const ajaxLink = e.target.closest(".ajax-link");
  if (ajaxLink && !ajaxLink.hasAttribute('data-bs-toggle')) {
      e.preventDefault();
      loadAjaxContent(ajaxLink.href);
      return;
  }
  
  // Handler para o botÃ£o Editar genÃ©rico
  const btnEditar = e.target.closest('#btn-editar');
  if (btnEditar && !btnEditar.disabled && !btnEditar.hasAttribute('data-bs-toggle')) {
      e.preventDefault();
      const href = btnEditar.getAttribute('data-href');
      if (href) {
          loadAjaxContent(href);
      }
      return;
  }

  // Handler para o botÃ£o Excluir genÃ©rico
  const btnExcluir = e.target.closest('#btn-excluir');
  if (btnExcluir && !btnExcluir.disabled) {
      e.preventDefault();

      const mainContent = document.getElementById('main-content');
      const identificadorTela = mainContent.querySelector("#identificador-tela");
      if (!identificadorTela) return;

      const urlExcluir = identificadorTela.dataset.urlExcluir;
      const seletorCheckbox = identificadorTela.dataset.seletorCheckbox;
      const entidadePlural = identificadorTela.dataset.entidadePlural || 'itens';

      const selectedIds = Array.from(mainContent.querySelectorAll(`${seletorCheckbox}:checked`)).map(cb => cb.value);

      if (selectedIds.length === 0) {
          mostrarMensagem('warning', 'Nenhum item selecionado para exclusÃ£o.');
          return;
      }

      Swal.fire({
          title: 'VocÃª tem certeza?',
          text: `VocÃª estÃ¡ prestes a excluir ${selectedIds.length} ${entidadePlural}. Esta aÃ§Ã£o nÃ£o pode ser desfeita.`,
          icon: 'warning',
          showCancelButton: true,
          confirmButtonColor: '#d33',
          cancelButtonColor: '#3085d6',
          confirmButtonText: 'Sim, excluir!',
          cancelButtonText: 'Cancelar'
      }).then(async (result) => {
          if (result.isConfirmed) {
              try {
                  const response = await fetchWithCreds(urlExcluir, {
                      method: 'POST',
                      headers: {
                          'Content-Type': 'application/json',
                          'X-CSRFToken': getCSRFToken()
                      },
                      body: JSON.stringify({ ids: selectedIds })
                  });

                  const data = await response.json();

                  if (data.success) {
                      const finalizarExclusao = () => {
                          if (data.redirect_url) {
                              loadAjaxContent(data.redirect_url);
                          } else {
                              window.location.reload();
                          }
                      };

                      const errosExclusao = Array.isArray(data.errors) ? data.errors.filter(Boolean) : [];
                      if (errosExclusao.length > 0) {
                          Swal.fire({
                              icon: 'warning',
                              title: 'Exclusao parcial',
                              html: `${data.message || 'Operacao concluida com ressalvas.'}<br><br>${errosExclusao.map(e => `<li class="text-start">${e}</li>`).join('')}`
                          }).then(() => finalizarExclusao());
                      } else {
                          mostrarMensagem('success', data.message);
                          finalizarExclusao();
                      }
                  } else {
                      mostrarMensagem('danger', data.message || 'Ocorreu um erro ao excluir os itens.');
                  }
              } catch (error) {
                  console.error('Erro ao excluir:', error);
                  mostrarMensagem('danger', 'Erro de comunicaÃ§Ã£o com o servidor.');
              }
          }
      });
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

    // LÃ³gica PAI -> FILHO: Se o checkbox mestre for alterado, atualiza todos os filhos.
    if (paiCheckbox && e.target === paiCheckbox) {
        filhosCheckboxes.forEach(filho => {
            filho.checked = paiCheckbox.checked;
        });
    }

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


// --- MÃ³dulos de PÃ¡gina EspecÃ­ficos ---

function initListaEmpresas() {
  const form = document.getElementById('filtro-empresas');
  if (!form || form.dataset.debounced === 'true') return;
  form.dataset.debounced = 'true';

  const handler = debounce(() => {
    form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
  }, 400);

  form.addEventListener('input', (e) => {
    if (e.target.matches('input, select, textarea')) handler();
  });
}


function setupAutocomplete(inputId, apiUrl, displayField = 'text', valueField = 'id', options = {}) {
  const inputElement = document.getElementById(inputId);
  if (!inputElement || inputElement.dataset.autocompleteBound === '1') return;
  inputElement.dataset.autocompleteBound = '1';

  const minLength = Number(options.minLength || 2);
  const queryParam = options.queryParam || 'search';
  const onSelect = typeof options.onSelect === 'function' ? options.onSelect : null;
  let currentDropdown = null;

  const removeDropdown = () => {
    if (currentDropdown) {
      currentDropdown.remove();
      currentDropdown = null;
    }
  };

  const displaySuggestions = (suggestions) => {
    removeDropdown();
    if (!Array.isArray(suggestions) || suggestions.length === 0) return;

    currentDropdown = document.createElement('div');
    currentDropdown.className = 'autocomplete-ncm-list';
    currentDropdown.style.position = 'absolute';
    currentDropdown.style.zIndex = '1080';
    currentDropdown.style.top = 'calc(100% + 4px)';
    currentDropdown.style.left = '0';
    currentDropdown.style.width = '100%';

    suggestions.forEach(item => {
      const suggestionItem = document.createElement('button');
      suggestionItem.type = 'button';
      suggestionItem.className = 'autocomplete-ncm-item';
      suggestionItem.textContent = item[displayField] || item.text || item[valueField] || '';
      suggestionItem.addEventListener('mousedown', (event) => {
        event.preventDefault();
        const chosenValue = item[valueField] || item[displayField] || '';
        inputElement.value = chosenValue;
        inputElement.dataset.selectedValue = item.id || chosenValue;
        removeDropdown();
        inputElement.dispatchEvent(new Event('change', { bubbles: true }));
        if (onSelect) onSelect(item, inputElement);
      });
      currentDropdown.appendChild(suggestionItem);
    });

    inputElement.parentNode.style.position = 'relative';
    inputElement.parentNode.appendChild(currentDropdown);
  };

  const fetchData = async (searchTerm) => {
    const term = (searchTerm || '').trim();
    if (term.length < minLength) {
      removeDropdown();
      return;
    }

    try {
      const url = new URL(apiUrl, window.location.origin);
      url.searchParams.set(queryParam, term);
      const response = await fetchWithCreds(url.toString(), { method: 'GET' }, 'application/json, text/plain, */*');
      if (!response || !response.ok) throw new Error('Erro ao buscar dados da API');
      const data = await response.json();
      const results = Array.isArray(data) ? data : (Array.isArray(data.results) ? data.results : []);
      displaySuggestions(results);
    } catch (error) {
      console.error('Erro no autocompletar:', error);
      removeDropdown();
    }
  };

  const debouncedFetchData = debounce(fetchData, Number(options.delay || 250));

  inputElement.addEventListener('input', (event) => {
    inputElement.dataset.selectedValue = '';
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
        queryParam: input.dataset.autocompleteQueryParam || 'search',
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
    root.querySelectorAll('.nested-submenu-toggle, .nested-submenu-collapse').forEach(el => {
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

  const handler = debounce(() => {
    // O formulÃ¡rio tem a classe 'ajax-form', entÃ£o o manipulador de envio global irÃ¡ capturÃ¡-lo
    form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
  }, 400);

  form.addEventListener('input', (e) => {
    if (e.target.matches('input, select')) {
        handler();
    }
  });
}

// --- InicializaÃ§Ã£o ---

function runInitializers() {
    showFlashMessage();
    // LÃ³gica global que roda em todas as cargas de pÃ¡gina/ajax
    if (document.getElementById('navbar-container')) {
        loadNavbar();
    }
    const mainContent = document.getElementById("main-content");
    if (mainContent && typeof updateButtonStates === 'function') {
        updateButtonStates(mainContent);
    }
    initTooltips(document);
    initMigrationTenantSelect(document);
    initNestedNavbarSubmenus(document);
    initGenericAutocomplete(document);
    initNcmMaintenance();

    // MÃ³dulos especÃ­ficos de pÃ¡gina
    const initializers = [
        initListaEmpresas,
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
            if (window.OneTech && window.OneTech.NotasEntradas) {
                const root = document.querySelector(OneTech.NotasEntradas.SELECTOR_ROOT);
                if (root) OneTech.NotasEntradas.init(root);
            }
        },
        () => {
            // A inicializaÃ§Ã£o de PovoamentoLotes foi movida para o prÃ³prio arquivo (povoamento_lotes.js)
            // para garantir a execuÃ§Ã£o correta e eliminar condiÃ§Ãµes de corrida.
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
        }
    ];
    initializers.forEach(init => {
        if (typeof init === 'function') {
            init();
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    console.log("âœ… DOM completamente carregado. Iniciando scripts.");
    runInitializers();
});

document.addEventListener("ajaxContentLoaded", (event) => {
    console.log("âœ… ConteÃºdo AJAX carregado. Re-inicializando scripts.");
    runInitializers();
});










