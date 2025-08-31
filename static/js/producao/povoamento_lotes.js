function initPovoamentoLotes() {
    const page = document.querySelector('[data-page="povoamento-lotes"]');
    if (!page || page.dataset.initialized) return;
    page.dataset.initialized = "true";

    // --- Seletores de Elementos ---
    const tipoTanqueSelect = page.querySelector('[data-role="tipo-tanque"]');
    const curvaContainer = page.querySelector('[data-container="curva-crescimento"]');
    const tanqueSelect = page.querySelector('[data-role="tanque"]');
    const curvaSelect = page.querySelector('[data-role="curva-crescimento"]');
    const adicionarBtn = page.querySelector('[data-action="adicionar-linha"]');
    const processarBtn = page.querySelector('[data-action="processar"]');
    const listagemBody = page.querySelector('[data-container="listagem-body"]');
    const buscarBtn = page.querySelector('[data-action="buscar-historico"]');
    const historicoBody = page.querySelector('[data-container="historico-body"]');

    // --- Funções Auxiliares ---
    const gerarGrupoOrigem = () => {
        const d = new Date();
        const mes = String(d.getMonth() + 1).padStart(2, '0');
        const ano = String(d.getFullYear()).slice(-2);
        return `LM${mes}${ano}`;
    };

    const atualizarOpcoesTanque = () => {
        const tipo = tipoTanqueSelect.value;
        const tanquesFiltrados = DJANGO_CONTEXT.tanques.filter(t => {
            if (tipo === 'Tanque Vazio') {
                // Um tanque está disponível se NÃO tiver lote ativo E seu status for 'livre'.
                return !t.tem_lote_ativo && t.status_nome === 'livre';
            } else { // Lógica para 'Tanque Povoado'
                // Um tanque é considerado povoado se tiver um lote ativo, independentemente do status.
                return t.tem_lote_ativo;
            }
        });
        tanqueSelect.innerHTML = '<option value="">Selecione...</option>' + tanquesFiltrados.map(t => `<option value="${t.pk}">${t.nome}</option>`).join('');
        $(tanqueSelect).trigger('change'); // Notifica o select2 da mudança
    };

    // --- Lógica Principal ---
    const adicionarLinha = async () => {
        if (!tanqueSelect.value) { mostrarMensagem('warning', 'Selecione um tanque primeiro.'); return; }

        const linhaId = `row-${Date.now()}`;
        const faseOptions = DJANGO_CONTEXT.fases.map(f => `<option value="${f.pk}">${f.nome}</option>`).join('');
        const linhaOptions = DJANGO_CONTEXT.linhas.map(l => `<option value="${l.pk}">${l.nome}</option>`).join('');

        const novaLinhaHTML = `
            <tr id="${linhaId}" data-tanque-id="${tanqueSelect.value}" data-curva-id="${curvaSelect.value}">
                <td><button class="btn btn-danger btn-sm" data-action="desfazer">X</button></td>
                <td>${tanqueSelect.options[tanqueSelect.selectedIndex].text}</td>
                <td>${gerarGrupoOrigem()}</td>
                <td>${curvaSelect.options[curvaSelect.selectedIndex].text}</td>
                <td><input type="date" class="form-control form-control-sm" data-field="data_lancamento" value="${new Date().toISOString().slice(0,10)}"></td>
                <td><input type="text" class="form-control form-control-sm" data-field="nome_lote"></td>
                <td><input type="number" class="form-control form-control-sm" data-field="quantidade" step="0.01"></td>
                <td><input type="number" class="form-control form-control-sm" data-field="peso_medio" step="0.01"></td>
                <td><select class="form-select form-select-sm select2-search-row" data-field="fase_id">${faseOptions}</select></td>
                <td><input type="text" class="form-control form-control-sm" data-field="tamanho"></td>
                <td><select class="form-select form-select-sm select2-search-row" data-field="linha_id">${linhaOptions}</select></td>
            </tr>
        `;
        listagemBody.insertAdjacentHTML('beforeend', novaLinhaHTML);
        const novaLinha = document.getElementById(linhaId);
        
        // Verifica se o tanque selecionado já tem um lote ativo
        if (tipoTanqueSelect.value === 'Tanque Povoado') {
            await verificarLoteAtivo(tanqueSelect.value, novaLinha);
        }

        // Inicializa o select2 na nova linha
        $(`#${linhaId} .select2-search-row`).select2();
    };

    const processarPovoamentos = async () => {
        const linhas = listagemBody.querySelectorAll('tr');
        if (linhas.length === 0) { mostrarMensagem('warning', 'Adicione pelo menos uma linha para processar.'); return; }

        const payload = {
            povoamentos: Array.from(linhas).map(linha => ({
                tipo_tanque: tipoTanqueSelect.value,
                curva_id: linha.dataset.curvaId,
                tanque_id: linha.dataset.tanqueId,
                grupo_origem: linha.cells[2].textContent,
                data_lancamento: linha.querySelector('[data-field="data_lancamento"]').value,
                nome_lote: linha.querySelector('[data-field="nome_lote"]').value,
                quantidade: linha.querySelector('[data-field="quantidade"]').value,
                peso_medio: linha.querySelector('[data-field="peso_medio"]').value,
                fase_id: linha.querySelector('[data-field="fase_id"]').value,
                tamanho: linha.querySelector('[data-field="tamanho"]').value,
                linha_id: linha.querySelector('[data-field="linha_id"]').value,
            }))
        };

        processarBtn.disabled = true;
        processarBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Processando...';

        try {
            const response = await fetch('/producao/povoamento/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken() // Utiliza a função global do projeto
                },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            mostrarMensagem(response.ok ? 'success' : 'danger', result.message);
            if (response.ok) {
                listagemBody.innerHTML = '';
            }
        } catch (error) {
            mostrarMensagem('danger', 'Ocorreu um erro de comunicação com o servidor.');
        } finally {
            processarBtn.disabled = false;
            processarBtn.innerHTML = 'Processar Povoamentos';
        }
    };

    const buscarHistorico = async () => { /* ... Lógica de busca ... */ };

    const verificarLoteAtivo = async (tanqueId, linha) => {
        if (!tanqueId) return;

        const nomeLoteInput = linha.querySelector('[data-field="nome_lote"]');
        try {
            const response = await fetch(`/producao/api/tanque/${tanqueId}/lote-ativo/`);
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    nomeLoteInput.value = data.lote.nome;
                    nomeLoteInput.readOnly = true;
                }
            } else {
                nomeLoteInput.value = '';
                nomeLoteInput.readOnly = false;
            }
        } catch (error) {
            console.error('Erro ao buscar lote ativo:', error);
            nomeLoteInput.value = '';
            nomeLoteInput.readOnly = false;
        }
    };

    // --- Event Listeners ---
    tipoTanqueSelect.addEventListener('change', () => {
        curvaContainer.style.display = tipoTanqueSelect.value === 'Tanque Povoado' ? 'none' : '';
        atualizarOpcoesTanque();
    });

    adicionarBtn.addEventListener('click', adicionarLinha);
    processarBtn.addEventListener('click', processarPovoamentos);
    if(buscarBtn) buscarBtn.addEventListener('click', buscarHistorico);

    listagemBody.addEventListener('click', (e) => {
        if (e.target.dataset.action === 'desfazer') {
            e.target.closest('tr').remove();
        }
    });

    // --- Inicialização ---
    atualizarOpcoesTanque();
    $('.select2-search').select2();
}

// Roda o inicializador na carga da página
initPovoamentoLotes();
// E também roda sempre que o conteúdo AJAX for carregado
document.addEventListener('ajaxContentLoaded', initPovoamentoLotes);
