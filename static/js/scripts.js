/* jshint esversion: 11 */

(function () {
  "use strict";

// ✅ OneTech - scripts.js - Aplicação do tema salvo

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

  if (typeof aplicarTemaSalvo === "function") {
    aplicarTemaSalvo();
  }
// 📌 Você pode continuar definindo outras funções aqui dentro
// como bindAjaxLinks(), loadAjaxContent(), etc.

})();


// 🔗 Bind de links AJAX
function bindAjaxLinks() {
document.body.removeEventListener('click', handleAjaxLinkClick);
document.body.addEventListener('click', handleAjaxLinkClick);
}

function handleAjaxLinkClick(event) {
const link = event.target.closest('a.ajax-link');
if (link) {
  event.preventDefault();
  const url = link.href;
  loadAjaxContent(url);
}
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

function loadAjaxContent(url, forceFullLoad = false) {
  const mainContent = document.getElementById('main-content');

  const headers = forceFullLoad
    ? {}
    : { 'X-Requested-With': 'XMLHttpRequest' };

  fetch(url, { headers })
    .then(response => response.text())
    .then(html => {
      if (mainContent) {
        mainContent.innerHTML = html;

        if (typeof aplicarTemaSalvo === "function") aplicarTemaSalvo();
        if (typeof bindAjaxLinks === "function") bindAjaxLinks();
        if (typeof bindCheckboxActions === "function") bindCheckboxActions();
        if (typeof ajaxContentLoaded === "function") {
          document.dispatchEvent(new Event('ajaxContentLoaded'));
        }
      }
    })
    .catch(error => {
      console.error('Erro ao carregar via AJAX:', error);
    });
}



/*function loadAjaxContent(url) {
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

        // ✅ Verificações seguras antes de chamar
        if (typeof aplicarTemaSalvo === "function") aplicarTemaSalvo();
        if (typeof bindAjaxLinks === "function") bindAjaxLinks();
        if (typeof bindCheckboxActions === "function") bindCheckboxActions();
        if (typeof ajaxContentLoaded === "function") {
          document.dispatchEvent(new Event('ajaxContentLoaded'));
        }
      }
    })
    .catch(error => {
      console.error('Erro ao carregar via AJAX:', error);
    });
}
*/

// ✅ Funções devem ser chamadas somente quando o DOM estiver pronto
//document.addEventListener("ajaxContentLoaded", ajaxContentLoaded);

// 🔄 Inicialização da busca dinâmica (pode ficar fora do escopo DOMContentLoaded se necessário)
/*if (typeof ativarBuscaDinamicaNCM === "function") {
  ativarBuscaDinamicaNCM();
}
  */

// 🔁 Função para ser disparada após carregamento AJAX
function ajaxContentLoaded() {
  if (typeof aplicarTemaSalvo === "function") aplicarTemaSalvo();
  if (typeof bindAjaxLinks === "function") bindAjaxLinks();
  if (typeof bindCheckboxActions === "function") bindCheckboxActions();
  if (typeof aplicarMascaraCEP === "function") aplicarMascaraCEP();
  if (typeof autoPreencherEnderecoPorCEP === "function") autoPreencherEnderecoPorCEP();
}



// 🚀 Disparar sempre que conteúdo for carregado via AJAX
//window.addEventListener("DOMContentLoaded", ajaxContentLoaded);
//document.addEventListener("ajaxContentLoaded", ajaxContentLoaded);


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

  if (tela === 'lista-empresas') {
    if (btnEditar) btnEditar.disabled = !apenasUm;
    if (btnExcluir) btnExcluir.disabled = !temSelecionado;
  }
};

atualizarBotoesGlobal = atualizarBotoes;
atualizarBotoes();

// ✅ Ações por tela

// Usuários
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
      // Implementar ação AJAX se necessário
    }
  };
}

// Grupos
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

// Permissões por grupo
if (btnEditPerm && tela === 'gerenciar-permissoes-grupo-selector') {
  btnEditPerm.onclick = () => {
    const selecionado = Array.from(checkboxes).find(cb => cb.checked);
    if (selecionado) {
      loadAjaxContent(`/accounts/grupos/${selecionado.value}/permissoes/`);
    }
  };
}

// Permissões por usuário
if (btnEditar && tela === 'selecionar-usuario-permissoes') {
  btnEditar.onclick = () => {
    const selecionado = Array.from(checkboxes).find(cb => cb.checked);
    if (selecionado) {
      loadAjaxContent(`/accounts/permissoes/editar/${selecionado.value}/`);
    }
  };
}

// Empresas
if (btnEditar && tela === 'lista-empresas') {
  btnEditar.onclick = () => {
    const selecionado = Array.from(checkboxes).find(cb => cb.checked);
    if (selecionado) {
      loadAjaxContent(`/empresas/editar/${selecionado.value}/`);
    }
  };
}

if (btnExcluir && tela === 'lista-empresas') {
  btnExcluir.onclick = () => {
    const form = document.getElementById('empresas-form');
    if (form) form.requestSubmit();
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

if (!selectGrupo || !btnAvancar) return;

// Remove qualquer evento anterior para evitar duplicação
selectGrupo.onchange = null;
btnAvancar.onclick = null;

// Ativa/desativa botão conforme a seleção
btnAvancar.disabled = !selectGrupo.value;

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

// 🚀 DOM pronto
document.addEventListener('DOMContentLoaded', () => {
  const themeToggle = document.getElementById('theme-toggle');
  const hamburgerToggle = document.getElementById('hamburger-toggle');
  const page = document.querySelector('[data-page]')?.dataset.page;

  // ✅ Garante que as funções existem antes de executar
  if (typeof aplicarTemaSalvo === "function") aplicarTemaSalvo();
  if (typeof initSelect2Campos === "function") initSelect2Campos();

  // ✅ Inicialização segura das funções
  if (typeof bindAjaxLinks === "function") bindAjaxLinks();
  if (typeof bindCheckboxActions === "function") bindCheckboxActions();
  if (typeof initSeletorGrupoPermissoes === "function") initSeletorGrupoPermissoes();
  if (typeof aplicarMascaras === "function") aplicarMascaras();
  if (typeof aplicarMascaraCEP === "function") aplicarMascaraCEP();
  if (typeof autoPreencherEnderecoPorCEP === "function") autoPreencherEnderecoPorCEP();
  /*if (typeof ativarBuscaDinamicaNCM === "function") ativarBuscaDinamicaNCM();*/

  // ✅ Detecta se está na tela de cadastro avançado de empresa
  if (page === 'cadastrar_empresa_avancado' || page === 'empresa_avancada') {
    if (typeof initCadastroEmpresaAvancado === "function") {
      initCadastroEmpresaAvancado();
    }
  }

  // ✅ Botão de alternância de tema
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

  // ✅ Botão de menu hambúrguer para mobile
  if (hamburgerToggle) {
    hamburgerToggle.addEventListener('click', () => {
      document.querySelectorAll('.menu-list').forEach(menu => menu.classList.toggle('show'));
    });
  }
});

document.addEventListener('submit', async (e) => {
  const form = e.target;
  if (!form.classList.contains('ajax-form')) return;
  e.preventDefault();

  const urlBase = form.dataset.url || form.action;
  const method = form.method.toUpperCase();

  if (method === 'GET') {
    const params = new URLSearchParams(new FormData(form));
    const finalUrl = `${urlBase}?${params.toString()}`;
    loadAjaxContent(finalUrl);
    return;
  }

  const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]')?.value;

  try {
    const response = await fetch(urlBase, {
      method: method,
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
        const mainContent = document.getElementById('main-content');
        if (mainContent && mainContent.closest('.layout')) {
          loadAjaxContent(data.redirect_url);
        } else {
          window.location.href = data.redirect_url;
        }
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

// ✅ Dispara ações específicas após qualquer carregamento via AJAX
//document.addEventListener("ajaxContentLoaded", ajaxContentLoaded);


// 🔄 AJAX content loaded

// ✅ scripts.js atualizado com logout automático funcional

// ... [demais funções e inicializações mantidas como estão no seu código anterior] ...

// 🚬 CSRF util
function getCSRFToken() {
const name = 'csrftoken';
const cookies = document.cookie.split(';');
for (let cookie of cookies) {
  const trimmed = cookie.trim();
  if (trimmed.startsWith(name + '=')) {
    return decodeURIComponent(trimmed.substring(name.length + 1));
  }
}
return '';
}

// 🔄 Logout automático por inatividade (1 minuto)
let timerInatividade;

function resetarTimerInatividade() {
clearTimeout(timerInatividade);
timerInatividade = setTimeout(() => {
  window.logoutPorInatividade();
}, 5 * 60 * 5000); // 5 minutos
}

window.logoutPorInatividade = function () {
fetch('/accounts/logout-auto/', {
  method: 'POST',
  headers: {
    'X-CSRFToken': getCSRFToken(),
    'X-Requested-With': 'XMLHttpRequest'
  }
})
.then(response => response.json())
.then(data => {
  if (data.redirect_url) {
    // ✅ Força recarregamento completo da página
    window.location.assign(data.redirect_url);
  }
})
.catch(err => {
  console.error('Erro ao tentar logout por inatividade:', err);
});
};


['click', 'mousemove', 'keydown', 'scroll'].forEach(evento => {
document.addEventListener(evento, resetarTimerInatividade);
});

resetarTimerInatividade();

function initCadastroEmpresaAvancado() {
const tipoSelect = document.getElementById('tipo_empresa');
const grupoPF = document.querySelectorAll('.grupo-pf');
const grupoPJ = document.querySelectorAll('.grupo-pj');

if (!tipoSelect) return;

function atualizarCampos() {
  const tipo = tipoSelect.value;
  grupoPF.forEach(el => el.classList.add('d-none'));
  grupoPJ.forEach(el => el.classList.add('d-none'));

  if (tipo === 'pf') {
    grupoPF.forEach(el => el.classList.remove('d-none'));
  } else if (tipo === 'pj') {
    grupoPJ.forEach(el => el.classList.remove('d-none'));
  }
}

tipoSelect.addEventListener('change', atualizarCampos);
atualizarCampos();
}

// 👤 Alternância de campos PF/PJ no cadastro avançado de empresa

// ✅ Máscaras de CPF, CNPJ, ie e telefones
function aplicarMascaras() {
const cpfInputs = document.querySelectorAll('.mascara-cpf');
const cnpjInputs = document.querySelectorAll('.mascara-cnpj');
const telInputs = document.querySelectorAll('.mascara-telefone');
const celInputs = document.querySelectorAll('.mascara-celular');
const ieInputs = document.querySelectorAll('.mascara-ie');

cpfInputs.forEach(input => {
  input.addEventListener('input', () => {
    input.value = input.value
      .replace(/\D/g, '')
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
  });
});

cnpjInputs.forEach(input => {
  input.addEventListener('input', () => {
    input.value = input.value
      .replace(/\D/g, '')
      .replace(/^(\d{2})(\d)/, '$1.$2')
      .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
      .replace(/\.(\d{3})(\d)/, '.$1/$2')
      .replace(/(\d{4})(\d)/, '$1-$2');
  });
});

telInputs.forEach(input => {
  input.addEventListener('input', () => {
    input.value = input.value
      .replace(/\D/g, '')
      .replace(/(\d{2})(\d)/, '($1) $2')
      .replace(/(\d{4})(\d)/, '$1-$2')
      .slice(0, 14);
  });
});

celInputs.forEach(input => {
  input.addEventListener('input', () => {
    input.value = input.value
      .replace(/\D/g, '')
      .replace(/(\d{2})(\d)/, '($1) $2')
      .replace(/(\d{5})(\d)/, '$1-$2')
      .slice(0, 15);
  });
});

ieInputs.forEach(input => {
  input.addEventListener('input', () => {
    input.value = input.value
      .replace(/\D/g, '')
      .replace(/^(\d{3})(\d)/, '$1.$2')
      .replace(/^(\d{3})\.(\d{3})(\d)/, '$1.$2.$3')
      .replace(/^(\d{3})\.(\d{3})\.(\d{3})(\d+)/, '$1.$2.$3.$4')
      .slice(0, 15);
  });
});
}

const cepInputs = document.querySelectorAll('.mascara-cep');
cepInputs.forEach(input => {
input.addEventListener('input', () => {
  input.value = input.value
    .replace(/\D/g, '')
    .replace(/(\d{5})(\d)/, '$1-$2')
    .slice(0, 9);
});
});

// ✅ Máscara de CEP e auto-preenchimento com ViaCEP
function aplicarMascaraCEP() {
const cepInputs = document.querySelectorAll('.mascara-cep');
cepInputs.forEach(input => {
  input.addEventListener('input', () => {
    input.value = input.value
      .replace(/\D/g, '')
      .replace(/(\d{5})(\d)/, '$1-$2')
      .slice(0, 9);
  });
});
}

function autoPreencherEnderecoPorCEP() {
const cepInput = document.getElementById('cep');
if (!cepInput) return;

cepInput.addEventListener('blur', () => {
  const cep = cepInput.value.replace(/\D/g, '');
  if (cep.length !== 8) return;

  fetch(`https://viacep.com.br/ws/${cep}/json/`)
    .then(response => response.json())
    .then(data => {
      if (!data.erro) {
        const map = {
          logradouro: 'logradouro',
          bairro: 'bairro',
          cidade: 'localidade',
          uf: 'uf'
        };
        for (const id in map) {
          const field = document.getElementById(id);
          if (field) field.value = data[map[id]] || '';
        }
      } else {
        mostrarAlertaBootstrap("CEP não encontrado.", "warning");
      }
    })
    .catch(() => {
      mostrarAlertaBootstrap("Erro ao consultar o CEP.", "danger");
    });
});
}

// ✅ Executa ao carregar a tela
aplicarMascaras();

function ativarBuscaDinamicaNCM() {
  const inputBuscaNCM = document.getElementById("busca-ncm");
  if (!inputBuscaNCM) return;

  let timer;
  inputBuscaNCM.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const termo = inputBuscaNCM.value.trim();
      const posCursor = inputBuscaNCM.selectionStart;
      const url = new URL("/produtos/ncm/", window.location.origin);
      if (termo) {
        url.searchParams.set("term", termo);
      }

      fetch(url.href, {
        headers: { "X-Requested-With": "XMLHttpRequest" }
      })
        .then(res => res.text())
        .then(html => {
          const wrapper = document.getElementById("ncm-tabela-wrapper");
          if (!wrapper) return;

          const temp = document.createElement("div");
          temp.innerHTML = html;

          const novaTabela = temp.querySelector("#ncm-tabela-wrapper");
          if (novaTabela) {
            // ✅ Resposta completa → atualiza só a tabela interna
            wrapper.innerHTML = novaTabela.innerHTML;
          } else {
            // ✅ Resposta parcial → substitui o conteúdo diretamente
            wrapper.innerHTML = html;
          }

          inputBuscaNCM.focus();
          inputBuscaNCM.setSelectionRange(posCursor, posCursor);
        })
        .catch(err => {
          console.error("Erro ao buscar NCM dinamicamente:", err);
        });
    }, 400);
  });
}


// ✅ Autocomplete de NCM no Cadastro de Produto (cadastrar_produto.html)
function initAutocompleteNCMProduto() {
  const inputNCM = document.getElementById("ncm-busca-produto");
  if (!inputNCM) return;

  let timer;

  inputNCM.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const termo = inputNCM.value.trim();
      const url = new URL("/produtos/ncm-autocomplete-produto/", window.location.origin);
      if (termo) {
        url.searchParams.set("term", termo);
      }

      fetch(url.href)
        .then(res => res.json())
        .then(data => {
          const dropdown = document.createElement("div");
          dropdown.className = "autocomplete-ncm-list bg-white border mt-1 position-absolute shadow-sm";
          dropdown.style.zIndex = "1000";
          dropdown.style.maxHeight = "200px";
          dropdown.style.overflowY = "auto";
          dropdown.style.width = inputNCM.offsetWidth + "px";

          // Remove sugestões anteriores
          const anterior = document.querySelector(".autocomplete-ncm-list");
          if (anterior) anterior.remove();

          if (data.results.length > 0) {
            data.results.forEach(item => {
              const option = document.createElement("div");
              option.className = "autocomplete-ncm-item p-2";
              option.textContent = item.text;
              option.style.cursor = "pointer";

              option.addEventListener("click", () => {
                inputNCM.value = item.text;
                dropdown.remove();
              });

              dropdown.appendChild(option);
            });

            inputNCM.parentNode.appendChild(dropdown);
          }
        });
    }, 300);
  });

  // Fecha a lista ao clicar fora
  document.addEventListener("click", (e) => {
    if (!inputNCM.contains(e.target)) {
      const dropdown = document.querySelector(".autocomplete-ncm-list");
      if (dropdown) dropdown.remove();
    }
  });
}

// ✅ Disparar após AJAX ou DOM carregado
document.addEventListener("ajaxContentLoaded", initAutocompleteNCMProduto);
document.addEventListener("DOMContentLoaded", initAutocompleteNCMProduto);


// 🚀 Garante execução ao carregar página normalmente
/*
document.addEventListener('DOMContentLoaded', () => {
  console.log("ajaxContentLoaded: tentando ativar Select2");

  if (typeof $ !== 'undefined' && typeof $.fn.select2 !== 'undefined') {
    const campo = document.querySelector('.select2-ncm');
    console.log("Campo Select2:", campo);
    if (campo && typeof initSelect2Campos === "function") {
      console.log("Select2 carregado, chamando initSelect2Campos()");
      initSelect2Campos();
    }
  }

  if (typeof ajaxContentLoaded === "function") ajaxContentLoaded();
});

// 🔄 Garante execução após carregamento via AJAX
document.addEventListener("ajaxContentLoaded", () => {
  if (typeof ajaxContentLoaded === "function") ajaxContentLoaded();
});
*/
/*
document.addEventListener("DOMContentLoaded", () => {
  if (typeof ativarBuscaDinamicaNCM === "function") {
    ativarBuscaDinamicaNCM();
  }
});
*/

document.addEventListener("ajaxContentLoaded", () => {
  if (typeof ativarBuscaDinamicaNCM === "function") {
    ativarBuscaDinamicaNCM();
  }
});

document.addEventListener("ajaxContentLoaded", () => {
  if (typeof initAutocompleteNCMProduto === "function") {
    initAutocompleteNCMProduto();
  }
});