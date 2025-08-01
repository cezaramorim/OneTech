function getCSRFToken() {
  const name = "csrftoken";
  const cookies = document.cookie.split(";");
  for (let cookie of cookies) {
    const trimmed = cookie.trim();
    if (trimmed.startsWith(name + "=")) {
      return decodeURIComponent(trimmed.substring(name.length + 1));
    }
  }
  return "";
}

function updateActiveMenuLink(url) {
    const currentPath = new URL(url, window.location.origin).pathname;
    const menuLinks = document.querySelectorAll('.sidebar .ajax-link, .navbar-superior .ajax-link');

    menuLinks.forEach(link => {
        const linkPath = new URL(link.href).pathname;
        if (linkPath === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

function closeAllCollapses() {
    document.querySelectorAll('.collapse.show').forEach(collapseElement => {
        const bsCollapse = bootstrap.Collapse.getInstance(collapseElement);
        if (bsCollapse) {
            bsCollapse.hide();
        } else {
            // Fallback if Bootstrap's JS is not fully initialized for this element
            collapseElement.classList.remove('show');
        }
    });
}

function initLayout() {
    const savedLayout = localStorage.getItem('layout_preferencia') || 'layout-superior';
    console.log(`DEBUG: Initializing layout to: ${savedLayout}`);
    document.body.classList.remove('layout-lateral', 'layout-superior');
    document.body.classList.add(savedLayout);
}

function alternarLayout() {
    console.log("DEBUG: alternarLayout() called.");
    const isLateral = document.body.classList.contains('layout-lateral');
    const newLayout = isLateral ? 'layout-superior' : 'layout-lateral';
    document.body.classList.remove('layout-lateral', 'layout-superior');
    document.body.classList.add(newLayout);
    localStorage.setItem('layout_preferencia', newLayout);
    console.log(`DEBUG: Layout changed to: ${newLayout}`);
}

 function alternarTema() {
  const isDark = document.documentElement.classList.toggle('dark');
  localStorage.setItem('tema', isDark ? 'dark' : 'light');
  console.log(`DEBUG: Tema alterado para: ${ isDark ? 'dark' : 'light' }`);

  // ── Atualiza classes do navbar para herdar contraste correto ──
  const navbar = document.querySelector('.navbar-superior');
  if (navbar) {
    navbar.classList.toggle('navbar-dark', isDark);
    navbar.classList.toggle('navbar-light', !isDark);
  }
 }


document.addEventListener("DOMContentLoaded", () => {
    // --- LÓGICA UNIFICADA DE INICIALIZAÇÃO ---

    // 1. Inicialização do Layout
    initLayout();
    closeAllCollapses(); // Fecha todos os collapses ao carregar a página

    // 2. Listeners de Eventos Globais (Click)
    document.addEventListener('click', (event) => {
        // Listener para o botão de alternar layout
        const toggleButton = event.target.closest('#btn-alternar-layout, #btn-alternar-layout-superior');
        if (toggleButton) {
            console.log("DEBUG: Layout toggle button clicked:", toggleButton);
            event.preventDefault();
            alternarLayout();
            closeAllCollapses(); // Fecha todos os collapses ao alternar layout
        }

        // ─── b) Toggle de tema ──────────────────────────────────────
        const themeButton = event.target.closest(
        '#btn-alternar-tema, #btn-alternar-tema-superior'
        );
        if (themeButton) {
        event.preventDefault();
        alternarTema();
        closeAllCollapses();
        }
    });

    // Impede que o dropdown feche ao clicar em um item para expandir/recolher
    document.querySelectorAll('.dropdown-menu a[data-bs-toggle="collapse"]').forEach(element => {
        element.addEventListener('click', e => {
            e.stopPropagation();
        });
    });

    // Listener para o link de logout no menu superior
    const logoutLink = document.getElementById('logout-link-superior');
    if (logoutLink) {
        logoutLink.addEventListener('click', function(e) {
            e.preventDefault();
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = this.href;
            const csrfToken = getCSRFToken();
            if (csrfToken) {
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = csrfToken;
                form.appendChild(csrfInput);
            }
            document.body.appendChild(form);
            form.submit();
        });
    }
});

document.addEventListener("ajaxContentLoaded", (event) => {
    // bindPageSpecificActions(); // Permanece em scripts.js
    const url = event.detail?.url || window.location.href;
    updateActiveMenuLink(url);
    closeAllCollapses(); // Fecha todos os collapses ao carregar conteúdo AJAX
});