// ✅ Inicializa a importação do XML da Nota Fiscal
function initImportarXML() {
  const form = document.getElementById("form-importar-xml");
  const input = document.getElementById("xml-input");
  const resultado = document.getElementById("resultado-xml");

  // Verifica se os elementos existem na página
  if (!form || !input || !resultado) return;

  form.addEventListener("submit", (e) => {
    e.preventDefault();

    const arquivo = input.files[0];
    if (!arquivo || !arquivo.name.endsWith(".xml")) {
      alert("Por favor, selecione um arquivo XML válido.");
      return;
    }

    const formData = new FormData();
    formData.append("xml", arquivo);
    formData.append("csrfmiddlewaretoken", getCSRFToken());

    // 🔁 Envia o arquivo via fetch para o backend
    fetch('/nota-fiscal/importar/upload/', {  // ✅ Corrigido com traço
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCSRFToken(),
      },
      body: formData
    })
    .then(async res => {
      const contentType = res.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) {
        const text = await res.text();
        throw new Error(`Resposta inesperada do servidor: ${text.slice(0, 200)}`);
      }

      const data = await res.json();

      if (data.erro) {
        resultado.innerHTML = `<div class="alert alert-danger">${data.erro}</div>`;
        return;
      }

      // ✅ Desestruturação dos dados recebidos
      const fornecedor = data.fornecedor || {};
      const produtos = data.produtos || [];
      const totais = data.totais || {};
      const nota = data.nota || {};
      const transporte = data.transporte || {};
      const duplicatas = data.duplicatas || [];
      const info_adicional = data.info_adicional || "";
      const chave_acesso = data.chave_acesso || "";

      // ✅ Começa a montar o HTML
      let html = `
        <!-- 🧾 Bloco: Dados da Nota Fiscal -->
        <h5 class="mt-4">Nota Fiscal</h5>
        <ul class="list-group mb-3">
          <li class="list-group-item"><strong>Número da Nota:</strong> ${nota.numero_nota || '-'}</li>
          <li class="list-group-item"><strong>Data de Emissão:</strong> ${nota.data_emissao || '-'}</li>
          <li class="list-group-item"><strong>Data de Saída:</strong> ${nota.data_saida || '-'}</li>
          <li class="list-group-item"><strong>Natureza da Operação:</strong> ${nota.natureza_operacao || '-'}</li>
          <li class="list-group-item"><strong>Chave de Acesso:</strong> ${chave_acesso || '-'}</li>
        </ul>

        <!-- 🏢 Bloco: Dados do Fornecedor -->
        <h5>Fornecedor</h5>
        <ul class="list-group mb-3">
          <li class="list-group-item"><strong>CNPJ:</strong> ${fornecedor.cnpj || '-'}</li>
          <li class="list-group-item"><strong>Razão Social:</strong> ${fornecedor.razao_social || '-'}</li>
          <li class="list-group-item"><strong>Nome Fantasia:</strong> ${fornecedor.nome_fantasia || '-'}</li>
          <li class="list-group-item"><strong>Endereço:</strong> ${fornecedor.logradouro || ''}, ${fornecedor.numero || ''}, ${fornecedor.bairro || ''}, ${fornecedor.municipio || ''} - ${fornecedor.uf || ''}</li>
          <li class="list-group-item"><strong>CEP:</strong> ${fornecedor.cep || '-'}</li>
          <li class="list-group-item"><strong>Telefone:</strong> ${fornecedor.telefone || '-'}</li>
          <li class="list-group-item"><strong>Inscrição Estadual (IE):</strong> ${fornecedor.ie || '-'}</li>
          <li class="list-group-item"><strong>Regime Tributário (CRT):</strong> ${fornecedor.crt || '-'}</li>
        </ul>

        <!-- 📦 Bloco: Produtos -->
        <h5>Produtos</h5>
        <div class="table-responsive">
          <table class="table table-bordered table-sm table-striped">
            <thead>
              <tr>
                <th>Código</th><th>Nome</th><th>NCM</th><th>CFOP</th><th>Qtd</th><th>Unid</th><th>Vlr Unit.</th><th>Vlr Total</th><th>Desc.</th><th>Outros</th>
              </tr>
            </thead>
            <tbody>
              ${produtos.map(p => `
                <tr>
                  <td>${p.codigo || ''}</td>
                  <td>${p.nome || ''}</td>
                  <td>${p.ncm || ''}</td>
                  <td>${p.cfop || ''}</td>
                  <td>${p.quantidade || ''}</td>
                  <td>${p.unidade || ''}</td>
                  <td>R$ ${p.valor_unitario || ''}</td>
                  <td>R$ ${p.valor_total || ''}</td>
                  <td>R$ ${p.valor_desconto || '0.00'}</td>
                  <td>R$ ${p.valor_outros || '0.00'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>

        <!-- 🚚 Bloco: Transporte -->
        <h5 class="mt-4">Transporte</h5>
        <ul class="list-group mb-3">
          <li class="list-group-item"><strong>Modalidade de Frete:</strong> ${transporte.modalidade_frete || '-'}</li>
          <li class="list-group-item"><strong>Transportadora:</strong> ${transporte.transportadora_nome || '-'}</li>
          <li class="list-group-item"><strong>CNPJ Transportadora:</strong> ${transporte.transportadora_cnpj || '-'}</li>
          <li class="list-group-item"><strong>Placa do Veículo:</strong> ${transporte.veiculo_placa || '-'}</li>
          <li class="list-group-item"><strong>UF do Veículo:</strong> ${transporte.veiculo_uf || '-'}</li>
          <li class="list-group-item"><strong>RNTC do Veículo:</strong> ${transporte.veiculo_rntc || '-'}</li>
          <li class="list-group-item"><strong>Quantidade Volumes:</strong> ${transporte.quantidade_volumes || '-'}</li>
          <li class="list-group-item"><strong>Espécie Volumes:</strong> ${transporte.especie_volumes || '-'}</li>
          <li class="list-group-item"><strong>Peso Líquido:</strong> ${transporte.peso_liquido || '-'}</li>
          <li class="list-group-item"><strong>Peso Bruto:</strong> ${transporte.peso_bruto || '-'}</li>
        </ul>

        <!-- 💳 Bloco: Parcelas -->
        <h5 class="mt-4">Parcelas</h5>
        <div class="table-responsive">
          <table class="table table-bordered table-sm table-striped">
            <thead>
              <tr>
                <th>Parcela</th><th>Valor</th><th>Vencimento</th>
              </tr>
            </thead>
            <tbody>
              ${duplicatas.map(d => `
                <tr>
                  <td>${d.numero || ''}</td>
                  <td>R$ ${d.valor || ''}</td>
                  <td>${d.vencimento || ''}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>

        <!-- 💰 Bloco: Totais -->
        <h5 class="mt-4">Totais</h5>
        <ul class="list-group">
          <li class="list-group-item"><strong>Valor Total Produtos:</strong> R$ ${totais.valor_total_produtos || '-'}</li>
          <li class="list-group-item"><strong>Valor Total Nota:</strong> R$ ${totais.valor_total_nota || '-'}</li>
          <li class="list-group-item"><strong>Valor Total ICMS:</strong> R$ ${totais.valor_total_icms || '-'}</li>
          <li class="list-group-item"><strong>Valor Total PIS:</strong> R$ ${totais.valor_total_pis || '-'}</li>
          <li class="list-group-item"><strong>Valor Total COFINS:</strong> R$ ${totais.valor_total_cofins || '-'}</li>
          <li class="list-group-item"><strong>Valor Total Descontos:</strong> R$ ${totais.valor_total_desconto || '-'}</li>
        </ul>

        <!-- 📝 Bloco: Informações Adicionais -->
        <h5 class="mt-4">Informações Adicionais</h5>
        <div class="alert alert-secondary">
          ${info_adicional || '-'}
        </div>
      `;

      resultado.innerHTML = html;
    })
    .catch(err => {
      resultado.innerHTML = `
        <div class="alert alert-danger">
          Erro no upload de XML. Tente novamente.<br>
          Detalhes técnicos: ${err.message}
        </div>`;
      console.error("Erro ao enviar XML:", err);
    });
  });
}

// 🔐 Recupera o CSRF token do cookie
function getCSRFToken() {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : "";
}

// 🚀 Inicializa tanto no carregamento normal quanto via AJAX dinâmico
document.addEventListener("ajaxContentLoaded", initImportarXML);
document.addEventListener("DOMContentLoaded", initImportarXML);
