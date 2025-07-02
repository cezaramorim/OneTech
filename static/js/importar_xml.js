// static/js/importar_xml.js

// Variável global para armazenar os dados recebidos da API do backend.
let dadosNotaFiscal = null;
// Lista de categorias, que será preenchida a partir do template.
let todasCategorias = [];

// --- Funções Auxiliares ---

function mostrarLoading(message = "Carregando...") {
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingMessage = document.getElementById('loadingMessage');
    if (loadingMessage) loadingMessage.textContent = message;
    if (loadingOverlay) loadingOverlay.style.display = 'flex';
}

function ocultarLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) loadingOverlay.style.display = 'none';
}

function formatarMoedaBr(valor) {
    const num = parseFloat(valor);
    return isNaN(num) ? 'R$ 0,00' : num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function formatarDataHora(datetimeStr) {
    if (!datetimeStr) return 'N/A';
    try {
        const date = new Date(datetimeStr);
        return isNaN(date.getTime()) ? datetimeStr : date.toLocaleString('pt-BR');
    } catch (e) {
        return datetimeStr;
    }
}

function mostrarMensagem(icon, title, text) {
    Swal.fire({ icon, title, text, confirmButtonText: 'Ok' });
}

// --- Funções Principais do Fluxo de Importação ---

/**
 * 1. Envia o arquivo XML para o backend.
 * O backend processa o XML e retorna um JSON estruturado.
 */
async function handleFileUpload() {
    const inputFile = document.getElementById("id_xml");
    const arquivo = inputFile.files[0];
    if (!arquivo) {
        return mostrarMensagem('error', 'Erro', 'Selecione um arquivo XML para importar.');
    }
    if (!arquivo.name.toLowerCase().endsWith('.xml')) {
        return mostrarMensagem('error', 'Erro', 'O arquivo selecionado não é um XML válido.');
    }

    mostrarLoading("Processando XML...");
    const formData = new FormData();
    formData.append("xml", arquivo);
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

    try {
        const response = await fetch("/nota-fiscal/api/importar-xml-nfe/", {
            method: "POST",
            body: formData,
            headers: { "X-CSRFToken": csrfToken }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.erro || `Erro HTTP: ${response.status}`);
        }

        // Armazena os dados recebidos do backend na variável global.
        dadosNotaFiscal = data;
        console.log("Dados recebidos do backend:", dadosNotaFiscal);

        // Exibe os dados na tela para o usuário revisar.
        exibirPreview(dadosNotaFiscal);

    } catch (err) {
        console.error("Erro no upload do XML:", err);
        mostrarMensagem('error', 'Erro no Upload', err.message);
    } finally {
        ocultarLoading();
    }
}

/**
 * 2. Renderiza o preview da Nota Fiscal na tela com os dados do backend.
 */
function exibirPreview(dados) {
    const previewDiv = document.getElementById("preview-nota");
    if (!previewDiv) return;

    const { emit, dest, produtos, chave_acesso, numero, natureza_operacao, data_emissao, data_saida, valor_total, informacoes_adicionais } = dados;

    previewDiv.innerHTML = `
        <div class="card mb-3"><div class="card-header bg-primary text-white"><h5 class="mb-0">Dados Gerais</h5></div>
            <div class="card-body">
                <p><strong>Chave:</strong> ${chave_acesso || 'N/A'}</p>
                <p><strong>Número:</strong> ${numero || 'N/A'}</p>
                <p><strong>Natureza:</strong> ${natureza_operacao || 'N/A'}</p>
                <p><strong>Emissão:</strong> ${formatarDataHora(data_emissao)}</p>
                <p><strong>Saída/Entrada:</strong> ${formatarDataHora(data_saida)}</p>
                <p><strong>Valor Total:</strong> ${formatarMoedaBr(valor_total)}</p>
                <p><strong>Info Adicionais:</strong> ${informacoes_adicionais || 'N/A'}</p>
            </div>
        </div>
        <div class="card mb-3"><div class="card-header bg-info text-white"><h5 class="mb-0">Emitente</h5></div>
            <div class="card-body">
                <p><strong>Razão Social:</strong> ${emit.xNome || 'N/A'}</p>
                <p><strong>CNPJ:</strong> ${emit.CNPJ || 'N/A'}</p>
            </div>
        </div>
        <div class="card mb-3"><div class="card-header bg-secondary text-white"><h5 class="mb-0">Destinatário</h5></div>
            <div class="card-body">
                <p><strong>Nome:</strong> ${dest.xNome || 'N/A'}</p>
                <p><strong>CNPJ/CPF:</strong> ${dest.CNPJ || dest.CPF || 'N/A'}</p>
            </div>
        </div>
        <div class="card mb-3"><div class="card-header bg-warning text-dark"><h5 class="mb-0">Produtos</h5></div>
            <div class="card-body"><div class="table-responsive">
                <table class="table table-striped table-bordered table-sm">
                    <thead><tr><th>Cód.</th><th>Nome</th><th>NCM</th><th>CFOP</th><th>Qtd</th><th>Vlr. Unit.</th><th>Vlr. Total</th><th>Status</th></tr></thead>
                    <tbody>
                        ${produtos.map(p => `
                            <tr>
                                <td>${p.codigo.replace('AUTO-', '')}</td>
                                <td>${p.nome}</td>
                                <td>${p.ncm}</td>
                                <td>${p.cfop}</td>
                                <td>${parseFloat(p.quantidade || '0').toLocaleString('pt-BR')}</td>
                                <td>${formatarMoedaBr(p.valor_unitario)}</td>
                                <td>${formatarMoedaBr(p.valor_total)}</td>
                                <td>${p.novo ? '<span class="badge bg-danger">Novo</span>' : '<span class="badge bg-success">Existente</span>'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div></div>
        </div>
        <div class="d-grid gap-2">
            <button id="confirmarImportacaoBtn" class="btn btn-success btn-lg">Confirmar e Salvar Importação</button>
        </div>
    `;

    document.getElementById('confirmarImportacaoBtn').addEventListener('click', abrirModalRevisaoCategorias);
}

/**
 * 3. Abre o modal para o usuário selecionar a categoria dos produtos novos.
 */
function abrirModalRevisaoCategorias() {
    if (!dadosNotaFiscal || !Array.isArray(dadosNotaFiscal.produtos)) {
        return mostrarMensagem('error', 'Erro', 'Dados da nota não encontrados.');
    }

    const produtosNovos = dadosNotaFiscal.produtos.filter(p => p.novo);

    if (produtosNovos.length === 0) {
        Swal.fire({
            title: 'Nenhum produto novo!',
            text: 'Todos os produtos já existem no sistema. Deseja prosseguir com a importação?',
            icon: 'info',
            showCancelButton: true,
            confirmButtonText: 'Sim, importar!',
            cancelButtonText: 'Cancelar'
        }).then(result => {
            if (result.isConfirmed) {
                salvarImportacao();
            }
        });
        return;
    }

    const listaDiv = document.getElementById("revisao-lista");
    listaDiv.innerHTML = produtosNovos.map((p, idx) => `
        <div class="row align-items-center mb-2">
            <div class="col-md-5"><strong>${p.nome}</strong></div>
            <div class="col-md-7">
                <select class="form-select form-select-sm categoria-select" required data-product-code="${p.codigo}">
                    <option value="" disabled selected>Selecione a categoria...</option>
                    ${todasCategorias.map(cat => `<option value="${cat.id}">${cat.nome}</option>`).join("")}
                </select>
            </div>
        </div>
    `).join('');

    new bootstrap.Modal(document.getElementById("revisaoCategoriasModal")).show();
}

/**
 * 4. Confirma as categorias selecionadas e avança para salvar.
 */
function confirmarRevisaoCategorias() {
    let valido = true;
    const selects = document.querySelectorAll('#revisaoCategoriasModal .categoria-select');

    selects.forEach(select => {
        const productCode = select.dataset.productCode;
        const selectedCategoryId = select.value;
        const produto = dadosNotaFiscal.produtos.find(p => p.codigo === productCode);

        if (!selectedCategoryId) {
            valido = false;
            select.classList.add("is-invalid");
        } else {
            select.classList.remove("is-invalid");
            if (produto) {
                produto.categoria_id = Number(selectedCategoryId);
            }
        }
    });

    if (!valido) {
        return mostrarMensagem('error', 'Erro de Validação', 'Por favor, selecione uma categoria para todos os produtos novos.');
    }

    bootstrap.Modal.getInstance(document.getElementById("revisaoCategoriasModal")).hide();
    salvarImportacao();
}

/**
 * 5. Envia os dados da nota (com as categorias) para o backend para salvamento final.
 */
async function salvarImportacao() {
    if (!dadosNotaFiscal) {
        return mostrarMensagem('error', 'Erro', 'Não há dados da nota para salvar.');
    }

    mostrarLoading("Salvando importação no sistema...");
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

    try {
        // A URL agora aponta para a nova view unificada.
        const response = await fetch("/nota-fiscal/api/processar-importacao-xml/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            // Envia o objeto 'dadosNotaFiscal' completo.
            // O backend terá acesso a todos os dados do XML mais as 'categoria_id' adicionadas.
            body: JSON.stringify(dadosNotaFiscal)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.erro || `Erro HTTP ${response.status}`);
        }

        Swal.fire({
            icon: 'success',
            title: 'Sucesso!',
            text: data.mensagem || "Importação concluída com sucesso.",
            confirmButtonText: 'Ok'
        }).then(() => {
            // Redireciona para a página de listagem de notas.
            if (data.redirect_url) {
                window.location.href = data.redirect_url;
            } else {
                window.location.reload(); // Fallback
            }
        });

    } catch (err) {
        console.error("Falha ao salvar a nota:", err);
        mostrarMensagem('error', 'Erro ao Salvar', err.message);
    } finally {
        ocultarLoading();
    }
}

/**
 * Função de inicialização que adiciona os event listeners.
 */
function init() {
    // Tenta carregar as categorias do objeto global injetado pelo Django.
    todasCategorias = window.CATEGORIAS_DISPONIVEIS || [];
    if (todasCategorias.length === 0) {
        console.warn("A lista de categorias de produtos não foi encontrada. O seletor de categorias ficará vazio.");
    }

    const formXml = document.getElementById("form-importar-xml");
    if (formXml) {
        formXml.addEventListener("submit", e => {
            e.preventDefault();
            handleFileUpload();
        });
    }

    const btnConfirmarCategorias = document.getElementById("btn-confirmar-categorias");
    if (btnConfirmarCategorias) {
        btnConfirmarCategorias.addEventListener("click", confirmarRevisaoCategorias);
    }
}

// Inicia o script quando o DOM estiver pronto.
document.addEventListener("DOMContentLoaded", init);
