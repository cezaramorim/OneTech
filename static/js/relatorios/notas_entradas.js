// static/js/relatorios/notas_entradas.js

const API_URL = '/relatorios/api/v1/notas-entradas/';

// Função utilitária para pegar o token CSRF do cookie
function getCSRFToken() {
  const m = document.cookie.match(/csrftoken=([^;]+)/);
  return m ? m[1] : '';
}

// Formatar datas para PT-BR
function formatarDataBR(dataString) {
    if (!dataString) return '-';
    const [ano, mes, dia] = dataString.split('-');
    return `${dia}/${mes}/${ano}`;
}

// Formatar valores numéricos para PT-BR
function formatarValorBR(valor) {
    if (valor == null) return '-';
    return parseFloat(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

// Buscar notas da API
async function fetchNotas(filtros = {}) {
  try {
    // Monta a querystring de filtros
    const queryString = new URLSearchParams(filtros).toString();
    const url = queryString ? `${API_URL}?${queryString}` : API_URL;

    const response = await fetch(url, {
      headers: {
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    });

    if (!response.ok) {
      throw new Error('Não foi possível carregar as notas.');
    }

    const data = await response.json();
    const notas = data.results || [];
    renderNotas(notas);

  } catch (error) {
    console.error('Erro ao buscar notas:', error);
    alert('Não foi possível carregar as notas.');
  }
}

// Preencher a tabela com as notas recebidas
function renderNotas(notas) {
  const tbody = document.querySelector('#notas-entradas-table tbody');
  tbody.innerHTML = '';

  notas.forEach(n => {
    const tr = document.createElement('tr');
    tr.dataset.id = n.id;
    tr.innerHTML = `
      <td><input type="checkbox" class="check-linha"></td>
      <td>${n.numero}</td>
      <td>${n.fornecedor}</td>
      <td>${formatarDataBR(n.data_emissao)}</td>
      <td>${formatarDataBR(n.data_saida)}</td>
      <td>${formatarValorBR(n.valor_total)}</td>
      <td>
        <a href="/relatorios/entradas/${n.id}/editar/" class="btn btn-sm btn-outline-primary ajax-link">
          Editar
        </a>
      </td>`;
    tbody.appendChild(tr);
  });
}

// Bindar formulário de filtro para buscar notas
function bindForm() {
  document.getElementById('filtro-notas').addEventListener('submit', e => {
    e.preventDefault();
    const f = e.target;
    const params = {
      fornecedor:  f.fornecedor.value,
      emissao_de:  f.emissao_de.value,
      emissao_ate: f.emissao_ate.value,
      entrada_de:  f.entrada_de.value,
      entrada_ate: f.entrada_ate.value,
      produto:     f.produto.value,
    };
    fetchNotas(params);
  });
}

// Bindar botão de exclusão de notas selecionadas
function bindDeleteButton() {
  document.getElementById('btn-excluir-selecionados')
    .addEventListener('click', async () => {
      const ids = Array.from(document.querySelectorAll('.check-linha:checked'))
        .map(cb => cb.closest('tr').dataset.id);
      if (!ids.length) return alert('Selecione ao menos uma nota.');
      if (!confirm(`Confirma excluir ${ids.length} notas?`)) return;
      try {
        const res = await fetch(API_URL, {
          method: 'DELETE',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
          },
          body: JSON.stringify({ ids })
        });
        if (!res.ok) throw new Error('Erro ao excluir');
        fetchNotas();
      } catch (e) {
        console.error(e);
        alert('Não foi possível excluir as notas.');
      }
    });
}

// Inicializar funcionalidades da página de notas
function initNotasEntradas() {
  if (!document.querySelector('[data-page="notas-entradas"]')) return;
  bindForm();
  bindDeleteButton();
  fetchNotas();
}

// Executa no carregamento completo e após carregamento AJAX parcial
document.addEventListener('DOMContentLoaded', initNotasEntradas);
document.addEventListener('ajaxContentLoaded', initNotasEntradas);
