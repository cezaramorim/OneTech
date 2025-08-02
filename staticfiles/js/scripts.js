// 🌙 Aplica o tema salvo no localStorage (antes do paint)
const temaSalvo = localStorage.getItem("tema");
const isDarkInit = temaSalvo === "dark";
if (isDarkInit) {
  document.documentElement.classList.add("dark");
}

// ✅ Objeto global para registrar inicializadores de página
window.pageInitializers = {};

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

function mostrarMensagem(type, message) {
    let container = document.getElementById("toast-container");
    // Se o container não existir, cria e anexa ao body. Abordagem robusta.
    if (!container) {
        console.warn("Container de toast não encontrado. Criando um novo.");
        container = document.createElement('div');
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.id = 'toast-container';
        container.style.zIndex = '1090'; // Garante que fique acima de outros elementos
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

// --- Carregamento de Conteúdo AJAX ---

function loadAjaxContent(url) {
    console.log("🔁 loadAjaxContent: Iniciando carregamento para URL:", url);
    const mainContent = document.getElementById("main-content");
    if (!mainContent) {
        console.error("❌ #main-content não encontrado. Recarregando a página.");
        window.location.href = url;
        return;
    }

    console.log("DEBUG: Enviando requisição AJAX com cabeçalho X-Requested-With: XMLHttpRequest");
    fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then(response => {
            if (response.status === 401) {
                return response.json().then(data => {
                    window.location.href = data.redirect_url;
                    throw new Error('Sessão expirada. Redirecionando para login.');
                });
            }
            if (!response.ok) {
                throw new Error(`Erro de rede: ${response.statusText}`);
            }
            return response.text();
        })
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const scriptTag = doc.querySelector('script[src]');
            
            // Injeta o HTML principal primeiro
            mainContent.innerHTML = doc.body.innerHTML;

            // Função para finalizar o processo
            const finishLoading = () => {
                const identificadorTela = mainContent.querySelector("#identificador-tela");
                if (identificadorTela) {
                    mainContent.dataset.page = identificadorTela.dataset.tela;
                    mainContent.dataset.tela = identificadorTela.dataset.tela;
                } else {
                    mainContent.dataset.page = "";
                    mainContent.dataset.tela = "";
                    console.warn("⚠️ Identificador de tela (#identificador-tela) não encontrado no conteúdo AJAX. A vinculação de ações pode estar incorreta.");
                }
                
                history.pushState({ ajaxUrl: url }, "", url);
                document.dispatchEvent(new CustomEvent("ajaxContentLoaded", { detail: { url } }));
                console.log("✅ Conteúdo e scripts (se houver) do #main-content atualizados.");
            };

            // Se um script for encontrado, carrega-o e depois finaliza.
            // Caso contrário, apenas finaliza.
            if (scriptTag && scriptTag.src) {
                const newScript = document.createElement('script');
                // Copia todos os atributos importantes
                newScript.src = scriptTag.src;
                if (scriptTag.defer) newScript.defer = true;
                if (scriptTag.async) newScript.async = true;
                
                newScript.onload = finishLoading;
                newScript.onerror = () => {
                    console.error(`❌ Falha ao carregar o script dinâmico: ${scriptTag.src}`);
                    finishLoading(); // Continua mesmo se o script falhar para não travar a navegação
                };
                document.body.appendChild(newScript); // Anexa ao body para garantir a execução
            } else {
                finishLoading();
            }
        })
        .catch(error => {
            if (error.message !== 'Sessão expirada. Redirecionando para login.') {
                console.error("❌ Falha ao carregar conteúdo via AJAX:", error);
                mostrarMensagem("danger", "Erro ao carregar a página.");
            }
        });
}

// --- Lógica de Inicialização e Bind de Eventos ---

// --- Funções de Ação de Tabela Genéricas ---
function updateButtonStates(mainContent) {
    if (!mainContent) {
        return;
    }

    const identificadorTela = mainContent.querySelector("#identificador-tela");
    if (!identificadorTela || !identificadorTela.dataset.seletorCheckbox) {
        return;
    }

    const itemCheckboxes = mainContent.querySelectorAll(identificadorTela.dataset.seletorCheckbox);
    const btnEditar = mainContent.querySelector('#btn-editar');
    const btnExcluir = mainContent.querySelector('#btn-excluir');

    const selectedItems = Array.from(itemCheckboxes).filter(cb => cb.checked);
    const hasSelection = selectedItems.length > 0;
    const hasSingleSelection = selectedItems.length === 1;

    if (btnEditar) {
        btnEditar.disabled = !hasSingleSelection;
        if (btnEditar.disabled) {
            btnEditar.classList.add('disabled');
        } else {
            btnEditar.classList.remove('disabled');
        }
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
        if (btnExcluir.disabled) {
            btnExcluir.classList.add('disabled');
        } else {
            btnExcluir.classList.remove('disabled');
        }
    }
    
    const selectAllCheckbox = mainContent.querySelector('input[type="checkbox"][id^="selecionar-todas-"]');
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = itemCheckboxes.length > 0 && selectedItems.length === itemCheckboxes.length;
    }
}

function bindPageSpecificActions() {
    const mainContent = document.getElementById("main-content");
    const page = mainContent?.dataset.tela || "";
    console.log(`🔎 Binding de ações para a página: ${page}`);
    if (page && window.pageInitializers[page]) {
        console.log(`🚀 Executando inicializador para a página '${page}'.`);
        window.pageInitializers[page]();
    }
}


document.addEventListener("DOMContentLoaded", () => {
    const themeToggle = document.getElementById("theme-toggle");
    if (themeToggle) {
        themeToggle.addEventListener("click", () => {
            const isDark = document.documentElement.classList.toggle("dark");
            localStorage.setItem("tema", isDark ? "dark" : "light");
        });
    }

    document.body.addEventListener("click", async e => {
        console.log("DEBUG: Evento de clique disparado.");
        const btnEditar = e.target.closest('#btn-editar');
        const btnExcluir = e.target.closest('#btn-excluir');
        const mainContent = document.getElementById("main-content");
        const identificadorTela = mainContent ? mainContent.querySelector("#identificador-tela") : null;
        const ajaxLink = e.target.closest(".ajax-link");
        console.log("DEBUG: ajaxLink encontrado:", ajaxLink);

        // CONDIÇÃO ADICIONADA: Ignora links que são componentes do Bootstrap (como dropdowns)
        if (ajaxLink && !ajaxLink.hasAttribute('data-bs-toggle')) {
            console.log("DEBUG: ajaxLink.href:", ajaxLink.href);
            e.preventDefault();
            loadAjaxContent(ajaxLink.href);
        } else if (btnEditar && !btnEditar.disabled) {
            e.preventDefault();
            const href = btnEditar.getAttribute('data-href');
            if(href) loadAjaxContent(href);
        } else if (btnExcluir && !btnExcluir.disabled) {
            e.preventDefault();
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
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken(),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({ ids: ids })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.sucesso) {
                        mostrarMensagem('success', data.mensagem);
                        loadAjaxContent(window.location.pathname); // Recarrega a lista
                    } else {
                        mostrarMensagem('danger', data.mensagem || 'Erro desconhecido.');
                    }
                })
                .catch(error => {
                    console.error('Erro na exclusão:', error);
                    mostrarMensagem('danger', 'Erro de comunicação ao tentar excluir.');
                });
            }
        }
    });

    // ←– Início do bloco a ser colado
    document.body.addEventListener("submit", e => {
        const form = e.target.closest(".ajax-form");
        if (!form) return;
        e.preventDefault();

        const apiUrl = form.getAttribute("data-api-url") || form.action;
        const method = form.method;
        const formData = new FormData(form);
        const headers = {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCSRFToken()
        };

        fetch(apiUrl, { method, headers, body: formData })
            .then(response => {
                // ✅ Se a resposta for 401 (Não Autorizado), o middleware retornou JSON
                if (response.status === 401) {
                    return response.json().then(data => {
                        // Força o redirecionamento para a página de login
                        window.location.href = data.redirect_url;
                        // Lança um erro para interromper a cadeia de promessas
                        throw new Error('Sessão expirada. Redirecionando para login.');
                    });
                }
                // Se não for 401, continua o fluxo normal
                return response.json();
            })
            .then(data => {
                console.log("✅ Resposta JSON recebida:", data);
                if (data.success) {
                    document.dispatchEvent(new CustomEvent("ajaxFormSuccess", { detail: { form, responseJson: data } }));
                }
                if (data.redirect_url) {
                    // Se a URL de redirecionamento for a mesma da página atual, recarrega a página
                    if (window.location.href === data.redirect_url) {
                        window.location.reload();
                    } else {
                        window.location.href = data.redirect_url;
                    }
                } else if (data.message || data.mensagem) {
                    const messageText = data.message || data.mensagem;
                    const messageType = data.success ? "success" : "danger";
                    mostrarMensagem(messageType, messageText);
                }
            })
            .catch(error => {
                // Evita mostrar a mensagem de erro de "Sessão expirada" para o usuário final
                if (error.message !== 'Sessão expirada. Redirecionando para login.') {
                    console.error("❌ Erro na submissão do formulário AJAX:", error);
                    mostrarMensagem("danger", error.message || "Ocorreu um erro de comunicação.");
                }
            });
    });
    // ←– Fim do bloco a ser colado


    window.addEventListener("popstate", e => {
        if (e.state && e.state.ajaxUrl) {
            loadAjaxContent(e.state.ajaxUrl);
        }
    });

    document.body.addEventListener("change", e => {
        const mainContent = document.getElementById("main-content");
        const identificadorTela = mainContent ? mainContent.querySelector("#identificador-tela") : null;
        // Check if the change event is from a checkbox within a table that has data-seletor-checkbox
        if (e.target.type === 'checkbox' && identificadorTela && identificadorTela.dataset.seletorCheckbox) {
            const itemCheckbox = e.target.closest(identificadorTela.dataset.seletorCheckbox);
            const selectAllCheckbox = e.target.id.startsWith('select-all-');

            if (itemCheckbox || selectAllCheckbox) {
                updateButtonStates(mainContent);
            }
        }
    });

    document.addEventListener("ajaxContentLoaded", () => {
        bindPageSpecificActions();
        const mainContent = document.getElementById("main-content");
        if (mainContent) {
            updateButtonStates(mainContent);
        }
        adjustMainContentPadding(); // Ajusta o padding após o carregamento AJAX
    });

    bindPageSpecificActions(); // Para a carga inicial da página
    const mainContent = document.getElementById("main-content");
    if (mainContent) {
        updateButtonStates(mainContent);
    }
    adjustMainContentPadding(); // Ajusta o padding na carga inicial
});

function adjustMainContentPadding() {
    const navbarSuperior = document.querySelector('.navbar-superior');
    const mainContent = document.getElementById('main-content');
    if (navbarSuperior && mainContent) {
        const navbarHeight = navbarSuperior.offsetHeight;
        mainContent.style.paddingTop = `${navbarHeight}px`;
    }
}
