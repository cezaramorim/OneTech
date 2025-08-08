// static/js/empresa_avancada_form.js

function initializeEmpresaAvancadaForm() {
    const form = document.getElementById('form-empresa-avancada');
    if (!form) {
        return; // Sai se o formulário específico não está na página.
    }

    const tipoEmpresaSelect = document.getElementById('id_tipo_empresa');
    const camposPj = document.getElementById('campos-pj');
    const camposPf = document.getElementById('campos-pf');

    if (!tipoEmpresaSelect || !camposPj || !camposPf) {
        return; // Sai se os elementos essenciais não existirem
    }

    function toggleCamposVisiveis(tipo) {
        const tipoNormalizado = tipo ? tipo.toUpperCase() : '';
        camposPj.classList.toggle('d-none', tipoNormalizado !== 'PJ');
        camposPf.classList.toggle('d-none', tipoNormalizado !== 'PF');
    }

    // Adiciona o listener para mudanças manuais no tipo de empresa
    tipoEmpresaSelect.addEventListener('change', () => {
        toggleCamposVisiveis(tipoEmpresaSelect.value);
    });

    // Garante que, no carregamento da página, os campos corretos sejam exibidos
    // com base no valor que o Django já renderizou no select.
    toggleCamposVisiveis(tipoEmpresaSelect.value);
}

// Garante a execução no carregamento inicial e na navegação AJAX, seguindo o padrão do projeto.
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeEmpresaAvancadaForm);
} else {
    initializeEmpresaAvancadaForm();
}
document.addEventListener('ajaxContentLoaded', initializeEmpresaAvancadaForm);
