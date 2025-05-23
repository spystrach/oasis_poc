"use strict";
// permet d'itérer facilement sur les collections d'éléments HTML
NodeList.prototype[Symbol.iterator] = Array.prototype[Symbol.iterator];
HTMLCollection.prototype[Symbol.iterator] = Array.prototype[Symbol.iterator];

// ------------------------------------------------------------------------
// SelectBox de localisations interactives (USID, ville, quartier et zones)
// ------------------------------------------------------------------------

// les constantes
var select_usid = document.getElementById("id_z_usid");
var select_ville = document.getElementById("id_z_ville");
var select_quartier = document.getElementById("id_z_quartier");
var select_zone = document.getElementById("id_z_zone");

// rend les select obligatoires
select_usid.required = true;
select_ville.required = true;
select_quartier.required = true;
select_zone.required = true;

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
            // réinitialise le select des quartiers et des zones (car dépendant de la valeur du select des villes)
            if (!init) {
                select_quartier.value = "";
                select_zone.value = "";
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
            // réinitialise le select des zones (car dépendant de la valeur du select des quartiers)
            if (!init) {
                select_zone.value = "";
            }
        })
}
function refresh_liste_zone() {
    // récupère le valeur du quartier sélectionnée
    var data = new URLSearchParams([["quartier", select_quartier.value]]);
    // envoie une requête AJAX au serveur pour obtenir les quartiers correspondants
    const request = new Request("/api/zones?" + data, {method: "GET"});
    fetch(request)
        .then(response => response.json())
        .then(result => {
            // les zones étant facultatives, la réponse api peut être une liste d'un élément vide
            if ("zones" in result && result["zones"].length == 1 && result["zones"][0] == "" ) {
                select_zone.removeAttribute("required");
            } else {
                select_zone.required = true;
            }
            // change les valeurs du select des quartiers avec les résultats renvoyés
            for (var elt of select_zone.options) {
                if (result['zones'].includes(elt.value)) {
                    elt.style.display = "";
                } else {
                    elt.style.display = "none";
                }
            }
            // réinitialise le select de zone en cours, si sa valeur n'est plus possible
            if (!result['zones'].includes(select_zone.value)) {
                select_zone.value = "";
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
select_quartier.addEventListener("change", event => {
    refresh_liste_zone();
})

// applique la fonction au chargement de la page
if (mode == "modification") {
    refresh_liste_zone();
    refresh_liste_quartier(true);
    refresh_liste_ville(true);
} else {
    select_usid.value = "";
    select_ville.value = "";
    select_quartier.value = "";
    select_zone.value = "";
}

// --------------------------------------------------------
// MultipleSelectBox interactive pour les fonctions métiers
// --------------------------------------------------------

// les constantes
var select_domaine = document.getElementById("id_domaine_metier");
var select_fonctions = document.getElementById("id_fonctions_metiers");

function refresh_liste_fonctions_metier() {
    // récupère le valeur du domaine métier sélectionnée
    var data = new URLSearchParams([["domaine", select_domaine.value]]);
    // envoie une requête AJAX au serveur pour obtenir les quartiers correspondants
    const request = new Request("/api/fonctions?" + data, {method: "GET"});
    fetch(request)
        .then(response => response.json())
        .then(result => {
            // change les valeurs du select des fonctions métiers avec les résultats renvoyés
            for (var elt of select_fonctions.options) {
                if (result['fonctions'].includes(Number(elt.value))) {
                    elt.style.display = "";
                } else {
                    elt.style.display = "none";
                }
            }
        })
}

// applique les fonction sur le select du domaine métier
select_domaine.addEventListener("change", event => {
    refresh_liste_fonctions_metier();
})

// applique la fonction au chargement de la page
if (mode == "modification") {
    refresh_liste_fonctions_metier();
} else {
    for (var elt of select_fonctions.options) {
        elt.style.display = "none";
    }
}
