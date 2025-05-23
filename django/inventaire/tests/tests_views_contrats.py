"""Définition des tests unitaires de l'inventaire pour les vues des systèmes"""

import logging
from datetime import date

from django.contrib.auth.models import User, Permission
from django.test import TestCase, tag
from django.urls import reverse

from inventaire.models import (
    ContratMaintenance,
    DomaineMetier,
    Localisation,
    SystemeIndustriel,
    ZoneUsid,
)


logger = logging.getLogger(__name__)


@tag("views", "views-contrats", "views-contrats-recherche")
class ContratsRechercheViewTest(TestCase):
    """Classe de test de la vue de recherche d'un contrat de maintenance"""

    @classmethod
    def setUpTestData(cls):
        # utilisateur pouvant consulter la zone AMS
        cls.user_ams = User.objects.create_user(
            username="ams",
            password="ams123",
        )
        cls.user_ams.user_permissions.add(Permission.objects.get(codename="consult_AMS"))
        # utilisateur pouvant consulter la zone RVC
        cls.user_rvc = User.objects.create_user(
            username="rvc",
            password="rvc123",
        )
        cls.user_rvc.user_permissions.add(Permission.objects.get(codename="consult_RVC"))
        # utilisateur pouvant tout consulter
        cls.user_admin = User.objects.create_superuser(
            username="admin",
            password="admin123",
        )
        # Trois contrats sur la zone AMS
        ContratMaintenance.objects.create(
            pk=1,
            zone_usid=ZoneUsid.AMS,
            numero_marche="2021AMSCAC0001",
            date_fin=date(year=2031, month=8, day=15),
            nom_societe="glabouni",
            nom_poc="jean jean",
            est_actif=True,
        )
        ContratMaintenance.objects.create(
            pk=2,
            zone_usid=ZoneUsid.AMS,
            numero_marche="2022RNSSAI0022",
            date_fin=date(year=2032, month=9, day=14),
            nom_societe="biboubou",
            nom_poc="pierre pierre",
            est_actif=True,
        )
        ContratMaintenance.objects.create(
            pk=3,
            zone_usid=ZoneUsid.AMS,
            numero_marche="2010AMSCAC0099",
            date_fin=date(year=2020, month=9, day=14),
            nom_societe="inutile",
            nom_poc="vieux",
            est_actif=False,
            fiche_corbeille=True,
        )
        # Deux contrats sur la zone RVC
        ContratMaintenance.objects.create(
            pk=4,
            zone_usid=ZoneUsid.RVC,
            numero_marche="2021RNSAI0001",
            date_fin=date(year=2031, month=4, day=18),
            nom_societe="espac",
            nom_poc="michel michel",
            est_actif=True,
        )
        ContratMaintenance.objects.create(
            pk=5,
            zone_usid=ZoneUsid.RVC,
            numero_marche="2022RNSSAI0002",
            date_fin=date(year=2032, month=7, day=4),
            nom_societe="panipano",
            nom_poc="paul paul",
            est_actif=False,
        )
        # un contrat dans la zone CBG
        ContratMaintenance.objects.create(
            pk=6,
            zone_usid=ZoneUsid.CBG,
            numero_marche="2022RNSSAI0003",
            date_fin=date(year=2026, month=6, day=5),
            nom_societe="gloubi gloubi",
            nom_poc="paul paul",
            est_actif=True,
        )

    def tearDown(self) -> None:
        self.client.logout()

    def test_recherche_anonyme(self):
        """Un utilisateur non connecté sera redirigé vers la page de login"""
        response = self.client.get(reverse("inventaire:contrats_recherche"))
        url_attendu = reverse("inventaire:login") + "?next=" + reverse("inventaire:contrats_recherche")
        self.assertRedirects(response, url_attendu)

    def test_recherche_droits_ams(self):
        """Un utilisateur ayant les droits de consultation 'ams' ne verra que ses contrats"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:contrats_recherche"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(response.context["tous_contrats"], ContratMaintenance.objects.filter(pk__in=[1, 2]))

    def test_recherche_droits_rvc(self):
        """Un utilisateur ayant les droits de consultation 'rvc' ne verra que ses contrats"""
        self.client.force_login(self.user_rvc)
        response = self.client.get(reverse("inventaire:contrats_recherche"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(response.context["tous_contrats"], ContratMaintenance.objects.filter(pk=4))

    def test_recherche_droits_tout(self):
        """Un utilisateur ayant tous les droits de consultation verra tous les contrats"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:contrats_recherche"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_contrats"],
            ContratMaintenance.objects.filter(pk__in=[1, 2, 4, 6]).order_by("zone_usid", "numero_marche"),
        )

    def test_recherche_filtre_invalid(self):
        """Un utilisateur filtre de manière invalide les contrats"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:contrats_recherche") + "?zone_usid=youpiha")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_contrats"],
            ContratMaintenance.objects.filter(pk__in=[1, 2, 4, 6]).order_by("zone_usid", "numero_marche"),
        )

    def test_recherche_filtre_zone_usid(self):
        """Un utilisateur filtre les contrats par zones d'USID"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:contrats_recherche") + "?zone_usid=AMS&zone_usid=RVC")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_contrats"],
            ContratMaintenance.objects.filter(pk__in=[1, 2, 4]).order_by("zone_usid", "numero_marche"),
        )

    def test_recherche_filtre_numero_marche(self):
        """Un utilisateur filtre les contrats par numéro de marché"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:contrats_recherche") + "?numero_marche=2021")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_contrats"],
            ContratMaintenance.objects.filter(pk__in=[1, 4]).order_by("zone_usid", "numero_marche"),
        )

    def test_recherche_filtre_S2I_nom_societe(self):
        """Un utilisateur filtre les contrats par nom de société"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:contrats_recherche") + "?nom_societe=bibou")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_contrats"],
            ContratMaintenance.objects.filter(pk=2),
        )

    def test_recherche_filtre_date_fin(self):
        """Un utilisateur filtre les contrats par date d'expiration"""
        self.client.force_login(self.user_admin)
        response = self.client.get(
            reverse("inventaire:contrats_recherche") + "?date_fin_day=1&date_fin_month=1&date_fin_year=2027"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_contrats"],
            ContratMaintenance.objects.filter(pk=6),
        )

    def test_recherche_filtre_est_actif(self):
        """Un utilisateur filtre les contrats par statut d'inactivité"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:contrats_recherche") + "?est_actif=True")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_contrats"],
            ContratMaintenance.objects.filter(pk__in=[1, 2, 4, 5, 6]).order_by("zone_usid", "numero_marche"),
        )

    def test_recherche_filtre_combine_zone_numero_marche(self):
        """Un utilisateur filtre les contrats en utilisant plusieurs filtres: zone_usid et numero_marche"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:contrats_recherche") + "?zone_usid=AMS&numero_marche=SAI")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_contrats"],
            ContratMaintenance.objects.filter(pk=2),
        )


@tag("views", "views-contrats", "views-contrats-creation")
class ContratsCreationViewTest(TestCase):
    """Classe de test de la vue de la création d'un contrat de maintenance"""

    @classmethod
    def setUpTestData(cls):
        # utilisateur pouvant modifier la zone AMS
        cls.user_ams = User.objects.create_user(
            username="ams",
            password="ams123",
        )
        cls.user_ams.user_permissions.add(Permission.objects.get(codename="consult_AMS"))
        cls.user_ams.user_permissions.add(Permission.objects.get(codename="modif_AMS"))
        # utilisateur pouvant modifier la zone RVC
        cls.user_rvc = User.objects.create_user(
            username="rvc",
            password="rvc123",
        )
        cls.user_rvc.user_permissions.add(Permission.objects.get(codename="consult_RVC"))
        cls.user_rvc.user_permissions.add(Permission.objects.get(codename="modif_RVC"))
        # utilisateur pouvant tout consulter
        cls.user_admin = User.objects.create_superuser(
            username="admin",
            password="admin123",
        )
        # Un contrat sur la zone AMS
        ContratMaintenance.objects.create(
            pk=1,
            zone_usid=ZoneUsid.AMS,
            numero_marche="2021AMSCAC0001",
            date_fin=date(year=2031, month=8, day=15),
            nom_societe="glabouni",
            nom_poc="jean jean",
            est_actif=True,
        )

    def tearDown(self) -> None:
        self.client.logout()

    def test_creation_anonyme(self):
        """Un utilisateur non connecté sera redirigé vers la page de login"""
        response = self.client.get(reverse("inventaire:contrats_creation"))
        url_attendu = reverse("inventaire:login") + "?next=" + reverse("inventaire:contrats_creation")
        self.assertRedirects(response, url_attendu)

    def test_creation_connecte_ams_get(self):
        """Un utilisateur ayant les droits de modification 'ams' pourra créer un contrat dans cette zone"""
        self.client.force_login(self.user_ams)
        response = self.client.get(
            reverse("inventaire:contrats_creation"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/contrats_modification.html")

    def test_creation_connecte_ams_post(self):
        """Un utilisateur ayant les droits de modification 'ams' pourra créer un contrat dans cette zone"""
        self.client.force_login(self.user_ams)
        data = {
            # le formulaire principal du S2I
            "numero_marche": ["2026AMS0004"],
            "zone_usid": ["AMS"],
            "date_fin": ["01/01/2030"],
            "est_actif": [True],
            "nom_societe": ["pani pano"],
            "nom_poc": ["robeeert"],
            "description": ["pas un roman non plus"],
        }
        response = self.client.post(
            reverse("inventaire:contrats_creation"),
            data=data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/contrats_details.html")
        # le S2I et ses éléments liés ont bien été enregistrés
        self.assertEqual(ContratMaintenance.objects.count(), 2)


@tag("views", "views-contrats", "views-contrats-modification")
class ContratsModificationViewTest(TestCase):
    """Classe de test de la vue de la modification d'un contrat de maintenance"""

    @classmethod
    def setUpTestData(cls):
        # utilisateur pouvant modifier la zone AMS
        cls.user_ams = User.objects.create_user(
            username="ams",
            password="ams123",
        )
        cls.user_ams.user_permissions.add(Permission.objects.get(codename="consult_AMS"))
        cls.user_ams.user_permissions.add(Permission.objects.get(codename="modif_AMS"))
        # utilisateur pouvant modifier la zone RVC
        cls.user_rvc = User.objects.create_user(
            username="rvc",
            password="rvc123",
        )
        cls.user_rvc.user_permissions.add(Permission.objects.get(codename="consult_RVC"))
        cls.user_rvc.user_permissions.add(Permission.objects.get(codename="modif_RVC"))
        # utilisateur pouvant tout consulter
        cls.user_admin = User.objects.create_superuser(
            username="admin",
            password="admin123",
        )
        # Un contrat sur la zone AMS
        ContratMaintenance.objects.create(
            pk=1,
            zone_usid=ZoneUsid.AMS,
            numero_marche="2021AMSCAC0001",
            date_fin=date(year=2031, month=8, day=15),
            nom_societe="glabouni",
            nom_poc="jean jean",
            est_actif=True,
        )

    def tearDown(self) -> None:
        self.client.logout()

    def test_modification_anonyme(self):
        """Un utilisateur non connecté sera redirigé vers la page de login"""
        response = self.client.get(reverse("inventaire:contrats_modification", args="1"))
        url_attendu = reverse("inventaire:login") + "?next=" + reverse("inventaire:contrats_modification", args="1")
        self.assertRedirects(response, url_attendu)

    def test_creation_connecte_ams_contrat_ams_get(self):
        """Un utilisateur ayant les droits de modification 'ams' pourra afficher la page de modification"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:contrats_modification", args="1"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/contrats_modification.html")

    def test_creation_connecte_rvc_contrat_ams_get(self):
        """Un utilisateur ayant les droits de modification 'rvc' ne pourra pas afficher la page de modification"""
        self.client.force_login(self.user_rvc)
        response = self.client.get(reverse("inventaire:contrats_modification", args="1"))
        self.assertEqual(response.status_code, 404)

    def test_modification_connecte_ams_contrat_ams_post(self):
        """Un utilisateur ayant les droits de modification 'ams' pourra modifier un contrat dans cette zone"""
        self.client.force_login(self.user_ams)
        data = {
            "numero_marche": ["2021AMSCAC0001"],
            "zone_usid": ["AMS"],
            "date_fin": ["01/01/2030"],  # ajout de 6 mois
            "est_actif": [False],  # passage en inactif
            "nom_societe": ["pani pano"],
            "nom_poc": ["patriiiick"],  # changement du contact
            "description": ["pas un roman non plus, ou presque !"],  # changement description
        }
        response = self.client.post(
            reverse("inventaire:contrats_modification", args="1"),
            data=data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/contrats_details.html")
        # le contrat à bien été enregistrés
        self.assertEqual(ContratMaintenance.objects.count(), 1)
        # vérification des modifications
        c: ContratMaintenance = ContratMaintenance.objects.get(pk=1)
        self.assertEqual(c.date_fin, date(2030, 1, 1))
        self.assertFalse(c.est_actif)
        self.assertEqual(c.nom_poc, "patriiiick")
        self.assertEqual(c.description, "pas un roman non plus, ou presque !")


@tag("views", "views-contrats", "views-contrats-suppression")
class ContratsSuppressionViewTest(TestCase):
    """Classe de test de la vue de la suppression d'un contrat de maintenance"""

    @classmethod
    def setUpTestData(cls):
        # utilisateur pouvant modifier la zone AMS
        cls.user_ams = User.objects.create_user(
            username="ams",
            password="ams123",
        )
        cls.user_ams.user_permissions.add(Permission.objects.get(codename="consult_AMS"))
        cls.user_ams.user_permissions.add(Permission.objects.get(codename="modif_AMS"))
        # utilisateur pouvant modifier la zone RVC
        cls.user_rvc = User.objects.create_user(
            username="rvc",
            password="rvc123",
        )
        cls.user_rvc.user_permissions.add(Permission.objects.get(codename="consult_RVC"))
        cls.user_rvc.user_permissions.add(Permission.objects.get(codename="modif_RVC"))
        # utilisateur pouvant tout consulter
        cls.user_admin = User.objects.create_superuser(
            username="admin",
            password="admin123",
        )

    def setUp(self) -> None:
        # Un système sur la zone AMS
        ContratMaintenance.objects.create(
            pk=1,
            zone_usid=ZoneUsid.AMS,
            numero_marche="2021AMSCAC0001",
            date_fin=date(year=2031, month=8, day=15),
            nom_societe="glabouni",
            nom_poc="jean jean",
            est_actif=True,
        )

    def tearDown(self) -> None:
        self.client.logout()

    def test_suppression_anonyme(self):
        """Un utilisateur non connecté sera redirigé vers la page de login"""
        response = self.client.get(reverse("inventaire:contrats_suppression", args="1"))
        url_attendu = reverse("inventaire:login") + "?next=" + reverse("inventaire:contrats_suppression", args="1")
        self.assertRedirects(response, url_attendu)

    def test_suppression_connecte_ams_contrat_ams_get(self):
        """Un utilisateur ayant les droits de modification 'ams' pourra afficher la page de suppression"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:contrats_suppression", args="1"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/contrats_suppression.html")

    def test_suppression_connecte_rvc_contrat_ams_get(self):
        """Un utilisateur ayant les droits de modification 'rvc' ne pourra pas afficher la page de suppression"""
        self.client.force_login(self.user_rvc)
        response = self.client.get(reverse("inventaire:contrats_suppression", args="1"))
        self.assertEqual(response.status_code, 404)

    def test_suppression_connecte_ams_contrat_ams_post(self):
        """Un utilisateur ayant les droits de modification 'ams' pourra supprimer un contrat dans cette zone"""
        self.client.force_login(self.user_ams)
        data = {}
        response = self.client.post(
            reverse("inventaire:contrats_suppression", args="1"),
            data=data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/contrats_recherche.html")
        # le contrat a bien été mis à la corbeille
        self.assertEqual(ContratMaintenance.objects.count(), 1)
        s: ContratMaintenance = ContratMaintenance.objects.get(pk=1)
        self.assertEqual(s.fiche_corbeille, True)


@tag("views", "views-contrats", "views-contrats-details")
class SystemesDetailsViewTest(TestCase):
    """Classe de test de la vue de la page des détails d'un S2I"""

    @classmethod
    def setUpTestData(cls):
        # utilisateur pouvant consulter la zone AMS
        cls.user_ams = User.objects.create_user(
            username="ams",
            password="ams123",
        )
        cls.user_ams.user_permissions.add(Permission.objects.get(codename="consult_AMS"))

        # Trois contrats sur la zone AMS
        ContratMaintenance.objects.create(
            pk=1,
            zone_usid=ZoneUsid.AMS,
            numero_marche="2021AMSCAC0001",
            date_fin=date(year=2031, month=8, day=15),
            nom_societe="glabouni",
            nom_poc="jean jean",
            est_actif=True,
        )
        ContratMaintenance.objects.create(
            pk=2,
            zone_usid=ZoneUsid.AMS,
            numero_marche="2022RNSSAI0022",
            date_fin=date(year=2032, month=9, day=14),
            nom_societe="biboubou",
            nom_poc="pierre pierre",
            est_actif=True,
        )
        ContratMaintenance.objects.create(
            pk=3,
            zone_usid=ZoneUsid.AMS,
            numero_marche="2010AMSCAC0099",
            date_fin=date(year=2020, month=9, day=14),
            nom_societe="inutile",
            nom_poc="vieux",
            est_actif=False,
            fiche_corbeille=True,
        )
        # un contrat dans la zone RVC
        ContratMaintenance.objects.create(
            pk=4,
            zone_usid=ZoneUsid.RVC,
            numero_marche="2022RNSSAI0003",
            date_fin=date(year=2026, month=6, day=5),
            nom_societe="gloubi gloubi",
            nom_poc="paul paul",
            est_actif=True,
        )
        # Un système sur la zone AMS, lié au contrat n°1
        DomaineMetier.objects.create(
            pk=1,
            nom="énergie électrique",
            code="EE",
            coeff_criticite=3,
        )
        Localisation.objects.create(
            pk=1,
            zone_usid=ZoneUsid.AMS,
            nom_ville="Angers",
            nom_quartier="Roseraie",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        SystemeIndustriel.objects.create(
            pk=1,
            localisation=Localisation.objects.get(pk=1),
            contrat_mcs=ContratMaintenance.objects.get(pk=1),
            nom="chargeur téléphone",
            environnement=SystemeIndustriel.Environnement.CYB,
            domaine_metier=DomaineMetier.objects.get(pk=1),
        )

    def tearDown(self) -> None:
        self.client.logout()

    def test_details_anonyme(self):
        """Un utilisateur non connecté sera redirigé vers la page de login"""
        response = self.client.get(reverse("inventaire:contrats_details", args="1"))
        url_attendu = reverse("inventaire:login") + "?next=" + reverse("inventaire:contrats_details", args="1")
        self.assertRedirects(response, url_attendu)

    def test_details_connecte_ams_contrat_ams(self):
        """Un utilisateur ayant les droits sur la zone ams verra ses 2 contrats (1 dans la corbeille)"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:contrats_details", args="1"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/contrats_details.html")
        response = self.client.get(reverse("inventaire:contrats_details", args="2"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/contrats_details.html")
        response = self.client.get(reverse("inventaire:contrats_details", args="3"))  # dans la corbeille
        self.assertEqual(response.status_code, 404)

    def test_details_connecte_ams_contrat_rvc(self):
        """Un utilisateur ayant les droits sur la zone ams ne verra pas le contrat n°4 (zone rvc)"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:contrats_details", args="4"))
        self.assertEqual(response.status_code, 404)

    def test_details_affichage_contrat(self):
        """Un utilisateur verra toutes les informations pertinentes de son contrat"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:contrats_details", args="1"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["contrat"],
            ContratMaintenance.objects.get(pk=1),
        )
        self.assertQuerysetEqual(
            response.context["tous_systemes_lies"],
            SystemeIndustriel.objects.filter(pk=1),
        )
