// producao/static/producao/js/eventos.js

$(document).ready(function() {
    const $selecionarTodosEventos = $('#selecionar-todos-eventos');
    const $selecionarEvento = $('.selecionar-evento');
    const $btnEditarEvento = $('#btn-editar-evento');
    const $btnExcluirEvento = $('#btn-excluir-evento');

    function atualizarBotoesAcao() {
        const selecionados = $selecionarEvento.filter(':checked').length;
        $btnExcluirEvento.prop('disabled', selecionados === 0);
        $btnEditarEvento.prop('disabled', selecionados !== 1);
    }

    // Selecionar/Deselecionar todos
    $selecionarTodosEventos.on('change', function() {
        $selecionarEvento.prop('checked', this.checked);
        atualizarBotoesAcao();
    });

    // Seleção individual
    $selecionarEvento.on('change', function() {
        if (!this.checked) {
            $selecionarTodosEventos.prop('checked', false);
        }
        atualizarBotoesAcao();
    });

    // Ação de Editar
    $btnEditarEvento.on('click', function() {
        const id = $selecionarEvento.filter(':checked').first().closest('tr').data('id');
        if (id) {
            window.location.href = `/producao/eventos/${id}/editar/`;
        }
    });

    // Ação de Excluir
    $btnExcluirEvento.on('click', function() {
        const ids = $selecionarEvento.filter(':checked').map(function() {
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
                        url: '/producao/eventos/excluir-multiplos/',
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
