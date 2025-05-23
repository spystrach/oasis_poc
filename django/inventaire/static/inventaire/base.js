"use strict";

// constantes
var menu = document.getElementById("id_menu");
var mobile_toggle_aside = document.getElementById("id_mobile_toggle_aside");
var mobile_toggle_navbar = document.getElementById("id_mobile_toggle_navbar");
var theme_toggle = document.getElementById("id_theme_toggle");

// Activation des sous-menus dans le aside (barre latérale gauche)
for (var elt of menu.getElementsByClassName("has-dropdown-icon")) {
    elt.addEventListener("click", function(elt) {
        var t = elt.currentTarget.getElementsByClassName("dropdown-icon")[0].getElementsByClassName("fa-solid")[0];
        elt.currentTarget.parentNode.classList.toggle("is-active"), t.classList.toggle("fa-plus"), t.classList.toggle("fa-minus")
    })
};

// Activation de la barre latérale droite (aside) en mode mobile
mobile_toggle_aside.addEventListener("click", event => {
    document.documentElement.classList.toggle("has-aside-mobile-expanded")
});

// activation du menu du haut (navbar) en mode mobile
mobile_toggle_navbar.addEventListener("click", function(elt) {
    var t = elt.currentTarget.getElementsByClassName("icon")[0].getElementsByClassName("fa-solid")[0];
    document.getElementById("navbar-menu").classList.toggle("is-active"), t.classList.toggle("fa-ellipsis-vertical"), t.classList.toggle("fa-xmark")
});

// Fonction permettant de cacher les notifications (bulma message)
function cache_notif(elt) {
  elt.parentElement.style.display="none"
};

// Bascule theme clair et sombre
theme_toggle.addEventListener("click", event => {
    var theme = document.getElementById("html").attributes["data-theme"];
    if (theme.value == "light") { // theme clair activé, on passe au foncé
      localStorage.setItem("theme", "dark")
    } else if (theme.value == "dark") { // theme foncé activé, on passe au clair
     localStorage.setItem("theme", "light")
    } else { // detection du theme automatique pour l'inverser
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
          localStorage.setItem("theme", "light")
        } else {
          localStorage.setItem("theme", "dark")
        }
    }
    theme.value = localStorage.getItem("theme")
})

