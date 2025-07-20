// producao/static/producao/js/alimentacao.js

$(document).ready(function() {
    const $selecionarTodasAlimentacoes = $('#selecionar-todas-alimentacoes');
    const $selecionarAlimentacao = $('.selecionar-alimentacao');
    const $btnEditarAlimentacao = $('#btn-editar-alimentacao');
    const $btnExcluirAlimentacao = $('#btn-excluir-alimentacao');

    function atualizarBotoesAcao() {
        const selecionados = $selecionarAlimentacao.filter(':checked').length;
        $btnExcluirAlimentacao.prop('disabled', selecionados === 0);
        $btnEditarAlimentacao.prop('disabled', selecionados !== 1);
    }

    // Selecionar/Deselecionar todos
    $selecionarTodasAlimentacoes.on('change', function() {
        $selecionarAlimentacao.prop('checked', this.checked);
        atualizarBotoesAcao();
    });

    // Seleção individual
    $selecionarAlimentacao.on('change', function() {
        if (!this.checked) {
            $selecionarTodasAlimentacoes.prop('checked', false);
        }
        atualizarBotoesAcao();
    });

    // Ação de Editar
    $btnEditarAlimentacao.on('click', function() {
        const id = $selecionarAlimentacao.filter(':checked').first().closest('tr').data('id');
        if (id) {
            window.location.href = `/producao/alimentacao/${id}/editar/`;
        }
    });

    // Ação de Excluir
    $btnExcluirAlimentacao.on('click', function() {
        const ids = $selecionarAlimentacao.filter(':checked').map(function() {
            return $(this).closest('tr').data('id');
        }).get();

        if (ids.length > 0) {
            Swal.fire({
                title: 'Tem certeza?',
                text: "Você não poderá reverter isso!",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Sim, excluir!',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    $.ajax({
                        url: '/producao/alimentacao/excluir-multipla/',
                        method: 'POST',
                        data: JSON.stringify({ ids: ids }),
                        contentType: 'application/json',
                        headers: { 'X-CSRFToken': $('[name="csrfmiddlewaretoken"]').val() },
                        success: function(response) {
                            Swal.fire(
                                'Excluído!',
                                response.mensagem,
                                'success'
                            ).then(() => {
                                window.location.reload(); // Recarrega a página para atualizar a lista
                            });
                        },
                        error: function(xhr) {
                            const errorData = xhr.responseJSON;
                            Swal.fire(
                                'Erro!',
                                errorData.mensagem || 'Ocorreu um erro ao excluir.',
                                'error'
                            );
                        }
                    });
                }
            });
        }
    });

    // Inicializar estado dos botões
    atualizarBotoesAcao();
});