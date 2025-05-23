"use strict";
// ----------------------------------------
// Filtres de localisations de zones d'USID
// ----------------------------------------

// permet d'itérer facilement sur les collections d'éléments HTML
NodeList.prototype[Symbol.iterator] = Array.prototype[Symbol.iterator];
HTMLCollection.prototype[Symbol.iterator] = Array.prototype[Symbol.iterator];

// les constantes
var filtre_zone_usid = document.getElementById("field_localisation_usid");

// cache le filtre de localisation par zone usid si un seul choix possible
if (filtre_zone_usid.children[1].childElementCount == 1) {
    filtre_zone_usid.parentElement.parentElement.parentElement.style.display = "none"
    //filtre_zone_usid.children[1].children[0].firstElementChild.checked = true;
    // pour l'instant il n'y a que l'accordéon des généralités, on désactive cela aussi
    var accordion_generalite = document.getElementById("accordion_generalite");
    accordion_generalite.children[0].children[0].style.display = "none"; // la checkbox
    accordion_generalite.children[0].children[1].style.display = "none"; // la card-header
    accordion_generalite.children[0].children[2].classList.remove("collapsible-item-content"); // la contenu
    accordion_generalite.children[0].classList.remove("collapsible-item");
    accordion_generalite.classList.remove("collapsible-accordion");
};
