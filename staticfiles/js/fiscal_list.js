// static/js/fiscal_list.js

document.addEventListener('DOMContentLoaded', function() {
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    const rowCheckboxes = document.querySelectorAll('.row-checkbox');
    const btnEditarSelecionado = document.getElementById('btn-editar-selecionado');
    const btnExcluirSelecionados = document.getElementById('btn-excluir-selecionados');
    const searchInput = document.getElementById('search-input');

    function updateButtonStates() {
        const checkedCheckboxes = document.querySelectorAll('.row-checkbox:checked');
        const selectedCount = checkedCheckboxes.length;

        btnEditarSelecionado.disabled = selectedCount !== 1;
        btnExcluirSelecionados.disabled = selectedCount === 0;

        // Atualiza o estado do checkbox "selecionar todos"
        selectAllCheckbox.checked = selectedCount > 0 && selectedCount === rowCheckboxes.length;
        selectAllCheckbox.indeterminate = selectedCount > 0 && selectedCount < rowCheckboxes.length;
    }

    // Event listener para o checkbox "selecionar todos"
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            rowCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateButtonStates();
        });
    }

    // Event listeners para os checkboxes de linha
    rowCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateButtonStates);
    });

    // Event listener para o botão "Editar Selecionado"
    if (btnEditarSelecionado) {
        btnEditarSelecionado.addEventListener('click', function() {
            const checkedCheckboxes = document.querySelectorAll('.row-checkbox:checked');
            if (checkedCheckboxes.length === 1) {
                const id = checkedCheckboxes[0].value;
                // Redireciona para a página de edição
                // A URL base (e.g., /fiscal/cfops/editar/ ou /fiscal/naturezas-operacao/editar/) deve ser definida no template
                const currentPath = window.location.pathname;
                let editUrl = '';
                if (currentPath.includes('/cfops/')) {
                    editUrl = `/fiscal/cfops/editar/${id}/`;
                } else if (currentPath.includes('/naturezas-operacao/')) {
                    editUrl = `/fiscal/naturezas-operacao/editar/${id}/`;
                }
                if (editUrl) {
                    window.location.href = editUrl;
                }
            }
        });
    }

    // Event listener para o botão "Excluir Selecionados"
    if (btnExcluirSelecionados) {
        btnExcluirSelecionados.addEventListener('click', function() {
            const checkedCheckboxes = document.querySelectorAll('.row-checkbox:checked');
            const ids = Array.from(checkedCheckboxes).map(cb => cb.value);

            if (ids.length > 0) {
                Swal.fire({
                    title: 'Tem certeza?',
                    text: `Você realmente deseja excluir ${ids.length} item(ns)? Esta ação é irreversível!`,
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#d33',
                    cancelButtonColor: '#3085d6',
                    confirmButtonText: 'Sim, excluir!',
                    cancelButtonText: 'Cancelar'
                }).then((result) => {
                    if (result.isConfirmed) {
                        const currentPath = window.location.pathname;
                        let itemType = '';
                        if (currentPath.includes('/cfops/')) {
                            itemType = 'cfop';
                        } else if (currentPath.includes('/naturezas-operacao/')) {
                            itemType = 'natureza_operacao';
                        }

                        fetch('/fiscal/delete-items/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': getCookie('csrftoken') // Função para obter CSRF token
                            },
                            body: JSON.stringify({ ids: ids, item_type: itemType })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                Swal.fire('Excluído!', data.message, 'success').then(() => {
                                    location.reload();
                                });
                            } else {
                                Swal.fire('Erro!', data.error || 'Ocorreu um erro ao excluir os itens.', 'error');
                            }
                        })
                        .catch(error => {
                            console.error('Erro na requisição de exclusão:', error);
                            Swal.fire('Erro!', 'Ocorreu um erro na comunicação com o servidor.', 'error');
                        });
                    }
                });
            }
        });
    }

    // Função auxiliar para obter o CSRF token (necessária para requisições POST/DELETE)
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Event listener para a busca dinâmica
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const currentUrl = new URL(window.location.href);
                currentUrl.searchParams.set('busca', this.value);
                currentUrl.searchParams.delete('ordenacao'); // Resetar ordenação na busca
                window.location.href = currentUrl.toString();
            }, 500); // Atraso de 500ms para evitar muitas requisições
        });
    }

    // Inicializa o estado dos botões ao carregar a página
    updateButtonStates();
});
