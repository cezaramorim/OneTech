// producao/gerenciar_curvas.js

// Função de inicialização para a tela de gerenciamento de curvas
function init_gerenciar_curvas() {
    console.log("DEBUG: init_gerenciar_curvas() chamada."); // Log para depuração

    const listaCurvas = document.getElementById('lista-curvas');
    const detalheCurvaTitulo = document.getElementById('detalhe-curva-titulo');
    const detalheCurvaConteudo = document.getElementById('detalhe-curva-conteudo');

    if (listaCurvas) {
        listaCurvas.addEventListener('click', function(event) {
            const target = event.target.closest('li.list-group-item');
            if (target) {
                const curvaId = target.dataset.curvaId;
                if (curvaId) {
                    // Remove a classe 'active' de todos os itens e adiciona ao clicado
                    document.querySelectorAll('#lista-curvas .list-group-item').forEach(item => {
                        item.classList.remove('active');
                    });
                    target.classList.add('active');

                    carregarDetalhesCurva(curvaId);
                }
            }
        });
    }

    function carregarDetalhesCurva(curvaId) {
        detalheCurvaTitulo.textContent = 'Carregando detalhes...';
        detalheCurvaConteudo.innerHTML = '<p class="text-center">...</p>';

        fetch(`/producao/api/curva/${curvaId}/detalhes/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erro ao carregar detalhes da curva.');
                }
                return response.json();
            })
            .then(data => {
                detalheCurvaTitulo.textContent = `Detalhes da Curva: ${data.curva.nome}`;
                renderizarDetalhesCurva(data.detalhes);
            })
            .catch(error => {
                console.error('Erro:', error);
                detalheCurvaTitulo.textContent = 'Erro ao carregar detalhes';
                detalheCurvaConteudo.innerHTML = `<p class="text-danger">${error.message}</p>`;
            });
    }

    function renderizarDetalhesCurva(detalhes) {
        if (detalhes.length === 0) {
            detalheCurvaConteudo.innerHTML = '<p class="text-muted">Nenhum detalhe encontrado para esta curva.</p>';
            return;
        }

        let html = `
            <table class="table table-striped table-hover table-sm">
                <thead>
                    <tr>
                        <th>Semana</th>
                        <th>Dias</th>
                        <th>Peso Inicial</th>
                        <th>Peso Final</th>
                        <th>Ganho Peso</th>
                        <th>Nº Tratos</th>
                        <th>Hora Início</th>
                        <th>% Arraç. Biomassa</th>
                        <th>% Mortalidade</th>
                        <th>Ração</th>
                        <th>GPD</th>
                        <th>TCA</th>
                    </tr>
                </thead>
                <tbody>
        `;

        detalhes.forEach(detalhe => {
            html += `
                <tr>
                    <td>${detalhe.periodo_semana}</td>
                    <td>${detalhe.periodo_dias}</td>
                    <td>${detalhe.peso_inicial}</td>
                    <td>${detalhe.peso_final}</td>
                    <td>${detalhe.ganho_de_peso}</td>
                    <td>${detalhe.numero_tratos}</td>
                    <td>${detalhe.hora_inicio || ''}</td>
                    <td>${detalhe.arracoamento_biomassa_perc}</td>
                    <td>${detalhe.mortalidade_presumida_perc}</td>
                    <td>${detalhe.racao_nome || ''}</td>
                    <td>${detalhe.gpd}</td>
                    <td>${detalhe.tca}</td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
        `;
        detalheCurvaConteudo.innerHTML = html;
    }
}

// Torna a função globalmente acessível
window.init_gerenciar_curvas = init_gerenciar_curvas;