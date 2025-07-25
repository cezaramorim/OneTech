// 🌙 Aplica o tema salvo no localStorage (antes do paint)
const temaSalvo = localStorage.getItem("tema");
if (temaSalvo === "dark") {
  document.documentElement.classList.add("dark");
} else {
  document.documentElement.classList.remove("dark");
}

// 🎛️ Alterna entre tema claro e escuro ao clicar no botão
document.addEventListener("DOMContentLoaded", () => {
  const btnToggleTema = document.querySelector("#btn-toggle-tema");

  if (btnToggleTema) {
    btnToggleTema.addEventListener("click", () => {
      const isDark = document.documentElement.classList.toggle("dark");
      localStorage.setItem("tema", isDark ? "dark" : "light");

      console.debug(`🌗 Tema alterado para: ${isDark ? "dark" : "light"}`);
    });
  } else {
    console.warn("⛔ Botão de troca de tema (#btn-toggle-tema) não encontrado.");
  }
});


// ✅ Libera a exibição da tela (importante!)
document.documentElement.classList.add("theme-ready");

document.addEventListener("ajaxContentLoaded", (event) => {
  bindPageSpecificActions();
  const url = event.detail?.url || window.location.href;
  updateActiveMenuLink(url);
  closeAllCollapses(); // Fecha todos os collapses ao carregar conteúdo AJAX
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
  console.log("DEBUG: Submit event triggered for form:", form.id, "with classList:", form.classList);
  if (!form.classList.contains("ajax-form")) {
    console.log("DEBUG: Form", form.id, "does NOT have 'ajax-form' class. Returning.");
    return;
  }
  console.log("DEBUG: Form", form.id, "HAS 'ajax-form' class. Proceeding.");
  e.preventDefault();
  console.log("DEBUG: e.preventDefault() called for form:", form.id);
  const urlBase = form.dataset.url || form.action;
  const method = form.method.toUpperCase();
  if (method === "GET") {
    const params = new URLSearchParams(new FormData(form));
    const finalUrl = `${urlBase}?${params.toString()}`;
    loadAjaxContent(finalUrl);
    return;
  }
  const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]")?.value;
  const formData = new FormData(form);
  console.log("DEBUG: Dados do formulário (FormData):");
  for (let [key, value] of formData.entries()) {
    console.log(`  ${key}: ${value}`);
  }
  try {
    let requestHeaders = {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrfToken
    };
    let requestBody;

    // Check if the form is for file uploads (multipart/form-data)
    if (form.enctype === "multipart/form-data") {
      // For file uploads, fetch automatically sets the Content-Type header
      // when FormData is passed directly as the body.
      requestBody = formData;
    } else {
      // For regular forms, use URLSearchParams and set Content-Type
      requestHeaders["Content-Type"] = "application/x-www-form-urlencoded";
      requestBody = new URLSearchParams(formData);
    }

    console.log("DEBUG: urlBase:", urlBase);
    console.log("DEBUG: method:", method);
    console.log("DEBUG: requestHeaders:", requestHeaders);
    console.log("DEBUG: requestBody:", requestBody);

    const response = await fetch(urlBase, {
      method: method,
      headers: requestHeaders,
      body: requestBody
    });
    console.log("DEBUG: Fetch response received:", response.status, response.statusText);
    const contentType = response.headers.get("Content-Type");
    console.log("DEBUG: Response Content-Type:", contentType);
    if (contentType && contentType.includes("application/json")) {
      const data = await response.json();
      console.log("DEBUG: Response data (JSON):");
      console.log(data);
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

      // Dispara um evento de sucesso para a página específica tratar
      if (data.success || data.sucesso) {
          document.dispatchEvent(new CustomEvent("ajaxFormSuccess", {
              detail: { form: form, responseJson: data }
          }));
      }
      
    } else {
      console.log("DEBUG: Response is NOT JSON. Attempting to read as text.");
      const html = await response.text();
      console.log("DEBUG: Response data (HTML):");
      console.log(html);
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

  

  // Delegação de eventos para os checkboxes
  document.addEventListener('change', (event) => {
    const target = event.target;
    const idTela = document.getElementById("identificador-tela");

    if (!idTela) return; // Garante que estamos em uma página com identificador-tela

    const { seletorCheckbox } = idTela.dataset;
    const selectAllCheckbox = document.querySelector('[id^="select-all-"]');
    const itemCheckboxes = document.querySelectorAll(seletorCheckbox);

    // Lógica para o checkbox "selecionar todos"
    if (target.matches('[id^="select-all-"]')) {
      itemCheckboxes.forEach(checkbox => { checkbox.checked = target.checked; });
      updateButtonStates();
    } 
    // Lógica para os checkboxes individuais
    else if (target.matches(seletorCheckbox)) {
      updateButtonStates();
      // Desmarca o "selecionar todos" se algum filho for desmarcado
      if (!target.checked) {
        if (selectAllCheckbox) {
          selectAllCheckbox.checked = false;
        }
      } else {
        // Se todos os filhos estiverem marcados, marca o "selecionar todos"
        const allChecked = Array.from(itemCheckboxes).every(cb => cb.checked);
        if (allChecked && selectAllCheckbox) {
          selectAllCheckbox.checked = true;
        }
      }
    }
  });

  updateButtonStatesGlobal();
}

// Listener global para o evento 'change' para lidar com elementos dinâmicos
document.addEventListener('change', (event) => {
  const target = event.target;
  const idTela = document.getElementById("identificador-tela");

  if (!idTela) return; // Não faz nada se não houver identificador-tela

  const { seletorCheckbox } = idTela.dataset;
  const selectAllCheckbox = document.querySelector('[id^="select-all-"]');
  const itemCheckboxes = document.querySelectorAll(seletorCheckbox);

  // Lógica para o checkbox "selecionar todos"
  if (target.matches('[id^="select-all-"]')) {
    itemCheckboxes.forEach(checkbox => { checkbox.checked = target.checked; });
    // A função updateButtonStates precisa ser chamada no contexto correto
    // ou ser adaptada para ser chamada globalmente.
    // Por enquanto, vamos garantir que a lógica de seleção funcione.
    // A atualização dos botões será tratada pela chamada de initGenericActionButtons
    // após o carregamento AJAX.
  } 
  // Lógica para os checkboxes individuais
  else if (target.matches(seletorCheckbox)) {
    // Desmarca o "selecionar todos" se algum filho for desmarcado
    if (!target.checked) {
      if (selectAllCheckbox) {
        selectAllCheckbox.checked = false;
      }
    } else {
      // Se todos os filhos estiverem marcados, marca o "selecionar todos"
      const allChecked = Array.from(itemCheckboxes).every(cb => cb.checked);
      if (allChecked && selectAllCheckbox) {
        selectAllCheckbox.checked = true;
      }
    }
  }
});

// A função updateButtonStates precisa ser acessível globalmente ou ser chamada
// após cada interação relevante. Como ela já é chamada em initGenericActionButtons,
// e initGenericActionButtons é chamada em ajaxContentLoaded, isso deve ser suficiente.
// No entanto, para garantir que os botões sejam atualizados imediatamente após
// uma interação com checkbox individual, vamos garantir que updateButtonStates
// seja chamada no contexto correto.

// A função updateButtonStates precisa ser definida fora de initGenericActionButtons
// ou ser passada como parâmetro, ou os elementos btnEditar e btnExcluir
// precisam ser re-consultados dentro do listener global.
// Para simplificar, vamos re-consultar os botões dentro do listener global.

// Removendo a definição de updateButtonStates de dentro de initGenericActionButtons
// e tornando-a uma função auxiliar global.
function updateButtonStatesGlobal() {
  const idTela = document.getElementById("identificador-tela");
  if (!idTela) return;

  const btnEditar = document.getElementById("btn-editar");
  const btnExcluir = document.getElementById("btn-excluir");
  if (!btnEditar || !btnExcluir) return;

  const { seletorCheckbox } = idTela.dataset;
  const selecionados = document.querySelectorAll(`${seletorCheckbox}:checked`);
  const count = selecionados.length;

  // Para o botão 'Editar' (tag <a>)
  if (count !== 1) {
    btnEditar.classList.add('disabled');
    btnEditar.setAttribute('aria-disabled', 'true');
    btnEditar.style.pointerEvents = 'none';
  } else {
    btnEditar.classList.remove('disabled');
    btnEditar.removeAttribute('aria-disabled');
    btnEditar.style.pointerEvents = 'auto';
  }

  // Para o botão 'Excluir' (tag <button>)
  btnExcluir.disabled = count === 0;
}

// Chamando updateButtonStatesGlobal no listener delegado
document.addEventListener('change', (event) => {
  const target = event.target;
  const idTela = document.getElementById("identificador-tela");

  if (!idTela) return;

  const { seletorCheckbox } = idTela.dataset;
  const selectAllCheckbox = document.querySelector('[id^="select-all-"]');
  const itemCheckboxes = document.querySelectorAll(seletorCheckbox);

  // Lógica para o checkbox "selecionar todos"
  if (target.matches('[id^="select-all-"]')) {
    itemCheckboxes.forEach(checkbox => { checkbox.checked = target.checked; });
    updateButtonStatesGlobal(); // Chama a função global
  } 
  // Lógica para os checkboxes individuais
  else if (target.matches(seletorCheckbox)) {
    updateButtonStatesGlobal(); // Chama a função global
    // Desmarca o "selecionar todos" se algum filho for desmarcado
    if (!target.checked) {
      if (selectAllCheckbox) {
        selectAllCheckbox.checked = false;
      }
    } else {
      // Se todos os filhos estiverem marcados, marca o "selecionar todos"
      const allChecked = Array.from(itemCheckboxes).every(cb => cb.checked);
      if (allChecked && selectAllCheckbox) {
        selectAllCheckbox.checked = true;
      }
    }
  }
});

// Certifique-se de que updateButtonStatesGlobal seja chamada na inicialização
// e após cada carregamento AJAX.
// A chamada original de updateButtonStates dentro de initGenericActionButtons
// será substituída por updateButtonStatesGlobal.

// Removendo a chamada final de updateButtonStates de initGenericActionButtons
// e garantindo que updateButtonStatesGlobal seja chamada no final de initGenericActionButtons.

function bindPageSpecificActions() {
  const mainContent = document.querySelector("#main-content");
  // Prioriza a leitura de data-tela do elemento identificador-tela
  const idTelaElement = document.getElementById("identificador-tela");
  const tela = idTelaElement?.dataset?.tela || mainContent?.dataset?.page || mainContent?.dataset?.tela || "";

  console.log("DEBUG: Valor da variável tela:", tela); // Adicionado para depuração

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
    //initPermissionsPage(); // Removido: será auto-executado por permissions.js
  }

  if (tela === "empresa_avancada") {
    initCadastroEmpresaAvancada();
  }

  if (tela === "importar_xml") {
    window.initImportarXml(); // Chama a função init do importar_xml.js
  }
}

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

document.addEventListener("click", (event) => {
  const idTela = document.getElementById("identificador-tela");
  if (!idTela) return;

  const { entidadeSingular, entidadePlural, urlEditar, urlExcluir, seletorCheckbox } = idTela.dataset;

  // Lógica para o botão Editar
  const btnEditar = event.target.closest("#btn-editar");
  if (btnEditar && !btnEditar.classList.contains("disabled")) {
    const selecionado = document.querySelector(`${seletorCheckbox}:checked`);
    if (selecionado) {
      const finalUrl = urlEditar.replace("/0/", `/${selecionado.value}/`);
      history.pushState({ ajaxUrl: finalUrl }, "", finalUrl);
      loadAjaxContent(finalUrl);
    }
    return; // Importante para evitar que o evento continue para outros listeners
  }

  // Lógica para o botão Excluir
  const btnExcluir = event.target.closest("#btn-excluir");
  if (btnExcluir && !btnExcluir.disabled) {
    const selecionados = document.querySelectorAll(`${seletorCheckbox}:checked`);
    const ids = Array.from(selecionados).map((cb) => cb.value);
    if (ids.length === 0) return;

    const text = `Excluir ${ids.length} ${ids.length === 1 ? entidadeSingular : entidadePlural}?`;
    Swal.fire({
      title: "Confirmar Exclusão",
      text: text,
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Sim, excluir!",
      cancelButtonText: "Cancelar",
    }).then((result) => {
      if (result.isConfirmed) {
        fetch(urlExcluir, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
            "X-Requested-With": "XMLHttpRequest",
          },
          body: JSON.stringify({ ids: ids }),
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.sucesso) {
              mostrarMensagemSucesso(data.mensagem || "Itens excluídos.");
              loadAjaxContent(window.location.href);
            } else {
              mostrarMensagemErro(data.mensagem || "Erro ao excluir.");
            }
          })
          .catch((error) => mostrarMensagemErro("Erro de comunicação."));
      }
    });
    return; // Importante para evitar que o evento continue para outros listeners
  }
});
