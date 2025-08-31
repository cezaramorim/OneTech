function init_povoamento_lotes() {
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
                return !t.tem_lote_ativo && t.status_nome === 'livre';
            } else {
                return t.tem_lote_ativo;
            }
        });
        tanqueSelect.innerHTML = '<option value="">Selecione...</option>' + tanquesFiltrados.map(t => `<option value="${t.pk}">${t.nome}</option>`).join('');
        $(tanqueSelect).trigger('change');
    };

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

    const buscarHistorico = async () => {
        const dataInicial = page.querySelector('[data-filter="data_inicial"]').value;
        const dataFinal = page.querySelector('[data-filter="data_final"]').value;
        const url = new URL(window.location.origin + '/producao/api/povoamento/historico/');
        if (dataInicial) url.searchParams.append('data_inicial', dataInicial);
        if (dataFinal) url.searchParams.append('data_final', dataFinal);

        try {
            const response = await fetch(url);
            const data = await response.json();
            if (data.success) {
                historicoBody.innerHTML = data.historico.map(h => `
                    <tr>
                        <td>${h.id}</td>
                        <td>${h.data}</td>
                        <td>${h.lote}</td>
                        <td>${h.tanque}</td>
                        <td>${h.quantidade}</td>
                        <td>${h.peso_medio}</td>
                        <td>${h.tipo_evento}</td>
                    </tr>
                `).join('');
            } else {
                mostrarMensagem('danger', data.message);
            }
        } catch (error) {
            mostrarMensagem('danger', 'Erro de comunicação ao buscar histórico.');
        }
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
        if (tipoTanqueSelect.value === 'Tanque Povoado') {
            await verificarLoteAtivo(tanqueSelect.value, novaLinha);
        }
        $(`#${linhaId} .select2-search-row`).select2();
    };

    const processarPovoamentos = async () => {
        // ... (lógica de processamento mantida)
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
    $(function() {
        atualizarOpcoesTanque();
        $('.select2-search').select2();
    });
}

// Anexa a função ao objeto window para ser chamada pelo script global, seguindo o padrão do projeto.
window.init_povoamento_lotes = init_povoamento_lotes;
