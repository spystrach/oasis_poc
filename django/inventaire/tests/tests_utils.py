"""Définition des tests unitaires de l'inventaire pour les objets utilitaires"""

import logging
from tempfile import NamedTemporaryFile

from django.contrib.auth.models import User, Permission
from django.test import TestCase, tag

from inventaire.utils import (
    DomainesMetiersOfficiels,
    ModeRestriction,
    restreint_zone,
)


logger = logging.getLogger(__name__)


@tag("utils", "utils-domaines")
class DomaineMetiersOfficielsTest(TestCase):
    """Classe de test de la classe répertoriant les domaines métiers officiels du CETID"""

    @classmethod
    def setUpTestData(cls):
        cls.dmo = DomainesMetiersOfficiels()

    def test_enum_domaines(self):
        """Liste contenant tous les domaines métiers officiels"""
        self.assertEqual(len(self.dmo.tous_domaines), 10)

    def test_enum_fonctions_par_domaines(self):
        """Dictionnaire contenant toutes les fonctions pour un domaine métier"""
        self.assertDictEqual(
            self.dmo.fonctions,
            {
                "GT": ["GTB", "GTS"],
                "SI": ["DIN", "DEI", "GTC"],
                "PS": ["CA", "DI", "VS", "GTC"],
                "CVC": ["CHA", "ECS", "ECT", "CLI", "FRI", "VT", "VTI", "GTC"],
                "GF": ["TF", "PF", "DF", "GTC"],
                "MA": ["LI", "ASC", "GTC"],
                "EN": ["MAE", "MAS", "REF", "GTC"],
                "SO": ["SO", "GTC"],
                "EE": ["PEE", "CEE", "TEE", "DEE", "SEE", "ECL", "GTC"],
                "AU": ["AUT", "GTC"],
            },
        )

    def test_affiche_maximum(self):
        """Calcul de la la valeur maximum atteinte par les coefficients officiels"""
        self.assertTupleEqual(
            self.dmo.affiche_maximum(),
            (13, 4),
        )


@tag("utils", "utils-zones")
class RestreintZoneTest(TestCase):
    """Classe de test de la fonction permettant de donner les USID dont un utilisateur à accès"""

    @classmethod
    def setUpTestData(cls):
        # un utilisateur de type RSSI-A
        cls.user_ams = User.objects.create_user(
            username="ams",
            password="ams123",
        )
        cls.user_ams.user_permissions.add(Permission.objects.get(codename="consult_AMS"))
        cls.user_ams.user_permissions.add(Permission.objects.get(codename="modif_AMS"))
        # un utilisateur de type BSSI
        cls.user_bssi = User.objects.create_user(
            username="bssi",
            password="bssi123",
        )
        cls.user_bssi.user_permissions.add(Permission.objects.get(codename="consult_AMS"))
        cls.user_bssi.user_permissions.add(Permission.objects.get(codename="consult_RVC"))
        cls.user_bssi.user_permissions.add(Permission.objects.get(codename="consult_CBG"))

    def test_restreint_rssi_consultation(self):
        """Obtient les codes des zones consultables pour l'utilisateur de type RSSI"""
        self.assertListEqual(
            restreint_zone(self.user_ams, ModeRestriction.CONSULTATION),
            ["AMS"],
        )

    def test_restreint_rssi_modification(self):
        """Obtient les codes des zones modifiables pour l'utilisateur de type RSSI"""
        self.assertListEqual(
            restreint_zone(self.user_ams, ModeRestriction.MODIFICATION),
            ["AMS"],
        )

    def test_restreint_bssi_consultation(self):
        """Obtient les codes des zones consultations pour l'utilisateur de type BSSI"""
        self.assertListEqual(
            restreint_zone(self.user_bssi, ModeRestriction.CONSULTATION),
            ["AMS", "CBG", "RVC"],
        )

    def test_restreint_bssi_modification(self):
        """Obtient les codes des zones modifications pour l'utilisateur de type BSSI"""
        self.assertListEqual(
            restreint_zone(self.user_bssi, ModeRestriction.MODIFICATION),
            [],
        )
