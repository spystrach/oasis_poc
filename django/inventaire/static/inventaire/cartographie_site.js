"use strict";
// permet d'itérer facilement sur les collections d'éléments HTML
NodeList.prototype[Symbol.iterator] = Array.prototype[Symbol.iterator];
HTMLCollection.prototype[Symbol.iterator] = Array.prototype[Symbol.iterator];

// ------------------------------------------------------------------------
// SelectBox de localisations interactives (USID, ville, quartier et zones)
// ------------------------------------------------------------------------

// les constantes
const hidden_page_vide = document.getElementById("id_page_vide");
var select_usid = document.getElementById("id_usid");
var select_ville = document.getElementById("id_ville");
var select_quartier = document.getElementById("id_quartier");

// rend les select obligatoires
select_usid.required = true;
select_ville.required = true;
select_quartier.required = true;

function refresh_liste_ville(init=false) {
    // récupère la valeur de la zone d'USID sélectionnée
    var data = new URLSearchParams([["usid", select_usid.value]]);
    // envoie une requête AJAX au serveur pour obtenir les villes correspondantes
    const request = new Request("/api/villes?" + data, {method: "GET"});
    fetch(request)
        .then(response => response.json())
        .then(result => {
            // change les valeurs du select des villes avec les résultats renvoyés
            for (var option of select_ville.options) {
                if (result['villes'].includes(option.value)) {
                    option.style.display = "";
                } else {
                    // réinitialise le select des quartiers et des zones
                    option.style.display = "none";
                }
            }
            // réinitialise le select de ville en cours, si sa valeur n'est plus possible
            if (!result['villes'].includes(select_ville.value)) {
                select_ville.value = "";
            }
            // réinitialise le select des quartiers (car dépendant de la valeur du select des villes)
            if (!init) {
                select_quartier.value = "";
            }
        })
}
function refresh_liste_quartier(init=false) {
    // récupère le valeur de la ville sélectionnée
    var data = new URLSearchParams([["ville", select_ville.value]]);
    // envoie une requête AJAX au serveur pour obtenir les quartiers correspondants
    const request = new Request("/api/quartiers?" + data, {method: "GET"});
    fetch(request)
        .then(response => response.json())
        .then(result => {
            // change les valeurs du select des quartiers avec les résultats renvoyés
            for (var elt of select_quartier.options) {
                if (result['quartiers'].includes(elt.value)) {
                    elt.style.display = "";
                } else {
                    elt.style.display = "none";
                }
            }
            // réinitialise le select des quartiers en cours, si sa valeur n'est plus possible
            if (!result['quartiers'].includes(select_quartier.value)) {
                select_quartier.value = "";
            }
        })
}

// applique les fonction sur les selects des zones USID et des villes
select_usid.addEventListener("change", event => {
    refresh_liste_ville();
})
select_ville.addEventListener("change", event => {
    refresh_liste_quartier();
})

if (hidden_page_vide.value == "True") {
    select_usid.value = "";
    select_ville.value = "";
    select_quartier.value = "";
} else {
    refresh_liste_quartier(true);
    refresh_liste_ville(true);
}

// pré-sélectionne l'USID si un seul choix possible
if (select_usid.childElementCount == 1) {
    select_usid.value = select_usid.children[0].value;
};
