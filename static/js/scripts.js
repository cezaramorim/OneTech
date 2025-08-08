// ============================================================================
// ARQUIVO scripts.js - VERSÃO FINAL COMPLETA E CORRIGIDA
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
// (Estas funções são declaradas no escopo global para serem acessíveis por todos os scripts)

function getCSRFToken() {
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
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
    console.log("🔁 loadAjaxContent: Carregando URL:", url);
    const mainContent = document.getElementById("main-content");
    if (!mainContent) {
        console.error("❌ #main-content não encontrado. Recarregando a página.");
        window.location.href = url;
        return;
    }
    fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then(response => {
            if (!response.ok) throw new Error(`Erro de rede: ${response.status} ${response.statusText}`);
            return response.text();
        })
        .then(html => {
            mainContent.innerHTML = html;
            
            // Re-executa os scripts do conteúdo carregado.
            // Esta é a forma correta de garantir que os scripts de página funcionem.
            Array.from(mainContent.querySelectorAll("script")).forEach( oldScript => {
                const newScript = document.createElement("script");
                Array.from(oldScript.attributes).forEach( attr => newScript.setAttribute(attr.name, attr.value) );
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
    fetch('/accounts/get-navbar/', { headers: { "X-Requested-With": "XMLHttpRequest" } })
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
// TUDO que interage com o DOM deve estar dentro deste listener.
document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ DOM completamente carregado. Iniciando scripts.");

    // 1. Carrega o Navbar
    if (document.getElementById('navbar-container')) {
        loadNavbar();
    }

    // 2. Ajusta o layout inicial
    adjustMainContentPadding();
    const mainContentInitial = document.getElementById("main-content");
    if (mainContentInitial) {
        updateButtonStates(mainContentInitial);
    }

    // 3. Anexa os listeners de eventos globais
    document.body.addEventListener("click", async (e) => {

        // Botão de Logout
        const logoutLink = e.target.closest('#logout-link-superior');
        if (logoutLink) {
            e.preventDefault();
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = logoutLink.href;
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = getCSRFToken(); // Usa a função global
            form.appendChild(csrfInput);
            document.body.appendChild(form);
            form.submit();
            return; // Encerra a execução para este clique
        }

        // Botão de Alternar Tema
        const themeButton = e.target.closest('#btn-alternar-tema-superior');
        if (themeButton) {
            e.preventDefault();
            alternarTema();
            return; // Encerra a execução para este clique
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
                fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken(), 'X-Requested-With': 'XMLHttpRequest' },
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
            const headers = { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": getCSRFToken() };

            fetch(apiUrl, { method, headers, body: formData })
                .then(response => {
                    if (response.status === 401) {
                        return response.json().then(data => {
                            window.location.href = data.redirect_url;
                            throw new Error('Sessão expirada.');
                        });
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
                    if (error.message !== 'Sessão expirada.') {
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
