"""Définition des widgets de l'inventaire"""

from django.forms import CheckboxSelectMultiple


class BulmaGridCheckboxSelectMultiple(CheckboxSelectMultiple):
    """Widget personnalisé pour afficher des checkbox"""

    template_name = "django/forms/widgets/bulma_cell_multiple_input.html"

    def get_context(self, name, value, attrs):
        """Surcharge la méthode pour pouvoir modifier le label du widget (la valeur affichée du formulaire)"""
        contexte = super().get_context(name, value, attrs)
        # la classe de grille
        contexte["widget"]["attrs"]["class"] = "checkboxes"
        for k in range(len(contexte["widget"]["optgroups"])):
            contexte["widget"]["optgroups"][k][1][0][
                "template_name"
            ] = "django/forms/widgets/bulma_checkbox_option.html"
        return contexte


class VillesCheckboxSelectMultiple(BulmaGridCheckboxSelectMultiple):
    """Widget personnalisé pour afficher le choix des villes dans le formulaire"""

    def _modifie_nom_ville(self, nom_ville):
        """Rendre plus lisible les noms des villes"""
        return nom_ville.replace("-", " ").title()

    def get_context(self, name, value, attrs):
        """Surcharge la méthode pour pouvoir modifier le label du widget (la valeur affichée du formulaire)"""
        contexte = super().get_context(name, value, attrs)

        # itère parmi tous les widgets
        for k in range(len(contexte["widget"]["optgroups"])):
            # change le label pour qu'il soit plus lisible
            contexte["widget"]["optgroups"][k][1][0]["label"] = self._modifie_nom_ville(
                contexte["widget"]["optgroups"][k][1][0]["label"]
            )

        return contexte


class QuartierCheckboxSelectMultiple(BulmaGridCheckboxSelectMultiple):
    """Widget personnalisé pour afficher le choix des quartiers dans le formulaire"""

    def _modifie_nom_quartier(self, nom_quartier):
        """Rendre plus lisible les noms des quartiers"""
        return nom_quartier.replace("-", " ").title()

    def get_context(self, name, value, attrs):
        """Surcharge la méthode pour pouvoir modifier le label du widget (la valeur affichée du formulaire)"""
        contexte = super().get_context(name, value, attrs)

        # itère parmi tous les widgets
        for k in range(len(contexte["widget"]["optgroups"])):
            # change le label pour qu'il soit plus lisible
            contexte["widget"]["optgroups"][k][1][0]["label"] = self._modifie_nom_quartier(
                contexte["widget"]["optgroups"][k][1][0]["label"]
            )

        return contexte
