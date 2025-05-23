"""Définition des tests unitaires de l'inventaire pour les vues de l'API"""

import logging

from django.contrib.auth.models import User, Permission
from django.test import TestCase, tag
from django.urls import reverse
from django.utils.encoding import force_str

from inventaire.models import (
    DomaineMetier,
    FonctionsMetier,
    Localisation,
    ZoneUsid,
)


logger = logging.getLogger(__name__)


@tag("views", "views-api", "views-api-villes")
class ApiVillesViewTest(TestCase):
    """Classe de test de la vue d'api de liste des villes"""

    @classmethod
    def setUpTestData(cls):
        # utilisateur pouvant consulter la zone AMS
        cls.user_ams = User.objects.create_user(
            username="ams",
            password="ams123",
        )
        cls.user_ams.user_permissions.add(Permission.objects.get(codename="consult_AMS"))
        # utilisateur pouvant consulter plusieurs zones
        cls.user_ams_rvc = User.objects.create_user(
            username="ams-rvc",
            password="ams-rvc123",
        )
        cls.user_ams_rvc.user_permissions.add(Permission.objects.get(codename="consult_AMS"))
        cls.user_ams_rvc.user_permissions.add(Permission.objects.get(codename="consult_RVC"))

        # une localisation pour AMS
        Localisation.objects.create(
            pk=1,
            zone_usid=ZoneUsid.AMS,
            nom_ville="Angers",
            nom_quartier="Roseraie",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        # une localisation pour RVC
        Localisation.objects.create(
            pk=2,
            zone_usid=ZoneUsid.RVC,
            nom_ville="Rennes",
            nom_quartier="Maurepas",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        Localisation.objects.create(
            pk=3,
            zone_usid=ZoneUsid.CBG,
            nom_ville="Cherbourg",
            nom_quartier="Fourches-Charcot",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )

    def tearDown(self) -> None:
        self.client.logout()

    def test_api_anonyme(self):
        """Un utilisateur non connecté sera redirigé vers la page de login"""
        response = self.client.get(reverse("inventaire:api_villes"))
        url_attendu = reverse("inventaire:login") + "?next=" + reverse("inventaire:api_villes")
        self.assertRedirects(response, url_attendu)

    def test_api_droits_ams_vide(self):
        """Un utilisateur ayant les droits de consultation 'ams' ne verra rien s'il ne demande rien"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:api_villes"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"villes": []},
        )

    def test_api_droits_ams_raisonnable(self):
        """Un utilisateur ayant les droits de consultation 'ams' ne verra que ses systèmes"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:api_villes") + "?usid=AMS")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"villes": ["Angers"]},
        )

    def test_api_droits_ams_trop(self):
        """Un utilisateur ayant les droits de consultation 'ams' ne verra rien s'il le demande"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:api_villes") + "?usid=AMS&usid=RVC")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"villes": ["Angers"]},
        )

    def test_api_droits_ams_rvc_vide(self):
        """Un utilisateur ayant les droits de consultation 'ams' et 'rvc' ne verra rien s'il ne demande rien"""
        self.client.force_login(self.user_ams_rvc)
        response = self.client.get(reverse("inventaire:api_villes"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"villes": []},
        )

    def test_api_droits_ams_rvc_raisonnable(self):
        """Un utilisateur ayant les droits de consultation 'ams' et 'rvc' ne verra que ses systèmes"""
        self.client.force_login(self.user_ams_rvc)
        response = self.client.get(reverse("inventaire:api_villes") + "?usid=AMS&usid=RVC")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"villes": ["Angers", "Rennes"]},
        )

    def test_api_droits_ams_rvc_trop(self):
        """Un utilisateur ayant les droits de consultation 'ams' et 'rvc' ne verra rien de plus même s'il le demande"""
        self.client.force_login(self.user_ams_rvc)
        response = self.client.get(reverse("inventaire:api_villes") + "?usid=AMS&usid=RVC&usid=CBG")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"villes": ["Angers", "Rennes"]},
        )


@tag("views", "views-api", "views-api-quartiers")
class ApiQuartiersViewTest(TestCase):
    """Classe de test de la vue d'api de liste des quartiers"""

    @classmethod
    def setUpTestData(cls):
        # utilisateur pouvant consulter la zone AMS
        cls.user_ams = User.objects.create_user(
            username="ams",
            password="ams123",
        )
        cls.user_ams.user_permissions.add(Permission.objects.get(codename="consult_AMS"))
        # utilisateur pouvant consulter plusieurs zones
        cls.user_ams_rvc = User.objects.create_user(
            username="ams-rvc",
            password="ams-rvc123",
        )
        cls.user_ams_rvc.user_permissions.add(Permission.objects.get(codename="consult_AMS"))
        cls.user_ams_rvc.user_permissions.add(Permission.objects.get(codename="consult_RVC"))

        # une localisation pour AMS
        Localisation.objects.create(
            pk=1,
            zone_usid=ZoneUsid.AMS,
            nom_ville="Angers",
            nom_quartier="Roseraie",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        # une localisation pour RVC
        Localisation.objects.create(
            pk=2,
            zone_usid=ZoneUsid.RVC,
            nom_ville="Rennes",
            nom_quartier="Maurepas",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        Localisation.objects.create(
            pk=3,
            zone_usid=ZoneUsid.CBG,
            nom_ville="Cherbourg",
            nom_quartier="Fourches-Charcot",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )

    def tearDown(self) -> None:
        self.client.logout()

    def test_api_anonyme(self):
        """Un utilisateur non connecté sera redirigé vers la page de login"""
        response = self.client.get(reverse("inventaire:api_quartiers"))
        url_attendu = reverse("inventaire:login") + "?next=" + reverse("inventaire:api_quartiers")
        self.assertRedirects(response, url_attendu)

    def test_api_droits_ams_vide(self):
        """Un utilisateur ayant les droits de consultation 'ams' ne verra rien s'il ne demande rien"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:api_quartiers"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"quartiers": []},
        )

    def test_api_droits_ams_raisonnable(self):
        """Un utilisateur ayant les droits de consultation 'ams' ne verra que ses systèmes"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:api_quartiers") + "?ville=Angers")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"quartiers": ["Roseraie"]},
        )

    def test_api_droits_ams_trop(self):
        """Un utilisateur ayant les droits de consultation 'ams' ne verra rien de plus même s'il le demande"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:api_quartiers") + "?ville=Angers&ville=Rennes")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"quartiers": ["Roseraie"]},
        )

    def test_api_droits_ams_rvc_vide(self):
        """Un utilisateur ayant les droits de consultation 'ams' et 'rvc' ne verra que ses systèmes"""
        self.client.force_login(self.user_ams_rvc)
        response = self.client.get(reverse("inventaire:api_quartiers"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"quartiers": []},
        )

    def test_api_droits_ams_rvc_raisonnable(self):
        """Un utilisateur ayant les droits de consultation 'ams' et 'rvc' ne verra que ses systèmes"""
        self.client.force_login(self.user_ams_rvc)
        response = self.client.get(reverse("inventaire:api_quartiers") + "?ville=Angers&ville=Rennes")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"quartiers": ["Roseraie", "Maurepas"]},
        )

    def test_api_droits_ams_rvc_trop(self):
        """Un utilisateur ayant les droits de consultation 'ams' et 'rvc' ne verra rien de plus même s'il le demande"""
        self.client.force_login(self.user_ams_rvc)
        response = self.client.get(reverse("inventaire:api_quartiers") + "?ville=Angers&ville=Rennes&ville=Cherbourg")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"quartiers": ["Roseraie", "Maurepas"]},
        )


@tag("views", "views-api", "views-api-zones")
class ApiZonesViewTest(TestCase):
    """Classe de test de la vue d'api de liste des zones d'un quartier"""

    @classmethod
    def setUpTestData(cls):
        # utilisateur pouvant consulter la zone AMS
        cls.user_ams = User.objects.create_user(
            username="ams",
            password="ams123",
        )
        cls.user_ams.user_permissions.add(Permission.objects.get(codename="consult_AMS"))
        # utilisateur pouvant consulter plusieurs zones
        cls.user_ams_rvc = User.objects.create_user(
            username="ams-rvc",
            password="ams-rvc123",
        )
        cls.user_ams_rvc.user_permissions.add(Permission.objects.get(codename="consult_AMS"))
        cls.user_ams_rvc.user_permissions.add(Permission.objects.get(codename="consult_RVC"))

        # deux localisations pour AMS
        Localisation.objects.create(
            pk=1,
            zone_usid=ZoneUsid.AMS,
            nom_ville="Angers",
            nom_quartier="Roseraie",
            zone_quartier="Ouest",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        Localisation.objects.create(
            pk=2,
            zone_usid=ZoneUsid.AMS,
            nom_ville="Angers",
            nom_quartier="Roseraie",
            zone_quartier="Est",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        # deux localisations pour RVC
        Localisation.objects.create(
            pk=3,
            zone_usid=ZoneUsid.RVC,
            nom_ville="Rennes",
            nom_quartier="Maurepas",
            zone_quartier="Nord",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        Localisation.objects.create(
            pk=4,
            zone_usid=ZoneUsid.RVC,
            nom_ville="Rennes",
            nom_quartier="Maurepas",
            zone_quartier="Sud",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        # une localisation pour CBG
        Localisation.objects.create(
            pk=5,
            zone_usid=ZoneUsid.CBG,
            nom_ville="Cherbourg",
            nom_quartier="Fourches-Charcot",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )

    def tearDown(self) -> None:
        self.client.logout()

    def test_api_anonyme(self):
        """Un utilisateur non connecté sera redirigé vers la page de login"""
        response = self.client.get(reverse("inventaire:api_zones"))
        url_attendu = reverse("inventaire:login") + "?next=" + reverse("inventaire:api_zones")
        self.assertRedirects(response, url_attendu)

    def test_api_droits_ams_vide(self):
        """Un utilisateur ayant les droits de consultation 'ams' ne verra rien s'il ne demande rien"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:api_zones"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"zones": []},
        )

    def test_api_droits_ams_raisonnable(self):
        """Un utilisateur ayant les droits de consultation 'ams' ne verra que ses systèmes"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:api_zones") + "?quartier=Roseraie")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"zones": ["Est", "Ouest"]},
        )

    def test_api_droits_ams_trop(self):
        """Un utilisateur ayant les droits de consultation 'ams' ne verra rien de plus même s'il le demande"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:api_zones") + "?quartier=Roseraie&quartier=Maurepas")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"zones": ["Est", "Ouest"]},
        )

    def test_api_droits_ams_rvc_vide(self):
        """Un utilisateur ayant les droits de consultation 'ams' et 'rvc' ne verra que ses systèmes"""
        self.client.force_login(self.user_ams_rvc)
        response = self.client.get(reverse("inventaire:api_zones"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"zones": []},
        )

    def test_api_droits_ams_rvc_raisonnable(self):
        """Un utilisateur ayant les droits de consultation 'ams' et 'rvc' ne verra que ses systèmes"""
        self.client.force_login(self.user_ams_rvc)
        response = self.client.get(reverse("inventaire:api_zones") + "?quartier=Roseraie&quartier=Maurepas")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"zones": ["Est", "Ouest", "Nord", "Sud"]},
        )

    def test_api_droits_ams_rvc_trop(self):
        """Un utilisateur ayant les droits de consultation 'ams' et 'rvc' ne verra rien de plus même s'il le demande"""
        self.client.force_login(self.user_ams_rvc)
        response = self.client.get(
            reverse("inventaire:api_zones") + "?quartier=Roseraie&quartier=Maurepas&quartier=Fourches-Charcot"
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"zones": ["Est", "Ouest", "Nord", "Sud"]},
        )


@tag("views", "views-api", "views-api-fonctions")
class ApiFonctionsMetierViewTest(TestCase):
    """Classe de test de la vue d'api de liste des fonctions métiers associées à un domaine métier"""

    @classmethod
    def setUpTestData(cls):
        # un utilisateur
        cls.user = User.objects.create_user(
            username="pipoudou",
            password="uoduopip",
        )
        # un domaine métier et ses fonctions
        DomaineMetier.objects.create(
            pk=1,
            nom="énergie électrique",
            code="EE",
        )
        FonctionsMetier.objects.create(
            pk=1,
            domaine=DomaineMetier.objects.get(pk=1),
            nom="production d'énergie électrique",
            code="CEE",
        )
        FonctionsMetier.objects.create(
            pk=2,
            domaine=DomaineMetier.objects.get(pk=1),
            nom="conversion d'énergie électrique",
            code="CEE",
        )
        # un autre domaine métier et ses fonctions
        DomaineMetier.objects.create(
            pk=2,
            nom="protection de site",
            code="PS",
        )
        FonctionsMetier.objects.create(
            pk=3,
            domaine=DomaineMetier.objects.get(pk=2),
            nom="contrôle d'accès",
            code="CA",
        )
        FonctionsMetier.objects.create(
            pk=4,
            domaine=DomaineMetier.objects.get(pk=2),
            nom="détection d'intrusion",
            code="DI",
        )
        FonctionsMetier.objects.create(
            pk=5,
            domaine=DomaineMetier.objects.get(pk=2),
            nom="vidéo-surveillance",
            code="VS",
        )

    def tearDown(self) -> None:
        self.client.logout()

    def test_api_anonyme(self):
        """Un utilisateur non connecté sera redirigé vers la page de login"""
        response = self.client.get(reverse("inventaire:api_fonctions"))
        url_attendu = reverse("inventaire:login") + "?next=" + reverse("inventaire:api_fonctions")
        self.assertRedirects(response, url_attendu)

    def test_api_connecte_vide(self):
        """Un utilisateur connecté ne verra rien s'il ne demande rien"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("inventaire:api_fonctions"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"fonctions": []},
        )

    def test_api_connecte_raisonnable_1(self):
        """Un utilisateur connecté verra que les fonctions métiers associées au domaine métier demandé (1/2)"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("inventaire:api_fonctions") + "?domaine=1")  # EE
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"fonctions": [1, 2]},  # PEE et CEE
        )

    def test_api_connecte_raisonnable_2(self):
        """Un utilisateur connecté verra que les fonctions métiers associées au domaine métier demandé (2/2)"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("inventaire:api_fonctions") + "?domaine=2")  # PS
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"fonctions": [3, 4, 5]},  # CA, DI et VS
        )

    def test_api_connecte_trop(self):
        """Un utilisateur connecté ne verra que le dernier argument demandé s'il demande plusieurs domaines métiers"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("inventaire:api_fonctions") + "?domaine=2&domaine=1")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"fonctions": [1, 2]},
        )
