// producao/static/producao/js/lotes.js

$(document).ready(function() {
    const $selecionarTodosLotes = $('#selecionar-todos-lotes');
    const $selecionarLote = $('.selecionar-lote');
    const $btnEditarLote = $('#btn-editar-lote');
    const $btnExcluirLote = $('#btn-excluir-lote');

    function atualizarBotoesAcao() {
        const selecionados = $selecionarLote.filter(':checked').length;
        $btnExcluirLote.prop('disabled', selecionados === 0);
        $btnEditarLote.prop('disabled', selecionados !== 1);
    }

    // Selecionar/Deselecionar todos
    $selecionarTodosLotes.on('change', function() {
        $selecionarLote.prop('checked', this.checked);
        atualizarBotoesAcao();
    });

    // Seleção individual
    $selecionarLote.on('change', function() {
        if (!this.checked) {
            $selecionarTodosLotes.prop('checked', false);
        }
        atualizarBotoesAcao();
    });

    // Ação de Editar
    $btnEditarLote.on('click', function() {
        const id = $selecionarLote.filter(':checked').first().closest('tr').data('id');
        if (id) {
            window.location.href = `/producao/lotes/${id}/editar/`;
        }
    });

    // Ação de Excluir
    $btnExcluirLote.on('click', function() {
        const ids = $selecionarLote.filter(':checked').map(function() {
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
                        url: '/producao/lotes/excluir-multiplos/',
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