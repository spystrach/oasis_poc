"use strict";
// ---------------------------------------------------------------
// retire les paramètres GET inutiles des formulaires de recherche
// ---------------------------------------------------------------

var mon_form = document.getElementById("form_recherche_get");
mon_form.addEventListener("submit", function (evt) {
    // pour les input texte
    var tous_texte_input = mon_form.querySelectorAll("input[type=text]");
    for (var i=0; i < tous_texte_input.length; i++) {
        var input = tous_texte_input[i];
        if (input.name && !input.value) {
            input.name = '';
        }
    }
    // pour les input de type select
    var tous_texte_input = mon_form.getElementsByTagName("select");
    for (var i=0; i < tous_texte_input.length; i++) {
        var input = tous_texte_input[i];
        if (input.name && !input.value) {
            input.name = '';
        }
    }
});