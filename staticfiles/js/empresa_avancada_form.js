// static/js/empresa_avancada_form.js

/**
 * Inicializador para o formulário avançado de empresa.
 * Gerencia a exibição de campos dinâmicos (PF/PJ) e o preenchimento
 * de dados no modo de edição.
 */
window.pageInitializers.empresa_avancada = function() {
  // --- Elementos do DOM ---
  const tipoEmpresaSelect = document.getElementById('id_tipo_empresa');
  const camposPj = document.getElementById('campos-pj');
  const camposPf = document.getElementById('campos-pf');
  const empresaDataElement = document.getElementById('empresa-data');

  // --- Validações Iniciais ---
  if (!tipoEmpresaSelect || !camposPj || !camposPf) {
    console.error('Elementos essenciais do formulário (tipo, campos PF/PJ) não foram encontrados. O script não pode continuar.');
    return;
  }

  // --- Funções ---

  /**
   * Alterna a visibilidade dos campos de Pessoa Física e Jurídica
   * com base no valor selecionado no dropdown.
   * @param {string} tipo - O tipo de empresa ('PJ' ou 'PF').
   */
  function toggleCamposVisiveis(tipo) {
    const tipoNormalizado = tipo ? tipo.toUpperCase() : '';
    camposPj.classList.toggle('d-none', tipoNormalizado !== 'PJ');
    camposPf.classList.toggle('d-none', tipoNormalizado !== 'PF');
  }

  /**
   * Preenche os campos do formulário com os dados da empresa
   * fornecidos pelo servidor (no modo de edição).
   * @param {object} data - O objeto com os dados da empresa.
   */
  function preencherFormulario(data) {
    if (!data) return;

    // Mapeamento simples de chave-valor para preenchimento
    const camposParaPreencher = {
      'cnpj': data.cnpj,
      'razao_social': data.razao_social,
      'nome_fantasia': data.nome_fantasia,
      'cnae_principal': data.cnae_principal,
      'cnae_secundario': data.cnae_secundario,
      'data_abertura': data.data_abertura,
      'cpf': data.cpf,
      'nome': data.nome,
      'rg': data.rg,
      'profissao': data.profissao,
      // Adicione outros campos aqui se necessário
    };

    for (const [id, valor] of Object.entries(camposParaPreencher)) {
      const campo = document.getElementById(`id_${id}`);
      if (campo && valor) {
        campo.value = valor;
      }
    }
  }

  // --- Lógica de Inicialização ---

  // 1. Listener para mudanças manuais no tipo de empresa
  tipoEmpresaSelect.addEventListener('change', () => {
    toggleCamposVisiveis(tipoEmpresaSelect.value);
  });

  // 2. Lógica de Edição: Preenche e exibe os dados ao carregar a página
  if (empresaDataElement) {
    try {
      const empresaData = JSON.parse(empresaDataElement.textContent);
      
      if (empresaData && empresaData.tipo_empresa) {
        // Define o valor correto no select
        tipoEmpresaSelect.value = empresaData.tipo_empresa;
        
        // Preenche os campos do formulário com os dados
        preencherFormulario(empresaData);
      }
    } catch (error) {
      console.error('Falha ao parsear os dados da empresa (JSON).', error);
    }
  }

  // 3. Exibição Inicial: Garante que os campos corretos sejam exibidos na carga inicial
  // (tanto para cadastro quanto para edição)
  toggleCamposVisiveis(tipoEmpresaSelect.value);

};
