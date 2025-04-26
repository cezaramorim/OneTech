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

    // 🔁 Só aqui dentro fazemos o fetch:
    fetch('/nota-fiscal/importar/upload/', {  // ✅ Com TRAÇO (-)
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

      const fornecedor = data.fornecedor || {};
      const produtos = data.produtos || [];

      let html = `
        <h5 class="mt-4">Fornecedor</h5>
        <ul class="list-group mb-3">
          <li class="list-group-item"><strong>CNPJ:</strong> ${fornecedor.cnpj || '-'}</li>
          <li class="list-group-item"><strong>Razão Social:</strong> ${fornecedor.razao_social || '-'}</li>
        </ul>
        <h5>Produtos</h5>
        <div class="table-responsive">
          <table class="table table-bordered table-sm table-striped">
            <thead>
              <tr>
                <th>Código</th><th>Nome</th><th>NCM</th><th>CFOP</th>
              </tr>
            </thead>
            <tbody>
              ${produtos.map(p => `
                <tr>
                  <td>${p.codigo || ''}</td>
                  <td>${p.nome || ''}</td>
                  <td>${p.ncm || ''}</td>
                  <td>${p.cfop || ''}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
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
