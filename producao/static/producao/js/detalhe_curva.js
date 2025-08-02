window.pageInitializers['detalhe_curva'] = function() {
    const identificadorTela = document.getElementById('identificador-tela');
    const API_URL = identificadorTela ? identificadorTela.dataset.apiAtualizarUrl : '';
    const CSRF_TOKEN = $('input[name="csrfmiddlewaretoken"]').val();

    // Função para buscar produtos de ração via API
    async function fetchRacoes() {
        const identificadorTela = document.getElementById('identificador-tela');
        const racoesApiUrl = identificadorTela ? identificadorTela.dataset.apiRacoesUrl : '';

        if (!racoesApiUrl) {
            console.error('URL da API de rações não encontrada no identificador-tela.');
            mostrarMensagem('danger', 'Erro: URL da API de rações não configurada.');
            return [];
        }

        try {
            const response = await fetch(racoesApiUrl, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Erro ao buscar rações:', error);
            mostrarMensagem('danger', 'Erro ao carregar lista de rações.');
            return [];
        }
    }

    $('.editable-racao').on('click', async function() {
        const $cell = $(this);
        const detalheId = $cell.data('detalhe-id');
        const currentRacaoId = $cell.data('racao-id');

        // Evita múltiplas edições na mesma célula
        if ($cell.find('select').length > 0) {
            return;
        }

        const racoes = await fetchRacoes();

        const $select = $('<select class="form-control form-control-sm"></select>');
        $select.append('<option value="">-- Selecionar --</option>');
        racoes.forEach(racao => {
            const $option = $('<option></option>')
                .val(racao.id)
                .text(racao.nome);
            if (racao.id == currentRacaoId) {
                $option.attr('selected', 'selected');
            }
            $select.append($option);
        });

        $cell.empty().append($select);
        $select.focus();

        // Salvar ao mudar a seleção
        $select.on('change', async function() {
            const newRacaoId = $(this).val() || null;

            try {
                console.log("DEBUG: CSRF Token enviado:", CSRF_TOKEN);
                const response = await fetch(API_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': CSRF_TOKEN,
                    },
                    body: JSON.stringify({
                        detalhe_id: detalheId,
                        racao_id: newRacaoId,
                    }),
                });

                const data = await response.json();

                if (data.success) {
                    mostrarMensagem('success', data.message);
                    // Atualizar a célula
                    $cell.data('racao-id', newRacaoId);
                    $cell.text($select.find('option:selected').text());
                } else {
                    mostrarMensagem('danger', data.message);
                    // Reverter a célula para o estado anterior
                    $cell.text(racoes.find(r => r.id == currentRacaoId)?.nome || '-- Selecionar --');
                }
            } catch (error) {
                console.error('Erro ao atualizar ração:', error);
                mostrarMensagem('danger', 'Erro de comunicação com o servidor.');
                $cell.text(racoes.find(r => r.id == currentRacaoId)?.nome || '-- Selecionar --');
            }
        });

        // Voltar ao texto se perder o foco sem selecionar
        $select.on('blur', function() {
            if (!$select.val()) {
                $cell.text(racoes.find(r => r.id == currentRacaoId)?.nome || '-- Selecionar --');
            }
        });
    });
};
