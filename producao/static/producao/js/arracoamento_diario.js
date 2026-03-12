// static/js/arracoamento_diario.js
(function () {
    'use strict';

    window.OneTech = window.OneTech || {};

    const ArracoamentoDiario = {
        SELECTOR_ROOT: '[data-page="arracoamento-diario"]',

        API_URL_SUGESTOES: '/producao/api/arracoamento/sugestoes/',
        API_URL_PENDENCIAS: '/producao/api/arracoamento/pendencias/',
        API_URL_LINHAS_PRODUCAO: '/producao/api/linhas-producao/',
        API_URL_APROVAR: '/producao/api/arracoamento/aprovar/',
        API_URL_FASES: '/producao/api/fases-com-tanques/',
        API_URL_AMBIENTE_GET: '/producao/api/ambiente/',
        API_URL_AMBIENTE_UPSERT: '/producao/api/ambiente/upsert/',
        API_URL_RACOES: '/produtos/api/racoes/',

        abortController: null,
        lastAmbienteDateOpened: null,
        racoes: [],

        init: function () {
            try {
                const root = document.querySelector(this.SELECTOR_ROOT);
                if (!root) return;
                if (root.dataset.arracoamentoInitialized === '1') return;
                root.dataset.arracoamentoInitialized = '1';

                if (this.abortController) this.abortController.abort();
                this.abortController = new AbortController();
                const { signal } = this.abortController;
                const self = this;
                const getCSRFTokenSafe = () => {
                    if (typeof window.getCSRFToken === 'function') return window.getCSRFToken();
                    const cookieValue = document.cookie
                        .split('; ')
                        .find((row) => row.startsWith('csrftoken='));
                    return cookieValue ? decodeURIComponent(cookieValue.split('=')[1]) : '';
                };
                const fetchWithCredsSafe = async (url, options = {}) => {
                    if (typeof window.fetchWithCreds === 'function') {
                        return window.fetchWithCreds(url, options);
                    }
                    const method = String(options.method || 'GET').toUpperCase();
                    const headers = { ...(options.headers || {}) };
                    if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
                        const csrf = getCSRFTokenSafe();
                        if (csrf && !headers['X-CSRFToken']) headers['X-CSRFToken'] = csrf;
                    }
                    return fetch(url, { credentials: 'same-origin', ...options, headers });
                };

                // Seletores
                const dataInicialInput = root.querySelector('#data-inicial');
                const dataFinalInput = root.querySelector('#data-final');
                const hojeIso = new Date().toISOString().slice(0, 10);
                if (dataInicialInput) dataInicialInput.setAttribute('max', hojeIso);
                if (dataFinalInput) dataFinalInput.setAttribute('max', hojeIso);
                const filtroStatusSelect = root.querySelector('#filtro-status');
                const filtroLinhaProducaoSelect = root.querySelector('#filtro-linha-producao');
                const btnBuscar = root.querySelector('#btn-buscar');
                const btnLimparFiltros = root.querySelector('#btn-limpar-filtros');
                const loadingSpinner = root.querySelector('#loading-spinner');
                const tabelaBody = root.querySelector('#corpo-tabela-sugestoes');
                const selecionarTodosCheckbox = root.querySelector('#selecionar-todos-sugestoes');
                const aprovarBtn = root.querySelector('#btn-aprovar-selecionados');
                const btnEditar = root.querySelector('#btn-editar');
                const btnExcluir = root.querySelector('#btn-excluir');
                const identificadorTela = root.querySelector('#identificador-tela');

                const modalAmbiente = document.querySelector('#modalAmbiente');
                const btnSalvarAmbiente = document.querySelector('#btn-salvar-ambiente');
                const ambienteDataInput = document.querySelector('#ambiente-data');
                const ambienteContainer = document.querySelector('#ambiente-container');
                const btnAmbienteHeader = root.querySelector('#btn-ambiente');
                const btnPendencias = root.querySelector('#btn-pendencias');

                const modalEdicao = document.querySelector('#modalEdicao');
                const formEdicao = document.querySelector('#formEdicao');

                const ensureModalInBody = (modalEl) => {
                    if (!modalEl) return;
                    if (modalEl.parentElement !== document.body) {
                        document.body.appendChild(modalEl);
                    }
                };
                ensureModalInBody(modalAmbiente);
                ensureModalInBody(modalEdicao);

                const getAmbienteModal = () => modalAmbiente ? bootstrap.Modal.getOrCreateInstance(modalAmbiente) : null;
                const escapeHtml = (value) => String(value ?? '')
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/"/g, '&quot;')
                    .replace(/'/g, '&#39;');

                // ---------- Funções auxiliares ----------
                const resetFiltros = () => {
                    if (dataInicialInput) dataInicialInput.value = '';
                    if (dataFinalInput) dataFinalInput.value = '';
                    if (filtroStatusSelect) filtroStatusSelect.value = '';
                    if (filtroLinhaProducaoSelect) filtroLinhaProducaoSelect.value = '';
                    if (selecionarTodosCheckbox) {
                        selecionarTodosCheckbox.checked = false;
                        selecionarTodosCheckbox.indeterminate = false;
                    }
                    self.lastAmbienteDateOpened = null;
                    atualizarBotoesAcao();
                };

                const clearTable = () => {
                    if (tabelaBody) {
                        tabelaBody.innerHTML = '<tr><td colspan="15" class="text-center text-muted">Utilize os filtros e clique em "Buscar" para ver as sugestões.</td></tr>';
                    }
                    const totalSugerido = root.querySelector('#total-sugerido');
                    const totalReal = root.querySelector('#total-real');
                    if (totalSugerido) totalSugerido.textContent = '0.000';
                    if (totalReal) totalReal.textContent = '0.000';
                };


                const mostrarPendencias = (pendencias, dataReferenciaLabel = null) => {
                    if (!Array.isArray(pendencias) || pendencias.length === 0) {
                        Swal.fire('Info', 'Nao existem pendencias anteriores para a data informada.', 'info');
                        return;
                    }

                    const lista = pendencias
                        .map((p) => `&bull; ${escapeHtml(p.lote_ref || p.lote_nome)}: pendente desde ${escapeHtml(p.primeira_data_pendente || 'N/A')}`)
                        .join('<br>');

                    const complemento = dataReferenciaLabel
                        ? `<br><small>Data de referencia: ${escapeHtml(dataReferenciaLabel)}</small>`
                        : '';

                    Swal.fire({
                        icon: 'warning',
                        title: 'Pendencias anteriores',
                        html: `Existem aprovacoes pendentes em datas anteriores:<br><br>${lista}${complemento}`,
                        confirmButtonText: 'Entendi'
                    });
                };

                const consultarPendencias = async () => {
                    const dataRef = dataInicialInput?.value || new Date().toISOString().slice(0, 10);
                    try {
                        const url = `${self.API_URL_PENDENCIAS}?data_referencia=${encodeURIComponent(dataRef)}`;
                        const response = await fetchWithCredsSafe(url);
                        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                        const result = await response.json();
                        if (!result.success) {
                            Swal.fire('Erro', result.message || 'Nao foi possivel consultar pendencias.', 'error');
                            return;
                        }
                        mostrarPendencias(result.pending_previous_approvals || [], result.data_referencia || null);
                    } catch (error) {
                        console.error('Erro ao consultar pendencias:', error);
                        Swal.fire('Erro', 'Falha ao consultar pendencias.', 'error');
                    }
                };

                const carregarRacoes = async () => {
                    try {
                        const response = await fetchWithCredsSafe(self.API_URL_RACOES);
                        if (response.ok) {
                            self.racoes = await response.json();
                        } else {
                            console.error('Erro ao carregar rações');
                        }
                    } catch (error) {
                        console.error('Erro na requisição de rações:', error);
                    }
                };

                const popularFiltroLinhaProducao = async () => {
                    if (!filtroLinhaProducaoSelect) return;
                    try {
                        const response = await fetchWithCredsSafe(self.API_URL_LINHAS_PRODUCAO);
                        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                        const data = await response.json();

                        if (Array.isArray(data)) {
                            filtroLinhaProducaoSelect.innerHTML = '<option value="">Todas</option>';
                            data.forEach((linha) => {
                                const option = new Option(linha.nome, linha.id);
                                filtroLinhaProducaoSelect.appendChild(option);
                            });
                        } else {
                            console.error('API de linhas de produção não retornou um array como esperado.');
                        }
                    } catch (error) {
                        console.error('Erro ao popular filtro de linha de produção:', error);
                        filtroLinhaProducaoSelect.innerHTML = '<option value="">Erro ao carregar</option>';
                    }
                };

                // Funções de controle dos checkboxes
                function atualizarSelecionarTodos() {
                    if (!selecionarTodosCheckbox) return;
                    const totalHabilitados = root.querySelectorAll('.sugestao-checkbox:not([disabled])').length;
                    const totalSelecionados = root.querySelectorAll('.sugestao-checkbox:checked:not([disabled])').length;
                    selecionarTodosCheckbox.checked = totalHabilitados > 0 && totalSelecionados === totalHabilitados;
                    selecionarTodosCheckbox.indeterminate = totalSelecionados > 0 && totalSelecionados < totalHabilitados;
                }
                function atualizarBotoesAcao() {
                    const selecionados = Array.from(root.querySelectorAll('.sugestao-checkbox:checked'));
                    const pendentes = selecionados.filter(cb => cb.dataset.status === 'Pendente');
                    const aprovadosComRealizado = selecionados.filter((cb) => {
                        if (cb.dataset.status !== 'Aprovado') return false;
                        const realizadoId = Number.parseInt(cb.dataset.realizadoId || '', 10);
                        return Number.isInteger(realizadoId) && realizadoId > 0;
                    });

                    if (aprovarBtn) aprovarBtn.disabled = pendentes.length === 0;

                    if (btnEditar) {
                        const podeEditar = selecionados.length === 1 && aprovadosComRealizado.length === 1;
                        btnEditar.disabled = !podeEditar;
                        btnEditar.classList.toggle('disabled', !podeEditar);

                        if (podeEditar) {
                            const realizadoId = aprovadosComRealizado[0].dataset.realizadoId;
                            const editUrlBase = identificadorTela?.dataset?.urlEditar || '/producao/api/arracoamento/realizado/0/';
                            btnEditar.dataset.href = editUrlBase.replace('/0/', `/${realizadoId}/`);
                        } else {
                            btnEditar.removeAttribute('data-href');
                        }
                    }

                    if (btnExcluir) {
                        const podeExcluir = selecionados.length > 0 && aprovadosComRealizado.length === selecionados.length;
                        btnExcluir.disabled = !podeExcluir;
                        btnExcluir.classList.toggle('disabled', !podeExcluir);
                    }
                }

                const buscarSugestoes = async () => {
                    if (!tabelaBody) {
                        console.error('Elemento #corpo-tabela-sugestoes não encontrado');
                        return;
                    }

                    let dataInicial = dataInicialInput.value;
                    let dataFinal = dataFinalInput.value;
                    if (dataInicial > hojeIso) dataInicial = hojeIso;
                    if (dataFinal > hojeIso) dataFinal = hojeIso;
                    if (dataInicialInput && dataInicialInput.value !== dataInicial) dataInicialInput.value = dataInicial;
                    if (dataFinalInput && dataFinalInput.value !== dataFinal) dataFinalInput.value = dataFinal;

                    if (!dataInicial || !dataFinal) {
                        Swal.fire('Atenção', 'Por favor, selecione a Data Inicial e a Data Final.', 'warning');
                        return;
                    }

                    loadingSpinner.style.display = 'block';
                    tabelaBody.innerHTML = '';

                    const params = new URLSearchParams({
                        data_inicial: dataInicial,
                        data_final: dataFinal,
                        status: filtroStatusSelect.value,
                        linha_producao_id: filtroLinhaProducaoSelect.value,
                    });

                    try {
                        const response = await fetchWithCredsSafe(`${self.API_URL_SUGESTOES}?${params.toString()}`);
                        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                        const result = await response.json();

                        if (result.success && Array.isArray(result.sugestoes)) {
                            // Preenche a tabela
                            if (result.sugestoes.length > 0) {
                                const racoesOptions = self.racoes.map(r => `<option value="${escapeHtml(r.id)}">${escapeHtml(r.nome)}</option>`).join('');

                                tabelaBody.innerHTML = result.sugestoes.map(s => {
                                    return `<tr data-id="${s.id}" data-status="${s.status}">
                                        <td><input type="checkbox" class="sugestao-checkbox" value="${s.id}" data-sugestao-id="${s.id}" data-realizado-id="${s.realizado_id || ''}" data-lote-diario-id="${s.lote_diario_id}" data-status="${s.status}"></td>
                                        <td>${escapeHtml(s.data || '')}</td>
                                        <td>${escapeHtml(s.lote_nome || '')}</td>
                                        <td>${escapeHtml(s.tanque_nome || '')}</td>
                                        <td>${escapeHtml(s.qtd_lote || '')}</td>
                                        <td>${escapeHtml(s.peso_medio || '')}</td>
                                        <td>${escapeHtml(s.linha_producao_nome || '')}</td>
                                        <td>${escapeHtml(s.sequencia || '')}</td>
                                        <td>${escapeHtml(s.racao_sugerida_nome || '')}</td>
                                        <td>
                                            <select class="form-select form-select-sm racao-realizada-select" data-sugestao-id="${s.id}" ${s.status !== 'Pendente' ? 'disabled' : ''}>
                                                <option value="">Sugerida</option>
                                                ${racoesOptions}
                                            </select>
                                        </td>
                                        <td class="text-end">${s.qtd_sugerida_kg || '0.000'}</td>
                                        <td class="text-end">${s.qtd_sugerida_ajustada_kg || '0.000'}</td>
                                        <td><input type="text" class="form-control form-control-sm qtd-real-input" value="${escapeHtml(s.qtd_real_kg || '')}" ${s.status !== 'Pendente' ? 'disabled' : ''}></td>
                                        <td><span class="badge bg-${s.status === 'Pendente' ? 'warning' : 'success'}">${escapeHtml(s.status)}</span></td>
                                    </tr>`;
                                }).join('');

                                // Após montar a tabela, atualiza os checkboxes e botões
                                atualizarSelecionarTodos();
                                atualizarBotoesAcao();
                            } else {
                                tabelaBody.innerHTML = '<tr><td colspan="15" class="text-center">Nenhuma sugest\u00e3o encontrada para os filtros aplicados.</td></tr>';
                            }

                            // Atualiza totais
                            const totalSugeridoEl = root.querySelector('#total-sugerido');
                            const totalRealEl = root.querySelector('#total-real');
                            if (totalSugeridoEl) totalSugeridoEl.textContent = result.totais?.total_sugerido_kg || '0.000';
                            if (totalRealEl) totalRealEl.textContent = result.totais?.total_real_kg || '0.000';
                            if (result.has_pending_previous_approvals && Array.isArray(result.pending_previous_approvals)) {
                                mostrarPendencias(result.pending_previous_approvals);
                            }
                            if (self.lastAmbienteDateOpened !== dataInicial) {
                                self.lastAmbienteDateOpened = dataInicial;
                                try {
                                    const checkResponse = await fetchWithCredsSafe(`${self.API_URL_AMBIENTE_GET}?data=${dataInicial}`);
                                    const checkData = await checkResponse.json();
                                    const dadosExistem =
                                        (checkData && checkData.success && Array.isArray(checkData.fases) && checkData.fases.length > 0) ||
                                        (Array.isArray(checkData) && checkData.length > 0);
                                    if (!dadosExistem) {
                                        await renderModalAmbiente(dataInicial);
                                        getAmbienteModal()?.show();
                                    }
                                } catch (error) {
                                    console.log('Erro ao verificar dados de ambiente, abrindo modal mesmo assim:', error);
                                    await renderModalAmbiente(dataInicial);
                                    getAmbienteModal()?.show();
                                }
                            }
                        } else {
                            throw new Error(result.error || 'Erro ao buscar sugestões.');
                        }
                    } catch (error) {
                        if (error.name !== 'AbortError') {
                            console.error('Erro na busca de sugestões:', error);
                            Swal.fire('Erro', 'Ocorreu um erro ao buscar as sugestões. Verifique o console.', 'error');
                            clearTable();
                        }
                    } finally {
                        loadingSpinner.style.display = 'none';
                    }
                };

                const renderModalAmbiente = async (dataISO) => {
                    ambienteDataInput.value = dataISO;
                    ambienteContainer.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Carregando...</span></div></div>';

                    try {
                        const fasesResponse = await fetchWithCredsSafe(self.API_URL_FASES);
                        if (!fasesResponse.ok) throw new Error(`Erro ao carregar fases: ${fasesResponse.status}`);
                        const fasesData = await fasesResponse.json();

                        let fases = [];
                        if (fasesData.success && Array.isArray(fasesData.fases)) fases = fasesData.fases;
                        else if (Array.isArray(fasesData)) fases = fasesData;
                        else throw new Error('Formato de resposta inválido da API de fases');

                        if (fases.length === 0) {
                            ambienteContainer.innerHTML = '<div class="alert alert-warning">Nenhuma fase de produção encontrada.</div>';
                            return;
                        }

                        const ambienteResponse = await fetchWithCredsSafe(`${self.API_URL_AMBIENTE_GET}?data=${dataISO}`);
                        if (!ambienteResponse.ok) throw new Error(`Erro ao carregar ambiente: ${ambienteResponse.status}`);
                        const ambienteData = await ambienteResponse.json();

                        const ambienteMap = new Map();
                        const ambienteFases =
                            (ambienteData && ambienteData.success && Array.isArray(ambienteData.fases)) ? ambienteData.fases :
                            (Array.isArray(ambienteData) ? ambienteData : []);
                        ambienteFases.forEach(item => ambienteMap.set(item.fase_id, item));

                        let accordionHtml = '<div class="accordion" id="accordionAmbiente">';

                        fases.forEach((fase, index) => {
                            const dados = ambienteMap.get(fase.id) || {};
                            const getValue = (obj, field) => {
                                if (!obj) return '';
                                const val = obj[field];
                                return (val !== null && val !== undefined && val !== '') ? val : '';
                            };

                            accordionHtml += `
                                <div class="accordion-item">
                                    <h2 class="accordion-header" id="heading-${fase.id}">
                                        <button class="accordion-button ${index > 0 ? 'collapsed' : ''}" type="button"
                                                data-bs-toggle="collapse" data-bs-target="#collapse-${fase.id}">
                                            <strong>${fase.nome}</strong>
                                        </button>
                                    </h2>
                                    <div id="collapse-${fase.id}" class="accordion-collapse collapse ${index === 0 ? 'show' : ''}">
                                        <div class="accordion-body">
                                            <input type="hidden" class="amb-fase-id" value="${fase.id}">

                                            <h6 class="mb-3">Leituras de OD e Temperatura por Trato</h6>
                                            <div class="table-responsive">
                                                <table class="table table-sm table-bordered">
                                                    <thead class="table-light">
                                                        <tr>
                                                            <th>Trato</th>
                                                            <th>OD (mg/L)</th>
                                                            <th>Temperatura (°C)</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>`;

                            for (let i = 1; i <= 5; i++) {
                                accordionHtml += `
                                        <tr>
                                            <td class="text-center fw-bold">${i}</td>
                                            <td><input type="number" step="0.1" class="form-control form-control-sm amb-od" data-n="${i}" value="${getValue(dados, `od_${i}`)}" placeholder="OD ${i}"></td>
                                            <td><input type="number" step="0.1" class="form-control form-control-sm amb-temp" data-n="${i}" value="${getValue(dados, `temp_${i}`)}" placeholder="Temp ${i}"></td>
                                        </tr>`;
                            }

                            accordionHtml += `
                                                    </tbody>
                                                </table>
                                            </div>

                                            <h6 class="mt-4 mb-3">Parâmetros Químicos</h6>
                                            <div class="row g-2">
                                                <div class="col"><label class="form-label fw-bold small">pH</label><input type="number" step="0.1" class="form-control form-control-sm amb-ph" value="${getValue(dados, 'ph')}" placeholder="Ex: 7.2"></div>
                                                <div class="col"><label class="form-label fw-bold small">Amônia</label><input type="number" step="0.1" class="form-control form-control-sm amb-amonia" value="${getValue(dados, 'amonia')}" placeholder="Ex: 0.5"></div>
                                                <div class="col"><label class="form-label fw-bold small">Nitrito</label><input type="number" step="0.1" class="form-control form-control-sm amb-nitrito" value="${getValue(dados, 'nitrito')}" placeholder="Ex: 0.1"></div>
                                                <div class="col"><label class="form-label fw-bold small">Nitrato</label><input type="number" step="0.1" class="form-control form-control-sm amb-nitrato" value="${getValue(dados, 'nitrato')}" placeholder="Ex: 5.0"></div>
                                                <div class="col"><label class="form-label fw-bold small">Alcalinidade</label><input type="number" step="0.1" class="form-control form-control-sm amb-alcalinidade" value="${getValue(dados, 'alcalinidade')}" placeholder="Ex: 80"></div>
                                            </div>`;

                            if (dados.od_medio) {
                                accordionHtml += `
                                            <div class="mt-4 p-3 bg-light rounded">
                                                <h6 class="mb-2">Valores Calculados</h6>
                                                <div class="row small">
                                                    <div class="col-md-6"><strong>OD Médio:</strong> ${dados.od_medio} mg/L</div>
                                                    <div class="col-md-6"><strong>Temperatura Média:</strong> ${dados.temp_media || ''}°C</div>
                                                    <div class="col-md-6"><strong>Temperatura Mínima:</strong> ${dados.temp_min || ''}°C</div>
                                                    <div class="col-md-6"><strong>Temperatura Máxima:</strong> ${dados.temp_max || ''}°C</div>
                                                    <div class="col-md-6"><strong>Variação Térmica:</strong> ${dados.variacao_termica || ''}°C</div>
                                                </div>
                                            </div>`;
                            }

                            accordionHtml += `
                                        </div>
                                    </div>
                                </div>`;
                        });

                        accordionHtml += '</div>';
                        ambienteContainer.innerHTML = accordionHtml;
                    } catch (error) {
                        console.error('Erro ao renderizar modal de ambiente:', error);
                        ambienteContainer.innerHTML = `<div class="alert alert-danger">Erro: ${error.message}</div>`;
                    }
                };

                const salvarAmbiente = async () => {
                    const data = ambienteDataInput.value;
                    const faseItems = ambienteContainer.querySelectorAll('.accordion-item');
                    if (faseItems.length === 0) {
                        Swal.fire('Atenção', 'Não há dados para salvar.', 'warning');
                        return;
                    }

                    Swal.fire({
                        title: 'Salvando...',
                        html: 'Processando dados de ambiente...',
                        allowOutsideClick: false,
                        didOpen: () => Swal.showLoading()
                    });

                    let sucessos = 0, erros = [];

                    for (const faseItem of faseItems) {
                        const body = faseItem.querySelector('.accordion-body');
                        const faseId = parseInt(body.querySelector('.amb-fase-id').value);
                        const faseData = { fase_id: faseId, data: data };

                        for (let i = 1; i <= 5; i++) {
                            const odInput = body.querySelector(`.amb-od[data-n="${i}"]`);
                            const tempInput = body.querySelector(`.amb-temp[data-n="${i}"]`);
                            if (odInput && odInput.value) faseData[`od_${i}`] = odInput.value;
                            if (tempInput && tempInput.value) faseData[`temp_${i}`] = tempInput.value;
                        }

                        ['ph', 'amonia', 'nitrito', 'nitrato', 'alcalinidade'].forEach(campo => {
                            const input = body.querySelector(`.amb-${campo}`);
                            if (input && input.value) faseData[campo] = input.value;
                        });

                        try {
                            const response = await fetchWithCredsSafe(self.API_URL_AMBIENTE_UPSERT, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(faseData)
                            });
                            const result = await response.json();
                            if (result.success) sucessos++;
                            else erros.push(`Fase ${faseId}: ${result.message || 'Erro desconhecido'}`);
                        } catch (error) {
                            erros.push(`Fase ${faseId}: ${error.message}`);
                        }
                    }

                    Swal.close();

                    if (erros.length === 0) {
                        Swal.fire({ icon: 'success', title: 'Sucesso!', html: `<p>Dados salvos para ${sucessos} fase(s)!</p>`, timer: 2000, showConfirmButton: false });
                        const modal = bootstrap.Modal.getInstance(modalAmbiente);
                        if (modal) modal.hide();
                        buscarSugestoes();
                    } else {
                        Swal.fire({
                            icon: 'warning',
                            title: 'Atenção',
                            html: `<p>${sucessos} fase(s) salvas, ${erros.length} erro(s):</p><div class="small">${erros.map(e => `<li class="text-danger">${e}</li>`).join('')}</div>`
                        });
                    }
                };

                const aprovarSugestoes = async () => {
                    const checkboxes = Array.from(root.querySelectorAll('.sugestao-checkbox:checked')).filter(cb => cb.dataset.status === 'Pendente');
                    if (checkboxes.length === 0) {
                        Swal.fire('Atenção', 'Nenhuma sugestão selecionada.', 'warning');
                        return;
                    }

                    const total = checkboxes.length;
                    let progressHtml = `
                        <div class="text-center">
                            <div class="progress mb-3" style="height: 20px;">
                                <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 0%;">0%</div>
                            </div>
                            <span>Processando 0 de ${total}</span>
                        </div>
                    `;

                    Swal.fire({
                        title: 'Aprovando...',
                        html: progressHtml,
                        allowOutsideClick: false,
                        didOpen: () => Swal.showLoading()
                    });

                    const resultados = [];
                    for (let i = 0; i < total; i++) {
                        const cb = checkboxes[i];
                        const tr = cb.closest('tr');
                        if (!tr) {
                            resultados.push({ sugestaoId: cb.value, success: false, message: 'Linha não encontrada' });
                            continue;
                        }

                        const sugestaoId = cb.dataset.sugestaoId || cb.value;
                        const loteDiarioId = cb.dataset.loteDiarioId || null;
                        const qtdRealInput = tr.querySelector('.qtd-real-input');
                        const racaSelect = tr.querySelector('.racao-realizada-select');

                        const payload = {
                            sugestao_id: sugestaoId,
                            lote_diario_id: loteDiarioId,
                            quantidade_real_kg: qtdRealInput?.value || '',
                            racao_realizada_id: racaSelect?.value || null
                        };

                        try {
                            const response = await fetchWithCredsSafe(self.API_URL_APROVAR, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(payload)
                            });
                            const result = await response.json();
                            resultados.push({ sugestaoId, success: result.success, message: result.message });
                        } catch (error) {
                            resultados.push({ sugestaoId, success: false, message: error.message });
                        }

                        const percent = Math.round(((i + 1) / total) * 100);
                        const newHtml = `
                            <div class="text-center">
                                <div class="progress mb-3" style="height: 20px;">
                                    <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: ${percent}%;">${percent}%</div>
                                </div>
                                <span>Processando ${i + 1} de ${total}</span>
                            </div>
                        `;
                        Swal.update({ html: newHtml });
                    }

                    Swal.close();

                    const sucessos = resultados.filter(r => r.success).length;
                    const falhas = resultados.filter(r => !r.success);

                    if (falhas.length === 0) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Sucesso!',
                            text: `${sucessos} sugestão(ões) aprovada(s).`,
                            timer: 2000,
                            showConfirmButton: false
                        });
                        buscarSugestoes();
                    } else {
                        const erroMsg = falhas.map(f => `ID ${f.sugestaoId}: ${f.message}`).join('<br>');
                        Swal.fire({
                            icon: 'error',
                            title: 'Erros na aprovação',
                            html: `${sucessos} sucesso(s), ${falhas.length} falha(s).<br><br>${erroMsg}`
                        });
                    }
                };

                // ---------- Event Listeners ----------
                if (btnBuscar) btnBuscar.addEventListener('click', buscarSugestoes, { signal });
                if (aprovarBtn) aprovarBtn.addEventListener('click', aprovarSugestoes, { signal });
                if (btnSalvarAmbiente) btnSalvarAmbiente.addEventListener('click', salvarAmbiente, { signal });

                if (btnExcluir) {
                    btnExcluir.addEventListener('click', async (event) => {
                        event.preventDefault();
                        event.stopPropagation();
                        if (btnExcluir.disabled) return;

                        const selecionados = Array.from(root.querySelectorAll('.sugestao-checkbox:checked'));
                        const idsRealizados = selecionados
                            .filter(cb => cb.dataset.status === 'Aprovado' && cb.dataset.realizadoId)
                            .map(cb => cb.dataset.realizadoId);

                        if (!idsRealizados.length) {
                            Swal.fire('Atencao', 'Selecione apenas lancamentos aprovados para exclusao.', 'warning');
                            return;
                        }

                        const confirmar = await Swal.fire({
                            title: 'Voce tem certeza?',
                            text: `Voce esta prestes a excluir ${idsRealizados.length} lancamento(s) aprovado(s). Esta acao nao pode ser desfeita.`,
                            icon: 'warning',
                            showCancelButton: true,
                            confirmButtonColor: '#d33',
                            cancelButtonColor: '#3085d6',
                            confirmButtonText: 'Sim, excluir!',
                            cancelButtonText: 'Cancelar'
                        });

                        if (!confirmar.isConfirmed) return;

                        try {
                            const response = await fetchWithCredsSafe(identificadorTela?.dataset?.urlExcluir || '/producao/api/arracoamento/realizado/bulk-delete/', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': getCSRFTokenSafe()
                                },
                                body: JSON.stringify({ ids: idsRealizados })
                            });
                            const result = await response.json();
                            if (response.ok && result.success) {
                                Swal.fire('Sucesso', result.message || 'Lancamentos excluidos com sucesso.', 'success');
                                buscarSugestoes();
                            } else {
                                Swal.fire('Erro', result.message || 'Nao foi possivel excluir os lancamentos.', 'error');
                            }
                        } catch (error) {
                            console.error('Erro ao excluir lancamentos de arracoamento:', error);
                            Swal.fire('Erro', 'Falha de comunicacao com o servidor.', 'error');
                        }
                    }, { signal });
                }


                if (btnPendencias) {
                    btnPendencias.addEventListener('click', () => {
                        consultarPendencias();
                    }, { signal });
                }

                if (btnAmbienteHeader) {
                    btnAmbienteHeader.addEventListener('click', () => {
                        const data = dataInicialInput?.value;
                        if (data) {
                            renderModalAmbiente(data);
                            getAmbienteModal()?.show();
                        } else {
                            Swal.fire('Atenção', 'Selecione uma Data Inicial para ver os parâmetros.', 'info');
                        }
                    }, { signal });
                }

                if (modalAmbiente) {
                    modalAmbiente.addEventListener('hide.bs.modal', () => {
                        if (document.activeElement && typeof document.activeElement.blur === 'function') {
                            document.activeElement.blur();
                        }
                        if (btnAmbienteHeader && typeof btnAmbienteHeader.focus === 'function') {
                            btnAmbienteHeader.focus({ preventScroll: true });
                        }
                    }, { signal });
                    modalAmbiente.addEventListener('show.bs.modal', () => {
                        modalAmbiente.setAttribute('aria-hidden', 'false');
                    }, { signal });
                    modalAmbiente.addEventListener('shown.bs.modal', () => {
                        modalAmbiente.setAttribute('aria-hidden', 'false');
                    }, { signal });

                    modalAmbiente.addEventListener('hidden.bs.modal', () => {
                        // Limpeza defensiva para evitar tela bloqueada por estado residual de modal.
                        document.querySelectorAll('.modal-backdrop').forEach((el) => el.remove());
                        document.body.classList.remove('modal-open');
                        document.body.style.removeProperty('padding-right');

                        const mainContent = document.getElementById('main-content');
                        if (mainContent && mainContent.getAttribute('aria-hidden') === 'true') {
                            mainContent.removeAttribute('aria-hidden');
                        }

                        if (btnAmbienteHeader) {
                            btnAmbienteHeader.focus();
                        }
                    }, { signal });
                }
                if (modalEdicao && formEdicao) {
                    modalEdicao.addEventListener('hide.bs.modal', () => {
                        if (document.activeElement && typeof document.activeElement.blur === 'function') {
                            document.activeElement.blur();
                        }
                        if (btnEditar && typeof btnEditar.focus === 'function') {
                            btnEditar.focus({ preventScroll: true });
                        }
                    }, { signal });
                    modalEdicao.addEventListener('show.bs.modal', () => {
                        modalEdicao.setAttribute('aria-hidden', 'false');
                    }, { signal });
                    modalEdicao.addEventListener('shown.bs.modal', () => {
                        modalEdicao.setAttribute('aria-hidden', 'false');
                    }, { signal });
                    const abrirModalEdicao = async () => {
                        if (!btnEditar || btnEditar.disabled) return;

                        const selecionadosNoClique = Array.from(root.querySelectorAll('.sugestao-checkbox:checked'));
                        const selecionadosValidos = selecionadosNoClique.filter((cb) => {
                            if (cb.dataset.status !== 'Aprovado') return false;
                            const rid = Number.parseInt(cb.dataset.realizadoId || '', 10);
                            return Number.isInteger(rid) && rid > 0;
                        });
                        if (selecionadosNoClique.length !== 1 || selecionadosValidos.length !== 1) {
                            atualizarBotoesAcao();
                            Swal.fire('Atencao', 'Lançamento pendente de aprovação. Selecione um lançamento já aprovado para editar.', 'warning');
                            return;
                        }

                        const realizadoIdSelecionado = String(selecionadosValidos[0].dataset.realizadoId || '').trim();
                        if (!realizadoIdSelecionado) {
                            Swal.fire('Atencao', 'Selecione um lancamento aprovado para editar.', 'warning');
                            return;
                        }
                        const url = `/producao/api/arracoamento/realizado/${realizadoIdSelecionado}/`;

                        try {
                            const response = await fetchWithCredsSafe(url);
                            const result = await response.json();
                            if (!response.ok || !result.success) {
                                buscarSugestoes();
                                Swal.fire('Erro', result.message || 'Erro ao carregar dados.', 'error');
                                return;
                            }

                            formEdicao.querySelector('#edit-id').value = result.data.id;
                            formEdicao.querySelector('#edit-lote-nome').value = result.data.lote_nome;
                                                        const racaoSelect = formEdicao.querySelector('#edit-produto-racao-id');
                            if (racaoSelect) {
                                if (!Array.isArray(self.racoes) || self.racoes.length === 0) {
                                    await carregarRacoes();
                                }

                                const currentRacaoId = String(result.data.produto_racao_id || '');
                                const currentRacaoNome = String(result.data.produto_racao_nome || '').trim();
                                const racoesDisponiveis = Array.isArray(self.racoes) ? [...self.racoes] : [];

                                if (currentRacaoId && !racoesDisponiveis.some((r) => String(r.id) === currentRacaoId)) {
                                    racoesDisponiveis.unshift({
                                        id: currentRacaoId,
                                        nome: currentRacaoNome || `Ração #${currentRacaoId}`,
                                    });
                                }

                                if (racoesDisponiveis.length === 0 && currentRacaoId) {
                                    racoesDisponiveis.push({
                                        id: currentRacaoId,
                                        nome: currentRacaoNome || `Ração #${currentRacaoId}`,
                                    });
                                }

                                racaoSelect.innerHTML = racoesDisponiveis
                                    .map((r) => {
                                        const rid = String(r.id);
                                        const selected = rid === currentRacaoId ? ' selected' : '';
                                        return `<option value="${escapeHtml(rid)}"${selected}>${escapeHtml(r.nome)}</option>`;
                                    })
                                    .join('');
                            }
                            formEdicao.querySelector('#edit-quantidade-kg').value = result.data.quantidade_kg;
                            formEdicao.querySelector('#edit-observacoes').value = result.data.observacoes;
                            formEdicao.dataset.apiUrl = `/producao/api/arracoamento/realizado/${result.data.id}/update/`;

                            modalEdicao.setAttribute('aria-hidden', 'false');
                            bootstrap.Modal.getOrCreateInstance(modalEdicao).show();
                        } catch (error) {
                            buscarSugestoes();
                            console.error('Erro ao carregar dados para edicao:', error);
                            Swal.fire('Erro', 'Falha ao carregar dados do lancamento.', 'error');
                        }
                    };

                    if (btnEditar) {
                        btnEditar.addEventListener('click', (event) => {
                            event.preventDefault();
                            event.stopPropagation();
                            abrirModalEdicao();
                        }, { signal });
                    }

                    formEdicao.addEventListener('submit', async (event) => {
                        event.preventDefault();
                        const apiUrl = formEdicao.dataset.apiUrl;
                        if (!apiUrl) return;
                        const formData = new FormData(formEdicao);
                        const payload = Object.fromEntries(formData.entries());

                        try {
                            const response = await fetchWithCredsSafe(apiUrl, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(payload)
                            });
                            const result = await response.json();
                            if (result.success) {
                                Swal.fire('Sucesso', result.message, 'success');
                                bootstrap.Modal.getInstance(modalEdicao)?.hide();
                                buscarSugestoes();
                            } else {
                                Swal.fire('Erro', result.message || 'Erro ao salvar.', 'error');
                            }
                        } catch (error) {
                            console.error('Erro ao salvar edição:', error);
                        }
                    }, { signal });
                }

                // Lógica do checkbox "selecionar todos"
                if (selecionarTodosCheckbox) {
                    selecionarTodosCheckbox.addEventListener('change', function (e) {
                        const checked = e.target.checked;
                        root.querySelectorAll('.sugestao-checkbox:not([disabled])').forEach(cb => {
                            cb.checked = checked;
                        });
                        atualizarBotoesAcao();
                    }, { signal });
                }

                // Atualiza estado do checkbox principal e botões quando um checkbox filho muda
                if (tabelaBody) {
                    tabelaBody.addEventListener('change', (e) => {
                        if (e.target.classList.contains('sugestao-checkbox')) {
                            atualizarSelecionarTodos();
                            atualizarBotoesAcao();
                        }
                    }, { signal });
                }

                if (btnLimparFiltros) {
                    btnLimparFiltros.addEventListener('click', (event) => {
                        event.preventDefault();
                        resetFiltros();
                        clearTable();
                    }, { signal });
                }

                // ---------- Inicialização ----------
                clearTable();
                popularFiltroLinhaProducao();
                carregarRacoes();
                resetFiltros();
                console.log('Módulo de Arraçoamento Diário inicializado.');
            } catch (err) {
                console.error('Erro na inicialização do módulo Arraçoamento Diário:', err);
            }
        }
    };

    window.OneTech.ArracoamentoDiario = ArracoamentoDiario;

    if (document.querySelector(ArracoamentoDiario.SELECTOR_ROOT)) {
        ArracoamentoDiario.init();
    }

    document.addEventListener('ajaxContentLoaded', () => {
        if (document.querySelector(ArracoamentoDiario.SELECTOR_ROOT)) {
            ArracoamentoDiario.init();
        }
    });
})();







