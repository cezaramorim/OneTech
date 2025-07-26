// 🌙 Aplica o tema salvo no localStorage (antes do paint)
const temaSalvo = localStorage.getItem("tema");
if (temaSalvo === "dark") {
  document.documentElement.classList.add("dark");
}

// ✅ Objeto global para registrar inicializadores de página
window.pageInitializers = {};

// ✅ Libera a exibição da tela (importante!)
document.documentElement.classList.add("theme-ready");

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

    fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then(response => {
            if (!response.ok) throw new Error(`Erro de rede: ${response.statusText}`);
            return response.text();
        })
        .then(html => {
            mainContent.innerHTML = html; // Substitui o conteúdo do main-content pelo HTML recebido

            // Encontra o identificador da tela dentro do novo conteúdo
            const identificadorTela = mainContent.querySelector("#identificador-tela");
            if (identificadorTela) {
                // Atualiza o data-page do main-content com o data-tela do identificador
                mainContent.dataset.page = identificadorTela.dataset.tela;
                mainContent.dataset.tela = identificadorTela.dataset.tela; // Garante consistência
            } else {
                // Se não encontrar o identificador, tenta limpar o data-page para evitar vinculação incorreta
                mainContent.dataset.page = "";
                mainContent.dataset.tela = "";
                console.warn("⚠️ Identificador de tela (#identificador-tela) não encontrado no conteúdo AJAX. A vinculação de ações pode estar incorreta.");
            }
            
            history.pushState({ ajaxUrl: url }, "", url);
            document.dispatchEvent(new CustomEvent("ajaxContentLoaded", { detail: { url } }));
            console.log("✅ Conteúdo do #main-content atualizado.");
        })
        .catch(error => {
            console.error("❌ Falha ao carregar conteúdo via AJAX:", error);
            mostrarMensagem("danger", "Erro ao carregar a página.");
        });
}

// --- Lógica de Inicialização e Bind de Eventos ---

// --- Funções de Ação de Tabela Genéricas ---
function updateButtonStates(mainContent) {
    if (!mainContent) return; // Garante que o mainContent exista

    const identificadorTela = mainContent.querySelector("#identificador-tela");
    if (!identificadorTela) return; // Garante que o identificadorTela exista

    const selectAllCheckbox = mainContent.querySelector('input[type="checkbox"][id^="select-all-"]');
    const itemCheckboxes = mainContent.querySelectorAll(identificadorTela.dataset.seletorCheckbox);
    const btnEditar = mainContent.querySelector('#btn-editar');
    const btnExcluir = mainContent.querySelector('#btn-excluir');

    const selectedItems = Array.from(itemCheckboxes).filter(cb => cb.checked);
    const hasSelection = selectedItems.length > 0;
    const hasSingleSelection = selectedItems.length === 1;

    if (btnEditar) {
        btnEditar.classList.toggle('disabled', !hasSingleSelection);
        if (hasSingleSelection) {
            const editUrlBase = identificadorTela.dataset.urlEditar;
            const itemId = selectedItems[0].value;
            btnEditar.href = editUrlBase.replace('0', itemId); // Substitui o placeholder '0' pelo ID
        } else {
            btnEditar.removeAttribute('href'); // Remove o href se não houver seleção única
        }
    }

    if (btnExcluir) {
        btnExcluir.disabled = !hasSelection;
    }

    // Update select all checkbox state
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = itemCheckboxes.length > 0 && Array.from(itemCheckboxes).every(c => c.checked);
    }
}

function bindPageSpecificActions() {
    const mainContent = document.getElementById("main-content");
    const page = mainContent?.dataset.page || "";
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
        const ajaxLink = e.target.closest(".ajax-link");
        const btnEditar = e.target.closest('#btn-editar');
        const btnExcluir = e.target.closest('#btn-excluir');
        const mainContent = document.getElementById("main-content");
        const identificadorTela = mainContent ? mainContent.querySelector("#identificador-tela") : null;

        if (ajaxLink) {
            e.preventDefault();
            loadAjaxContent(ajaxLink.href);
        } else if (btnEditar && !btnEditar.classList.contains('disabled')) {
            e.preventDefault();
            loadAjaxContent(btnEditar.href);
        } else if (btnExcluir && !btnExcluir.disabled) {
            e.preventDefault();
            if (!identificadorTela) return; // Ensure identificadorTela exists

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
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = identificadorTela.dataset.urlExcluir;
                form.classList.add('ajax-form');

                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = getCSRFToken();
                form.appendChild(csrfInput);

                selectedItems.forEach(item => {
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = item.name;
                    input.value = item.value;
                    form.appendChild(input);
                });

                document.body.appendChild(form);
                form.submit();
                document.body.removeChild(form);
            }
        }
    });

    // ←– Início do bloco a ser colado
    document.body.addEventListener("submit", e => {
        const form = e.target.closest(".ajax-form");
        if (!form) return;
        e.preventDefault();

        // Tenta ler data-api-url, cai em action caso não exista
        const apiUrl = form.getAttribute("data-api-url") || form.action;
        const method = form.method;
        const formData = new FormData(form);
        const headers = {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCSRFToken()
        };

        fetch(apiUrl, { method, headers, body: formData })
            .then(response => response.json())
            .then(data => {
                console.log("✅ Resposta JSON recebida:", data);
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
                console.error("❌ Erro na submissão do formulário AJAX:", error);
                mostrarMensagem("danger", error.message || "Ocorreu um erro de comunicação.");
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
    });
    bindPageSpecificActions(); // Para a carga inicial da página
    const mainContent = document.getElementById("main-content");
    if (mainContent) {
        updateButtonStates(mainContent);
    }
});
