// static/js/empresa_avancada_form.js

document.addEventListener('DOMContentLoaded', function() {
    const tipoEmpresaSelect = document.getElementById('id_tipo_empresa');
    const camposPj = document.getElementById('campos-pj');
    const camposPf = document.getElementById('campos-pf');

    function toggleFields() {
        if (tipoEmpresaSelect.value === 'pj') {
            camposPj.classList.remove('d-none');
            camposPf.classList.add('d-none');
        } else if (tipoEmpresaSelect.value === 'pf') {
            camposPf.classList.remove('d-none');
            camposPj.classList.add('d-none');
        } else {
            camposPj.classList.add('d-none');
            camposPf.classList.add('d-none');
        }
    }

    // Executa ao carregar a página
    toggleFields();

    // Adiciona event listener para mudanças no select
    tipoEmpresaSelect.addEventListener('change', toggleFields);

    // Lógica para preencher campos na edição
    // Verifica se a página está em modo de edição (se a variável 'empresa' existe no contexto do template)
    const empresaDataElement = document.getElementById('empresa-data');
    if (empresaDataElement) {
        const empresaData = JSON.parse(empresaDataElement.textContent);
        if (empresaData.pk) { // Se existe um PK, é uma edição
            // Define o tipo de empresa no select
            tipoEmpresaSelect.value = empresaData.tipo_empresa;
            toggleFields(); // Atualiza a visibilidade dos campos

            // Preenche os campos específicos de PJ ou PF
            if (empresaData.tipo_empresa === 'pj') {
                document.getElementById('id_cnpj').value = empresaData.cnpj || '';
                document.getElementById('id_razao_social').value = empresaData.razao_social || '';
                document.getElementById('id_nome_fantasia').value = empresaData.nome_fantasia || '';
                // Preencher outros campos PJ aqui
            } else if (empresaData.tipo_empresa === 'pf') {
                document.getElementById('id_cpf').value = empresaData.cpf || '';
                document.getElementById('id_nome').value = empresaData.nome || '';
                document.getElementById('id_rg').value = empresaData.rg || '';
                document.getElementById('id_profissao').value = empresaData.profissao || '';
                // Preencher outros campos PF aqui
            }
        }
    }
});
