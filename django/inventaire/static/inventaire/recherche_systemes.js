"use strict";
// permet d'itérer facilement sur les collections d'éléments HTML
NodeList.prototype[Symbol.iterator] = Array.prototype[Symbol.iterator];
HTMLCollection.prototype[Symbol.iterator] = Array.prototype[Symbol.iterator];

// --------------------------------------------------------------
// Filtres de localisations de villes et de quartiers interactifs
// --------------------------------------------------------------

// les constantes
var filtre_zone_usid = document.getElementById("field_localisation_usid");
var filtre_zone_ville = document.getElementById("field_localisation_ville");
var filtre_zone_quartier = document.getElementById("field_localisation_quartier");

// cache le filtre de localisation par zone usid si un seul choix possible
if (filtre_zone_usid.children[1].childElementCount == 1) {
    filtre_zone_usid.style.display = "none";
    filtre_zone_usid.children[1].children[0].firstElementChild.checked = true;
};

function refresh_liste_ville() {
    // récupère toutes les zones d'USID cochées
    var data = new URLSearchParams();
    for (var elt of filtre_zone_usid.children[1].children) {
        if (elt.firstElementChild.checked) {
            data.append("usid", elt.firstElementChild.value)
        }
    }
    // envoie une requête AJAX au serveur pour obtenir les villes correspondantes
    const request = new Request("/api/villes?" + data, {method: "GET"});
    fetch(request)
        .then(response => response.json())
        .then(result => {
            filtre_zone_ville.style.display = "";
            // affiche seulement les bonnes villes
            for (var elt of filtre_zone_ville.children[1].children) {
               if (result['villes'].includes(elt.firstElementChild.value)) {
                   elt.style.display = "";
               } else {
                   // utilise un évènement 'click' car changer la valeur de checked ne fonctionnait pas
                   // l'évènement va automatiquement actionner la fonction refresh_list_quartier
                   if (elt.firstElementChild.checked) {
                       elt.firstElementChild.click();
                   }
                   elt.style.display = "none";
               }
            }
            // si aucune ville n'est à afficher, cache en plus toute la section
            if (!result["villes"].length) {
                filtre_zone_ville.style.display = "none";
            }
        })
}
function refresh_liste_quartier() {
    // récupère toutes les villes cochées
    var data = new URLSearchParams();
    for (var elt of filtre_zone_ville.children[1].children) {
        if (elt.firstElementChild.checked) {
            data.append("ville", elt.firstElementChild.value)
        }
    }
    // envoie une requête AJAX au serveur pour obtenir les villes correspondantes
    const request = new Request("/api/quartiers?" + data, {method: "GET"});
    fetch(request)
        .then(response => response.json())
        .then(result => {
            filtre_zone_quartier.style.display = "";
            // sinon, affiche seulement les bons quartier
            for (var elt of filtre_zone_quartier.children[1].children) {
               if (result['quartiers'].includes(elt.firstElementChild.value)) {
                   elt.style.display = "";
               } else {
                   elt.style.display = "none";
                   elt.firstElementChild.checked = false;
               }
            }
            // si aucune ville n'est à afficher, cache en plus toute la section
            if (!result["quartiers"].length) {
                filtre_zone_quartier.style.display = "none";
            }
        })
}

// applique les fonction sur toutes les checkbox des zones d'USID et des zones de villes
for (var elt of filtre_zone_usid.children[1].children) {
    elt.firstElementChild.addEventListener("click", event => {
        refresh_liste_ville();
    })
}
for (var elt of filtre_zone_ville.children[1].children) {
    elt.firstElementChild.addEventListener("click", event => {
        refresh_liste_quartier();
    })
}

// applique la fonction après le chargement de la page (car des éléments peuvent être déjà cochés)
refresh_liste_ville();
refresh_liste_quartier();
