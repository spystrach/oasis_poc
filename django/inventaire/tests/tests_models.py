"""Définition des tests unitaires de l'inventaire pour les modèles"""

import logging
from datetime import date
from packaging.version import parse as parse_version

from django.db import connection
from django.test import TestCase, tag

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
from inventaire.utils import DomainesMetiersOfficiels


logger = logging.getLogger(__name__)


@tag("models", "models-localisations")
class LocalisationTest(TestCase):
    """Classe de test pour le modèle Localisation"""

    @classmethod
    def setUpTestData(cls):
        cls.z1 = Localisation(
            zone_usid=ZoneUsid.RVC,
            nom_ville="Rennes",
            nom_quartier="Blosne",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        cls.z2 = Localisation(
            zone_usid=ZoneUsid.RVC,
            nom_ville="Rennes",
            nom_quartier="Maurepas",
            zone_quartier="point de deal n°1",
            protection=Localisation.Protection.ZDHS,
            sensibilite=Localisation.Sensibilite.VITALE,
        )

    def test_str_court(self):
        """Affichage d'un lieu avec le champ zone_quartier vide"""
        self.assertEqual(
            str(self.z1),
            "Rennes - Blosne",
        )

    def test_str_long(self):
        """Affichage d'un lieu avec le champ zone_quartier rempli"""
        self.assertEqual(
            str(self.z2),
            "Rennes - Maurepas - point de deal n°1",
        )


@tag("models", "models-contrat")
class ContratMaintenanceTest(TestCase):
    """Classe de test pour le modèle ContratMaintenance"""

    @classmethod
    def setUpTestData(cls):
        cls.c1 = ContratMaintenance(
            zone_usid=ZoneUsid.RVC,
            numero_marche="2022RNSSAI00001",
            date_fin=date(2020, 1, 1),
            nom_societe="cotorep",
            nom_poc="jean jean",
            est_actif=True,
        )

    def test_str(self):
        """Affichage d'un contrat de maintenance"""
        self.assertEqual(
            str(self.c1),
            "Contrat avec cotorep (2022RNSSAI00001)",
        )


@tag("models", "models-domaines")
class DomaineMetierTest(TestCase):
    """Classe de test pour le modèle DomaineMetier"""

    @classmethod
    def setUpTestData(cls):
        cls.d1 = DomaineMetier(
            nom="gestion technique",
        )

    def test_str(self):
        """Affichage d'un domaine métier"""
        self.assertEqual(
            str(self.d1),
            "gestion technique",
        )


@tag("models", "models-fonctions")
class FonctionMetierTest(TestCase):
    """Classe de test pour le modèle FonctionMetier"""

    @classmethod
    def setUpTestData(cls):
        DomaineMetier.objects.create(
            pk=1,
            nom="Gestion technique",
            code="GT",
        )
        cls.f1 = FonctionsMetier(
            domaine=DomaineMetier.objects.get(pk=1),
            nom="gestion technique bâtimentaire",
        )

    def test_str(self):
        """Affichage d'une fonction associée à un domaine métier"""
        self.assertEqual(
            str(self.f1),
            "gestion technique bâtimentaire",
        )


@tag("models", "models-systemes")
class SystemeIndustrielTest(TestCase):
    """Classe de test pour le modèle SystemeIndustriel"""

    @classmethod
    def setUpTestData(cls):
        Localisation.objects.create(
            pk=1,
            zone_usid=ZoneUsid.RVC,
            nom_ville="Rennes",
            nom_quartier="Blosne",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        Localisation.objects.create(
            pk=2,
            zone_usid=ZoneUsid.RVC,
            nom_ville="Rennes",
            nom_quartier="Maurepas",
            zone_quartier="point de deal n°1",
            protection=Localisation.Protection.ZDHS,
            sensibilite=Localisation.Sensibilite.VITALE,
        )
        ContratMaintenance.objects.create(
            pk=1,
            zone_usid=ZoneUsid.RVC,
            numero_marche="2022RNSSAI00001",
            date_fin=date(2032, 10, 25),
            nom_societe="cotorep",
            nom_poc="jean jean",
            est_actif=True,
        )
        DomaineMetier.objects.create(
            pk=1,
            nom=DomainesMetiersOfficiels.EE["nom"],
            code=DomainesMetiersOfficiels.EE["code"],
            coeff_criticite=DomainesMetiersOfficiels.EE["coeff"],
        )
        DomaineMetier.objects.create(
            pk=2,
            nom=DomainesMetiersOfficiels.PS["nom"],
            code=DomainesMetiersOfficiels.PS["code"],
            coeff_criticite=DomainesMetiersOfficiels.PS["coeff"],
        )
        FonctionsMetier.objects.create(
            pk=1,
            domaine=DomaineMetier.objects.get(pk=1),
            nom=DomainesMetiersOfficiels.EE["fonctions"][0]["nom"],  # production d'énergie électrique
            code=DomainesMetiersOfficiels.EE["fonctions"][0]["code"],
            coeff_criticite=DomainesMetiersOfficiels.EE["fonctions"][0]["coeff"],
        )
        FonctionsMetier.objects.create(
            pk=2,
            domaine=DomaineMetier.objects.get(pk=1),
            nom=DomainesMetiersOfficiels.EE["fonctions"][1]["nom"],  # conversion d'énergie électrique
            code=DomainesMetiersOfficiels.EE["fonctions"][1]["code"],
            coeff_criticite=DomainesMetiersOfficiels.EE["fonctions"][1]["coeff"],
        )
        FonctionsMetier.objects.create(
            pk=4,
            domaine=DomaineMetier.objects.get(pk=1),
            nom=DomainesMetiersOfficiels.EE["fonctions"][6]["nom"],  # gtc
            code=DomainesMetiersOfficiels.EE["fonctions"][6]["code"],
            coeff_criticite=DomainesMetiersOfficiels.EE["fonctions"][6]["coeff"],
        )
        FonctionsMetier.objects.create(
            pk=3,
            domaine=DomaineMetier.objects.get(pk=1),
            nom=DomainesMetiersOfficiels.PS["fonctions"][0]["nom"],  # contrôle d'accès
            code=DomainesMetiersOfficiels.PS["fonctions"][0]["code"],
            coeff_criticite=DomainesMetiersOfficiels.PS["fonctions"][0]["coeff"],
        )
        SystemeIndustriel.objects.create(
            pk=1,
            localisation=Localisation.objects.get(pk=1),
            contrat_mcs=ContratMaintenance.objects.get(pk=1),
            nom="chargeur iphone",
            environnement=SystemeIndustriel.Environnement.CYB,
            domaine_metier=DomaineMetier.objects.get(pk=1),
            numero_gtp="123456789",
            homologation_classe=SystemeIndustriel.ClasseHomologation.C1,
            homologation_responsable=SystemeIndustriel.ResponsableHomologation.SID,
            homologation_fin=date(2025, 5, 10),
            sauvegarde_config=date(2020, 3, 25),
            sauvegarde_donnees=date(2020, 3, 25),
            sauvegarde_comptes=date(2023, 2, 11),
            date_maintenance=date(2023, 2, 11),
            description="bien caché au fond du bâtiment",
        )
        SystemeIndustriel.objects.get(pk=1).fonctions_metiers.add(
            FonctionsMetier.objects.get(pk=1),
            FonctionsMetier.objects.get(pk=2),
            FonctionsMetier.objects.get(pk=3),
        )
        SystemeIndustriel.objects.create(
            pk=2,
            localisation=Localisation.objects.get(pk=2),
            contrat_mcs=ContratMaintenance.objects.get(pk=1),
            nom="lave voiture",
            environnement=SystemeIndustriel.Environnement.OPS,
            domaine_metier=DomaineMetier.objects.get(pk=2),
            numero_gtp="789456123",
            homologation_classe=SystemeIndustriel.ClasseHomologation.C1,
            homologation_responsable=SystemeIndustriel.ResponsableHomologation.EMA,
            homologation_fin=date(2025, 4, 8),
            sauvegarde_config=date(2020, 6, 24),
            sauvegarde_donnees=date(2020, 6, 24),
            sauvegarde_comptes=date(2023, 3, 7),
            date_maintenance=date(2023, 3, 7),
            description="refaire le plein de gel moussant ASAP",
        )
        SystemeIndustriel.objects.get(pk=2).fonctions_metiers.add(
            FonctionsMetier.objects.get(pk=3),
        )

    def test_str_court(self):
        """Affichage d'un système industriel avec une localisation sans zone_quartier"""
        self.assertEqual(
            str(SystemeIndustriel.objects.get(pk=1)),
            "Rennes - Blosne - chargeur iphone",
        )

    def test_str_long(self):
        """Affichage d'un système industriel avec une localisation avec zone_quartier"""
        self.assertEqual(
            str(SystemeIndustriel.objects.get(pk=2)),
            "Rennes - Maurepas - point de deal n°1 - lave voiture",
        )

    def test_criticite(self):
        """Calcul de la criticité d'un système"""
        self.assertEqual(SystemeIndustriel.objects.get(pk=1).criticite(), 26)
        self.assertEqual(SystemeIndustriel.objects.get(pk=2).criticite(), 16)


@tag("models", "models-interconnexions")
class InterconnexionTest(TestCase):
    """Classe de test pour le modèle Interconnexion"""

    @classmethod
    def setUpTestData(cls):
        Localisation.objects.create(
            pk=1,
            zone_usid=ZoneUsid.RVC,
            nom_ville="Cyr",
            nom_quartier="QG",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        DomaineMetier.objects.create(
            pk=1,
            nom="énergie électrique",
            code="EE",
        )
        SystemeIndustriel.objects.create(
            pk=1,
            localisation=Localisation.objects.get(pk=1),
            nom="slip connecté",
            environnement=SystemeIndustriel.Environnement.AUTRE,
            domaine_metier=DomaineMetier.objects.get(pk=1),
        )
        SystemeIndustriel.objects.create(
            pk=2,
            localisation=Localisation.objects.get(pk=1),
            nom="volet roulant",
            environnement=SystemeIndustriel.Environnement.AUTRE,
            domaine_metier=DomaineMetier.objects.get(pk=1),
        )
        cls.i1 = Interconnexion(
            systeme_from=SystemeIndustriel.objects.get(pk=1),
            systeme_to=SystemeIndustriel.objects.get(pk=2),
            type_reseau=Interconnexion.Reseau.A_C,
            type_liaison=Interconnexion.Liaison.BLUETOOTH,
        )

    def tearDown(self) -> None:
        Interconnexion.objects.all().delete()

    def test_str(self):
        """Affichage d'une interconnexion entre deux systèmes"""
        self.assertEqual(
            str(self.i1),
            "Liaison bluetooth (autre réseau connecté) de [Cyr - QG - slip connecté] vers [Cyr - QG - volet roulant]",
        )

    def test_save(self):
        """Ajout d'une interconnexion entre deux S2I"""
        SystemeIndustriel.objects.get(pk=1).systemes_connectes.add(
            SystemeIndustriel.objects.get(pk=2),
            through_defaults={"type_reseau": Interconnexion.Reseau.A_C, "type_liaison": Interconnexion.Liaison.WIFI},
        )
        self.assertEqual(Interconnexion.objects.count(), 2)
        i1 = Interconnexion.objects.filter(
            systeme_from=SystemeIndustriel.objects.get(pk=1),
            systeme_to=SystemeIndustriel.objects.get(pk=2),
        ).first()
        i2 = Interconnexion.objects.filter(
            systeme_from=SystemeIndustriel.objects.get(pk=2),
            systeme_to=SystemeIndustriel.objects.get(pk=1),
        ).first()
        self.assertEqual(i1.type_reseau, i2.type_reseau)
        self.assertEqual(i1.type_liaison, i2.type_liaison)
        self.assertEqual(i1.protocole, i2.protocole)
        self.assertEqual(i1.description, i2.description)

    def test_delete_ok(self):
        """Suppression d'une interconnexion entre deux S2I (cas normal)"""
        SystemeIndustriel.objects.get(pk=1).systemes_connectes.add(
            SystemeIndustriel.objects.get(pk=2),
            through_defaults={"type_reseau": Interconnexion.Reseau.A_C, "type_liaison": Interconnexion.Liaison.WIFI},
        )
        Interconnexion.objects.get(pk=1).delete()
        self.assertEqual(Interconnexion.objects.count(), 0)

    def test_delete_ko(self):
        """Suppression d'une interconnexion entre deux S2I (cas d'interconnexion orpheline)"""
        # obligation de passer hors de l'ORM pour générer une base de donnée corrompue
        cursor = connection.cursor()
        cursor.execute(
            (
                "INSERT INTO inventaire_interconnexion "
                "(id, type_reseau, type_liaison, protocole, description, systeme_from_id, systeme_to_id) "
                "VALUES (1, 1, 1, 'hello', 'inutile', 1, 2)"
            )
        )
        self.assertEqual(Interconnexion.objects.count(), 1)
        Interconnexion.objects.get(pk=1).delete()
        self.assertEqual(Interconnexion.objects.count(), 0)


@tag("models", "models-ordinateurs")
class MaterielOrdinateurTest(TestCase):
    """Classe de test pour le modèle MaterielOrdinateur"""

    @classmethod
    def setUpTestData(cls):
        Localisation.objects.create(
            pk=1,
            zone_usid=ZoneUsid.OAN,
            nom_ville="Orléans",
            nom_quartier="La Source",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        DomaineMetier.objects.create(
            pk=1,
            nom="énergie électrique",
            code="EE",
        )
        SystemeIndustriel.objects.create(
            pk=1,
            localisation=Localisation.objects.get(pk=1),
            nom="compteur billet",
            environnement=SystemeIndustriel.Environnement.AUTRE,
            domaine_metier=DomaineMetier.objects.get(pk=1),
        )
        cls.o1 = MaterielOrdinateur(
            systeme=SystemeIndustriel.objects.get(pk=1),
            fonction=MaterielOrdinateur.Fonction.MAINT,
            marque="HP",
            modele="MEGA lent 200XP",
            os_famille=MaterielOrdinateur.FamilleOs.WIN_P_XP,
            os_version=parse_version("2710"),
            nombre=1,
        )

    def test_str(self):
        """Affichage d'un matériel ordinateur/serveur"""
        self.assertEqual(str(self.o1), "poste de maintenance (HP) de Orléans - La Source - compteur billet")

    def test_version(self):
        """Fonctionne bien"""
        matos_1 = MaterielOrdinateur(
            systeme=SystemeIndustriel.objects.get(pk=1),
            fonction=MaterielOrdinateur.Fonction.MAINT,
            marque="HP",
            modele="MEGA lent 200XP",
            os_famille=MaterielOrdinateur.FamilleOs.WIN_P_XP,
            os_version=parse_version("2710"),
            nombre=1,
        )
        matos_2 = MaterielOrdinateur(
            systeme=SystemeIndustriel.objects.get(pk=1),
            fonction=MaterielOrdinateur.Fonction.MAINT,
            marque="HP",
            modele="TROP récent pro max",
            os_famille=MaterielOrdinateur.FamilleOs.WIN_P_11,
            os_version=parse_version("22631"),
            nombre=1,
        )
        self.assertLess(matos_1.os_version, matos_2.os_version, "erreur")


@tag("models", "models-effecteurs")
class MaterielEffecteurTest(TestCase):
    """Classe de test pour le modèle MaterielEffecteur"""

    @classmethod
    def setUpTestData(cls):
        Localisation.objects.create(
            pk=1,
            zone_usid=ZoneUsid.OAN,
            nom_ville="Orléans",
            nom_quartier="La Source",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        DomaineMetier.objects.create(
            pk=1,
            nom="énergie électrique",
            code="EE",
        )
        SystemeIndustriel.objects.create(
            pk=1,
            localisation=Localisation.objects.get(pk=1),
            nom="compteur billet",
            environnement=SystemeIndustriel.Environnement.AUTRE,
            domaine_metier=DomaineMetier.objects.get(pk=1),
        )
        cls.e1 = MaterielEffecteur(
            systeme=SystemeIndustriel.objects.get(pk=1),
            type=MaterielEffecteur.Type.AUTOMATE,
            marque="Teuton anark",
            modele="trop cher pour ce que c'est",
            nombre=1,
        )

    def test_str(self):
        """Affichage d'un matériel ordinateur/serveur"""
        self.assertEqual(str(self.e1), "automate (Teuton anark) de Orléans - La Source - compteur billet")


@tag("models", "models-licences")
class LicenceLogicielTest(TestCase):
    """Classe de test pour le modèle LicenceLogiciel"""

    @classmethod
    def setUpTestData(cls):
        Localisation.objects.create(
            pk=1,
            zone_usid=ZoneUsid.OAN,
            nom_ville="Orléans",
            nom_quartier="La Source",
            protection=Localisation.Protection.TM,
            sensibilite=Localisation.Sensibilite.MOINDRE,
        )
        DomaineMetier.objects.create(
            pk=1,
            nom="énergie électrique",
            code="EE",
        )
        SystemeIndustriel.objects.create(
            pk=1,
            localisation=Localisation.objects.get(pk=1),
            nom="compteur billet",
            environnement=SystemeIndustriel.Environnement.AUTRE,
            domaine_metier=DomaineMetier.objects.get(pk=1),
        )
        cls.l1 = LicenceLogiciel(
            systeme=SystemeIndustriel.objects.get(pk=1),
            editeur="Nulosoft",
            logiciel="windaube",
            version="2016 R2",
            licence="1234-5678-9456-1230",
            date_fin=date(2025, 1, 1),
        )

    def test_str(self):
        """Affichage d'un matériel ordinateur/serveur"""
        self.assertEqual(str(self.l1), "windaube (Nulosoft) de Orléans - La Source - compteur billet")
