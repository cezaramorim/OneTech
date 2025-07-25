// 🌙 Aplica o tema salvo no localStorage (antes do paint)
const temaSalvo = localStorage.getItem("tema");
if (temaSalvo === "dark") {
  document.documentElement.classList.add("dark");
}

// ✅ Objeto global para registrar inicializadores de página
window.pageInitializers = window.pageInitializers || {};

// ✅ Libera a exibição da tela (importante!)
document.documentElement.classList.add("theme-ready");

// --- Funções de Utilidade Global ---

function getCSRFToken() {
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
}

function mostrarMensagem(type, message) {
    const container = document.getElementById("toast-container");
    if (!container) {
        console.error("Elemento #toast-container não encontrado para exibir a mensagem.");
        return;
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
        console.error("❌ loadAjaxContent: Elemento #main-content não encontrado. Recarregando a página inteira.");
        window.location.href = url;
        return;
    }

    fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then(response => {
            if (!response.ok) throw new Error(`Erro de rede: ${response.statusText}`);
            return response.text();
        })
        .then(html => {
            const tempDiv = document.createElement("div");
            tempDiv.innerHTML = html;
            const newMainContent = tempDiv.querySelector("#main-content");

            if (newMainContent) {
                mainContent.innerHTML = newMainContent.innerHTML;
                // Atualiza os atributos data-* do container principal
                Object.keys(newMainContent.dataset).forEach(key => {
                    mainContent.dataset[key] = newMainContent.dataset[key];
                });

                history.pushState({ ajaxUrl: url }, "", url);
                document.dispatchEvent(new CustomEvent("ajaxContentLoaded", { detail: { url } }));
                console.log("✅ loadAjaxContent: Conteúdo do #main-content atualizado com sucesso.");
            } else {
                console.warn("⚠️ loadAjaxContent: #main-content não encontrado na resposta. A página será recarregada.");
                window.location.href = url;
            }
        })
        .catch(error => {
            console.error("❌ loadAjaxContent: Falha ao carregar conteúdo via AJAX:", error);
            mostrarMensagem("danger", "Erro ao carregar a página.");
        });
}

// --- Lógica de Inicialização e Bind de Eventos ---

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

    document.body.addEventListener("click", e => {
        const ajaxLink = e.target.closest(".ajax-link");
        if (ajaxLink) {
            e.preventDefault();
            loadAjaxContent(ajaxLink.href);
        }
    });

    document.body.addEventListener("submit", e => {
        const form = e.target.closest(".ajax-form");
        if (!form) return;
        e.preventDefault();
        const url = form.action;
        const method = form.method;
        const formData = new FormData(form);
        const headers = { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": getCSRFToken() };

        fetch(url, { method, headers, body: formData })
            .then(response => {
                const contentType = response.headers.get("content-type");
                if (!contentType || !contentType.includes("application/json")) {
                    throw new Error("A resposta do servidor não é JSON.");
                }
                return response.json();
            })
            .then(data => {
                console.log("✅ Resposta JSON recebida:", data);
                if (data.success) {
                    document.dispatchEvent(new CustomEvent("ajaxFormSuccess", { detail: { form, responseJson: data } }));
                }
                if (data.message || data.mensagem) {
                    const msg = data.message || data.mensagem;
                    const type = data.success ? "success" : "danger";
                    mostrarMensagem(type, msg);
                }
                if (data.redirect_url) {
                    setTimeout(() => loadAjaxContent(data.redirect_url), 1500);
                }
            })
            .catch(error => {
                console.error("❌ Erro na submissão do formulário AJAX:", error);
                mostrarMensagem("danger", error.message || "Erro de comunicação.");
            });
    });

    window.addEventListener("popstate", e => {
        if (e.state && e.state.ajaxUrl) {
            loadAjaxContent(e.state.ajaxUrl);
        }
    });

    document.addEventListener("ajaxContentLoaded", bindPageSpecificActions);
    bindPageSpecificActions(); // Para a carga inicial da página
});