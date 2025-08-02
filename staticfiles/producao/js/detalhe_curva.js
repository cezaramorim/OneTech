window.pageInitializers['detalhe_curva'] = function() {
    const API_URL = '{% url "producao:api_atualizar_detalhe_curva" %}';
    const CSRF_TOKEN = $('input[name="csrfmiddlewaretoken"]').val();

    // Função para buscar produtos de ração (simulada por enquanto)
    // Em um cenário real, isso faria uma chamada AJAX para uma API de produtos
    async function fetchRacoes() {
        // TODO: Implementar chamada AJAX real para buscar produtos de categoria 'Ração'
        // Por enquanto, retorna um mock
        return [
            { id: 1, nome: 'Ração A' },
            { id: 2, nome: 'Ração B' },
            { id: 3, nome: 'Ração C' },
        ];
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

        const $fillDownCheckbox = $('<input type="checkbox" id="fill-down-checkbox" class="ms-2"><label for="fill-down-checkbox" class="ms-1">Preencher para baixo</label>');

        $cell.empty().append($select).append($fillDownCheckbox);
        $select.focus();

        // Salvar ao mudar a seleção
        $select.on('change', async function() {
            const newRacaoId = $(this).val() || null;
            const fillDown = $fillDownCheckbox.is(':checked');

            try {
                const response = await fetch(API_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': CSRF_TOKEN,
                    },
                    body: JSON.stringify({
                        detalhe_id: detalheId,
                        racao_id: newRacaoId,
                        fill_down: fillDown,
                    }),
                });

                const data = await response.json();

                if (data.sucesso) {
                    mostrarMensagem('success', data.mensagem);
                    // Atualizar a célula e, se fillDown, as células abaixo
                    if (fillDown) {
                        // Recarregar a página ou atualizar dinamicamente todas as células afetadas
                        loadAjaxContent(window.location.pathname); // Recarrega a página para simplicidade
                    } else {
                        $cell.data('racao-id', newRacaoId);
                        $cell.text($select.find('option:selected').text());
                    }
                } else {
                    mostrarMensagem('danger', data.mensagem);
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
