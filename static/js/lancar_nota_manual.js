// static/js/lancar_nota_manual.js

let todasCategorias = [];
let todasEmpresas = [];

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

function mostrarMensagem(icon, title, text) {
    return Swal.fire({ icon, title, text, confirmButtonText: 'Ok' });
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

// Função para adicionar um novo item de produto ao formulário
function adicionarItemProduto() {
    const container = document.getElementById('itens-container');
    const index = container.children.length; // Próximo índice disponível

    const newItemHtml = `
        <div class="item-produto row g-3 mb-3 p-3" data-index="${index}">
            <div class="col-md-3">
                <label for="item-${index}-codigo" class="form-label">Código</label>
                <input type="text" id="item-${index}-codigo" class="form-control" required>
            </div>
            <div class="col-md-4">
                <label for="item-${index}-nome" class="form-label">Nome</label>
                <input type="text" id="item-${index}-nome" class="form-control" required>
            </div>
            <div class="col-md-2">
                <label for="item-${index}-quantidade" class="form-label">Quantidade</label>
                <input type="number" id="item-${index}-quantidade" class="form-control" step="0.001" required>
            </div>
            <div class="col-md-3">
                <label for="item-${index}-valor_unitario" class="form-label">Valor Unitário</label>
                <input type="number" id="item-${index}-valor_unitario" class="form-control" step="0.01" required>
            </div>
            <div class="col-md-4">
                <label for="item-${index}-ncm" class="form-label">NCM</label>
                <input type="text" id="item-${index}-ncm" class="form-control">
            </div>
            <div class="col-md-4">
                <label for="item-${index}-cfop" class="form-label">CFOP</label>
                <input type="text" id="item-${index}-cfop" class="form-control">
            </div>
            <div class="col-md-4">
                <label for="item-${index}-unidade" class="form-label">Unidade</label>
                <input type="text" id="item-${index}-unidade" class="form-control">
            </div>
            <div class="col-md-12">
                <label for="item-${index}-categoria_id" class="form-label">Categoria</label>
                <select id="item-${index}-categoria_id" class="form-select categoria-select" required>
                    <option value="" disabled selected>Selecione a categoria...</option>
                    ${todasCategorias.map(cat => `<option value="${cat.id}">${cat.nome}</option>`).join("")}
                </select>
            </div>
            <div class="col-md-12 text-end">
                <button type="button" class="btn btn-danger btn-sm remover-item-produto">Remover Item</button>
            </div>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', newItemHtml);
}

// Funções para gerenciar a busca e seleção de empresas via modal
function preencherCamposEmpresa(formPrefix, empresa) {
    const prefix = `id_${formPrefix}_`;
    // Preenche CNPJ ou CPF
    if (empresa.cnpj) {
        document.getElementById(`${prefix}cnpj`).value = empresa.cnpj;
        if (document.getElementById(`${prefix}cpf`)) document.getElementById(`${prefix}cpf`).value = ''; // Limpa CPF se CNPJ for preenchido
    } else if (empresa.cpf) {
        document.getElementById(`${prefix}cpf`).value = empresa.cpf;
        if (document.getElementById(`${prefix}cnpj`)) document.getElementById(`${prefix}cnpj`).value = ''; // Limpa CNPJ se CPF for preenchido
    }

    // Preenche Razão Social / Nome
    document.getElementById(`${prefix}xNome`).value = empresa.razao_social || empresa.nome || '';
    // Preenche Nome Fantasia (se existir o campo)
    const xFantField = document.getElementById(`${prefix}xFant`);
    if (xFantField) xFantField.value = empresa.nome_fantasia || '';
    
    document.getElementById(`${prefix}ie`).value = empresa.ie || '';
    document.getElementById(`${prefix}logradouro`).value = empresa.logradouro || '';
    document.getElementById(`${prefix}numero`).value = empresa.numero || '';
    document.getElementById(`${prefix}bairro`).value = empresa.bairro || '';
    document.getElementById(`${prefix}cidade`).value = empresa.cidade || '';
    document.getElementById(`${prefix}uf`).value = empresa.uf || '';
    document.getElementById(`${prefix}cep`).value = empresa.cep || '';
}

function searchEmpresas(searchTerm, formPrefix, modalPrefix) {
    const resultsContainer = document.getElementById(`${modalPrefix}_search_results`);
    resultsContainer.innerHTML = '';

    const term = searchTerm.toLowerCase();
    const filteredEmpresas = todasEmpresas.filter(empresa => {
        // Se o termo de busca estiver vazio, mostra todas as empresas
        if (!term) return true;

        return (empresa.cnpj && empresa.cnpj.toLowerCase().includes(term)) ||
               (empresa.cpf && empresa.cpf.toLowerCase().includes(term)) ||
               (empresa.razao_social && empresa.razao_social.toLowerCase().includes(term)) ||
               (empresa.nome && empresa.nome.toLowerCase().includes(term));
    });

    if (filteredEmpresas.length === 0) {
        resultsContainer.innerHTML = '<p class="text-muted">Nenhuma empresa encontrada.</p>';
        return;
    }

    // Adiciona cabeçalho da tabela
    let tableHtml = `
        <table class="table table-striped table-hover table-sm">
            <thead>
                <tr>
                    <th></th>
                    <th>Nome / Razão Social</th>
                    <th>CNPJ / CPF</th>
                </tr>
            </thead>
            <tbody>
    `;

    filteredEmpresas.forEach(empresa => {
        const nomeDisplay = empresa.razao_social || empresa.nome || 'N/A';
        const cnpjCpfDisplay = empresa.cnpj || empresa.cpf || 'N/A';
        tableHtml += `
            <tr>
                <td>
                    <div class="form-check">
                        <input class="form-check-input empresa-checkbox" type="checkbox" value="${empresa.id}" 
                               id="empresa-${formPrefix}-${empresa.id}" 
                               data-form-prefix="${formPrefix}">
                        <label class="form-check-label" for="empresa-${formPrefix}-${empresa.id}"></label>
                    </div>
                </td>
                <td>${nomeDisplay}</td>
                <td>${cnpjCpfDisplay}</td>
            </tr>
        `;
    });

    tableHtml += `
            </tbody>
        </table>
    `;
    resultsContainer.innerHTML = tableHtml;

    // Adiciona event listeners aos checkboxes
    resultsContainer.querySelectorAll('.empresa-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            // Desmarca outros checkboxes no mesmo modal
            resultsContainer.querySelectorAll('.empresa-checkbox').forEach(otherCheckbox => {
                if (otherCheckbox !== e.target) {
                    otherCheckbox.checked = false;
                }
            });
            // Habilita/desabilita o botão "Selecionar"
            const selectButton = document.getElementById(`select_${modalPrefix}_btn`);
            if (selectButton) {
                selectButton.disabled = !e.target.checked;
            }
        });
    });
}

// Função para coletar os dados do formulário e montar o payload
function coletarDadosFormulario() {
    const payload = {};

    // Dados da Nota Fiscal (Cabeçalho)
    payload.chave_acesso = document.getElementById('id_chave_acesso').value;
    payload.numero = document.getElementById('id_numero').value;
    payload.natureza_operacao = document.getElementById('id_natureza_operacao').value;
    payload.data_emissao = document.getElementById('id_data_emissao').value;
    payload.data_saida = document.getElementById('id_data_saida').value;
    payload.informacoes_adicionais = document.getElementById('id_informacoes_adicionais').value;

    // Dados do Emitente (sempre lendo dos campos de input, que podem ter sido preenchidos via modal ou manualmente)
    payload.emit = {
        CNPJ: document.getElementById('id_emit_cnpj').value,
        xNome: document.getElementById('id_emit_xNome').value,
        xFant: document.getElementById('id_emit_xFant').value,
        IE: document.getElementById('id_emit_ie').value,
        enderEmit: {
            xLgr: document.getElementById('id_emit_logradouro').value,
            nro: document.getElementById('id_emit_numero').value,
            xBairro: document.getElementById('id_emit_bairro').value,
            xMun: document.getElementById('id_emit_cidade').value,
            UF: document.getElementById('id_emit_uf').value,
            CEP: document.getElementById('id_emit_cep').value,
        }
    };

    // Dados do Destinatário (sempre lendo dos campos de input)
    payload.dest = {
        CNPJ: document.getElementById('id_dest_cnpj').value,
        CPF: document.getElementById('id_dest_cpf').value, 
        xNome: document.getElementById('id_dest_xNome').value,
        IE: document.getElementById('id_dest_ie').value,
        enderDest: {
            xLgr: document.getElementById('id_dest_logradouro').value,
            nro: document.getElementById('id_dest_numero').value,
            xBairro: document.getElementById('id_dest_bairro').value,
            xMun: document.getElementById('id_dest_cidade').value,
            UF: document.getElementById('id_dest_uf').value,
            CEP: document.getElementById('id_dest_cep').value,
        }
    };

    // Itens de Produto
    payload.produtos = [];
    let totalNota = 0;
    document.querySelectorAll('.item-produto').forEach(itemDiv => {
        const index = itemDiv.dataset.index;
        const quantidade = parseFloat(document.getElementById(`item-${index}-quantidade`).value) || 0;
        const valorUnitario = parseFloat(document.getElementById(`item-${index}-valor_unitario`).value) || 0;
        const valorTotalItem = quantidade * valorUnitario; // Simplificado, sem desconto por enquanto

        payload.produtos.push({
            codigo: document.getElementById(`item-${index}-codigo`).value,
            nome: document.getElementById(`item-${index}-nome`).value,
            ncm: document.getElementById(`item-${index}-ncm`).value,
            cfop: document.getElementById(`item-${index}-cfop`).value,
            unidade: document.getElementById(`item-${index}-unidade`).value,
            quantidade: quantidade,
            valor_unitario: valorUnitario,
            valor_total: valorTotalItem,
            desconto: 0, // Por enquanto, sem desconto
            novo: true, // Sempre 'novo' para lançamento manual
            categoria_id: parseInt(document.getElementById(`item-${index}-categoria_id`).value),
            imposto_detalhes: {} // Não aplicável para lançamento manual simplificado
        });
        totalNota += valorTotalItem;
    });

    payload.valor_total = totalNota;
    payload.raw_payload = {}; // Não há XML original para lançamento manual

    // Transporte e Cobrança (simplificados, podem ser expandidos depois)
    payload.transporte = {};
    payload.cobranca = {};

    return payload;
}

// Função para enviar os dados para o backend
async function salvarNotaFiscal(forceUpdate = false) {
    mostrarLoading("Salvando nota fiscal...");
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

    let payload;
    try {
        payload = coletarDadosFormulario();
        if (forceUpdate) {
            payload.force_update = true;
        }
    } catch (e) {
        ocultarLoading();
        return mostrarMensagem('error', 'Erro de Validação', e.message);
    }

    try {
        const response = await fetch("/nota-fiscal/api/processar-importacao-xml/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok && data.nota_existente && !forceUpdate) {
            ocultarLoading();
            Swal.fire({
                icon: 'warning',
                title: 'Nota Fiscal Já Importada!',
                text: data.mensagem + ' Deseja substituir/atualizar os dados existentes?',
                showCancelButton: true,
                confirmButtonText: 'Sim, atualizar!',
                cancelButtonText: 'Não, cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    mostrarLoading("Atualizando dados existentes...");
                    salvarNotaFiscal(true);
                } else {
                    mostrarMensagem('info', 'Operação Cancelada', 'A importação foi cancelada pelo usuário.').then(() => {
                        if (data.redirect_url) {
                            window.location.href = data.redirect_url;
                        }
                    });
                }
            });
            return;
        }

        if (!response.ok) {
            throw new Error(data.erro || `Erro HTTP ${response.status}`);
        }

        mostrarMensagem('success', 'Sucesso!', data.mensagem || "Nota fiscal salva com sucesso.").then(() => {
            if (data.redirect_url) {
                window.location.href = data.redirect_url;
            } else {
                window.location.reload();
            }
        });

    } catch (err) {
        console.error("Falha ao salvar a nota:", err);
        mostrarMensagem('error', 'Erro ao Salvar', err.message);
    } finally {
        ocultarLoading();
    }
}

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    // Carrega categorias
    const categoriasEl = document.getElementById('categorias-disponiveis-data');
    try {
        todasCategorias = categoriasEl ? JSON.parse(categoriasEl.textContent.trim() || '[]') : [];
    } catch (e) {
        console.warn('JSON categorias inválido, usando lista vazia.', e);
        todasCategorias = [];
    }

    // Carrega empresas
    const empresasEl = document.getElementById('empresas-disponiveis-data');
    try {
        todasEmpresas = empresasEl ? JSON.parse(empresasEl.textContent.trim() || '[]') : [];
    } catch (e) {
        console.warn('JSON empresas inválido, usando lista vazia.', e);
        todasEmpresas = [];
    }

    // Adiciona o primeiro item de produto por padrão
    adicionarItemProduto();

    // Event listeners para adicionar item
    document.getElementById('add-item-produto').addEventListener('click', adicionarItemProduto);

    // Event listener para remover item (delegação de evento)
    document.getElementById('itens-container').addEventListener('click', function(event) {
        if (event.target.classList.contains('remover-item-produto')) {
            const itemDiv = event.target.closest('.item-produto');
            if (document.querySelectorAll('.item-produto').length > 1) {
                itemDiv.remove();
            } else {
                mostrarMensagem('info', 'Atenção', 'É necessário ter pelo menos um item na nota fiscal.');
            }
        }
    });

    // Event listeners para os botões de seleção de emitente/destinatário
    document.getElementById('btn_selecionar_emitente').addEventListener('click', () => {
        const modal = new bootstrap.Modal(document.getElementById('modalSelecionarEmitente'));
        modal.show();
        document.getElementById('search_emitente_input').value = ''; // Limpa busca anterior
        document.getElementById('emitente_search_results').innerHTML = ''; // Limpa resultados anteriores
        searchEmpresas('', 'emit', 'emitente'); // Exibe todas as empresas inicialmente
        document.getElementById('select_emitente_btn').disabled = true; // Desabilita o botão Selecionar
    });

    document.getElementById('btn_selecionar_destinatario').addEventListener('click', () => {
        const modal = new bootstrap.Modal(document.getElementById('modalSelecionarDestinatario'));
        modal.show();
        document.getElementById('search_destinatario_input').value = ''; // Limpa busca anterior
        document.getElementById('destinatario_search_results').innerHTML = ''; // Limpa resultados anteriores
        searchEmpresas('', 'dest', 'destinatario'); // Exibe todas as empresas inicialmente
        document.getElementById('select_destinatario_btn').disabled = true; // Desabilita o botão Selecionar
    });

    // Event listeners para os botões "Selecionar" dentro dos modais
    document.getElementById('select_emitente_btn').addEventListener('click', () => {
        const selectedCheckbox = document.querySelector('#modalSelecionarEmitente .empresa-checkbox:checked');
        if (selectedCheckbox) {
            const empresaId = selectedCheckbox.value;
            const selectedEmpresa = todasEmpresas.find(emp => emp.id == empresaId);
            if (selectedEmpresa) {
                preencherCamposEmpresa('emit', selectedEmpresa);
                bootstrap.Modal.getInstance(document.getElementById('modalSelecionarEmitente')).hide();
            }
        }
    });

    document.getElementById('select_destinatario_btn').addEventListener('click', () => {
        const selectedCheckbox = document.querySelector('#modalSelecionarDestinatario .empresa-checkbox:checked');
        if (selectedCheckbox) {
            const empresaId = selectedCheckbox.value;
            const selectedEmpresa = todasEmpresas.find(emp => emp.id == empresaId);
            if (selectedEmpresa) {
                preencherCamposEmpresa('dest', selectedEmpresa);
                bootstrap.Modal.getInstance(document.getElementById('modalSelecionarDestinatario')).hide();
            }
        }
    });

    // Event listeners para os campos de busca nos modais
    document.getElementById('search_emitente_input').addEventListener('input', (event) => {
        searchEmpresas(event.target.value, 'emit', 'emitente');
    });
    document.getElementById('search_destinatario_input').addEventListener('input', (event) => {
        searchEmpresas(event.target.value, 'dest', 'destinatario');
    });

    // Event listener para o formulário principal
    document.getElementById('form-lancar-nota').addEventListener('submit', function(event) {
        event.preventDefault();
        salvarNotaFiscal();
    });
});
