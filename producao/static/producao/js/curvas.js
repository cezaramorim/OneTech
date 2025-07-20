// producao/static/producao/js/curvas.js

$(document).ready(function() {
    const $selecionarTodasCurvas = $('#selecionar-todas-curvas');
    const $selecionarCurva = $('.selecionar-curva');
    const $btnEditarCurva = $('#btn-editar-curva');
    const $btnExcluirCurva = $('#btn-excluir-curva');

    function atualizarBotoesAcao() {
        const selecionados = $selecionarCurva.filter(':checked').length;
        $btnExcluirCurva.prop('disabled', selecionados === 0);
        $btnEditarCurva.prop('disabled', selecionados !== 1);
    }

    // Selecionar/Deselecionar todos
    $selecionarTodasCurvas.on('change', function() {
        $selecionarCurva.prop('checked', this.checked);
        atualizarBotoesAcao();
    });

    // Seleção individual
    $selecionarCurva.on('change', function() {
        if (!this.checked) {
            $selecionarTodasCurvas.prop('checked', false);
        }
        atualizarBotoesAcao();
    });

    // Ação de Editar
    $btnEditarCurva.on('click', function() {
        const id = $selecionarCurva.filter(':checked').first().closest('tr').data('id');
        if (id) {
            window.location.href = `/producao/curvas/${id}/editar/`;
        }
    });

    // Ação de Excluir
    $btnExcluirCurva.on('click', function() {
        const ids = $selecionarCurva.filter(':checked').map(function() {
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
                        url: '/producao/curvas/excluir-multiplas/',
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
