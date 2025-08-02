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

function renderizarPreviewNota(dados) {
    const container = document.getElementById('preview-nota');
    if (!container) return;

    if (!dados || typeof dados !== 'object') {
        container.innerHTML = '<div class="alert alert-danger">Erro: dados inválidos para renderização.</div>';
        return;
    }

    window.__lastXmlResponseData = dados;

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
    const itens = Array.isArray(infNFe.det) ? infNFe.det : (infNFe.det ? [infNFe.det] : []);

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

    if (itens.length > 0) {
        itens.forEach(item => {
            const prod = item.prod || {};
            const isNew = dados.itens_para_revisar?.some(rev => rev.codigo_produto === prod.cProd);
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

    if (transp.modFrete) {
        html += `
            <div class="card mb-3 shadow-sm">
                <div class="card-header"><h5 class="mb-0">Transporte / Frete</h5></div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-4"><p><strong>Modalidade:</strong> ${getModalidadeFrete(transp.modFrete)}</p></div>
                        <div class="col-md-8"><p><strong>Transportadora:</strong> ${transporta.xNome || 'N/A'}</p></div>
                        <div class="col-md-4"><p><strong>Qtd. Volumes:</strong> ${vol.qVol || 0}</p></div>
                        <div class="col-md-4"><p><strong>Peso Líquido:</strong> ${vol.pesoL || 0} kg</p></div>
                        <div class="col-md-4"><p><strong>Peso Bruto:</strong> ${vol.pesoB || 0} kg</p></div>
                    </div>
                </div>
            </div>`;
    }

    if (duplicatas.length > 0) {
        html += `
            <div class="card mb-3 shadow-sm">
                <div class="card-header"><h5 class="mb-0">Cobrança / Duplicatas</h5></div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-bordered table-striped mb-0">
                            <thead class="table-light"><tr><th>Número</th><th>Vencimento</th><th>Valor</th></tr></thead>
                            <tbody>`;
        duplicatas.forEach(dup => {
            html += `
                <tr>
                    <td>${dup.nDup || 'N/A'}</td>
                    <td>${formatarData(dup.dVenc)}</td>
                    <td>${formatarMoeda(dup.vDup)}</td>
                </tr>`;
        });
        html += `</tbody></table></div></div></div>`;
    }

    if (infAdic.infCpl) {
        html += `
            <div class="card mb-3 shadow-sm">
                <div class="card-header"><h5 class="mb-0">Informações Adicionais</h5></div>
                <div class="card-body">
                    <p class="small text-muted">${infAdic.infCpl}</p>
                </div>
            </div>`;
    }
    
    html += `
        <div class="card shadow-sm">
            <div class="card-header"><h5 class="mb-0">Ações</h5></div>
            <div class="card-body text-center">
                ${dados.itens_para_revisar.length > 0 ? 
                    `<button id="btn-revisar-categorias" class="btn btn-warning me-2" data-bs-toggle="modal" data-bs-target="#revisaoCategoriasModal">Revisar Categorias de ${dados.itens_para_revisar.length} Iten(s)</button>` : ''}
                <button id="btn-confirmar-importacao" class="btn btn-success">Confirmar Importação</button>
            </div>
        </div>`;

    container.innerHTML = html;
    adicionarEventListenersBotoes();
}

function renderizarItensParaRevisao() {
    const revisaoLista = document.getElementById('revisao-lista');
    if (!revisaoLista) return;
    let html = '<div class="container-fluid">';
    dadosNotaFiscal.itens_para_revisar.forEach((item, index) => {
        html += `
            <div class="row align-items-center py-2 border-bottom">
                <div class="col-md-7"><label for="categoria-${index}" class="form-label mb-0">${item.descricao_produto}</label></div>
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
                    text: "Esta nota já existe. Deseja substituir os dados com esta nova importação?",
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
            categoriasRevisadas.push({ codigo_produto: select.dataset.codigoProduto, categoria_id: select.value });
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

    // tenta ler a URL da API do atributo data-api-url do form ou cai em action
    const form = document.getElementById('form-importar-xml');
    const apiUrl = form?.getAttribute('data-api-url') || form?.action;

    if (!apiUrl) {
        ocultarLoading();
        mostrarMensagem(
          'error',
          'Erro de Configuração',
          'A URL da API para processar o XML não foi encontrada no form (data-api-url ou action).'
        );
        console.error(
          'Erro: A URL da API para processar o XML não foi encontrada no form.'
        );
        return;
    }
    
    // A seguir continua: const payloadFinal = …

    const payloadFinal = JSON.parse(JSON.stringify(dadosNotaFiscal));
    payloadFinal.force_update = force;
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

    // renomeei para evitar redeclaração
    const importForm = document.getElementById('form-importar-xml');
    const formData = new FormData(importForm);
    formData.append('force_update', force);
    formData.append('payload', JSON.stringify(payloadFinal));

    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        body: formData
    })


    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.erro || `Erro no servidor: ${response.statusText}`); })
            .catch(() => { throw new Error(`Erro na comunicação com o servidor: ${response.status} ${response.statusText}`); });
        }
        return response.json();
    })
    .then(data => {
        ocultarLoading();
        if (data.success) {
            // Exibe a mensagem de sucesso primeiro
            mostrarMensagem('success', 'Sucesso!', data.mensagem);
            
            // Aguarda um pouco antes de redirecionar para dar tempo ao usuário de ler a mensagem
            setTimeout(() => {
                // Usa a URL vindoura do JSON ou, em último caso, o path completo de Entradas de Nota
                loadAjaxContent(data.redirect_url || '/nota-fiscal/entradas/');
            }, 1500); // 1.5 segundos de atraso

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

function initImportarXml() {
    console.log("🚀 Inicializando a página de importação de XML...");
}

document.addEventListener("ajaxFormSuccess", function (e) {
    const { responseJson, form } = e.detail || {};
    if (form && form.id === 'form-importar-xml' && responseJson?.success) {
        console.debug("🔁 importar_xml.js: Evento ajaxFormSuccess recebido. Renderizando preview...");
        dadosNotaFiscal = responseJson;
        renderizarPreviewNota(responseJson);
    }
});

// Registra o inicializador da página
window.pageInitializers['importar_xml'] = initImportarXml;