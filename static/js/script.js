document.addEventListener('DOMContentLoaded', function () {
    var menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(function (item) {
        item.addEventListener('click', function () {
            var submenu = document.getElementById(item.getAttribute('data-submenu'));
            if (submenu.style.display === 'block') {
                submenu.style.display = 'none';
            } else {
                submenu.style.display = 'block';
            }
        });
    });
});
