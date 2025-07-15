// static/js/nota_fiscal/importar_xml.js

// Variável global para armazenar os dados completos da nota fiscal recebidos da API.
let dadosNotaFiscal = null;

// Armazena as categorias disponíveis, carregadas a partir do template.
let todasCategorias = [];

// --- Funções Auxiliares ---

function getCSRFToken() {
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
}

function mostrarLoading(message = "Carregando...") {
    Swal.fire({
        title: message,
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });
}

function ocultarLoading() {
    Swal.close();
}

function mostrarMensagem(type, title, message) {
    Swal.fire({
        icon: type,
        title: title,
        text: message,
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 4000,
        timerProgressBar: true,
    });
}

function formatarMoeda(valor) {
    const num = parseFloat(valor);
    return isNaN(num) ? 'R$ 0,00' : num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function formatarData(datetimeStr) {
    if (!datetimeStr) return 'N/A';
    // Adiciona 'T00:00:00' se for apenas uma data para evitar problemas de fuso horário
    const dateStr = datetimeStr.includes('T') ? datetimeStr : `${datetimeStr}T00:00:00`;
    const date = new Date(dateStr);
    return isNaN(date.getTime()) ? datetimeStr : date.toLocaleDateString('pt-BR', { timeZone: 'UTC' });
}

function getModalidadeFrete(modFrete) {
    const modalidades = {
        '0': '0 - Por conta do Emitente',
        '1': '1 - Por conta do Destinatário/Remetente',
        '2': '2 - Por conta de Terceiros',
        '3': '3 - Transporte Próprio por conta do Remetente',
        '4': '4 - Transporte Próprio por conta do Destinatário',
        '9': '9 - Sem Ocorrência de Transporte'
    };
    return modalidades[modFrete] || 'Não especificado';
}


// --- Lógica Principal de Importação ---

/**
 * Renderiza a pré-visualização completa da nota fiscal, incluindo novas seções.
 * @param {object} dados - O objeto completo com os dados da nota fiscal.
 */
function renderizarPreviewNota(dados) {
    const container = document.getElementById('preview-nota');
    if (!container) return;

    const infNFe = dados.raw_payload?.NFe?.infNFe || {};
    const ide = infNFe.ide || {};
    const emit = infNFe.emit || {};
    const dest = infNFe.dest || {};
    const total = infNFe.total?.ICMSTot || {};
    const transp = infNFe.transp || {};
    const transporta = transp.transporta || {};
    const vol = Array.isArray(transp.vol) ? transp.vol[0] : transp.vol || {};
    const cobr = infNFe.cobr || {};
    const duplicatas = Array.isArray(cobr.dup) ? cobr.dup : (cobr.dup ? [cobr.dup] : []);
    const infAdic = infNFe.infAdic || {};

    let html = `
        <div class="card mb-3 shadow-sm">
            <div class="card-header bg-primary text-white"><h5 class="mb-0">Detalhes da Nota Fiscal</h5></div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Chave:</strong> <span class="text-muted small">${dados.chave_acesso || 'N/A'}</span></p>
                        <p><strong>Número:</strong> ${dados.numero || 'N/A'} (Série: ${ide.serie || 'N/A'})</p>
                        <p><strong>Emissão:</strong> ${formatarData(dados.data_emissao)}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Valor Total:</strong> ${formatarMoeda(dados.valor_total_nota)}</p>
                        <p><strong>Emitente:</strong> ${emit.xNome || 'N/A'} (${emit.CNPJ || emit.CPF || 'N/A'})</p>
                        <p><strong>Destinatário:</strong> ${dest.xNome || 'N/A'} (${dest.CNPJ || dest.CPF || 'N/A'})</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="card mb-3 shadow-sm">
            <div class="card-header bg-info text-white"><h5 class="mb-0">Itens da Nota</h5></div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-bordered table-striped table-hover mb-0">
                        <thead class="table-light">
                            <tr><th>Cód.</th><th>Descrição</th><th>NCM</th><th>Qtd</th><th>Un.</th><th>Vl. Unit.</th><th>Vl. Total</th><th>Status</th></tr>
                        </thead>
                        <tbody>`;

    const itens = Array.isArray(infNFe.det) ? infNFe.det : [infNFe.det];
    if (itens.length > 0 && itens[0]) {
        itens.forEach(item => {
            const prod = item.prod || {};
            const isNew = dados.itens_para_revisar.some(rev => rev.codigo_produto === prod.cProd);
            html += `
                <tr>
                    <td>${prod.cProd || 'N/A'}</td>
                    <td>${prod.xProd || 'N/A'}</td>
                    <td>${prod.NCM || 'N/A'}</td>
                    <td>${parseFloat(prod.qCom) || 0}</td>
                    <td>${prod.uCom || 'N/A'}</td>
                    <td>${formatarMoeda(prod.vUnCom)}</td>
                    <td>${formatarMoeda(prod.vProd)}</td>
                    <td>${isNew ? '<span class="badge bg-warning text-dark">Revisar</span>' : '<span class="badge bg-success">OK</span>'}</td>
                </tr>`;
        });
    } else {
        html += '<tr><td colspan="8" class="text-center">Nenhum item encontrado.</td></tr>';
    }
    html += `</tbody></table></div></div></div>`;

    // Seção de Transporte
    if (transp.modFrete) {
        html += `
        <div class="card mb-3 shadow-sm">
            <div class="card-header"><h5 class="mb-0">Dados de Transporte</h5></div>
            <div class="card-body">
                <p><strong>Modalidade do Frete:</strong> ${getModalidadeFrete(transp.modFrete)}</p>
                ${transporta.xNome ? `<p><strong>Transportadora:</strong> ${transporta.xNome} (${transporta.CNPJ || transporta.CPF || 'N/A'})</p>` : ''}
                ${vol.qVol ? `<p><strong>Volumes:</strong> ${vol.qVol}</p>` : ''}
                ${vol.pesoL ? `<p><strong>Peso Líquido:</strong> ${vol.pesoL} kg</p>` : ''}
                ${vol.pesoB ? `<p><strong>Peso Bruto:</strong> ${vol.pesoB} kg</p>` : ''}
            </div>
        </div>`;
    }

    // Seção de Duplicatas
    if (duplicatas.length > 0) {
        html += `
        <div class="card mb-3 shadow-sm">
            <div class="card-header"><h5 class="mb-0">Faturas / Duplicatas</h5></div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-striped table-hover mb-0">
                        <thead class="table-light"><tr><th>Número</th><th>Vencimento</th><th>Valor</th></tr></thead>
                        <tbody>`;
        duplicatas.forEach(dup => {
            html += `<tr><td>${dup.nDup || 'N/A'}</td><td>${formatarData(dup.dVenc)}</td><td>${formatarMoeda(dup.vDup)}</td></tr>`;
        });
        html += `</tbody></table></div></div></div>`;
    }

    // Seção de Informações Adicionais
    if (infAdic.infCpl) {
        html += `
        <div class="card mb-3 shadow-sm">
            <div class="card-header"><h5 class="mb-0">Informações Adicionais</h5></div>
            <div class="card-body">
                <p class="font-monospace small text-muted">${infAdic.infCpl}</p>
            </div>
        </div>`;
    }

    // Botões de Ação
    html += `
        <div class="d-grid gap-2 d-md-flex justify-content-md-end mt-3">
            ${dados.itens_para_revisar && dados.itens_para_revisar.length > 0 ?
                `<button type="button" class="btn btn-warning" id="btn-revisar-categorias" data-bs-toggle="modal" data-bs-target="#revisaoCategoriasModal">
                    Revisar Categorias (${dados.itens_para_revisar.length})
                 </button>` : ''
            }
            <button type="button" class="btn btn-success" id="btn-confirmar-importacao">Confirmar Importação</button>
        </div>`;

    container.innerHTML = html;
    adicionarEventListenersBotoes();
}

/**
 * Renderiza os itens para revisão de categoria no modal com layout simplificado.
 */
function renderizarItensParaRevisao() {
    const revisaoLista = document.getElementById('revisao-lista');
    if (!revisaoLista) return;

    let html = '<div class="container-fluid">';
    dadosNotaFiscal.itens_para_revisar.forEach((item, index) => {
        html += `
            <div class="row align-items-center py-2 border-bottom">
                <div class="col-md-7">
                    <label for="categoria-${index}" class="form-label mb-0">${item.descricao_produto}</label>
                </div>
                <div class="col-md-5">
                    <select id="categoria-${index}" class="form-select form-select-sm categoria-select" data-codigo-produto="${item.codigo_produto}" required>
                        <option value="">Selecione uma categoria...</option>
                        ${todasCategorias.map(cat => `<option value="${cat.id}">${cat.nome}</option>`).join('')}
                    </select>
                </div>
            </div>`;
    });
    html += '</div>';
    revisaoLista.innerHTML = html;
}


function adicionarEventListenersBotoes() {
    const btnRevisar = document.getElementById('btn-revisar-categorias');
    if (btnRevisar) {
        btnRevisar.addEventListener('click', renderizarItensParaRevisao);
    }

    const btnConfirmar = document.getElementById('btn-confirmar-importacao');
    if (btnConfirmar) {
        btnConfirmar.addEventListener('click', () => {
            if (dadosNotaFiscal.itens_para_revisar && dadosNotaFiscal.itens_para_revisar.length > 0) {
                mostrarMensagem('info', 'Revisão Pendente', 'Por favor, revise as categorias dos novos produtos antes de confirmar.');
                new bootstrap.Modal(document.getElementById('revisaoCategoriasModal')).show();
                return;
            }

            if (dadosNotaFiscal.is_duplicate) {
                Swal.fire({
                    title: 'Nota Fiscal Duplicada',
                    text: "Esta nota já existe. Deseja substituir todos os dados com esta nova importação?",
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#d33',
                    confirmButtonText: 'Sim, substituir!',
                    cancelButtonText: 'Cancelar'
                }).then(result => {
                    if (result.isConfirmed) {
                        finalizarImportacao(true);
                    }
                });
            } else {
                finalizarImportacao(false);
            }
        });
    }
}

function salvarCategoriasRevisadas() {
    const selects = document.querySelectorAll('#revisao-lista .categoria-select');
    let todasValidas = true;
    const categoriasRevisadas = [];

    selects.forEach(select => {
        if (!select.value) {
            select.classList.add('is-invalid');
            todasValidas = false;
        } else {
            select.classList.remove('is-invalid');
            categoriasRevisadas.push({
                codigo_produto: select.dataset.codigoProduto,
                categoria_id: select.value
            });
        }
    });

    if (!todasValidas) {
        mostrarMensagem('error', 'Validação Falhou', 'Selecione uma categoria para todos os itens.');
        return;
    }

    const produtosPayload = dadosNotaFiscal.raw_payload.NFe.infNFe.det;
    const produtosArray = Array.isArray(produtosPayload) ? produtosPayload : [produtosPayload];

    categoriasRevisadas.forEach(revisao => {
        const produto = produtosArray.find(p => p.prod.cProd === revisao.codigo_produto);
        if (produto) {
            // Adiciona a categoria ao objeto do produto para ser enviado ao backend
            if (!produto.prod) produto.prod = {};
            produto.prod.categoria_id = revisao.categoria_id;
        }
    });
    
    dadosNotaFiscal.itens_para_revisar = [];

    const modalInstance = bootstrap.Modal.getInstance(document.getElementById('revisaoCategoriasModal'));
    if (modalInstance) {
        modalInstance.hide();
    }

    document.getElementById('btn-confirmar-importacao').click();
}

function finalizarImportacao(force = false) {
    mostrarLoading("Processando e salvando a nota fiscal...");

    // Garante que a URL da API está definida.
    if (!window.API_PROCESSAR_IMPORTACAO_XML_URL) {
        ocultarLoading();
        mostrarMensagem('error', 'Erro de Configuração', 'A URL da API para processar o XML não foi encontrada.');
        console.error('A variável window.API_PROCESSAR_IMPORTACAO_XML_URL não está definida.');
        return;
    }

    const payloadFinal = JSON.parse(JSON.stringify(dadosNotaFiscal));
    payloadFinal.force_update = force;

    // Prepara o payload com os dados necessários para o backend.
    const infNFe = payloadFinal.raw_payload?.NFe?.infNFe || {};
    payloadFinal.produtos = Array.isArray(infNFe.det) ? infNFe.det : [infNFe.det];
    payloadFinal.emit = infNFe.emit;
    payloadFinal.dest = infNFe.dest;
    payloadFinal.transporte = infNFe.transp;
    payloadFinal.cobranca = infNFe.cobr;
    payloadFinal.informacoes_adicionais = infNFe.infAdic?.infCpl;
    payloadFinal.natureza_operacao = infNFe.ide?.natOp;
    payloadFinal.valor_total_produtos = infNFe.total?.ICMSTot?.vProd;
    payloadFinal.valor_total_icms = infNFe.total?.ICMSTot?.vICMS;
    payloadFinal.valor_total_pis = infNFe.total?.ICMSTot?.vPIS;
    payloadFinal.valor_total_cofins = infNFe.total?.ICMSTot?.vCOFINS;
    payloadFinal.valor_total_desconto = infNFe.total?.ICMSTot?.vDesc;

    // Envia os dados para o endpoint correto, sem ID na URL.
    fetch(window.API_PROCESSAR_IMPORTACAO_XML_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(payloadFinal)
    })
    .then(response => {
        if (!response.ok) {
            // Tenta extrair uma mensagem de erro do JSON, caso contrário, usa o status.
            return response.json().then(err => { 
                throw new Error(err.erro || `Erro no servidor: ${response.statusText}`);
            }).catch(() => {
                // Se o corpo não for JSON, lança um erro com o status da resposta.
                throw new Error(`Erro na comunicação com o servidor: ${response.status} ${response.statusText}`);
            });
        }
        return response.json();
    })
    .then(data => {
        ocultarLoading();
        if (data.success) {
            mostrarMensagem('success', 'Sucesso!', data.mensagem);
            // Redireciona para a página de edição da nota recém-criada.
            setTimeout(() => {
                window.location.href = data.redirect_url || '/painel/';
            }, 1500);
        } else {
            throw new Error(data.erro || 'Ocorreu um erro desconhecido ao salvar a nota.');
        }
    })
    .catch(error => {
        ocultarLoading();
        console.error('Erro ao finalizar importação:', error);
        mostrarMensagem('error', 'Erro ao Salvar', error.message);
    });
}

function init() {
    // Define a URL da API lendo o atributo data do contêiner principal.
    const mainContainer = document.querySelector('[data-page="importar-xml"]');
    if (mainContainer) {
        window.API_PROCESSAR_IMPORTACAO_XML_URL = mainContainer.dataset.apiUrl;
    }

    if (!window.API_PROCESSAR_IMPORTACAO_XML_URL) {
        console.error('Erro Crítico: A URL da API para processar o XML não foi encontrada no atributo data-api-url.');
        mostrarMensagem('error', 'Erro de Configuração', 'Não foi possível encontrar a URL da API. A funcionalidade de importação está desativada.');
        return; // Impede a execução do resto da função se a URL não estiver definida.
    }

    const categoriasData = document.getElementById('categorias-disponiveis-data');
    if (categoriasData) {
        try {
            todasCategorias = JSON.parse(categoriasData.textContent || '[]');
        } catch (e) {
            console.error("Erro ao carregar categorias:", e);
        }
    }

    const form = document.getElementById('form-importar-xml');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            mostrarLoading("Analisando XML...");
            const formData = new FormData(this);
            fetch(this.action, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCSRFToken() },
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { throw new Error(err.error || 'Erro na análise do XML.') });
                }
                return response.json();
            })
            .then(data => {
                ocultarLoading();
                if (data.success) {
                    mostrarMensagem('success', 'XML Processado', data.message);
                    dadosNotaFiscal = data;
                    renderizarPreviewNota(data);
                } else {
                    throw new Error(data.error || 'Falha ao processar XML.');
                }
            })
            .catch(error => {
                ocultarLoading();
                console.error('Erro na importação do XML:', error);
                mostrarMensagem('error', 'Erro na Importação', error.message);
            });
        });
    }
    
    const btnConfirmarCategorias = document.getElementById('btn-confirmar-categorias');
    if (btnConfirmarCategorias) {
        btnConfirmarCategorias.addEventListener('click', salvarCategoriasRevisadas);
    }
    
    const btnAplicarTodos = document.getElementById('btn-aplicar-categoria-todos');
    if (btnAplicarTodos) {
        btnAplicarTodos.addEventListener('click', () => {
            const primeiroSelect = document.querySelector('#revisao-lista .categoria-select');
            if (primeiroSelect && primeiroSelect.value) {
                document.querySelectorAll('#revisao-lista .categoria-select').forEach(select => {
                    select.value = primeiroSelect.value;
                    select.classList.remove('is-invalid');
                });
            } else {
                mostrarMensagem('warning', 'Atenção', 'Selecione uma categoria no primeiro item.');
            }
        });
    }
}

window.initImportarXml = init;