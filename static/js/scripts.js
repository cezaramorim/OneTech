// 🌙 Aplica o tema dark o mais cedo possível (antes do paint)
const temaSalvo = localStorage.getItem("tema");
if (temaSalvo === "dark") {
  document.documentElement.classList.add("dark");
} else {
  document.documentElement.classList.remove("dark");
}

// ✅ Libera a exibição da tela (importante!)
document.documentElement.classList.add("theme-ready");


document.addEventListener("ajaxContentLoaded", bindPageSpecificActions);

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

  // Get the current active content area, which is expected to be #identificador-tela or #main-content
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

      // Get the new content area from the fetched HTML, prioritizing #main-content
      const newActiveContent = tempDiv.querySelector("#main-content") || tempDiv.querySelector("main");

      if (!newActiveContent) {
        console.warn("⚠️ loadAjaxContent: Conteúdo não encontrado ou estrutura inválida na resposta HTML (novo conteúdo - #main-content ou main).");
        return;
      }

      // Preserve focus logic (if applicable)
      const campoBuscaAntigo = currentActiveContent.querySelector("#busca-nota") || currentActiveContent.querySelector("#busca-empresa");

      if (campoBuscaAntigo) {
        const valor = campoBuscaAntigo.value || "";
        const posicao = campoBuscaAntigo.selectionStart || valor.length;
        const idCampo = campoBuscaAntigo.id;

        currentActiveContent.replaceWith(newActiveContent); // Replace the current with the new

        const campoBuscaNovo = newActiveContent.querySelector(`#${idCampo}`);
        if (campoBuscaNovo) {
          campoBuscaNovo.focus();
          campoBuscaNovo.setSelectionRange(posicao, posicao);
        }
        console.log(`✅ loadAjaxContent: Conteúdo com #${idCampo} atualizado preservando foco.`);
      } else {
        // Normal content update
        currentActiveContent.replaceWith(newActiveContent);
        console.log("✅ loadAjaxContent: Novo conteúdo carregado (normal update).");
      }

      // Re-trigger page-specific actions
      setTimeout(() => {
        document.dispatchEvent(new CustomEvent("ajaxContentLoaded", { detail: { url: url } }));
      }, 10);

      // Exibir e limpar mensagem de sucesso do localStorage
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
    loadAjaxContent(url);
  }
});

document.addEventListener("submit", async e => {
  const form = e.target;
  if (!form.classList.contains("ajax-form")) {
    console.log("DEBUG JS: Form does not have ajax-form class.");
    return;
  }
  e.preventDefault();
  const urlBase = form.dataset.url || form.action;
  const method = form.method.toUpperCase();
  console.log("DEBUG JS: AJAX Form Submit - URL:", urlBase, "Method:", method);
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

    console.log("DEBUG JS: Response Status:", response.status, response.statusText);
    const contentType = response.headers.get("Content-Type");
    console.log("DEBUG JS: Response Content-Type:", contentType);

    if (contentType && contentType.includes("application/json")) {
      const data = await response.json();
      console.log("DEBUG JS: JSON Response Data:", data);
      if (data.message) {
        if (!data.redirect_url) { // Só exibe se não houver redirecionamento
          if (data.success) {
            mostrarMensagemSucesso(data.message);
          } else {
            mostrarMensagemErro(data.message);
          }
        }
      } else if (data.mensagem) { // Fallback para 'mensagem' e 'sucesso' antigos
        if (!data.redirect_url) { // Só exibe se não houver redirecionamento
          if (data.sucesso) {
            mostrarMensagemSucesso(data.mensagem);
          } else {
            mostrarMensagemErro(data.mensagem);
          }
        }
      }
      if (data.redirect_url) {
        console.log("DEBUG JS: Redirecionamento detectado. URL:", data.redirect_url);
        if (data.message || data.mensagem) {
          const msg = data.message || data.mensagem;
          console.log("DEBUG JS: Salvando mensagem no localStorage:", msg);
          localStorage.setItem("mensagem_sucesso", msg);
          console.log("DEBUG JS: Mensagem salva no localStorage.");
        }
        const mainContent = document.getElementById("main-content");
        if (mainContent && mainContent.closest(".layout")) {
          history.pushState({ ajaxUrl: data.redirect_url }, "", data.redirect_url);
          console.log("DEBUG JS: Chamando loadAjaxContent para redirecionamento.");
          loadAjaxContent(data.redirect_url);
          console.log("DEBUG JS: Redirecionando para:", data.redirect_url);

        } else {
          window.location.href = data.redirect_url;
        }

      }
    } else {
      const html = await response.text();
      console.log("DEBUG JS: Non-JSON HTML Response:", html);
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
    if (err?.errors) {
      exibirMensagem("Erro ao enviar dados. Verifique os campos.", "danger");
    } else if (err?.message) {
      exibirMensagem("Erro de rede: " + err.message, "danger");
    } else {
      mostrarMensagemErro("Erro desconhecido ao processar requisição.");
    }
  }
});

document.addEventListener("change", function (e) {
  const grupoSelect = document.getElementById("grupo-selecionado");
  const btnAvancar = document.getElementById("btn-avancar");
  if (grupoSelect && btnAvancar) {
    btnAvancar.disabled = !grupoSelect.value;
  }
});

window.addEventListener("popstate", e => {
  if (e.state && e.state.ajaxUrl) {
    loadAjaxContent(e.state.ajaxUrl);
  } else {
    loadAjaxContent(window.location.href, true); // Fallback para recarga completa se não houver estado
  }
});

function setupColumnSorting() {
  console.log("setupColumnSorting chamada");
  const linksOrdenacao = document.querySelectorAll(".ordenar-coluna");
  const urlParamsAtual = new URLSearchParams(window.location.search);
  const ordemCorrente = urlParamsAtual.get("ordem");
  console.log("Ordem corrente da URL:", ordemCorrente);

  linksOrdenacao.forEach(link => {
    const campoLink = link.dataset.campo;
    const textoOriginal = link.dataset.originalText || link.innerText.replace(/ (▲|▼)$/, "").replace(/ <span class="arrow (asc|desc)">.*?<\/span>$/, "").trim();
    link.dataset.originalText = textoOriginal;
    link.innerHTML = textoOriginal;

    if (ordemCorrente === campoLink) {
      link.innerHTML += ' <span class="arrow asc" style="font-size: 0.8em; vertical-align: middle; color: inherit;">&#9650;</span>'; // ▲
      console.log("Seta ASC adicionada para:", campoLink);
    } else if (ordemCorrente === `-${campoLink}`) {
      link.innerHTML += ' <span class="arrow desc" style="font-size: 0.8em; vertical-align: middle; color: inherit;">&#9660;</span>'; // ▼
      console.log("Seta DESC adicionada para:", campoLink);
    }

    if (link.clickHandler) {
      link.removeEventListener("click", link.clickHandler);
    }

    link.clickHandler = function (e) {
      e.preventDefault();
      console.log("Cabeçalho clicado:", campoLink);
      const urlParams = new URLSearchParams(window.location.search);
      const ordemAtualClick = urlParams.get("ordem");
      const novaOrdem = ordemAtualClick === campoLink ? `-${campoLink}` : campoLink;
      urlParams.set("ordem", novaOrdem);
      const termo = document.getElementById("busca-nota")?.value || "";
      if (termo) {
        urlParams.set("termo", termo);
      } else {
        urlParams.delete("termo");
      }

      const currentPath = window.location.pathname;
      const novaUrl = `${currentPath}?${urlParams.toString()}`;
      console.log("Nova URL para ordenação:", novaUrl);

      history.pushState({ ajaxUrl: novaUrl }, "", novaUrl);
      loadAjaxContent(novaUrl);
    };
    link.addEventListener("click", link.clickHandler);
  });
}

// FUNÇÃO LISTA EMPRESAS AVANÇADAS, NÃO ALTERAR
function bindPageSpecificActions() {
  console.log("🔁 bindPageSpecificActions: Iniciando vinculação de ações específicas da página.");
  const mainContent   = document.querySelector("#main-content");
  const identificador = document.querySelector("#identificador-tela");
  let tela = identificador?.dataset?.tela
          || mainContent?.dataset?.tela
          || mainContent?.dataset?.page
          || "";
  tela = tela.replace(/-/g, "_");
  console.log("✅ bindPageSpecificActions: Tela identificada como:", tela);
  if (identificador) {
    console.log("✅ bindPageSpecificActions: Dataset do #identificador-tela:", identificador.dataset);
  }
  if (mainContent) {
    console.log("✅ bindPageSpecificActions: Dataset do #main-content:", mainContent.dataset);
  }

  if (tela === "empresa_avancada") {
    initCadastroEmpresaAvancada();
  }

  if (tela === "lista_empresas_avancadas") {
    const form              = document.getElementById("filtro-empresas-avancadas");
    const tabelaWrapper     = document.getElementById("empresas-avancadas-tabela-wrapper");
    const campoBusca        = document.getElementById("busca-empresa");

    if (form && tabelaWrapper) {
      let debounceTimer;

      // Função única para enviar o filtro
      function enviarFiltroEmpresas(campoAlterado = null) {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          const posicao = campoAlterado?.selectionStart || 0;
          const params  = new URLSearchParams(new FormData(form));
          const novaUrl = `${window.location.pathname}?${params.toString()}`;
          history.pushState({ ajaxUrl: novaUrl }, "", novaUrl);

          console.log("DEBUG JS: Input no campo de busca detectado.");
          loadAjaxContent(novaUrl);
        }, 300); // ✅ Debounce de 300ms
      }

      // Evento de input para o campo de busca com debounce
      if (campoBusca && !campoBusca.dataset.listenerAttached) {
        campoBusca.addEventListener("input", () => enviarFiltroEmpresas(campoBusca));
        campoBusca.dataset.listenerAttached = "true";
      }

      const selects = form.querySelectorAll("select");
      selects.forEach(select => {
        if (!select.dataset.listenerAttached) {
          select.addEventListener("change", () => {
            console.log("DEBUG JS: Select alterado. Enviando filtro.");
            enviarFiltroEmpresas();
          });
          select.dataset.listenerAttached = "true";
        }
      });
    }
  }

  if (tela === "entradas_nota") {
    console.log("Lógica específica para entradas_nota está a ser vinculada.");
    setupColumnSorting();

    const campoBusca = document.getElementById("busca-nota");
    if (campoBusca) {
      let debounceTimer;
      campoBusca.addEventListener("input", () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          const termo     = campoBusca.value.trim();
          const urlParams = new URLSearchParams(window.location.search);
          urlParams.set("termo", termo);
          const novaUrl = `${window.location.pathname}?${urlParams.toString()}`;
          history.pushState({ ajaxUrl: novaUrl }, "", novaUrl);
          loadAjaxContent(novaUrl);
        }, 300);
      });
    }
  }

  if (tela === "selecionar_grupo_permissoes") {
    const grupoSelect = document.getElementById("grupo-selecionado");
    const btnAvancar  = document.getElementById("btn-avancar");
    if (grupoSelect && btnAvancar) {
      grupoSelect.addEventListener("change", () => { btnAvancar.disabled = !grupoSelect.value; });
      btnAvancar.onclick = () => {
        const grupoId = grupoSelect.value;
        if (!grupoId) return mostrarMensagemErro("Selecione um grupo para continuar.");
        const url = `/accounts/grupos/${grupoId}/permissoes/`;
        history.pushState({ ajaxUrl: url }, "", url);
        loadAjaxContent(url);
      };
    }
  }

  if (tela === "gerenciar_permissoes") {
    initPermissionsPage();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  
  bindPageSpecificActions();
  history.replaceState({ ajaxUrl: window.location.href }, "", window.location.href);
});




function initSeletorGrupoPermissoes() {
  const form = document.getElementById("form-seletor-grupo");
  const select = document.getElementById("grupo-selecionado");
  const btn = document.getElementById("btn-avancar");
  if (!form || !select || !btn) return;
  btn.disabled = !select.value;
  select.addEventListener("change", () => { btn.disabled = !select.value; });
  btn.addEventListener("click", () => {
    const grupoId = select.value;
    if (grupoId) {
      const url = `/accounts/grupos/${grupoId}/permissoes/`;
      history.pushState({ ajaxUrl: url }, "", url);
      loadAjaxContent(url);
    }
  });
}

function atualizarTipoSelecionado() {
  const grupoSelect = document.getElementById("grupo");
  const usuarioSelect = document.getElementById("usuario");
  const tipoInput = document.getElementById("tipo-selecionado");
  let url = new URL(window.location.href);
  url.search = "";
  if (grupoSelect && grupoSelect.value) {
    tipoInput.value = "grupo";
    url.searchParams.set("grupo", grupoSelect.value);
  } else if (usuarioSelect && usuarioSelect.value) {
    tipoInput.value = "usuario";
    url.searchParams.set("usuario", usuarioSelect.value);
  }
  const finalUrl = url.toString();
  history.pushState({ ajaxUrl: finalUrl }, "", finalUrl);
  loadAjaxContent(finalUrl);
}

function initCadastroEmpresaAvancada() {
  const selectTipo = document.getElementById("id_tipo_empresa");
  const camposPJ = document.getElementById("campos-pj");
  const camposPF = document.getElementById("campos-pf");
  if (!selectTipo || !camposPJ || !camposPF) return;
  function atualizarCampos(tipo) {
    if (tipo === "pj") {
      camposPJ.classList.remove("d-none");
      camposPF.classList.add("d-none");
    } else if (tipo === "pf") {
      camposPF.classList.remove("d-none");
      camposPJ.classList.add("d-none");
    } else {
      camposPJ.classList.add("d-none");
      camposPF.classList.add("d-none");
    }
  }
  selectTipo.addEventListener("change", () => atualizarCampos(selectTipo.value));
  atualizarCampos(selectTipo.value);
}

// 💡 Alterna o tema ao clicar no botão
document.addEventListener("DOMContentLoaded", () => {
  const botaoTema = document.getElementById("theme-toggle");
  if (botaoTema) {
    botaoTema.addEventListener("click", () => {
      const html = document.documentElement;
      const modoEscuroAtivo = html.classList.toggle("dark");
      localStorage.setItem("tema", modoEscuroAtivo ? "dark" : "light");
    });
  }
});