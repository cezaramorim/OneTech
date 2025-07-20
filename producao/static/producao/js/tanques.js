// producao/static/producao/js/tanques.js

$(document).ready(function() {
    const $selecionarTodosTanques = $('#selecionar-todos-tanques');
    const $selecionarTanque = $('.selecionar-tanque');
    const $btnEditarTanque = $('#btn-editar-tanque');
    const $btnExcluirTanque = $('#btn-excluir-tanque');

    function atualizarBotoesAcao() {
        const selecionados = $selecionarTanque.filter(':checked').length;
        $btnExcluirTanque.prop('disabled', selecionados === 0);
        $btnEditarTanque.prop('disabled', selecionados !== 1);
    }

    // Selecionar/Deselecionar todos
    $selecionarTodosTanques.on('change', function() {
        $selecionarTanque.prop('checked', this.checked);
        atualizarBotoesAcao();
    });

    // Seleção individual
    $selecionarTanque.on('change', function() {
        if (!this.checked) {
            $selecionarTodosTanques.prop('checked', false);
        }
        atualizarBotoesAcao();
    });

    // Ação de Editar
    $btnEditarTanque.on('click', function() {
        const id = $selecionarTanque.filter(':checked').first().closest('tr').data('id');
        if (id) {
            window.location.href = `/producao/tanques/${id}/editar/`;
        }
    });

    // Ação de Excluir
    $btnExcluirTanque.on('click', function() {
        const ids = $selecionarTanque.filter(':checked').map(function() {
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
                        url: '/producao/tanques/excluir-multiplos/',
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
