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

function exibirMensagem(texto, tipo = "info") {
  const mensagens = document.getElementById("mensagens");
  if (!mensagens) return;
  const icones = {
    success: '<i class="bi bi-check-circle-fill me-1 text-success"></i>',
    danger: '<i class="bi bi-x-circle-fill me-1 text-danger"></i>',
    error: '<i class="bi bi-x-circle-fill me-1 text-danger"></i>',
    warning: '<i class="bi bi-exclamation-triangle-fill me-1 text-warning"></i>',
    info: '<i class="bi bi-info-circle-fill me-1 text-info"></i>'
  };
  mensagens.innerHTML = `<div class="alert alert-${tipo} alert-dismissible fade show" role="alert">${icones[tipo] || icones.info} ${texto}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button></div>`;
  setTimeout(() => {
    const alerta = mensagens.querySelector(".alert");
    if (alerta) {
      alerta.classList.remove("show");
      alerta.classList.add("fade");
      setTimeout(() => alerta.remove(), 300);
    }
  }, 5000);
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
  console.log("🔁 loadAjaxContent chamada com URL:", url);

  // Get the current active content area, which is expected to be #identificador-tela or #main-content
  const currentActiveContent = document.querySelector("#main-content") || document.querySelector("main");

  if (!currentActiveContent) {
    console.error("❌ Não foi possível encontrar o elemento de conteúdo ativo para substituição (#main-content ou main).");
    return;
  }

  const headers = forceFullLoad ? {} : { "X-Requested-With": "XMLHttpRequest" };

  fetch(url, { headers })
    .then(response => {
      if (!response.ok) throw new Error(`Erro ${response.status}: ${response.statusText}`);
      return response.text();
    })
    .then(html => {
      const tempDiv = document.createElement("div");
      tempDiv.innerHTML = html;

      // Get the new content area from the fetched HTML, prioritizing #main-content
      const newActiveContent = tempDiv.querySelector("#main-content") || tempDiv.querySelector("main");

      if (!newActiveContent) {
        console.warn("⚠️ Conteúdo não encontrado ou estrutura inválida na resposta HTML (novo conteúdo - #main-content ou main).");
        return;
      }

      // Preserve focus logic (if applicable)
      const campoBuscaAntigo = currentActiveContent.querySelector("#busca-nota") || currentActiveContent.querySelector("#busca-empresa");

      console.log("DEBUG JS: currentActiveContent before replacement:", currentActiveContent);

      if (campoBuscaAntigo) {
        const valor = campoBuscaAntigo.value || "";
        const posicao = campoBuscaAntigo.selectionStart || valor.length;
        const idCampo = campoBuscaAntigo.id;

        currentActiveContent.replaceWith(newActiveContent); // Replace the current with the new
        console.log("DEBUG JS: currentActiveContent replaced. New content is now in DOM (with focus preservation).");

        const campoBuscaNovo = newActiveContent.querySelector(`#${idCampo}`);
        if (campoBuscaNovo) {
          campoBuscaNovo.focus();
          campoBuscaNovo.setSelectionRange(posicao, posicao);
        }
        console.log(`✅ Conteúdo com #${idCampo} atualizado preservando foco.`);
      } else {
        // Normal content update
        currentActiveContent.replaceWith(newActiveContent);
        console.log("DEBUG JS: currentActiveContent replaced. New content is now in DOM (normal update).");
        console.log("✅ Novo conteúdo carregado.");
      }

      // Re-trigger page-specific actions
      setTimeout(() => {
        document.dispatchEvent(new CustomEvent("ajaxContentLoaded", { detail: { url: url } }));
      }, 10);
    })
    .catch(error => {
      console.error("❌ Erro ao carregar conteúdo via AJAX:", error);
      exibirMensagem("Erro ao carregar conteúdo: " + error.message, "danger");
    });
}




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
      if (data.mensagem) {
        const tipo = data.sucesso ? "success" : "danger";
        exibirMensagem(data.mensagem, tipo);
      }
      if (data.redirect_url) {
        if (data.message || data.mensagem || data.sucesso) {
          const msg = data.message || data.mensagem || "Operação realizada com sucesso.";
          localStorage.setItem("mensagem_sucesso", msg);
        }
        const mainContent = document.getElementById("main-content");
        if (mainContent && mainContent.closest(".layout")) {
          history.pushState({ ajaxUrl: data.redirect_url }, "", data.redirect_url);
          loadAjaxContent(data.redirect_url);
          console.log("DEBUG JS: Redirecionando para:", data.redirect_url);
          document.dispatchEvent(new CustomEvent("ajaxContentLoaded", { detail: { url: data.redirect_url } }));

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
      exibirMensagem("Erro desconhecido ao processar requisição.", "danger");
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
  console.log("bindPageSpecificActions chamada");
  const mainContent   = document.querySelector("#main-content");
  const identificador = document.querySelector("#identificador-tela");
  let tela = identificador?.dataset?.tela
          || mainContent?.dataset?.tela
          || mainContent?.dataset?.page
          || "";
  tela = tela.replace(/-/g, "_");
  console.log("Tela identificada:", tela);

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

  if (tela === "gerenciar_permissoes_geral") {
    const grupoSelect   = document.getElementById("grupo");
    const usuarioSelect = document.getElementById("usuario");
    const tipoInput     = document.getElementById("tipo-selecionado");
    if (grupoSelect && usuarioSelect && tipoInput) {
      grupoSelect.addEventListener("change", () => {
        usuarioSelect.selectedIndex = 0;
        tipoInput.value            = "grupo";
        document.querySelector("form.ajax-form").submit();
      });
      usuarioSelect.addEventListener("change", () => {
        grupoSelect.selectedIndex = 0;
        tipoInput.value           = "usuario";
        document.querySelector("form.ajax-form").submit();
      });
    }
  }

  // ============================================
  // FUNÇÃO CENTRAL DE AÇÕES (GENÉRICA + LEGADO)
  // ============================================
  const atualizarBotoesAcao = () => {
    const identificador = document.querySelector("#identificador-tela");
    const btnEditar  = document.getElementById("btn-editar") || document.getElementById("btn-editar-nota");
    const btnExcluir = document.getElementById("btn-excluir") || document.getElementById("btn-excluir-nota");

    // ✅ NOVA LÓGICA GENÉRICA (baseada em data-atributos)
    if (identificador && identificador.dataset.entidadeSingular) {
      const {
        entidadeSingular,
        entidadePlural,
        urlEditar,
        urlExcluir,
        seletorCheckbox
      } = identificador.dataset;

      console.log("DEBUG JS: Lógica genérica ativada para:", entidadeSingular);
      console.log("DEBUG JS: urlEditar:", urlEditar);
      console.log("DEBUG JS: urlExcluir:", urlExcluir);
      console.log("DEBUG JS: seletorCheckbox:", seletorCheckbox);

      if (!entidadeSingular || !urlEditar || !urlExcluir || !seletorCheckbox) {
        console.error("❌ Atributos data-* ausentes para a lógica de ações genéricas.");
        return;
      }

      const checkboxes = document.querySelectorAll(seletorCheckbox);
      const selecionados = Array.from(checkboxes).filter(cb => cb.checked);
      const selectAll = document.getElementById(`select-all-${entidadePlural}`);

      // Habilitar/desabilitar botões
      if (btnEditar) btnEditar.disabled = selecionados.length !== 1;
      if (btnExcluir) btnExcluir.disabled = selecionados.length === 0;

      // Ação de Editar
      if (btnEditar) {
        btnEditar.onclick = () => {
          const selecionado = document.querySelector(`${seletorCheckbox}:checked`);
          console.log("DEBUG JS: Botão Editar clicado. Item selecionado:", selecionado?.value);
          if (!selecionado) return exibirMensagem(`Selecione um(a) ${entidadeSingular} para editar.`, "warning");
          const url = `${urlEditar}${selecionado.value}/editar/`;
          console.log("DEBUG JS: URL de edição construída:", url);
          history.pushState({ ajaxUrl: url }, "", url);
          loadAjaxContent(url);
        };
      }

      // Ação de Excluir
      if (btnExcluir) {
        btnExcluir.onclick = () => {
          const selecionados = Array.from(document.querySelectorAll(`${seletorCheckbox}:checked`));
          console.log("DEBUG JS: Botão Excluir clicado. IDs selecionados:", selecionados.map(cb => cb.value));
          if (selecionados.length === 0) return exibirMensagem(`Selecione ao menos um(a) ${entidadeSingular} para excluir.`, "warning");

          const confirmMsg = `Deseja realmente excluir ${selecionados.length} ${selecionados.length > 1 ? entidadePlural : entidadeSingular}?`;
          if (!confirm(confirmMsg)) return;

          exibirMensagem(`Excluindo ${entidadePlural}...`, "info");
          const ids = selecionados.map(cb => cb.value);

          fetch(urlExcluir, {
            method: "POST",
            headers: {
              "X-CSRFToken": getCSRFToken(),
              "Content-Type": "application/json",
              "X-Requested-With": "XMLHttpRequest"
            },
            body: JSON.stringify({ ids })
          })
          .then(res => res.json())
          .then(data => {
            console.log("DEBUG JS: Resposta da exclusão:", data);
            if (data.success || data.sucesso) {
              exibirMensagem(data.mensagem || `${entidadePlural.charAt(0).toUpperCase() + entidadePlural.slice(1)} excluídos com sucesso.`, "success");
              loadAjaxContent(data.redirect_url || window.location.href);
            } else {
              exibirMensagem(data.erro || `Erro ao excluir as ${entidadePlural}.`, "danger");
            }
          })
          .catch(err => {
            console.error("DEBUG JS: Erro no fetch de exclusão:", err);
            exibirMensagem("Erro ao excluir: " + err.message, "danger");
          });
        };
      }

      // Ação do "Selecionar Todos"
      if (selectAll && !selectAll.dataset.listenerAttached) {
        selectAll.addEventListener("change", (e) => {
          document.querySelectorAll(seletorCheckbox).forEach(cb => cb.checked = e.target.checked);
          atualizarBotoesAcao();
        });
        selectAll.dataset.listenerAttached = "true";
      }

      return; // Finaliza a execução para não entrar na lógica antiga
    }

    // ⚠️ LÓGICA ANTIGA (Fallback para telas não refatoradas)
    let tela = identificador?.dataset?.tela || document.querySelector("#main-content")?.dataset?.page || "";
    tela = tela.replace(/-/g, "_");

    const checkboxes = document.querySelectorAll(
      `input[type="checkbox"].checkbox-nota,
       #grupos-form input[type="checkbox"],
       #usuarios-form input[type="checkbox"],
       input.check-produto`
    );
    const selecionados = Array.from(checkboxes).filter(cb => cb.checked);
    const apenasUm = selecionados.length === 1;
    const temSelecionado = selecionados.length > 0;
    const telasComSelecao = [
      "lista_grupos", "lista_empresas",
      "selecionar_usuario_permissoes", "gerenciar-permissoes-grupo-selector",
      "entradas_nota", "lista_produtos"
    ];

    if (telasComSelecao.includes(tela)) {
      if (btnEditar)  btnEditar.disabled  = !apenasUm;
      if (btnExcluir) btnExcluir.disabled = !temSelecionado;
    }

    if (tela === "lista_produtos") {
      if (btnEditar) {
        btnEditar.onclick = () => {
          const selecionado = document.querySelector("input.check-produto:checked");
          if (!selecionado) return exibirMensagem("Selecione um produto para editar.", "warning");
          const url = `/produtos/editar/${selecionado.value}/`;
          history.pushState({ ajaxUrl: url }, "", url);
          loadAjaxContent(url);
        };
      }
      if (btnExcluir) {
        btnExcluir.onclick = () => {
          const selecionados = Array.from(document.querySelectorAll("input.check-produto:checked"));
          if (selecionados.length === 0) {
            return exibirMensagem("Selecione ao menos um produto para excluir.", "warning");
          }
          exibirMensagem("Excluindo produtos...", "info");
          const ids = selecionados.map(cb => cb.value);
          fetch("/produtos/excluir-multiplos/", {
            method: "POST",
            headers: {
              "X-CSRFToken": getCSRFToken(),
              "Content-Type": "application/json",
              "X-Requested-With": "XMLHttpRequest"
            },
            body: JSON.stringify({ ids })
          })
            .then(res => res.json())
            .then(data => {
              if (data.sucesso) {
                exibirMensagem(data.mensagem || "Produtos excluídos com sucesso.", "success");
                loadAjaxContent(window.location.href);
              } else {
                exibirMensagem(data.erro || "Erro ao excluir os produtos.", "danger");
              }
            })
            .catch(err => exibirMensagem("Erro ao excluir: " + err.message, "danger"));
        };
      }
      const selectAll = document.getElementById("select-all-produtos");
      if (selectAll) {
        selectAll.addEventListener("change", (e) => {
          const chks = document.querySelectorAll("input.check-produto");
          chks.forEach(cb => cb.checked = e.target.checked);
          atualizarBotoesAcao();
        });
      }
    }

    if (tela === "entradas_nota") {
      if (btnEditar) {
        btnEditar.onclick = () => {
          const sel = Array.from(
            document.querySelectorAll('input[type="checkbox"].checkbox-nota:checked')
          );
          if (sel.length !== 1) {
            return exibirMensagem("Selecione exatamente uma nota para editar.", "warning");
          }
          const url = `/nota-fiscal/editar/${sel[0].value}/`;
          history.pushState({ ajaxUrl: url }, "", url);
          loadAjaxContent(url);
        };
      }
      if (btnExcluir) {
        btnExcluir.onclick = () => {
          const sel = Array.from(
            document.querySelectorAll('input[type="checkbox"].checkbox-nota:checked')
          );
          if (sel.length === 0) return exibirMensagem("Nenhuma nota selecionada para excluir.", "warning");
          if (!confirm(`Deseja realmente excluir ${sel.length > 1 ? sel.length + " notas fiscais" : "esta nota fiscal"}?`)) return;
          fetch(`/nota-fiscal/excluir/${sel[0].value}/`, {
            method: "POST",
            headers: { "X-CSRFToken": getCSRFToken(), "X-Requested-With": "XMLHttpRequest" }
          })
            .then(res => res.json())
            .then(data => {
              if (data.sucesso || data.mensagem || data.success) {
                exibirMensagem(data.mensagem || data.success || "Nota excluída com sucesso.", "success");
                const novaURL = "/nota-fiscal/entradas/";
                history.pushState({ ajaxUrl: novaURL }, "", novaURL);
                loadAjaxContent(novaURL);
              } else {
                exibirMensagem(data.erro || data.error || "Erro ao excluir nota.", "danger");
              }
            })
            .catch(err => exibirMensagem("Erro ao excluir: " + err.message, "danger"));
        };
      }
    }

    // ============================================
    // ←←← AQUI: lógica para editar_entrada ←←←
    // ============================================
    if (tela === "editar_entrada") {
      console.log("Lógica específica para editar_entrada está a ser vinculada.");

      // Botões e form
      const btnFinalizar = document.getElementById("btn-finalizar-lancamento");
      const btnDescartar = document.getElementById("btn-descartar-alteracoes");
      const form         = document.getElementById("form-editar-entrada");

      // Finalizar Lançamento via AJAX
      if (btnFinalizar && form) {
        btnFinalizar.onclick = () => {
          // 1) Cria um FormData completo do <form>
          const data = new FormData(form);

          // 2) Envia como multipart/form-data (sem setar Content-Type)
          fetch(window.location.pathname, {
            method: "POST",
            headers: {
              "X-CSRFToken":      getCSRFToken(),
              "X-Requested-With": "XMLHttpRequest"
            },
            body: data
          })
          .then(res => res.json().then(json => ({ status: res.status, body: json })))
          .then(({ status, body }) => {
            if (status === 200) {
              // sucesso
              mostrarMensagemSucesso(body.mensagem || "Alterações salvas com sucesso!");
              setTimeout(() => {
                const listUrl = "/nota-fiscal/entradas/";
                history.pushState({ ajaxUrl: listUrl }, "", listUrl);
                loadAjaxContent(listUrl);
              }, 500);
            } else {
              // validação falhou: exibe lista de erros
              const erros = body.erros || body.error || body;
              mostrarMensagemErro("Erros: " + JSON.stringify(erros));
            }
          })
          .catch(err => {
            console.error("Erro no fetch:", err);
            mostrarMensagemErro("Erro ao salvar alterações.");
          });
        };
      }

      // Descartar alterações
      if (btnDescartar) {
        btnDescartar.onclick = () => {
          if (confirm("Descartar alterações?")) {
            const listUrl = "/nota-fiscal/entradas/";
            history.pushState({ ajaxUrl: listUrl }, "", listUrl);
            loadAjaxContent(listUrl);
          }
        };
      }
    }
  };

  window.atualizarBotoesAcaoGlobal = atualizarBotoesAcao;
  document.body.removeEventListener("change", globalCheckboxListener);
  document.body.addEventListener("change", globalCheckboxListener);

  function globalCheckboxListener(e) {
    if (e.target && e.target.matches('input[type="checkbox"]')) {
      if (typeof window.atualizarBotoesAcaoGlobal === "function") {
        window.atualizarBotoesAcaoGlobal();
      }
    }
  }
  atualizarBotoesAcao();
}

document.addEventListener("DOMContentLoaded", () => {
  console.log("DOMContentLoaded - chamando bindPageSpecificActions");
  bindPageSpecificActions();
  const mensagemSucesso = localStorage.getItem("mensagem_sucesso");
  if (mensagemSucesso) {
    exibirMensagem(mensagemSucesso, "success");
    localStorage.removeItem("mensagem_sucesso");
  }
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