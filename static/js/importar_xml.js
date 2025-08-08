// static/js/importar_xml.js

// DEBUG: Adicionado para rastrear execuções múltiplas
window.importarXmlExecutionCount = (window.importarXmlExecutionCount || 0) + 1;
console.log('DEBUG: importar_xml.js executado. Contagem: ' + window.importarXmlExecutionCount);

var dadosNotaFiscal = null;
var todasCategorias = [];

// --- Funções Utilitárias ---

function getCSRFToken() {
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
}

function mostrarLoading(message = "Carregando...") {
    if (window.Swal) {
        Swal.fire({ title: message, allowOutsideClick: false, didOpen: () => Swal.showLoading() });
    }
}

function ocultarLoading() {
    if (window.Swal) Swal.close();
}

function mostrarMensagem(type, title, message) {
    if (window.Swal) {
        Swal.fire({
            icon: type,
            title: title,
            text: message,
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 6000,
            timerProgressBar: true
        });
    }
}

function formatarMoeda(valor) {
    const num = parseFloat(valor);
    return isNaN(num) ? 'R$ 0,00' : num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function formatarData(datetimeStr) {
    if (!datetimeStr) return 'N/A';
    const date = new Date(datetimeStr.includes('T') ? datetimeStr : `${datetimeStr}T00:00:00`);
    return isNaN(date.getTime()) ? datetimeStr : date.toLocaleDateString('pt-BR', { timeZone: 'UTC' });
}

function getModalidadeFrete(modFrete) {
    const modalidades = { '0': 'Por conta do Emitente', '1': 'Por conta do Destinatário', '2': 'Por conta de Terceiros', '9': 'Sem Transporte' };
    return modalidades[modFrete] || 'Não especificado';
}

// --- Funções de Lógica Principal ---

function resetarInterface() {
    console.trace("resetarInterface() foi chamada por:");
    const previewDiv = document.getElementById('preview-nota');
    const form = document.getElementById('form-importar-xml');
    if (previewDiv) previewDiv.innerHTML = '';
    if (form) form.reset();
    dadosNotaFiscal = null;
}

function renderizarPreviewNota(dados) {
    const previewDiv = document.getElementById('preview-nota');
    if (!previewDiv) return;

    const { is_duplicate, itens_para_revisar, raw_payload } = dados;
    const infNFe = raw_payload?.NFe?.infNFe || {};
    const emit = infNFe.emit || {};
    const dest = infNFe.dest || {};
    const total = infNFe.total?.ICMSTot || {};
    const transp = infNFe.transp || {};
    const cobr = infNFe.cobr || {};
    const dup = Array.isArray(cobr.dup) ? cobr.dup : (cobr.dup ? [cobr.dup] : []);
    const det = Array.isArray(infNFe.det) ? infNFe.det : [infNFe.det].filter(Boolean);

    const duplicataAlertaHtml = `
        <div class="alert alert-warning shadow-sm p-3" role="alert">
            <h4 class="alert-heading">Nota Fiscal Duplicada!</h4>
            <p>Esta nota fiscal já existe no sistema. Você pode revisar os dados abaixo.</p>
            <hr>
            <p class="mb-0">Deseja importá-la novamente e substituir os dados existentes?</p>
            <div class="mt-3">
                <button id="btn-confirmar-duplicata" class="btn btn-warning me-2">Sim, importar novamente</button>
                <button id="btn-cancelar-duplicata" class="btn btn-danger">Não, cancelar</button>
            </div>
        </div>
    `;

    const acoesFinaisHtml = `
        <div class="d-flex justify-content-end mt-4">
            ${itens_para_revisar.length > 0 ? `<button id="btn-revisar-categorias" class="btn btn-info me-2">Revisar Categorias</button>` : ''}
            <button id="btn-finalizar-importacao" class="btn btn-primary">Finalizar Importação</button>
        </div>
    `;

    previewDiv.innerHTML = `
        ${is_duplicate ? duplicataAlertaHtml : ''}
        ${!is_duplicate && itens_para_revisar.length > 0 ? `<div class="alert alert-info"><strong>Revisão Necessária:</strong> Existem ${itens_para_revisar.length} novo(s) produto(s) que precisam de categoria.</div>` : ''}
        
        <div class="card mb-3 shadow-sm">
            <div class="card-header"><h5 class="mb-0">Dados Principais</h5></div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6"><p><strong>Emitente:</strong> ${emit.xNome || 'N/A'}</p></div>
                    <div class="col-md-6"><p><strong>CNPJ:</strong> ${emit.CNPJ || 'N/A'}</p></div>
                </div>
                <div class="row">
                    <div class="col-md-4"><p><strong>Nota Fiscal:</strong> ${infNFe.ide?.nNF || 'N/A'}</p></div>
                    <div class="col-md-8"><p><strong>Chave de Acesso:</strong> <small>${dados.chave_acesso || 'N/A'}</small></p></div>
                </div>
                <div class="row">
                    <div class="col-md-4"><p><strong>Data Emissão:</strong> ${formatarData(infNFe.ide?.dhEmi)}</p></div>
                    <div class="col-md-4"><p><strong>Data Saída/Entrada:</strong> ${formatarData(infNFe.ide?.dhSaiEnt)}</p></div>
                    <div class="col-md-4"><p><strong>Valor Total:</strong> ${formatarMoeda(total.vNF)}</p></div>
                </div>
                <hr>
                <div class="row">
                    <div class="col-md-6"><p><strong>Destinatário:</strong> ${dest.xNome || 'N/A'}</p></div>
                    <div class="col-md-6"><p><strong>CNPJ/CPF:</strong> ${dest.CNPJ || dest.CPF || 'N/A'}</p></div>
                </div>
            </div>
        </div>

        <div class="card mb-3 shadow-sm"><div class="card-header"><h5 class="mb-0">Itens</h5></div><div class="table-responsive"><table class="table table-sm table-striped table-hover mb-0"><thead><tr><th>#</th><th>Cód.</th><th>Descrição</th><th class="text-end">Qtd.</th><th class="text-end">Vlr. Unit.</th><th class="text-end">Vlr. Total</th><th>Status</th></tr></thead><tbody>
                        ${det.map(item => `<tr><td>${item.nItem}</td><td>${item.prod.cProd}</td><td>${item.prod.xProd}</td><td class="text-end">${parseFloat(item.prod.qCom).toFixed(2)}</td><td class="text-end">${formatarMoeda(item.prod.vUnCom)}</td><td class="text-end">${formatarMoeda(item.prod.vProd)}</td><td>${itens_para_revisar.some(p => p.codigo_produto === item.prod.cProd) ? '<span class="badge bg-warning">Revisar</span>' : '<span class="badge bg-success">OK</span>'}</td></tr>`).join('')}
                    </tbody></table></div></div>
        <div class="card mb-3 shadow-sm"><div class="card-header"><h6 class="mb-0">Faturamento (Duplicatas)</h6></div><div class="table-responsive"><table class="table table-sm table-striped mb-0"><thead><tr><th>Número</th><th>Vencimento</th><th class="text-end">Valor</th></tr></thead><tbody>
                        ${dup.length > 0 ? dup.map(d => `<tr><td>${d.nDup || 'N/A'}</td><td>${formatarData(d.dVenc)}</td><td class="text-end">${formatarMoeda(d.vDup)}</td></tr>`).join('') : '<tr><td colspan="3" class="text-center">Nenhuma duplicata encontrada.</td></tr>'}
                    </tbody></table></div></div>
        <div class="card mb-3 shadow-sm"><div class="card-header"><h6 class="mb-0">Transporte</h6></div><div class="card-body"><div class="row"><div class="col-md-6"><p><strong>Transportadora:</strong> ${transp.transporta?.xNome || 'N/A'}</p></div><div class="col-md-6"><p><strong>Modalidade do Frete:</strong> ${getModalidadeFrete(transp.modFrete)}</p></div><div class="col-md-6"><p><strong>Valor do Frete:</strong> ${formatarMoeda(transp.retTransp?.vServ)}</p></div><div class="col-md-3"><p><strong>Placa:</strong> ${transp.veicTransp?.placa || 'N/A'}</p></div><div class="col-md-3"><p><strong>UF:</strong> ${transp.veicTransp?.UF || 'N/A'}</p></div><div class="col-md-4"><p><strong>Qtd. Volumes:</strong> ${transp.vol?.qVol || 'N/A'}</p></div><div class="col-md-4"><p><strong>Peso Líquido:</strong> ${transp.vol?.pesoL || 'N/A'} kg</p></div><div class="col-md-4"><p><strong>Peso Bruto:</strong> ${transp.vol?.pesoB || 'N/A'} kg</p></div></div></div></div>
        
        ${!is_duplicate ? acoesFinaisHtml : ''}
    `;
    adicionarEventListenersBotoes();
}

function renderizarItensParaRevisao() {
    const corpoModal = document.getElementById('corpoModalRevisao');
    if (!corpoModal) return;
    corpoModal.innerHTML = dadosNotaFiscal.itens_para_revisar.map(item => `
        <div class="row mb-3 border-bottom pb-3"><div class="col-md-5"><strong>Código:</strong> ${item.codigo_produto}<br><strong>Descrição:</strong> ${item.descricao_produto}</div><div class="col-md-3"><strong>NCM:</strong> ${item.ncm}</div><div class="col-md-4"><label for="categoria-${item.codigo_produto}" class="form-label">Categoria:</label><select id="categoria-${item.codigo_produto}" class="form-select form-select-sm categoria-select" data-item-codigo="${item.codigo_produto}" required><option value="" selected disabled>Selecione...</option>${todasCategorias.map(cat => `<option value="${cat.id}">${cat.nome}</option>`).join('')}</select></div></div>
    `).join('');
}

function adicionarEventListenersBotoes() {
    // Listeners para o fluxo normal
    document.getElementById('btn-revisar-categorias')?.addEventListener('click', () => { renderizarItensParaRevisao(); new bootstrap.Modal(document.getElementById('revisaoCategoriasModal')).show(); });
    document.getElementById('btn-finalizar-importacao')?.addEventListener('click', () => finalizarImportacao(false));

    // Listeners para o fluxo de duplicata
    document.getElementById('btn-confirmar-duplicata')?.addEventListener('click', () => finalizarImportacao(true));
    document.getElementById('btn-cancelar-duplicata')?.addEventListener('click', resetarInterface);
}

function salvarCategoriasRevisadas() {
    const selects = document.querySelectorAll('.categoria-select');
    const categoriasSelecionadas = {};
    if (Array.from(selects).some(s => !s.value)) { mostrarMensagem('warning', 'Atenção', 'Selecione uma categoria para todos os itens.'); return; }
    selects.forEach(s => { categoriasSelecionadas[s.dataset.itemCodigo] = { categoria_id: s.value }; });
    dadosNotaFiscal.itens_para_revisar.forEach(item => { item.categoria_id = categoriasSelecionadas[item.codigo_produto].categoria_id; });
    bootstrap.Modal.getInstance(document.getElementById('revisaoCategoriasModal'))?.hide();
    mostrarMensagem('success', 'Sucesso', 'Categorias salvas.');
}

function finalizarImportacao(force = false) {
    const apiUrl = document.getElementById('preview-nota')?.dataset.processarUrl;
    if (!apiUrl) { mostrarMensagem('error', 'Erro', 'URL de processamento não encontrada.'); return; }

    mostrarLoading("Processando e salvando a nota fiscal...");
    const payload = { ...dadosNotaFiscal, force_update: force };

    fetch(apiUrl, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() }, body: JSON.stringify(payload) })
    .then(res => res.json()).then(data => {
        ocultarLoading();
        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Sucesso!',
                text: data.message,
                confirmButtonText: 'OK'
            }).then(() => {
                window.location.href = data.redirect_url || '/nota-fiscal/entradas/';
            });
        } else { throw new Error(data.message); }
    }).catch(err => { ocultarLoading(); mostrarMensagem('error', 'Erro ao Salvar', err.message); });
}

function handleFormSubmit(e) {
    e.preventDefault();
    e.stopPropagation(); // Impede que o evento se propague para o listener global em scripts.js

    const form = e.target;
    fetch(form.action, { method: 'POST', headers: { 'X-CSRFToken': getCSRFToken(), 'X-Requested-With': 'XMLHttpRequest' }, body: new FormData(form) })
    .then(res => { 
        if (!res.ok) return res.json().then(err => { throw new Error(err.message); }); 
        return res.json(); 
    })
    .then(data => { 
        if (data.success) { 
            dadosNotaFiscal = data; 
            renderizarPreviewNota(data);
        } else { 
            throw new Error(data.message); 
        } 
        ocultarLoading(); // Oculta o loading APÓS a renderização ou erro de dados
    })
    .catch(err => { 
        ocultarLoading(); 
        mostrarMensagem('error', 'Erro de Upload', err.message); 
    });
}

function initImportarXml() {
    const form = document.getElementById('form-importar-xml');
    if (!form) {
        return; // Sai se o formulário não existe.
    }

    // Verifica se o listener já foi adicionado usando um atributo de dados.
    if (form.dataset.initialized === 'true') {
        console.log("DEBUG: initImportarXml - Listener de submit já foi adicionado. Ignorando nova tentativa.");
        return;
    }

    console.log("DEBUG: initImportarXml - Adicionando listener de submit pela primeira vez.");
    form.dataset.initialized = 'true'; // Marca o formulário como inicializado.
    form.addEventListener('submit', handleFormSubmit);
    
    const categoriasDataEl = document.getElementById('categorias-data');
    if (categoriasDataEl) {
        try {
            todasCategorias = JSON.parse(categoriasDataEl.textContent);
        } catch (e) {
            console.error("Erro ao parsear categorias JSON:", e);
        }
    }
}

// Garante que o script rode após o carregamento do conteúdo, mesmo em navegação AJAX
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initImportarXml);
} else {
    initImportarXml();
}
document.addEventListener('ajaxContentLoaded', initImportarXml);

