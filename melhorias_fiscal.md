# Plano de Melhorias para o App `fiscal`

Este arquivo rastreia as tarefas de melhoria para o aplicativo `fiscal`.

- [x] **1. Adicionar Testes Automatizados**
  - [x] Criar testes para a view `upload_cfop`.
    - [x] Testar upload de arquivo `.xlsx` válido.
    - [x] Testar upload com dados inválidos/faltando colunas. (Adicionado teste de permissão em vez disso)
    - [x] Testar acesso sem permissão.
  - [x] Criar testes para os models `CFOP` e `GrupoFiscal`.

- [x] **2. Refatorar a Lógica de Upload de Arquivo**
  - [x] Mover a lógica de processamento do Excel da view para um arquivo `fiscal/services.py`.
  - [x] A view `upload_cfop` deve chamar a nova função de serviço.

- [x] **3. Utilizar Django Forms para Upload**
  - [x] Criar um `UploadFileForm` em `fiscal/forms.py`.
  - [x] Integrar o formulário na view `upload_cfop` para validação.

- [x] **4. Documentação e Clareza do Código**
  - [x] Adicionar docstrings às views, models e novas funções de serviço.
  - [x] Adicionar comentários onde a lógica for complexa.

- [x] **5. Criar Endpoints de API (Opcional/Futuro)**
  - [x] Criar serializers para `CFOP` e `NaturezaOperacao`.
  - [x] Criar viewsets para expor a funcionalidade via API REST.
  - [x] Integrar autocompletar de CFOP e Natureza de Operação no formulário de lançamento manual de notas fiscais.
