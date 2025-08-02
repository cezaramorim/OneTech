function initPermissionsPage() {
    console.log("DEBUG: initPermissionsPage iniciada.");
    const permissionGroupToggles = document.querySelectorAll('.permission-group-toggle');
    console.log("DEBUG: permissionGroupToggles encontradas:", permissionGroupToggles.length);

    // Lógica Pai -> Filho
    permissionGroupToggles.forEach(toggle => {
        console.log("DEBUG: Adicionando listener ao toggle de grupo:", toggle.id);
        toggle.addEventListener('change', function() {
            console.log("DEBUG: Toggle de grupo alterado:", this.id, "Checked:", this.checked);
            const parentDiv = this.closest('[data-permission-group]');
            if (parentDiv) {
                const permissionItems = parentDiv.querySelectorAll('.permission-item');
                console.log("DEBUG: Itens de permissão no grupo:", permissionItems.length);
                permissionItems.forEach(item => {
                    item.checked = this.checked;
                    console.log(`DEBUG: Setando item ${item.id} para checked: ${item.checked}`); // Added debug
                });
            }
        });
    });

    // Lógica Filho -> Pai
    const permissionItems = document.querySelectorAll('.permission-item');
    console.log("DEBUG: permissionItems encontradas:", permissionItems.length);
    permissionItems.forEach(item => {
        console.log("DEBUG: Adicionando listener ao item de permissão:", item.id);
        item.addEventListener('change', function () {
            console.log("DEBUG: Item de permissão alterado:", this.id, "Checked:", this.checked);
            const parentDiv = this.closest('[data-permission-group]');
            if (parentDiv) {
                const groupToggle = parentDiv.querySelector('.permission-group-toggle');
                const allItemsInGroup = parentDiv.querySelectorAll('.permission-item');
                const allCheckedInGroup = parentDiv.querySelectorAll('.permission-item:checked');

                console.log("DEBUG: Grupo Toggle:", groupToggle ? groupToggle.id : "Nenhum");
                console.log("DEBUG: Total de itens no grupo:", allItemsInGroup.length);
                console.log("DEBUG: Itens marcados no grupo:", allCheckedInGroup.length);

                if (groupToggle) {
                    const total = allItemsInGroup.length;
                    const marcados = allCheckedInGroup.length;

                    if (marcados === total && total > 0) {
                        groupToggle.checked = true;
                        groupToggle.indeterminate = false;
                        console.log(`DEBUG: ${groupToggle.id} -> checked = true, indeterminate = false`);
                    } else if (marcados === 0) {
                        groupToggle.checked = false;
                        groupToggle.indeterminate = false;
                        console.log(`DEBUG: ${groupToggle.id} -> checked = false, indeterminate = false`);
                    } else {
                        groupToggle.checked = false;
                        groupToggle.indeterminate = true;
                        console.log(`DEBUG: ${groupToggle.id} -> checked = false, indeterminate = true`);
                    }
                }
            }
        });
    });


    // Inicializar o estado dos toggles de grupo ao carregar a página
    permissionGroupToggles.forEach(toggle => {
        console.log("DEBUG: Inicializando estado do toggle de grupo:", toggle.id);
        const parentDiv = toggle.closest('[data-permission-group]');
        if (parentDiv) {
            const allItemsInGroup = parentDiv.querySelectorAll('.permission-item');
            const allCheckedInGroup = parentDiv.querySelectorAll('.permission-item:checked');
            const total = allItemsInGroup.length;
            const marcados = allCheckedInGroup.length;

            console.log("DEBUG: Inicialização - Total de itens no grupo:", total);
            console.log("DEBUG: Inicialização - Itens marcados no grupo:", marcados);

            if (marcados === total && total > 0) {
                toggle.checked = true;
                toggle.indeterminate = false;
                console.log(`DEBUG: ${toggle.id} -> checked = true, indeterminate = false`);
            } else if (marcados === 0) {
                toggle.checked = false;
                toggle.indeterminate = false;
                console.log(`DEBUG: ${toggle.id} -> checked = false, indeterminate = false`);
            } else {
                toggle.checked = false;
                toggle.indeterminate = true;
                console.log(`DEBUG: ${toggle.id} -> checked = false, indeterminate = true`);
            }
        }
    });

}

//Adicionado
document.addEventListener("ajaxContentLoaded", () => {
  const tela = document.getElementById("identificador-tela")?.dataset?.tela;
  console.log("DEBUG (permissions.js): ajaxContentLoaded recebido - tela:", tela); // ✅ LOG CLARO
  if (tela === "gerenciar_permissoes") {
    console.log("DEBUG (permissions.js): Chamando initPermissionsPage()");
    initPermissionsPage();
  }
});
