/* jshint esversion: 11 */

(function () {
  "use strict";

  // Utilitários de formatação
  function formatarDataBR(dataISO) {
    if (!dataISO || typeof dataISO !== 'string') return '-';
    try {
      const parts = (dataISO.split('T')[0] || dataISO).split('-');
      return `${parts[2]}/${parts[1]}/${parts[0]}`;
    } catch {
      return '-';
    }
  }

  function formatarNumeroBR(valor) {
    if (!valor) return '0,00';
    return parseFloat(valor).toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  function formatarMoedaBR(valor) {
    if (!valor) return 'R$ 0,00';
    return parseFloat(valor).toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    });
  }

  // Expõe globalmente (para uso no template)
  window.formatarDataBR   = formatarDataBR;
  window.formatarNumeroBR = formatarNumeroBR;
  window.formatarMoedaBR  = formatarMoedaBR;
})();

document.addEventListener("DOMContentLoaded", initImportarXML);
document.addEventListener("ajaxContentLoaded", initImportarXML);

function initImportarXML() {
  const form     = document.getElementById("form-importar-xml");
  const input    = document.getElementById("xml-input");
  const resultado= document.getElementById("resultado-xml");
  if (!form || !input || !resultado) return;

  let dadosImportados = null;

  form.addEventListener("submit", e => {
    e.preventDefault();
    const arquivo = input.files[0];
    if (!arquivo || !arquivo.name.toLowerCase().endsWith(".xml")) {
      mostrarMensagemErro("Por favor, selecione um arquivo XML válido.");
      return;
    }

    const fd = new FormData();
    fd.append("xml", arquivo);
    fd.append("csrfmiddlewaretoken", getCSRFToken());

    fetch("/nota-fiscal/importar/upload/", {
      method: "POST",
      headers: { "X-Requested-With": "XMLHttpRequest" },
      body: fd
    })
    .then(res => res.json())
    .then(data => {
      if (data.erro) {
        mostrarMensagemErro(data.erro);
        return;
      }
      dadosImportados = data;
      montarResultadoNaTela(data);
      mostrarMensagemSucesso("Arquivo XML importado com sucesso!");
    })
    .catch(() => {
      mostrarMensagemErro("Erro inesperado ao importar XML.");
    });
  });

  function montarResultadoNaTela(data) {
    const { nota, fornecedor, produtos, totais, transporte, duplicatas, info_adicional, chave_acesso } = data;

    let html = `
      <div class="mb-3">
        <button id="botao-salvar-importacao" class="btn btn-success me-2">Salvar Importação</button>
        <button id="botao-descartar-importacao" class="btn btn-danger">Descartar</button>
      </div>

      <h5>Nota Fiscal</h5>
      <ul class="list-group mb-4">
        <li class="list-group-item"><strong>Número:</strong> ${nota.numero_nota}</li>
        <li class="list-group-item"><strong>Data Emissão:</strong> ${formatarDataBR(nota.data_emissao)}</li>
        <li class="list-group-item"><strong>Data Saída:</strong> ${formatarDataBR(nota.data_saida)}</li>
        <li class="list-group-item"><strong>Natureza:</strong> ${nota.natureza_operacao}</li>
        <li class="list-group-item"><strong>Chave de Acesso:</strong> ${chave_acesso}</li>
      </ul>

      <h5>Fornecedor</h5>
      <ul class="list-group mb-4">
        <li class="list-group-item"><strong>CNPJ:</strong> ${fornecedor.cnpj}</li>
        <li class="list-group-item"><strong>Razão Social:</strong> ${fornecedor.razao_social}</li>
        <li class="list-group-item"><strong>Nome Fantasia:</strong> ${fornecedor.nome_fantasia}</li>
        <li class="list-group-item"><strong>Endereço:</strong>
            ${fornecedor.logradouro}, ${fornecedor.numero} – ${fornecedor.bairro} –
            ${fornecedor.municipio}/${fornecedor.uf} – CEP ${fornecedor.cep}
        </li>
        <li class="list-group-item"><strong>Telefone:</strong> ${fornecedor.telefone}</li>
      </ul>

      <h5>Produtos</h5>
      <div class="table-responsive mb-4">
        <table class="table table-bordered table-striped table-sm">
          <thead>
            <tr>
              <th>Código</th>
              <th>Nome</th>
              <th>NCM</th>
              <th>CFOP</th>
              <th>Unid.</th>
              <th>Qtd</th>
              <th>Vlr Unit.</th>
              <th>Vlr Total</th>
              <th>ICMS (R$)</th>
              <th>ICMS (%)</th>
              <th>PIS (R$)</th>
              <th>PIS (%)</th>
              <th>COFINS (R$)</th>
              <th>COFINS (%)</th>
            </tr>
          </thead>
          <tbody>
            ${produtos.map(p => `
              <tr>
                <td>${p.codigo}</td>
                <td>${p.nome}</td>
                <td>${p.ncm}</td>
                <td>${p.cfop}</td>
                <td>${p.unidade}</td>
                <td>${formatarNumeroBR(p.quantidade)}</td>
                <td>${formatarMoedaBR(p.valor_unitario)}</td>
                <td>${formatarMoedaBR(p.valor_total)}</td>
                <td>${formatarMoedaBR(p.impostos.icms_valor)}</td>
                <td>${formatarNumeroBR(p.impostos.icms_aliquota)}</td>
                <td>${formatarMoedaBR(p.impostos.pis_valor)}</td>
                <td>${formatarNumeroBR(p.impostos.pis_aliquota)}</td>
                <td>${formatarMoedaBR(p.impostos.cofins_valor)}</td>
                <td>${formatarNumeroBR(p.impostos.cofins_aliquota)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>

      <h5>Totais</h5>
      <ul class="list-group mb-4">
        <li class="list-group-item"><strong>Total Produtos:</strong> ${formatarMoedaBR(totais.valor_total_produtos)}</li>
        <li class="list-group-item"><strong>Total Nota:</strong> ${formatarMoedaBR(totais.valor_total_nota)}</li>
        <li class="list-group-item"><strong>Total ICMS:</strong> ${formatarMoedaBR(totais.valor_total_icms)}</li>
        <li class="list-group-item"><strong>Total PIS:</strong> ${formatarMoedaBR(totais.valor_total_pis)}</li>
        <li class="list-group-item"><strong>Total COFINS:</strong> ${formatarMoedaBR(totais.valor_total_cofins)}</li>
        <li class="list-group-item"><strong>Desconto:</strong> ${formatarMoedaBR(totais.valor_total_desconto)}</li>
      </ul>

      <h5>Transporte</h5>
      <ul class="list-group mb-4">
        <li class="list-group-item"><strong>Frete:</strong> ${transporte.modalidade_frete}</li>
        <li class="list-group-item"><strong>Transportadora:</strong> ${transporte.transportadora_nome} (${transporte.transportadora_cnpj})</li>
        <li class="list-group-item"><strong>Volumes:</strong> ${transporte.quantidade_volumes} x ${transporte.especie_volumes}</li>
        <li class="list-group-item"><strong>Peso Líquido:</strong> ${transporte.peso_liquido}</li>
        <li class="list-group-item"><strong>Peso Bruto:</strong> ${transporte.peso_bruto}</li>
        <li class="list-group-item"><strong>Veículo:</strong> ${transporte.veiculo_placa}/${transporte.veiculo_uf} RNTC ${transporte.veiculo_rntc}</li>
      </ul>

      <h5>Duplicatas</h5>
      <ul class="list-group mb-4">
        ${duplicatas.map(d => `
          <li class="list-group-item">
            <strong>${d.numero}</strong> – Venc: ${formatarDataBR(d.vencimento)} – Valor: ${formatarMoedaBR(d.valor)}
          </li>
        `).join('')}
      </ul>

      <h5>Info Adicional</h5>
      <p>${info_adicional}</p>
    `;

    resultado.innerHTML = html;
    document.getElementById("botao-salvar-importacao")
            .addEventListener("click", salvarImportacaoNoBanco);
    document.getElementById("botao-descartar-importacao")
            .addEventListener("click", descartarImportacao);
  }

  function salvarImportacaoNoBanco() {
    if (!dadosImportados) {
      mostrarMensagemErro("Nenhuma importação para salvar.");
      return;
    }
    fetch("/nota-fiscal/importar/salvar/", {
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
        mostrarMensagemSucesso(data.mensagem || "Dados salvos com sucesso!");
        setTimeout(() => window.location.reload(), 2000);
      } else {
        mostrarMensagemErro(data.erro);
      }
    })
    .catch(() => mostrarMensagemErro("Erro ao salvar importação."));
  }

  function descartarImportacao() {
    if (confirm("Descartar importação?")) {
      document.getElementById("resultado-xml").innerHTML = "";
      dadosImportados = null;
      input.value = "";
      mostrarMensagemSucesso("Importação descartada.");
    }
  }
}

// CSRF helper
function getCSRFToken() {
  const m = document.cookie.match(/csrftoken=([^;]+)/);
  return m ? m[1] : "";
}
