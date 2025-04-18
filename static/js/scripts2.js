// ✅ OneTech - scripts.js - Versão completa e estável

// 🌙 Aplicar tema salvo no carregamento
function aplicarTemaSalvo() {
  const temaSalvo = localStorage.getItem('tema');
  const html = document.documentElement;
  const body = document.body;
  const sidebar = document.querySelector('.sidebar');

  const isEscuro = temaSalvo === 'escuro';
  html.classList.toggle('dark', isEscuro);
  body.classList.toggle('dark', isEscuro);
  if (sidebar) sidebar.classList.toggle('dark', isEscuro);
}

// 🔗 Bind de links AJAX
function bindAjaxLinks() {
  const links = document.querySelectorAll('a.ajax-link');
  links.forEach(link => {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      loadAjaxContent(this.href);
    });
  });
}

// 🧠 Função externa para atualizar botões (será preenchida dinamicamente)
let atualizarBotoesGlobal = () => {};

// 📌 Listener de checkbox centralizado (nunca recriado)
function globalCheckboxListener(e) {
  if (e.target && e.target.matches('input[type="checkbox"]')) {
    atualizarBotoesGlobal();
  }
}
document.body.addEventListener('change', globalCheckboxListener);

// 🔄 Carregamento AJAX
function loadAjaxContent(url) {
  const mainContent = document.getElementById('main-content');

  fetch(url, {
    headers: {
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
    .then(response => response.text())
    .then(html => {
      if (mainContent) {
        mainContent.innerHTML = html;
        aplicarTemaSalvo();
        bindAjaxLinks();
        bindCheckboxActions();
        document.dispatchEvent(new Event('ajaxContentLoaded'));
      }
    })
    .catch(error => {
      console.error('Erro ao carregar via AJAX:', error);
    });
}

// ✅ Função global de ativação por checkbox
function bindCheckboxActions() {
  const tela = document.querySelector('#identificador-tela')?.dataset?.tela;
  const checkboxes = document.querySelectorAll('input[type="checkbox"]');
  const btnEditar = document.getElementById('btn-editar');
  const btnExcluir = document.getElementById('btn-excluir');
  const btnVerPerm = document.getElementById('btn-ver-permissoes');
  const btnEditPerm = document.getElementById('btn-permissoes');

  if (!checkboxes.length) return;

  const atualizarBotoes = () => {
    const selecionados = Array.from(checkboxes).filter(cb => cb.checked);
    const apenasUm = selecionados.length === 1;
    const temSelecionado = selecionados.length > 0;

    if (tela === 'lista-grupos') {
      if (btnVerPerm) btnVerPerm.disabled = !apenasUm;
      if (btnEditar) btnEditar.disabled = !apenasUm;
      if (btnExcluir) btnExcluir.disabled = !temSelecionado;
    }

    if (tela === 'gerenciar-permissoes-grupo-selector') {
      if (btnEditPerm) btnEditPerm.disabled = !apenasUm;
    }

    if (tela === 'lista-usuarios') {
      if (btnEditar) btnEditar.disabled = !apenasUm;
      if (btnExcluir) btnExcluir.disabled = !temSelecionado;
    }

    if (tela === 'selecionar-usuario-permissoes') {
      if (btnEditar) btnEditar.disabled = !apenasUm;
      if (btnExcluir) btnExcluir.disabled = !temSelecionado;
    }
  };

  atualizarBotoesGlobal = atualizarBotoes;
  atualizarBotoes();

  // ✅ Botões por tela
  if (btnEditar && tela === 'lista-usuarios') {
    btnEditar.onclick = () => {
      const selecionado = Array.from(checkboxes).find(cb => cb.checked);
      if (selecionado) {
        loadAjaxContent(`/accounts/usuarios/${selecionado.value}/editar/`);
      }
    };
  }

  if (btnExcluir && tela === 'lista-usuarios') {
    btnExcluir.onclick = () => {
      const selecionados = Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.value);
      if (selecionados.length) {
        console.log("Excluir usuários:", selecionados);
      }
    };
  }

  if (btnVerPerm && tela === 'lista-grupos') {
    btnVerPerm.onclick = () => {
      const selecionado = Array.from(checkboxes).find(cb => cb.checked);
      if (selecionado) {
        loadAjaxContent(`/accounts/grupos/${selecionado.value}/ver-permissoes/`);
      }
    };
  }

  if (btnEditar && tela === 'lista-grupos') {
    btnEditar.onclick = () => {
      const selecionado = Array.from(checkboxes).find(cb => cb.checked);
      if (selecionado) {
        loadAjaxContent(`/accounts/grupos/${selecionado.value}/editar/`);
      }
    };
  }

  if (btnEditPerm && tela === 'gerenciar-permissoes-grupo-selector') {
    btnEditPerm.onclick = () => {
      const selecionado = Array.from(checkboxes).find(cb => cb.checked);
      if (selecionado) {
        loadAjaxContent(`/accounts/grupos/${selecionado.value}/permissoes/`);
      }
    };
  }
}

// 📢 Alerta com Bootstrap
function mostrarAlertaBootstrap(mensagem, tipo = "success") {
  const container = document.getElementById("alert-container") || criarContainerDeAlertas();
  const alerta = document.createElement("div");
  alerta.className = `alert alert-${tipo} alert-dismissible fade show shadow-sm mt-2`;
  alerta.setAttribute("role", "alert");
  alerta.innerHTML = `${mensagem}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>`;
  container.appendChild(alerta);
  setTimeout(() => alerta.classList.remove("show"), 5000);
  setTimeout(() => alerta.remove(), 5500);
}

function criarContainerDeAlertas() {
  const container = document.createElement("div");
  container.id = "alert-container";
  container.className = "position-fixed top-0 start-50 translate-middle-x mt-3 z-3";
  container.style.width = "90%";
  container.style.maxWidth = "600px";
  document.body.appendChild(container);
  return container;
}

// 📌 Seletor de grupo (permissões por grupo)
function initSeletorGrupoPermissoes() {
  const selectGrupo = document.getElementById('grupo-selecionado');
  const btnAvancar = document.getElementById('btn-avancar');

  if (selectGrupo && btnAvancar) {
    selectGrupo.addEventListener('change', () => {
      btnAvancar.disabled = !selectGrupo.value;
    });

    btnAvancar.addEventListener('click', () => {
      const grupoId = selectGrupo.value;
      if (grupoId) {
        const url = `/accounts/grupos/${grupoId}/permissoes/`;
        if (window.loadAjaxContent) {
          loadAjaxContent(url);
        } else {
          window.location.href = url;
        }
      }
    });
  }
}

// 🚀 DOM pronto
document.addEventListener('DOMContentLoaded', () => {
  const themeToggle = document.getElementById('theme-toggle');
  const hamburgerToggle = document.getElementById('hamburger-toggle');

  aplicarTemaSalvo();
  bindAjaxLinks();
  bindCheckboxActions();
  initSeletorGrupoPermissoes();

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const html = document.documentElement;
      const body = document.body;
      const sidebar = document.querySelector('.sidebar');
      const modoEscuro = !html.classList.contains('dark');

      html.classList.toggle('dark', modoEscuro);
      body.classList.toggle('dark', modoEscuro);
      if (sidebar) sidebar.classList.toggle('dark', modoEscuro);
      localStorage.setItem('tema', modoEscuro ? 'escuro' : 'claro');
    });
  }

  if (hamburgerToggle) {
    hamburgerToggle.addEventListener('click', () => {
      document.querySelectorAll('.menu-list').forEach(menu => menu.classList.toggle('show'));
    });
  }

  document.addEventListener('submit', async (e) => {
    const form = e.target;
    if (!form.classList.contains('ajax-form')) return;
    e.preventDefault();

    const url = form.action || form.dataset.url;
    const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]')?.value;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrfToken,
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams(new FormData(form)),
      });

      const contentType = response.headers.get('Content-Type');

      if (contentType?.includes('application/json')) {
        const data = await response.json();
        if (data.message)
          mostrarAlertaBootstrap(data.message, data.success ? 'success' : 'danger');

        if (data.redirect_url) {
          loadAjaxContent(data.redirect_url);
        }
      } else {
        const html = await response.text();
        const mainContent = document.getElementById('main-content');
        if (mainContent) {
          mainContent.innerHTML = html;
          aplicarTemaSalvo();
          bindAjaxLinks();
          bindCheckboxActions();
          document.dispatchEvent(new Event('ajaxContentLoaded'));
        }
      }
    } catch (err) {
      mostrarAlertaBootstrap("Erro de rede: " + err.message, "danger");
    }
  });

  window.addEventListener('popstate', () => {
    loadAjaxContent(window.location.pathname);
  });
});

// 🔄 AJAX content loaded
document.addEventListener('ajaxContentLoaded', () => {
  bindCheckboxActions();
});
