// 🌐 Variável global usada para armazenar dados importados
let dadosImportados = null;

function initImportarXML() {
  const form = document.getElementById("form-importar-xml");
  const input = document.getElementById("xml-input");
  const resultadoWrapper = document.getElementById("resultado-xml");

  if (!form || !input || !resultadoWrapper) return;

  form.addEventListener("submit", function (e) {
    e.preventDefault();

    const file = input.files[0];
    if (!file) {
      mostrarMensagemErro("Selecione um arquivo XML.");
      return;
    }

    const formData = new FormData();
    formData.append("xml", file);

    fetch("/nota-fiscal/importar/processar/", {
      method: "POST",
      body: formData,
      headers: { "X-CSRFToken": getCSRFToken() }
    })
      .then(res => res.json())
      .then(data => {
        if (data.erro) {
          mostrarMensagemErro(data.erro);
          return;
        }

        dadosImportados = data;
        console.log("📦 Dados Importados:", JSON.stringify(dadosImportados, null, 2));
        exibirDadosImportados(data);
      })
      .catch(() => mostrarMensagemErro("Erro ao processar o XML."));
  });

  function exibirDadosImportados(data) {
    let html = `
      <div class="card mt-3">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="mb-0">Nota Fiscal ${data.nota.numero_nota}</h5>
            <div>
              <button class="btn btn-success btn-sm me-2" onclick="salvarImportacaoNoBanco()">Salvar Importação</button>
              <button class="btn btn-outline-secondary btn-sm" onclick="descartarImportacao()">Descartar</button>
            </div>
          </div>

          <p><strong>Data Emissão:</strong> ${formatarDataBR(data.nota.data_emissao)} &nbsp;&nbsp;
             <strong>Data Saída:</strong> ${formatarDataBR(data.nota.data_saida)}</p>
          <p><strong>Natureza:</strong> ${data.nota.natureza_operacao}</p>
          <p><strong>Chave de Acesso:</strong> ${data.chave_acesso}</p>

          <hr>
          <h6>Fornecedor</h6>
          <p><strong>CNPJ:</strong> ${data.fornecedor.cnpj}</p>
          <p><strong>Razão Social:</strong> ${data.fornecedor.razao_social}</p>
          <p><strong>Nome Fantasia:</strong> ${data.fornecedor.nome_fantasia || "—"}</p>
          <p><strong>Endereço:</strong> ${data.fornecedor.logradouro}, ${data.fornecedor.numero}, ${data.fornecedor.bairro} — ${data.fornecedor.municipio}/${data.fornecedor.uf} — CEP ${data.fornecedor.cep}</p>
          <p><strong>Telefone:</strong> ${data.fornecedor.telefone || "—"}</p>

          <hr>
          <h6>Produtos</h6>
          <div class="table-responsive">
            <table class="table table-sm table-bordered table-striped">
              <thead>
                <tr>
                  <th>Código</th><th>Nome</th><th>NCM</th><th>CFOP</th>
                  <th>Unid.</th><th>Qtd</th><th>Vlr Unit.</th><th>Vlr Total</th>
                  <th>ICMS (R$)</th><th>PIS (R$)</th><th>COFINS (R$)</th>
                </tr>
              </thead>
              <tbody>
                ${data.produtos.map(p => `
                  <tr>
                    <td>${p.codigo}</td>
                    <td>${p.nome}</td>
                    <td>${p.ncm}</td>
                    <td>${p.cfop}</td>
                    <td>${p.unidade}</td>
                    <td>${p.quantidade}</td>
                    <td>${formatarMoedaBR(p.valor_unitario)}</td>
                    <td>${formatarMoedaBR(p.valor_total)}</td>
                    <td>${formatarMoedaBR(p.impostos.icms_valor)}</td>
                    <td>${formatarMoedaBR(p.impostos.pis_valor)}</td>
                    <td>${formatarMoedaBR(p.impostos.cofins_valor)}</td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </div>

          <hr>
          <h6>Totais</h6>
          <p><strong>Total Produtos:</strong> ${formatarMoedaBR(data.totais.valor_total_produtos)}<br>
             <strong>Total Nota:</strong> ${formatarMoedaBR(data.totais.valor_total_nota)}<br>
             <strong>ICMS:</strong> ${formatarMoedaBR(data.totais.valor_total_icms)} |
             <strong>PIS:</strong> ${formatarMoedaBR(data.totais.valor_total_pis)} |
             <strong>COFINS:</strong> ${formatarMoedaBR(data.totais.valor_total_cofins)} |
             <strong>Descontos:</strong> ${formatarMoedaBR(data.totais.valor_total_desconto)}</p>

          <hr>
          <h6>Duplicatas</h6>
          <ul>
            ${data.duplicatas.map(d => `
              <li>Nº ${d.numero} - ${formatarMoedaBR(d.valor)} - Vencimento: ${formatarDataBR(d.vencimento)}</li>
            `).join("")}
          </ul>

          <hr>
          <h6>Transporte</h6>
          <p><strong>Transportadora:</strong> ${data.transporte.transportadora_nome || "—"}<br>
             <strong>CNPJ:</strong> ${data.transporte.transportadora_cnpj || "—"}<br>
             <strong>Placa:</strong> ${data.transporte.veiculo_placa || "—"} (${data.transporte.veiculo_uf || "--"})<br>
             <strong>Frete:</strong> ${data.transporte.modalidade_frete || "—"}, RNTC: ${data.transporte.veiculo_rntc || "—"}<br>
             <strong>Volumes:</strong> ${data.transporte.quantidade_volumes || 0} × ${data.transporte.especie_volumes || "—"}<br>
             <strong>Peso Líquido:</strong> ${formatarMoedaBR(data.transporte.peso_liquido)} |
             <strong>Peso Bruto:</strong> ${formatarMoedaBR(data.transporte.peso_bruto)}</p>

          <hr>
          <h6>Informações Adicionais</h6>
          <p>${data.info_adicional || "—"}</p>
        </div>
      </div>
    `;
    resultadoWrapper.innerHTML = html;
  }
}

// ✅ Salvar no banco
function salvarImportacaoNoBanco() {
  if (!dadosImportados) {
    mostrarMensagemErro("Nenhuma importação para salvar.");
    return;
  }

  console.log("🔁 Enviando para /nota-fiscal/importar/salvar/");
  console.log("📦 Dados:", JSON.stringify(dadosImportados, null, 2));

  fetch('/nota-fiscal/importar/salvar/', {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCSRFToken()
    },
    body: JSON.stringify(dadosImportados)
  })
    .then(async res => {
      const data = await res.json();
      if (res.ok) {
        mostrarMensagemSucesso(data.mensagem || "Importação salva com sucesso!");
        setTimeout(() => window.location.reload(), 2000);
      } else {
        mostrarMensagemErro(data.erro);
      }
    })
    .catch(() => mostrarMensagemErro("Erro ao salvar importação."));
}

// ✅ Descartar importação
function descartarImportacao() {
  if (confirm("Descartar importação?")) {
    document.getElementById("resultado-xml").innerHTML = "";
    dadosImportados = null;
    document.getElementById("xml-input").value = "";
    mostrarMensagemSucesso("Importação descartada.");
  }
}

// 🔐 CSRF token
function getCSRFToken() {
  const m = document.cookie.match(/csrftoken=([^;]+)/);
  return m ? m[1] : "";
}

// ✅ Inicializar quando carregar a página
document.addEventListener("DOMContentLoaded", initImportarXML);

// 🧩 Formatadores auxiliares
function formatarMoedaBR(valor) {
  if (!valor || valor === "0") return "R$ 0,00";
  return parseFloat(valor).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL"
  });
}

function formatarDataBR(data) {
  if (!data) return "—";
  const [ano, mes, dia] = data.split("-");
  return `${dia}/${mes}/${ano}`;
}
