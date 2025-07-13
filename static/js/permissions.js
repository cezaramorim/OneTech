function initPermissionsPage() {
    const permissionGroupToggles = document.querySelectorAll('.permission-group-toggle');

    permissionGroupToggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const parentDiv = this.closest('.mb-4.p-3.border.rounded.bg-white');
            if (parentDiv) {
                const permissionItems = parentDiv.querySelectorAll('.permission-item');
                permissionItems.forEach(item => {
                    item.checked = this.checked;
                });
            }
        });
    });
}