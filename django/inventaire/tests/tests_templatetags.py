"""Définition des tests unitaires de l'inventaire pour les fonctions de templates"""

import logging
from datetime import datetime

from django.forms import Form, MultipleChoiceField, CharField, ChoiceField
from django.test import TestCase, tag
from django.test.client import RequestFactory

from inventaire.templatetags.inventaire_extras import (
    lien_pagination,
    get_mailto_contact,
    nom_ville_humain,
    format_date_heure_court,
    format_date_court,
    format_date_long,
    bulma_form_label,
    bulma_form_label_checkbox,
    bulma_menu_actif,
    bulma_message_tag_couleur,
)


logger = logging.getLogger(__name__)


class MockUser:
    """Créer une fausse variable 'user' à ajouter dans une 'request' pour simuler un utilisateur"""

    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])

    def get_full_name(self):
        return "Tchoupi"


class MockContext:
    """Créer une fausse variable 'context' pour l'utiliser dans les filtres et tags"""

    def __init__(self):
        self._rf = RequestFactory()
        self.request = None

    def get(self, url: str, data: dict):
        self.request = self._rf.get(url, data=data)

    # def post(self, url: str, data: dict):
    #    self.request = self._rf.post(url, data=data)


class TestForm(Form):
    """Formulaire pour l'API qui liste tous les quartiers"""

    texte = CharField(label="citrouille")
    choix_uni = ChoiceField(label="carotte", choices=[(1, "petite"), (2, "moyenne"), (3, "grosse")])
    choix_mul = MultipleChoiceField(label="choux", choices=[(1, "petite"), (2, "moyenne"), (3, "grosse")])


@tag("templatetags", "templatetags-tag")
class LienPaginationTest(TestCase):
    """Classe de test de la fonction 'lien_pagination' de type 'tag'"""

    @classmethod
    def setUpTestData(cls):
        cls.context = MockContext()

    def test_lien_pagination_pas_args(self):
        """Teste la fonction dans le cas où la requête n'a pas d'arguments GET"""
        self.context.get("hello", {})
        self.assertEqual(lien_pagination(self.context, 1), "page=1")

    def test_lien_pagination_presence_args(self):
        """Teste la fonction dans le cas où la requête à plusieurs arguments GET"""
        self.context.get("hello", {"coucou": "oui", "haha": 0})
        self.assertEqual(lien_pagination(self.context, 1), "coucou=oui&haha=0&page=1")


@tag("templatetags", "templatetags-tag")
class GetMailtoContactTest(TestCase):
    """Classe de test de la fonction 'get_mailto_contact' de type 'tag'"""

    @classmethod
    def setUpTestData(cls):
        cls.context = MockContext()

    def test_get_mailto_contact_non_connecte(self):
        """Teste la fonction dans le cas où l'utilisateur n'est pas connecté"""
        self.context.get("hello", {})
        self.context.request.user = MockUser(is_authenticated=False)
        self.assertEqual(get_mailto_contact(self.context), "mailto:?subject=Oasis - demande de création de compte")

    def test_get_mailto_contact_connecte(self):
        """Teste la fonction dans le cas où l'utilisateur est connecté"""
        self.context.get("hello", {})
        self.context.request.user = MockUser(is_authenticated=True)
        self.assertEqual(get_mailto_contact(self.context), "mailto:?subject=Oasis - demande de Tchoupi")


@tag("templatetags", "templatetags-filter")
class NomVilleHumainTest(TestCase):
    """Classe de test de la fonction 'nom_ville_humain' de type 'filter'"""

    def test_nom_ville_humain(self):
        """Teste la fonction 'nom_ville_humain'"""
        self.assertEqual(nom_ville_humain("saint-jean-trolimon"), "Saint jean trolimon")


@tag("templatetags", "templatetags-filter")
class FormatDatesTest(TestCase):
    """Classe de test des fonctions de transfert de formats, toutes de type 'filter'"""

    def test_format_date_heure_court(self):
        """Teste la fonction 'format_date_heure_court'"""
        self.assertEqual(
            format_date_heure_court(datetime(day=26, month=4, year=2021, hour=15, minute=35, second=16)),
            "26/04/2021 à 15h35",
        )

    def test_format_date_court(self):
        """Teste la fonction 'format_date_court'"""
        self.assertEqual(format_date_court(datetime(day=26, month=4, year=2021)), "26/04/2021")

    def test_format_date_long(self):
        """Teste la fonction 'format_date_long'"""
        self.assertEqual(format_date_long(datetime(day=26, month=4, year=2021)), "26 avril 2021")


@tag("templatetags", "templatetags-filter")
class BulmaFormLabelTest(TestCase):
    """Classe de test des fonctions d'affichage de label bulma, toutes de type 'filter'"""

    def test_bulma_form_label_sans_arg(self):
        """Teste la fonction 'bulma_form_label' sans argument"""
        form = TestForm()
        boundfield = [k for k in form]
        self.assertEqual(
            bulma_form_label(boundfield[0]),  # le texte
            """<label class="label is-normal" for="id_texte">citrouille\xa0:</label>""",
        )
        self.assertEqual(
            bulma_form_label(boundfield[1]),  # le select
            """<label class="label is-normal" for="id_choix_uni">carotte\xa0:</label>""",
        )
        self.assertEqual(
            bulma_form_label(boundfield[2]),  # le select multiple
            """<label class="label is-normal" for="id_choix_mul">choux\xa0:</label>""",
        )

    def test_bulma_form_label_avec_arg(self):
        """Teste la fonction 'bulma_form_label' avec un argument"""
        form = TestForm()
        boundfield = [k for k in form]
        self.assertEqual(
            bulma_form_label(boundfield[0], "small"),  # le texte
            """<label class="label is-small" for="id_texte">citrouille\xa0:</label>""",
        )
        self.assertEqual(
            bulma_form_label(boundfield[1], "medium"),  # le select
            """<label class="label is-medium" for="id_choix_uni">carotte\xa0:</label>""",
        )
        self.assertEqual(
            bulma_form_label(boundfield[2], "bizarre"),  # le select multiple
            """<label class="label is-bizarre" for="id_choix_mul">choux\xa0:</label>""",
        )

    def test_bulma_form_label_checkbox_sans_arg(self):
        """Teste la fonction 'bulma_form_label_checkbox' sans argument"""
        form = TestForm()
        boundfield = [k for k in form]
        self.assertEqual(
            bulma_form_label_checkbox(boundfield[0]),  # le texte
            """<label class="checkbox label is-display-inline-block is-normal" for="id_texte">citrouille\xa0:</label>""",
        )
        self.assertEqual(
            bulma_form_label_checkbox(boundfield[1]),  # le select
            """<label class="checkbox label is-display-inline-block is-normal" for="id_choix_uni">carotte\xa0:</label>""",
        )
        self.assertEqual(
            bulma_form_label_checkbox(boundfield[2]),  # le select multiple
            """<label class="checkbox label is-display-inline-block is-normal" for="id_choix_mul">choux\xa0:</label>""",
        )

    def test_bulma_form_label_checkbox_avec_arg(self):
        """Teste la fonction 'bulma_form_label_checkbox' avec un argument"""
        form = TestForm()
        boundfield = [k for k in form]
        self.assertEqual(
            bulma_form_label_checkbox(boundfield[0], "small"),  # le texte
            """<label class="checkbox label is-display-inline-block is-small" for="id_texte">citrouille\xa0:</label>""",
        )
        self.assertEqual(
            bulma_form_label_checkbox(boundfield[1], "medium"),  # le select
            """<label class="checkbox label is-display-inline-block is-medium" for="id_choix_uni">carotte\xa0:</label>""",
        )
        self.assertEqual(
            bulma_form_label_checkbox(boundfield[2], "bizarre"),  # le select multiple
            """<label class="checkbox label is-display-inline-block is-bizarre" for="id_choix_mul">choux\xa0:</label>""",
        )


@tag("templatetags", "templatetags-filter")
class BulmaDiversTest(TestCase):
    """Classe de test des fonctions d'affichage bulma diverses, toutes de type 'filter'"""

    def test_bulma_menu_actif_ok(self):
        """Teste la fonction 'bulma_menu_actif' si actif"""
        self.assertEqual(bulma_menu_actif("hello", "hello"), "is-active ")

    def test_bulma_menu_actif_ko(self):
        """Teste la fonction 'bulma_menu_actif' si inactif"""
        self.assertEqual(bulma_menu_actif("hello", "olleh"), "")

    def test_bulma_message_tag_couleur_info(self):
        """Teste la fonction 'bulma_message_tag_couleur' si niveau 'info'"""
        self.assertEqual(bulma_message_tag_couleur("info"), "is-info")

    def test_bulma_message_tag_couleur_success(self):
        """Teste la fonction 'bulma_message_tag_couleur' si niveau 'success'"""
        self.assertEqual(bulma_message_tag_couleur("success"), "is-success")

    def test_bulma_message_tag_couleur_warning(self):
        """Teste la fonction 'bulma_message_tag_couleur' si niveau 'warning'"""
        self.assertEqual(bulma_message_tag_couleur("warning"), "is-warning")

    def test_bulma_message_tag_couleur_error(self):
        """Teste la fonction 'bulma_message_tag_couleur' si niveau 'error'"""
        self.assertEqual(bulma_message_tag_couleur("error"), "is-danger")

    def test_bulma_message_tag_couleur_autre(self):
        """Teste la fonction 'bulma_message_tag_couleur' si niveau inconnu"""
        self.assertEqual(bulma_message_tag_couleur("blabla"), "")
