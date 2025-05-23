"""Définition des tests unitaires de l'inventaire pour les vues des systèmes"""

import logging
from datetime import date

from django.contrib.auth.models import User, Permission
from django.test import TestCase, tag
from django.urls import reverse

from inventaire.models import (
    ContratMaintenance,
    DomaineMetier,
    FonctionsMetier,
    Interconnexion,
    LicenceLogiciel,
    Localisation,
    MaterielEffecteur,
    MaterielOrdinateur,
    SystemeIndustriel,
    ZoneUsid,
)


logger = logging.getLogger(__name__)


@tag("views", "views-systemes", "views-systemes-recherche")
class SystemesRechercheViewTest(TestCase):
    """Classe de test de la vue de recherche de S2I"""

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
        # ajout de domaine et fonctions métiers
        DomaineMetier.objects.create(
            pk=1,
            nom="énergie électrique",
            code="EE",
            coeff_criticite=3,
        )
        DomaineMetier.objects.create(
            pk=2,
            nom="autre",
            code="AU",
            coeff_criticite=1,
        )
        # Deux systèmes sur la zone AMS
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
            nom="chargeur téléphone",
            environnement=SystemeIndustriel.Environnement.CYB,
            domaine_metier=DomaineMetier.objects.get(pk=1),
        )
        SystemeIndustriel.objects.create(  # celui-ci est dans la corbeille
            pk=4,
            localisation=Localisation.objects.get(pk=1),
            nom="dans la corbeille",
            environnement=SystemeIndustriel.Environnement.AUTRE,
            domaine_metier=DomaineMetier.objects.get(pk=1),
            fiche_corbeille=True,
        )
        MaterielOrdinateur.objects.create(
            pk=1,
            systeme=SystemeIndustriel.objects.get(pk=1),
            fonction=MaterielOrdinateur.Fonction.MAINT,
            marque="extreme pc",
            modele="Xtrem pro max",
            os_famille=MaterielOrdinateur.FamilleOs.WIN_P_11,
        )
        LicenceLogiciel.objects.create(
            pk=1,
            systeme=SystemeIndustriel.objects.get(pk=1),
            editeur="ankamou",
            logiciel="fodus",
            version="1234",
            licence="123456789",
            date_fin=date(2026, 1, 1),
        )
        # un système dans la zone RVC
        Localisation.objects.create(
            pk=2,
            zone_usid=ZoneUsid.RVC,
            nom_ville="Rennes",
            nom_quartier="Maurepas",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        SystemeIndustriel.objects.create(
            pk=2,
            localisation=Localisation.objects.get(pk=2),
            nom="enceinte bluetooth",
            environnement=SystemeIndustriel.Environnement.AUTRE,
            domaine_metier=DomaineMetier.objects.get(pk=2),
            homologation_classe=SystemeIndustriel.ClasseHomologation.C1,
            homologation_fin=date(2020, 1, 1),
        )
        MaterielOrdinateur.objects.create(
            pk=2,
            systeme=SystemeIndustriel.objects.get(pk=2),
            fonction=MaterielOrdinateur.Fonction.MAINT,
            marque="grille pain pc",
            modele="potato pentium",
            os_famille=MaterielOrdinateur.FamilleOs.WIN_P_XP,
        )
        MaterielEffecteur.objects.create(
            pk=1,
            systeme=SystemeIndustriel.objects.get(pk=2),
            type=MaterielEffecteur.Type.TELECOMMANDE,
            marque="sound mix",
            modele="click IR v3",
            nombre=1,
        )
        LicenceLogiciel.objects.create(
            systeme=SystemeIndustriel.objects.get(pk=2),
            editeur="Nulosoft",
            logiciel="windaube",
            version="2016 R2",
            licence="1234-5678-9456-1230",
            date_fin=date(2025, 1, 1),
        )
        # un système dans la zone CBG
        Localisation.objects.create(
            pk=3,
            zone_usid=ZoneUsid.CBG,
            nom_ville="Cherbourg",
            nom_quartier="Fourches-Charcot",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        SystemeIndustriel.objects.create(
            pk=3,
            localisation=Localisation.objects.get(pk=3),
            nom="détecteur fantômes",
            environnement=SystemeIndustriel.Environnement.AUTRE,
            domaine_metier=DomaineMetier.objects.get(pk=2),
            homologation_classe=SystemeIndustriel.ClasseHomologation.C2,
            homologation_fin=date(2020, 7, 7),
        )
        MaterielEffecteur.objects.create(
            pk=2,
            systeme=SystemeIndustriel.objects.get(pk=3),
            type=MaterielEffecteur.Type.ANTENNE,
            marque="fantomas debunk",
            modele="buster 2000",
            nombre=3,
        )

    def tearDown(self) -> None:
        self.client.logout()

    def test_recherche_anonyme(self):
        """Un utilisateur non connecté sera redirigé vers la page de login"""
        response = self.client.get(reverse("inventaire:systemes_recherche"))
        url_attendu = reverse("inventaire:login") + "?next=" + reverse("inventaire:systemes_recherche")
        self.assertRedirects(response, url_attendu)

    def test_recherche_droits_ams(self):
        """Un utilisateur ayant les droits de consultation 'ams' ne verra que ses systèmes"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:systemes_recherche"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(response.context["tous_sys_indus"], SystemeIndustriel.objects.filter(pk=1))

    def test_recherche_droits_rvc(self):
        """Un utilisateur ayant les droits de consultation 'rvc' ne verra que ses systèmes"""
        self.client.force_login(self.user_rvc)
        response = self.client.get(reverse("inventaire:systemes_recherche"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(response.context["tous_sys_indus"], SystemeIndustriel.objects.filter(pk=2))

    def test_recherche_droits_tout(self):
        """Un utilisateur ayant tous les droits de consultation verra tous les systèmes"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:systemes_recherche"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk__in=[1, 2, 3]).order_by("localisation__zone_usid"),
        )

    def test_recherche_filtre_invalid(self):
        """Un utilisateur filtre de manière invalide les systèmes"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:systemes_recherche") + "?z_usid=youpiha")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk__in=[1, 2, 3]).order_by("localisation__zone_usid"),
        )

    def test_recherche_filtre_localisation_zone(self):
        """Un utilisateur filtre les systèmes par zones d'USID"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:systemes_recherche") + "?z_usid=AMS&z_usid=RVC")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk__in=[1, 2]).order_by("localisation__zone_usid"),
        )

    def test_recherche_filtre_localisation_ville(self):
        """Un utilisateur filtre les systèmes par villes"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:systemes_recherche") + "?z_ville=Angers&z_ville=Cherbourg")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk__in=[1, 3]).order_by("localisation__zone_usid"),
        )

    def test_recherche_filtre_localisation_quartier(self):
        """Un utilisateur filtre les systèmes par quartiers"""
        self.client.force_login(self.user_admin)
        response = self.client.get(
            reverse("inventaire:systemes_recherche") + "?z_quartier=Maurepas&z_quartier=Roseraie"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk__in=[1, 2]).order_by("localisation__zone_usid"),
        )

    def test_recherche_filtre_S2I_nom(self):
        """Un utilisateur filtre les systèmes par nom de S2I"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:systemes_recherche") + "?s_nom=enceinte")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk=2),
        )

    def test_recherche_filtre_S2I_domaine_metier(self):
        """Un utilisateur filtre les systèmes par domaine métier de S2I"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:systemes_recherche") + "?s_metier=1")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk=1),
        )

    def test_recherche_filtre_S2I_homologation_classe(self):
        """Un utilisateur filtre les systèmes par classe d'homologation de S2I"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:systemes_recherche") + "?s_classe=1")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk=2),
        )

    def test_recherche_filtre_S2I_homologation_fin(self):
        """Un utilisateur filtre les systèmes par date de fin d'homologation de S2I"""
        self.client.force_login(self.user_admin)
        response = self.client.get(
            reverse("inventaire:systemes_recherche") + "?s_fin_day=6&s_fin_month=3&s_fin_year=2020"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk=2),
        )

    def test_recherche_filtre_ordinateur_fonction(self):
        """Un utilisateur filtre les systèmes par fonction des ordinateurs/serveurs du S2I"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:systemes_recherche") + "?o_fonction=0")  # poste de maintenance
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk__in=[1, 2]),
        )

    def test_recherche_filtre_ordinateur_famille(self):
        """Un utilisateur filtre les systèmes par famille d'os des ordinateurs/serveurs du S2I"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:systemes_recherche") + "?o_famille=6")  # windows 11 perso
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk=1),
        )

    def test_recherche_filtre_ordinateur_marque(self):
        """Un utilisateur filtre les systèmes par marque des ordinateurs/serveurs du S2I"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:systemes_recherche") + "?o_marque_modele=grille pain")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk=2),
        )

    def test_recherche_filtre_ordinateur_modele(self):
        """Un utilisateur filtre les systèmes par modèle des ordinateurs/serveurs du S2I"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:systemes_recherche") + "?o_marque_modele=rem pro")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk=1),
        )

    def test_recherche_filtre_effecteur_type(self):
        """Un utilisateur filtre les systèmes par type des effecteurs du S2I"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:systemes_recherche") + "?e_type=2")  # antenne
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk=3),
        )

    def test_recherche_filtre_effecteur_marque(self):
        """Un utilisateur filtre les systèmes par marque des effecteurs du S2I"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:systemes_recherche") + "?e_marque_modele=fantomas")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk=3),
        )

    def test_recherche_filtre_effecteur_modele(self):
        """Un utilisateur filtre les systèmes par modèle des effecteurs du S2I"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:systemes_recherche") + "?e_marque_modele=click")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk=2),
        )

    def test_recherche_filtre_licence_editeur(self):
        """Un utilisateur filtre les systèmes par éditeur d'un logiciel du S2I"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:systemes_recherche") + "?l_editeur_logiciel=ankamou")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk=1),
        )

    def test_recherche_filtre_licence_logiciel(self):
        """Un utilisateur filtre les systèmes par nom d'un logiciel du S2I"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:systemes_recherche") + "?l_editeur_logiciel=windaube")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk=2),
        )

    def test_recherche_filtre_licence_fin(self):
        """Un utilisateur filtre les systèmes par date de fin d'une licence de logiciel du S2I"""
        self.client.force_login(self.user_admin)
        response = self.client.get(
            reverse("inventaire:systemes_recherche") + "?l_fin_day=6&l_fin_month=3&l_fin_year=2025"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk=2),
        )

    def test_recherche_filtre_combine_S2I_domaine_metier_effecteur_modele(self):
        """Un utilisateur filtre les systèmes en utilisant plusieurs filtres: domaine métier et modèle d'effecteur"""
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("inventaire:systemes_recherche") + "?s_metier=2&e_marque_modele=buster")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertQuerySetEqual(
            response.context["tous_sys_indus"],
            SystemeIndustriel.objects.filter(pk=3),
        )


@tag("views", "views-systemes", "views-systemes-creation")
class SystemesCreationViewTest(TestCase):
    """Classe de test de la vue de la création d'un S2I"""

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
        # ajout de domaine et fonctions métiers
        DomaineMetier.objects.create(
            pk=1,
            nom="énergie électrique",
            code="EE",
            coeff_criticite=3,
        )
        FonctionsMetier.objects.create(
            pk=1,
            domaine=DomaineMetier.objects.get(pk=1),
            nom="conversion d'énergie électrique",
            code="CEE",
        )
        # Un système sur la zone AMS
        Localisation.objects.create(
            pk=1,
            zone_usid=ZoneUsid.AMS,
            nom_ville="Angers",
            nom_quartier="Roseraie",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        ContratMaintenance.objects.create(
            pk=1,
            zone_usid=ZoneUsid.AMS,
            numero_marche="2022RNSSAI00001",
            date_fin=date(2032, 10, 25),
            nom_societe="cotorep",
            nom_poc="jean jean",
            est_actif=True,
        )
        SystemeIndustriel.objects.create(
            pk=1,
            localisation=Localisation.objects.get(pk=1),
            nom="chargeur téléphone",
            environnement=SystemeIndustriel.Environnement.CYB,
            domaine_metier=DomaineMetier.objects.get(pk=1),
        )
        SystemeIndustriel.objects.get(pk=1).fonctions_metiers.add(FonctionsMetier.objects.get(pk=1))

    def tearDown(self) -> None:
        self.client.logout()

    def test_creation_anonyme(self):
        """Un utilisateur non connecté sera redirigé vers la page de login"""
        response = self.client.get(reverse("inventaire:systemes_creation"))
        url_attendu = reverse("inventaire:login") + "?next=" + reverse("inventaire:systemes_creation")
        self.assertRedirects(response, url_attendu)

    def test_creation_connecte_ams_get(self):
        """Un utilisateur ayant les droits de modification 'ams' pourra créer un système dans cette zone"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:systemes_creation"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/systemes_modification.html")

    def test_creation_connecte_ams_post(self):
        """Un utilisateur ayant les droits de modification 'ams' pourra créer un système dans cette zone"""
        self.client.force_login(self.user_ams)
        data = {
            # le formulaire principal du S2I
            "nom": ["un super S2I indispensable"],
            "z_usid": ["AMS"],
            "z_ville": ["Angers"],
            "z_quartier": ["Roseraie"],
            "z_zone": [""],
            "environnement": ["3"],
            "domaine_metier": ["1"],
            "fonctions_metiers": ["1"],
            "numero_gtp": ["010203040506070809"],
            "description": ["pas un roman non plus"],
            "homologation_classe": ["2"],
            "homologation_responsable": ["2"],
            "homologation_fin": ["01/05/2026"],
            "contrat_mcs": ["1"],
            "date_maintenance": ["01/02/2021"],
            "sauvegarde_config": ["01/01/2025"],
            "sauvegarde_donnees": [""],
            "sauvegarde_comptes": [""],
            # le formset pour les interconnexions
            "systeme_from-TOTAL_FORMS": ["1"],
            "systeme_from-INITIAL_FORMS": ["0"],
            "systeme_from-MIN_NUM_FORMS": ["0"],
            "systeme_from-MAX_NUM_FORMS": ["1000"],
            "systeme_from-0-id": [""],
            "systeme_from-0-systeme_from": [""],
            "systeme_from-0-systeme_to": ["1"],
            "systeme_from-0-type_reseau": ["2"],
            "systeme_from-0-type_liaison": ["7"],
            "systeme_from-0-protocole": ["bazar"],
            "systeme_from-0-description": ["bizarre"],
            "systeme_from-0-DELETE": [""],
            # le formset pour les ordinateurs/serveurs liés
            "materiels_it-TOTAL_FORMS": ["2"],
            "materiels_it-INITIAL_FORMS": ["0"],
            "materiels_it-MIN_NUM_FORMS": ["0"],
            "materiels_it-MAX_NUM_FORMS": ["1000"],
            "materiels_it-0-id": [""],
            "materiels_it-0-systeme": [""],
            "materiels_it-0-fonction": ["0"],
            "materiels_it-0-marque": ["big bg"],
            "materiels_it-0-modele": ["okela"],
            "materiels_it-0-nombre": ["1"],
            "materiels_it-0-os_famille": ["1"],
            "materiels_it-0-os_version": ["gu"],
            "materiels_it-0-description": [""],
            "materiels_it-0-DELETE": [""],
            "materiels_it-1-id": [""],
            "materiels_it-1-systeme": [""],
            "materiels_it-1-fonction": ["1"],
            "materiels_it-1-marque": ["big bg"],
            "materiels_it-1-modele": ["koulos"],
            "materiels_it-1-nombre": ["2"],
            "materiels_it-1-os_famille": ["10"],
            "materiels_it-1-os_version": ["ygy"],
            "materiels_it-1-description": [""],
            "materiels_it-1-DELETE": [""],
            # le formset pour les matériels divers liés
            "materiels_ot-TOTAL_FORMS": ["1"],
            "materiels_ot-INITIAL_FORMS": ["0"],
            "materiels_ot-MIN_NUM_FORMS": ["0"],
            "materiels_ot-MAX_NUM_FORMS": ["1000"],
            "materiels_ot-0-id": [""],
            "materiels_ot-0-systeme": [""],
            "materiels_ot-0-type": ["12"],
            "materiels_ot-0-marque": ["caribou"],
            "materiels_ot-0-modele": ["bazar beach"],
            "materiels_ot-0-nombre": ["2"],
            "materiels_ot-0-firmware": ["123456"],
            "materiels_ot-0-cortec": [""],
            "materiels_ot-0-description": [""],
            "materiels_ot-0-DELETE": [""],
            # le formset pour les licences liées
            "licences-TOTAL_FORMS": ["1"],
            "licences-INITIAL_FORMS": ["0"],
            "licences-MIN_NUM_FORMS": ["0"],
            "licences-MAX_NUM_FORMS": ["1000"],
            "licences-0-id": [""],
            "licences-0-systeme": [""],
            "licences-0-editeur": ["bg inc."],
            "licences-0-logiciel": ["spyware"],
            "licences-0-version": ["ftygf"],
            "licences-0-licence": ["tygft"],
            "licences-0-date_fin": ["01/01/2025"],
            "licences-0-description": [""],
            "licences-0-DELETE": [""],
        }
        response = self.client.post(
            reverse("inventaire:systemes_creation"),
            data=data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/systemes_details.html")
        # le S2I et ses éléments liés ont bien été enregistrés
        self.assertEqual(SystemeIndustriel.objects.count(), 2)
        self.assertEqual(Interconnexion.objects.count(), 2)  # car interconnexions symétriques
        self.assertEqual(MaterielOrdinateur.objects.count(), 2)
        self.assertEqual(MaterielEffecteur.objects.count(), 1)
        self.assertEqual(LicenceLogiciel.objects.count(), 1)


@tag("views", "views-systemes", "views-systemes-modification")
class SystemesModificationViewTest(TestCase):
    """Classe de test de la vue de la modification d'un S2I"""

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
        # ajout de domaine et fonctions métiers
        DomaineMetier.objects.create(
            pk=1,
            nom="énergie électrique",
            code="EE",
            coeff_criticite=3,
        )
        FonctionsMetier.objects.create(
            pk=1,
            domaine=DomaineMetier.objects.get(pk=1),
            nom="distribution d'énergie électrique",
            code="DEE",
        )
        FonctionsMetier.objects.create(
            pk=2,
            domaine=DomaineMetier.objects.get(pk=1),
            nom="conversion d'énergie électrique",
            code="CEE",
        )
        # Un système sur la zone AMS
        Localisation.objects.create(
            pk=1,
            zone_usid=ZoneUsid.AMS,
            nom_ville="Angers",
            nom_quartier="Roseraie",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        ContratMaintenance.objects.create(
            pk=1,
            zone_usid=ZoneUsid.AMS,
            numero_marche="2022RNSSAI00001",
            date_fin=date(2032, 10, 25),
            nom_societe="cotorep",
            nom_poc="jean jean",
            est_actif=True,
        )
        SystemeIndustriel.objects.create(
            pk=1,
            localisation=Localisation.objects.get(pk=1),
            contrat_mcs=ContratMaintenance.objects.get(pk=1),
            nom="chargeur iphone",
            environnement=SystemeIndustriel.Environnement.CYB,
            domaine_metier=DomaineMetier.objects.get(pk=1),
            numero_gtp="123456789",
            homologation_fin=date(2025, 5, 10),
            homologation_classe=SystemeIndustriel.ClasseHomologation.C1,
            sauvegarde_config=date(2020, 3, 25),
            sauvegarde_donnees=date(2020, 3, 25),
            sauvegarde_comptes=date(2020, 3, 25),
            date_maintenance=date(2023, 2, 11),
            description="bien caché au fond du bâtiment",
        )
        SystemeIndustriel.objects.create(  # un système mineur pour l'interconnexion
            pk=2,
            localisation=Localisation.objects.get(pk=1),
            nom="chargeur cassé",
            environnement=SystemeIndustriel.Environnement.OPS,
            domaine_metier=DomaineMetier.objects.get(pk=1),
        )
        SystemeIndustriel.objects.get(pk=1).fonctions_metiers.add(
            FonctionsMetier.objects.get(pk=1),
            FonctionsMetier.objects.get(pk=2),
        )
        SystemeIndustriel.objects.get(pk=1).systemes_connectes.add(
            SystemeIndustriel.objects.get(pk=2),
            through_defaults={"type_reseau": Interconnexion.Reseau.A_C, "type_liaison": Interconnexion.Liaison.WIFI},
        )
        MaterielOrdinateur.objects.create(
            pk=1,
            systeme=SystemeIndustriel.objects.get(pk=1),
            fonction=MaterielOrdinateur.Fonction.MAINT,
            marque="pas du tout la NSA",
            modele="aspir' data 2000",
            os_famille=MaterielOrdinateur.FamilleOs.WIN_P_10,
            os_version="010203",
        )
        MaterielEffecteur.objects.create(
            pk=1,
            systeme=SystemeIndustriel.objects.get(pk=1),
            type=MaterielEffecteur.Type.ONDULEUR,
            marque="energy mix",
            modele="nrj pro max",
            nombre=2,
        )
        LicenceLogiciel.objects.create(
            pk=1,
            systeme=SystemeIndustriel.objects.get(pk=1),
            editeur="EduSoft",
            logiciel="Adibou",
            version="2000 NT",
            licence="0000",
            date_fin=date(2077, 7, 7),
        )

    def tearDown(self) -> None:
        self.client.logout()

    def test_modification_anonyme(self):
        """Un utilisateur non connecté sera redirigé vers la page de login"""
        response = self.client.get(reverse("inventaire:systemes_modification", args="1"))
        url_attendu = reverse("inventaire:login") + "?next=" + reverse("inventaire:systemes_modification", args="1")
        self.assertRedirects(response, url_attendu)

    def test_creation_connecte_ams_systeme_ams_get(self):
        """Un utilisateur ayant les droits de modification 'ams' pourra afficher la page de modification"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:systemes_modification", args="1"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/systemes_modification.html")

    def test_creation_connecte_rvc_systeme_ams_get(self):
        """Un utilisateur ayant les droits de modification 'rvc' ne pourra pas afficher la page de modification"""
        self.client.force_login(self.user_rvc)
        response = self.client.get(reverse("inventaire:systemes_modification", args="1"))
        self.assertEqual(response.status_code, 404)

    def test_modification_connecte_ams_systeme_ams_post(self):
        """Un utilisateur ayant les droits de modification 'ams' pourra modifier un système dans cette zone"""
        self.client.force_login(self.user_ams)
        data = {
            # le formulaire principal du S2I
            "nom": ["chargeur iphone V2"],  # changement du nom
            "z_usid": ["AMS"],
            "z_ville": ["Angers"],
            "z_quartier": ["Roseraie"],
            "z_zone": [""],
            "environnement": ["3"],  # changement de l'environnement: OPS
            "domaine_metier": ["1"],
            "fonctions_metiers": ["1"],  # changement: uniquement DEE (suppression CEE)
            "numero_gtp": ["inutile pour les S2I"],  # changement
            "description": ["bien caché au fond du bâtiment"],
            "homologation_classe": ["1"],
            "homologation_responsable": ["2"],  # ajout de cette donnée
            "homologation_fin": ["01/05/2026"],  # changement de la date
            "contrat_mcs": ["1"],
            "date_maintenance": ["11/02/2024"],  # changement
            "sauvegarde_config": ["25/03/2020"],
            "sauvegarde_donnees": ["25/03/2020"],
            "sauvegarde_comptes": ["25/03/2020"],
            # le formset pour les interconnexions
            "systeme_from-TOTAL_FORMS": ["2"],
            "systeme_from-INITIAL_FORMS": ["1"],
            "systeme_from-MIN_NUM_FORMS": ["0"],
            "systeme_from-MAX_NUM_FORMS": ["1000"],
            "systeme_from-0-id": ["1"],
            "systeme_from-0-systeme_from": ["1"],
            "systeme_from-0-systeme_to": ["2"],
            "systeme_from-0-type_reseau": ["0"],
            "systeme_from-0-type_liaison": ["3"],  # changement
            "systeme_from-0-protocole": ["bazar"],
            "systeme_from-0-description": ["bizarre"],
            "systeme_from-0-DELETE": [""],
            # le formset pour les ordinateurs/serveurs liés
            "materiels_it-TOTAL_FORMS": ["2"],
            "materiels_it-INITIAL_FORMS": ["1"],
            "materiels_it-MIN_NUM_FORMS": ["0"],
            "materiels_it-MAX_NUM_FORMS": ["1000"],
            "materiels_it-0-id": ["1"],
            "materiels_it-0-systeme": ["1"],
            "materiels_it-0-fonction": ["0"],
            "materiels_it-0-marque": ["pas du tout la NSA"],
            "materiels_it-0-modele": ["aspir' data 2020"],  # changement
            "materiels_it-0-nombre": ["1"],
            "materiels_it-0-os_famille": ["5"],
            "materiels_it-0-os_version": ["010203"],
            "materiels_it-0-description": [""],
            "materiels_it-0-DELETE": [""],
            "materiels_it-1-id": [""],  # ajout d'un matériel
            "materiels_it-1-systeme": ["1"],
            "materiels_it-1-fonction": ["1"],
            "materiels_it-1-marque": ["big bg"],
            "materiels_it-1-modele": ["koulos"],
            "materiels_it-1-nombre": ["2"],
            "materiels_it-1-os_famille": ["10"],
            "materiels_it-1-os_version": ["ygy"],
            "materiels_it-1-description": [""],
            "materiels_it-1-DELETE": [""],
            # le formset pour les matériels divers liés
            "materiels_ot-TOTAL_FORMS": ["1"],
            "materiels_ot-INITIAL_FORMS": ["1"],
            "materiels_ot-MIN_NUM_FORMS": ["0"],
            "materiels_ot-MAX_NUM_FORMS": ["1000"],
            "materiels_ot-0-id": ["1"],
            "materiels_ot-0-systeme": ["1"],
            "materiels_ot-0-type": ["11"],
            "materiels_ot-0-marque": ["energy mix"],
            "materiels_ot-0-modele": ["nrj pro max"],
            "materiels_ot-0-nombre": ["2"],
            "materiels_ot-0-firmware": ["456"],  # changement
            "materiels_ot-0-cortec": [""],
            "materiels_ot-0-description": [""],
            "materiels_ot-0-DELETE": [""],
            # le formset pour les licences liées
            "licences-TOTAL_FORMS": ["1"],
            "licences-INITIAL_FORMS": ["1"],
            "licences-MIN_NUM_FORMS": ["0"],
            "licences-MAX_NUM_FORMS": ["1000"],
            "licences-0-id": ["1"],
            "licences-0-systeme": ["1"],
            "licences-0-editeur": ["EduSoft"],
            "licences-0-logiciel": ["Adibou"],
            "licences-0-version": ["2000 NT"],
            "licences-0-licence": ["0000"],
            "licences-0-date_fin": ["07/07/2077"],
            "licences-0-description": [""],
            "licences-0-DELETE": ["1"],
        }
        response = self.client.post(
            reverse("inventaire:systemes_modification", args="1"),
            data=data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/systemes_details.html")
        # le S2I et ses éléments liés ont bien été enregistrés
        self.assertEqual(SystemeIndustriel.objects.count(), 2)
        self.assertEqual(MaterielOrdinateur.objects.count(), 2)
        self.assertEqual(MaterielEffecteur.objects.count(), 1)
        self.assertEqual(LicenceLogiciel.objects.count(), 0)
        # vérification des modifications
        s: SystemeIndustriel = SystemeIndustriel.objects.get(pk=1)
        self.assertEqual(s.nom, "chargeur iphone V2")
        self.assertEqual(s.environnement, SystemeIndustriel.Environnement.OPS)
        self.assertQuerySetEqual(s.fonctions_metiers.all(), FonctionsMetier.objects.filter(pk=1))
        self.assertEqual(s.numero_gtp, "inutile pour les S2I")
        self.assertEqual(s.homologation_responsable, SystemeIndustriel.ResponsableHomologation.SGA)
        self.assertEqual(s.homologation_fin, date(2026, 5, 1))
        self.assertEqual(s.date_maintenance, date(2024, 2, 11))
        self.assertEqual(s.systemes_connectes.count(), 1)
        self.assertEqual(Interconnexion.objects.get(pk=1).type_liaison, Interconnexion.Liaison.BLUETOOTH)
        self.assertEqual(Interconnexion.objects.get(pk=2).type_liaison, Interconnexion.Liaison.BLUETOOTH)  # symétrique
        o1: MaterielOrdinateur = MaterielOrdinateur.objects.get(pk=1)
        o2: MaterielOrdinateur = MaterielOrdinateur.objects.get(pk=2)
        self.assertEqual(o1.modele, "aspir' data 2020")
        self.assertEqual(o2.systeme, s)
        self.assertEqual(o2.marque, "big bg")
        e: MaterielEffecteur = MaterielEffecteur.objects.get(pk=1)
        self.assertEqual(e.firmware, "456")
        self.assertQuerysetEqual(LicenceLogiciel.objects.filter(systeme=s), [])


@tag("views", "views-systemes", "views-systemes-suppression")
class SystemesSuppressionViewTest(TestCase):
    """Classe de test de la vue de la suppression d'un S2I"""

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
        # ajout de domaine métiers
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

    def setUp(self) -> None:
        # Un système sur la zone AMS
        SystemeIndustriel.objects.create(
            pk=1,
            localisation=Localisation.objects.get(pk=1),
            nom="chaussette chauffante",
            environnement=SystemeIndustriel.Environnement.OPS,
            domaine_metier=DomaineMetier.objects.get(pk=1),
        )

    def tearDown(self) -> None:
        self.client.logout()

    def test_suppression_anonyme(self):
        """Un utilisateur non connecté sera redirigé vers la page de login"""
        response = self.client.get(reverse("inventaire:systemes_suppression", args="1"))
        url_attendu = reverse("inventaire:login") + "?next=" + reverse("inventaire:systemes_suppression", args="1")
        self.assertRedirects(response, url_attendu)

    def test_suppression_connecte_ams_systeme_ams_get(self):
        """Un utilisateur ayant les droits de modification 'ams' pourra afficher la page de suppression"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:systemes_suppression", args="1"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/systemes_suppression.html")

    def test_suppression_connecte_rvc_systeme_ams_get(self):
        """Un utilisateur ayant les droits de modification 'rvc' ne pourra pas afficher la page de suppression"""
        self.client.force_login(self.user_rvc)
        response = self.client.get(reverse("inventaire:systemes_suppression", args="1"))
        self.assertEqual(response.status_code, 404)

    def test_suppression_connecte_ams_systeme_ams_post(self):
        """Un utilisateur ayant les droits de modification 'ams' pourra supprimer un système dans cette zone"""
        self.client.force_login(self.user_ams)
        data = {}
        response = self.client.post(
            reverse("inventaire:systemes_suppression", args="1"),
            data=data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/systemes_recherche.html")
        # le S2I a bien été mis à la corbeille
        self.assertEqual(SystemeIndustriel.objects.count(), 1)
        s: SystemeIndustriel = SystemeIndustriel.objects.get(pk=1)
        self.assertEqual(s.fiche_corbeille, True)


@tag("views", "views-systemes", "views-systemes-details")
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

        # deux systèmes sur la zone AMS
        Localisation.objects.create(
            pk=1,
            zone_usid=ZoneUsid.AMS,
            nom_ville="Angers",
            nom_quartier="Roseraie",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        ContratMaintenance.objects.create(
            pk=1,
            zone_usid=ZoneUsid.AMS,
            numero_marche="2022AMSCAC00001",
            date_fin=date(2028, 2, 1),
            nom_societe="repar'tout",
            nom_poc="guigui bricolo",
            est_actif=True,
        )
        # ajout de domaine et fonctions métiers
        DomaineMetier.objects.create(
            pk=1,
            nom="énergie électrique",
            code="EE",
            coeff_criticite=3,
        )
        DomaineMetier.objects.create(
            pk=2,
            nom="autre",
            code="AU",
            coeff_criticite=1,
        )
        FonctionsMetier.objects.create(
            pk=1,
            domaine=DomaineMetier.objects.get(pk=1),
            nom="distribution d'énergie électrique",
            code="DEE",
        )
        FonctionsMetier.objects.create(
            pk=2,
            domaine=DomaineMetier.objects.get(pk=1),
            nom="conversion d'énergie électrique",
            code="CEE",
        )
        # système numéro 1 (le principal, bien rempli)
        SystemeIndustriel.objects.create(
            pk=1,
            localisation=Localisation.objects.get(pk=1),
            contrat_mcs=ContratMaintenance.objects.get(pk=1),
            nom="chargeur iphone",
            environnement=SystemeIndustriel.Environnement.CYB,
            domaine_metier=DomaineMetier.objects.get(pk=1),
            numero_gtp="123456789",
            homologation_fin=date(2025, 5, 10),
            homologation_classe=SystemeIndustriel.ClasseHomologation.C1,
            sauvegarde_config=date(2020, 3, 25),
            sauvegarde_donnees=date(2020, 3, 25),
            sauvegarde_comptes=date(2023, 2, 11),
            date_maintenance=date(2023, 2, 11),
            description="bien caché au fond du bâtiment",
        )
        SystemeIndustriel.objects.get(pk=1).fonctions_metiers.add(
            FonctionsMetier.objects.get(pk=1),
            FonctionsMetier.objects.get(pk=2),
        )
        MaterielOrdinateur.objects.create(
            pk=1,
            systeme=SystemeIndustriel.objects.get(pk=1),
            fonction=MaterielOrdinateur.Fonction.MAINT,
            marque="pas du tout la NSA",
            modele="aspir' data 2000",
            os_famille=MaterielOrdinateur.FamilleOs.WIN_P_10,
        )
        MaterielEffecteur.objects.create(
            pk=1,
            systeme=SystemeIndustriel.objects.get(pk=1),
            type=MaterielEffecteur.Type.ONDULEUR,
            marque="energy mix",
            modele="nrj pro max",
            nombre=2,
        )
        LicenceLogiciel.objects.create(
            pk=1,
            systeme=SystemeIndustriel.objects.get(pk=1),
            editeur="EduSoft",
            logiciel="Adibou",
            version="2000 NT",
            licence="0000",
            date_fin=date(2077, 7, 7),
        )
        # système numéro 2 et 3 (remplis au minimum)
        SystemeIndustriel.objects.create(
            pk=2,
            localisation=Localisation.objects.get(pk=1),
            nom="chaussette chauffante",
            environnement=SystemeIndustriel.Environnement.OPS,
            domaine_metier=DomaineMetier.objects.get(pk=2),
        )
        SystemeIndustriel.objects.create(
            pk=3,
            localisation=Localisation.objects.get(pk=1),
            nom="gant chauffant",
            environnement=SystemeIndustriel.Environnement.OPS,
            domaine_metier=DomaineMetier.objects.get(pk=2),
        )
        # système numéro 4 (dans la corbeille)
        SystemeIndustriel.objects.create(
            pk=5,
            localisation=Localisation.objects.get(pk=1),
            nom="dans la corbeille",
            environnement=SystemeIndustriel.Environnement.AUTRE,
            domaine_metier=DomaineMetier.objects.get(pk=1),
            fiche_corbeille=True,
        )
        # interconnexion entre le système principal et les secondaires de la zone AMS
        SystemeIndustriel.objects.get(pk=1).systemes_connectes.add(
            SystemeIndustriel.objects.get(pk=2),
            through_defaults={"type_reseau": Interconnexion.Reseau.NP_C, "type_liaison": Interconnexion.Liaison.WIFI},
        )
        SystemeIndustriel.objects.get(pk=1).systemes_connectes.add(
            SystemeIndustriel.objects.get(pk=3),
            through_defaults={"type_reseau": Interconnexion.Reseau.NP_C, "type_liaison": Interconnexion.Liaison.WIFI},
        )
        # un système dans la zone RVC
        Localisation.objects.create(
            pk=2,
            zone_usid=ZoneUsid.RVC,
            nom_ville="Rennes",
            nom_quartier="Maurepas",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        SystemeIndustriel.objects.create(
            pk=4,
            localisation=Localisation.objects.get(pk=2),
            nom="enceinte bluetooth",
            environnement=SystemeIndustriel.Environnement.AUTRE,
            domaine_metier=DomaineMetier.objects.get(pk=2),
        )

    def tearDown(self) -> None:
        self.client.logout()

    def test_details_anonyme(self):
        """Un utilisateur non connecté sera redirigé vers la page de login"""
        response = self.client.get(reverse("inventaire:systemes_details", args="1"))
        url_attendu = reverse("inventaire:login") + "?next=" + reverse("inventaire:systemes_details", args="1")
        self.assertRedirects(response, url_attendu)

    def test_details_connecte_ams_systeme_ams(self):
        """Un utilisateur ayant les droits sur la zone ams verra ses 3 systèmes"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:systemes_details", args="1"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/systemes_details.html")
        response = self.client.get(reverse("inventaire:systemes_details", args="2"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/systemes_details.html")
        response = self.client.get(reverse("inventaire:systemes_details", args="3"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/systemes_details.html")
        response = self.client.get(reverse("inventaire:systemes_details", args="5"))  # dans la corbeille
        self.assertEqual(response.status_code, 404)

    def test_details_connecte_ams_systeme_rvc(self):
        """Un utilisateur ayant les droits sur la zone ams ne verra pas le système n°3 (zone rvc)"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:systemes_details", args="4"))
        self.assertEqual(response.status_code, 404)

    def test_details_affichage_systeme(self):
        """Un utilisateur verra toutes les informations pertinentes de son système"""
        self.client.force_login(self.user_ams)
        response = self.client.get(reverse("inventaire:systemes_details", args="1"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["systeme"],
            SystemeIndustriel.objects.get(pk=1),
        )
        self.assertQuerysetEqual(
            response.context["ordis"],
            MaterielOrdinateur.objects.filter(pk=1),
        )
        self.assertQuerysetEqual(
            response.context["effecteurs"],
            MaterielEffecteur.objects.filter(pk=1),
        )
        self.assertQuerysetEqual(
            response.context["licences"],
            LicenceLogiciel.objects.filter(pk=1),
        )
        self.assertQuerysetEqual(
            response.context["interconnexions"],
            Interconnexion.objects.filter(systeme_from=1).order_by("systeme_to__localisation", "systeme_to__nom"),
        )
