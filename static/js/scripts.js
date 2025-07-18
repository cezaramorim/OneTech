// 🌙 Aplica o tema dark o mais cedo possível (antes do paint)
const temaSalvo = localStorage.getItem("tema");
if (temaSalvo === "dark") {
  document.documentElement.classList.add("dark");
} else {
  document.documentElement.classList.remove("dark");
}

// ✅ Libera a exibição da tela (importante!)
document.documentElement.classList.add("theme-ready");

document.addEventListener("ajaxContentLoaded", (event) => {
  bindPageSpecificActions();
  const url = event.detail?.url || window.location.href;
  updateActiveMenuLink(url);
});

function mostrarMensagemBootstrap(mensagem, tipo = "success") {
  const container = document.getElementById("alert-container");
  if (!container) return;
  const alerta = document.createElement("div");
  alerta.className = `alert alert-${tipo} alert-dismissible fade show shadow-sm`;
  alerta.role = "alert";
  alerta.innerHTML = `${mensagem}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>`;
  container.appendChild(alerta);
  setTimeout(() => {
    alerta.classList.remove("show");
    alerta.classList.add("hide");
    alerta.addEventListener("transitionend", () => alerta.remove());
  }, 5000);
}

function mostrarMensagemSucesso(mensagem) {
  mostrarMensagemBootstrap(mensagem, "success");
}

function mostrarMensagemErro(mensagem) {
  mostrarMensagemBootstrap(mensagem, "danger");
}

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

function loadAjaxContent(url, forceFullLoad = false) {
  console.log("🔁 loadAjaxContent: Iniciando carregamento para URL:", url);
  const currentActiveContent = document.querySelector("#main-content") || document.querySelector("main");
  if (!currentActiveContent) {
    console.error("❌ loadAjaxContent: Não foi possível encontrar o elemento de conteúdo ativo para substituição (#main-content ou main).");
    return;
  }
  const headers = forceFullLoad ? {} : { "X-Requested-With": "XMLHttpRequest" };
  fetch(url, { headers })
    .then(response => {
      if (!response.ok) {
        console.error(`❌ loadAjaxContent: Erro na resposta HTTP: ${response.status} - ${response.statusText}`);
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }
      return response.text();
    })
    .then(html => {
      console.log("✅ loadAjaxContent: HTML recebido. Tamanho:", html.length);
      const tempDiv = document.createElement("div");
      tempDiv.innerHTML = html;
      const newActiveContent = tempDiv.querySelector("#main-content") || tempDiv.querySelector("main");
      if (!newActiveContent) {
        console.warn("⚠️ loadAjaxContent: Conteúdo não encontrado ou estrutura inválida na resposta HTML (novo conteúdo - #main-content ou main).");
        return;
      }
      const campoBuscaAntigo = currentActiveContent.querySelector("#busca-nota") || currentActiveContent.querySelector("#busca-empresa");
      if (campoBuscaAntigo) {
        const valor = campoBuscaAntigo.value || "";
        const posicao = campoBuscaAntigo.selectionStart || valor.length;
        const idCampo = campoBuscaAntigo.id;
        currentActiveContent.replaceWith(newActiveContent);
        const campoBuscaNovo = newActiveContent.querySelector(`#${idCampo}`);
        if (campoBuscaNovo) {
          campoBuscaNovo.focus();
          campoBuscaNovo.setSelectionRange(posicao, posicao);
        }
        console.log(`✅ loadAjaxContent: Conteúdo com #${idCampo} atualizado preservando foco.`);
      } else {
        currentActiveContent.replaceWith(newActiveContent);
        console.log("✅ loadAjaxContent: Novo conteúdo carregado (normal update).");
      }
      setTimeout(() => {
        document.dispatchEvent(new CustomEvent("ajaxContentLoaded", { detail: { url: url } }));
      }, 10);
      const mensagemSucesso = localStorage.getItem("mensagem_sucesso");
      if (mensagemSucesso) {
        mostrarMensagemSucesso(mensagemSucesso);
        localStorage.removeItem("mensagem_sucesso");
      }
    })
    .catch(error => {
      console.error("❌ loadAjaxContent: Erro ao carregar conteúdo via AJAX:", error);
      mostrarMensagemErro("Erro ao carregar conteúdo: " + error.message);
    });
}

document.addEventListener("click", e => {
  const target = e.target.closest(".ajax-link");
  if (target) {
    e.preventDefault();
    const url = target.href;
    history.pushState({ ajaxUrl: url }, "", url); // Adicionado para atualizar a URL
    loadAjaxContent(url);
  }
});

document.addEventListener("submit", async e => {
  const form = e.target;
  if (!form.classList.contains("ajax-form")) {
    return;
  }
  e.preventDefault();
  const urlBase = form.dataset.url || form.action;
  const method = form.method.toUpperCase();
  if (method === "GET") {
    const params = new URLSearchParams(new FormData(form));
    const finalUrl = `${urlBase}?${params.toString()}`;
    loadAjaxContent(finalUrl);
    return;
  }
  const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]")?.value;
  try {
    const response = await fetch(urlBase, {
      method: method,
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": csrfToken,
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: new URLSearchParams(new FormData(form))
    });
    const contentType = response.headers.get("Content-Type");
    if (contentType && contentType.includes("application/json")) {
      const data = await response.json();
      if (data.message || data.mensagem) {
        const msg = data.message || data.mensagem;
        if (!data.redirect_url) {
          if (data.success || data.sucesso) {
            mostrarMensagemSucesso(msg);
          } else {
            mostrarMensagemErro(msg);
          }
        }
      }
      if (data.redirect_url) {
        if (data.message || data.mensagem) {
          localStorage.setItem("mensagem_sucesso", data.message || data.mensagem);
        }

        // Força a recarga completa da página se a URL de redirecionamento for a do painel ou raiz
        if (data.redirect_url === '/painel/' || data.redirect_url === '/') {
            console.log("DEBUG: Redirecting to painel or root. Forcing full page reload.");
            window.location.href = data.redirect_url;
            return;
        }

        history.pushState({ ajaxUrl: data.redirect_url }, "", data.redirect_url);
        loadAjaxContent(data.redirect_url);
      }
    } else {
      const html = await response.text();
      const tempDiv = document.createElement("div");
      tempDiv.innerHTML = html;
      const novoMain = tempDiv.querySelector("#main-content") || tempDiv.firstElementChild;
      const mainContent = document.getElementById("main-content");
      if (mainContent && novoMain) {
        mainContent.replaceWith(novoMain);
        document.dispatchEvent(new CustomEvent("ajaxContentLoaded", { detail: { url: urlBase } }));
      } else {
        console.warn("⚠️ Conteúdo não encontrado ou estrutura inválida na resposta HTML.");
      }
    }
  } catch (err) {
    console.warn("Erro capturado no submit AJAX:", err);
    mostrarMensagemErro("Erro ao processar requisição.");
  }
});

window.addEventListener("popstate", e => {
  if (e.state && e.state.ajaxUrl) {
    loadAjaxContent(e.state.ajaxUrl);
  } else {
    loadAjaxContent(window.location.href, true);
  }
});

function setupColumnSorting() {
  const linksOrdenacao = document.querySelectorAll(".ordenar-coluna");
  const urlParamsAtual = new URLSearchParams(window.location.search);
  const ordemCorrente = urlParamsAtual.get("ordem");
  linksOrdenacao.forEach(link => {
    const campoLink = link.dataset.campo;
    const textoOriginal = link.dataset.originalText || link.innerText.replace(/ (▲|▼)$/, "").trim();
    link.dataset.originalText = textoOriginal;
    link.innerHTML = textoOriginal;
    if (ordemCorrente === campoLink) {
      link.innerHTML += ' <span class="arrow asc">&#9650;</span>';
    } else if (ordemCorrente === `-${campoLink}`) {
      link.innerHTML += ' <span class="arrow desc">&#9660;</span>';
    }
    link.addEventListener("click", function (e) {
      e.preventDefault();
      const urlParams = new URLSearchParams(window.location.search);
      const ordemAtualClick = urlParams.get("ordem");
      const novaOrdem = ordemAtualClick === campoLink ? `-${campoLink}` : campoLink;
      urlParams.set("ordem", novaOrdem);
      const novaUrl = `${window.location.pathname}?${urlParams.toString()}`;
      history.pushState({ ajaxUrl: novaUrl }, "", novaUrl);
      loadAjaxContent(novaUrl);
    });
  });
}

function initGenericActionButtons() {
  console.log("DEBUG: initGenericActionButtons iniciada.");
  const idTela = document.getElementById("identificador-tela");
  const btnEditar = document.getElementById("btn-editar");
  const btnExcluir = document.getElementById("btn-excluir");

  if (!idTela || !btnEditar || !btnExcluir) {
    console.log("DEBUG: Elementos principais não encontrados. idTela:", !!idTela, "btnEditar:", !!btnEditar, "btnExcluir:", !!btnExcluir);
    return;
  }

  const { entidadeSingular, entidadePlural, urlEditar, urlExcluir, seletorCheckbox } = idTela.dataset;
  if (!entidadeSingular || !entidadePlural || !urlEditar || !seletorCheckbox) { // urlExcluir pode ser nulo/comentado
    console.log("DEBUG: Atributos data- ausentes. entidadeSingular:", !!entidadeSingular, "entidadePlural:", !!entidadePlural, "urlEditar:", !!urlEditar, "seletorCheckbox:", !!seletorCheckbox);
    return;
  }
  console.log("DEBUG: Data attributes lidos:", { entidadeSingular, entidadePlural, urlEditar, urlExcluir, seletorCheckbox });

  const itemCheckboxes = document.querySelectorAll(seletorCheckbox);
  const selectAllCheckbox = document.querySelector('[id^="select-all-"]');
  if (!itemCheckboxes.length || !selectAllCheckbox) {
    console.log("DEBUG: Checkboxes não encontrados. itemCheckboxes.length:", itemCheckboxes.length, "selectAllCheckbox:", !!selectAllCheckbox);
    return;
  }
  console.log("DEBUG: Checkboxes encontrados. Total de itens:", itemCheckboxes.length);

  function updateButtonStates() {
    const selecionados = document.querySelectorAll(`${seletorCheckbox}:checked`);
    const count = selecionados.length;
    console.log("DEBUG: updateButtonStates - Itens selecionados:", count);

    // Para o botão 'Editar' (tag <a>)
    if (count !== 1) {
      btnEditar.classList.add('disabled'); // Adiciona a classe 'disabled' do Bootstrap
      btnEditar.setAttribute('aria-disabled', 'true'); // Para acessibilidade
      btnEditar.style.pointerEvents = 'none'; // Impede eventos de clique
    } else {
      btnEditar.classList.remove('disabled');
      btnEditar.removeAttribute('aria-disabled');
      btnEditar.style.pointerEvents = 'auto';
    }

    // Para o botão 'Excluir' (tag <button>)
    btnExcluir.disabled = count === 0;

    console.log("DEBUG: updateButtonStates - btnEditar.classList.contains('disabled'):", btnEditar.classList.contains('disabled'), "btnExcluir.disabled:", btnExcluir.disabled);
  }

  selectAllCheckbox.addEventListener("change", () => {
    itemCheckboxes.forEach(checkbox => { checkbox.checked = selectAllCheckbox.checked; });
    updateButtonStates();
  });

  itemCheckboxes.forEach(checkbox => {
    checkbox.addEventListener("change", updateButtonStates);
  });

  btnEditar.addEventListener("click", () => {
    const selecionado = document.querySelector(`${seletorCheckbox}:checked`);
    if (selecionado) {
      // Substitui o '0' na URL base pelo ID do item selecionado
      const finalUrl = urlEditar.replace('/0/', `/${selecionado.value}/`);
      history.pushState({ ajaxUrl: finalUrl }, "", finalUrl);
      loadAjaxContent(finalUrl);
    }
  });

  // Só adiciona o listener de exclusão se a URL de exclusão estiver definida
  if (urlExcluir) {
    btnExcluir.addEventListener("click", () => {
      const selecionados = document.querySelectorAll(`${seletorCheckbox}:checked`);
      const ids = Array.from(selecionados).map(cb => cb.value);
      if (ids.length === 0) return;
      const text = `Excluir ${ids.length} ${ids.length === 1 ? entidadeSingular : entidadePlural}?`;
      Swal.fire({
        title: "Confirmar Exclusão",
        text: text,
        icon: "warning",
        showCancelButton: true,
        confirmButtonText: "Sim, excluir!",
        cancelButtonText: "Cancelar"
      }).then((result) => {
        if (result.isConfirmed) {
          fetch(urlExcluir, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken(), "X-Requested-With": "XMLHttpRequest" },
            body: JSON.stringify({ ids: ids })
          })
          .then(response => response.json())
          .then(data => {
            if (data.sucesso) {
              mostrarMensagemSucesso(data.mensagem || "Itens excluídos.");
              loadAjaxContent(window.location.href);
            } else {
              mostrarMensagemErro(data.mensagem || "Erro ao excluir.");
            }
          })
          .catch(error => mostrarMensagemErro("Erro de comunicação."));
        }
      });
    });
  }

  updateButtonStates();
}

function bindPageSpecificActions() {
  initGenericActionButtons();

  const mainContent = document.querySelector("#main-content");
  const tela = mainContent?.dataset?.page || mainContent?.dataset?.tela || "";

  if (tela === "lista_empresas_avancadas") {
    // Lógica específica para filtro de empresas
  }

  if (tela === "entradas_nota") {
    setupColumnSorting();
    // Lógica específica para busca de notas
  }

  if (tela === "selecionar_grupo_permissoes") {
    const grupoSelect = document.getElementById("grupo-selecionado");
    const btnAvancar = document.getElementById("btn-avancar");
    if (grupoSelect && btnAvancar) {
      grupoSelect.addEventListener("change", () => { btnAvancar.disabled = !grupoSelect.value; });
      btnAvancar.onclick = () => {
        const grupoId = grupoSelect.value;
        if (grupoId) {
          const url = `/accounts/grupos/${grupoId}/permissoes/`;
          loadAjaxContent(url);
        }
      };
    }
  }

  if (tela === "gerenciar_permissoes") {
    // initPermissionsPage(); // Função não definida, comentada para evitar erros
  }

  if (tela === "empresa_avancada") {
    initCadastroEmpresaAvancada();
  }

  if (tela === "importar_xml") {
    window.initImportarXml(); // Chama a função init do importar_xml.js
  }
}

document.addEventListener("DOMContentLoaded", () => {
  bindPageSpecificActions();
  history.replaceState({ ajaxUrl: window.location.href }, "", window.location.href);
  initLayout();
});

function initCadastroEmpresaAvancada() {
  const selectTipo = document.getElementById("id_tipo_empresa");
  const camposPJ = document.getElementById("campos-pj");
  const camposPF = document.getElementById("campos-pf");
  if (!selectTipo || !camposPJ || !camposPF) return;
  function atualizarCampos(tipo) {
    camposPJ.classList.toggle("d-none", tipo !== "pj");
    camposPF.classList.toggle("d-none", tipo !== "pf");
  }
  selectTipo.addEventListener("change", () => atualizarCampos(selectTipo.value));
  atualizarCampos(selectTipo.value);
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

document.addEventListener("DOMContentLoaded", () => {
  // ... (código existente do primeiro DOMContentLoaded)

  const botaoTema = document.getElementById("theme-toggle");
  if (botaoTema) {
    botaoTema.addEventListener("click", () => {
      const html = document.documentElement;
      const modoEscuroAtivo = html.classList.toggle("dark");
      localStorage.setItem("tema", modoEscuroAtivo ? "dark" : "light");
    });
  }

  // --- LÓGICA DO SWITCHER DE LAYOUT ---
  console.log("DEBUG: Layout switcher logic initializing...");

  function initLayout() {
      const savedLayout = localStorage.getItem('layout_preferencia') || 'layout-lateral';
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

  // Listener delegado para os botões de troca
  document.addEventListener('click', (event) => {
      const toggleButton = event.target.closest('#btn-alternar-layout, #btn-alternar-layout-superior');
      if (toggleButton) {
          console.log("DEBUG: Layout toggle button clicked:", toggleButton);
          event.preventDefault();
          alternarLayout();
      }
  });

  // Inicializa o layout no carregamento inicial
  initLayout();
});
