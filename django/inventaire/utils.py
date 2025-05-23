"""Définition de diverses fonctions utiles pour l'inventaire"""

from enum import IntEnum

from django.core.management import call_command
from pydantic import BaseModel

from inventaire.models import ZoneUsid


class DomainesMetiersOfficiels:
    """Les domaines métiers et leurs fonctions sont fixés par une note et énumérés ici"""

    _nom_gtc = "gestion technique centralisée"  # la GTC revenant pour tous les domaines, on l'orthographie ici
    _code_gtc = "GTC"
    GT = {
        "code": "GT",
        "nom": "gestion technique",
        "coeff": 2,
        "fonctions": [
            {"code": "GTB", "nom": "gestion technique bâtimentaire", "coeff": 1},
            {"code": "GTS", "nom": "gestion technique de site", "coeff": 2},
        ],
    }
    SI = {
        "code": "SI",
        "nom": "sécurité incendie",
        "coeff": 3,
        "fonctions": [
            {"code": "DIN", "nom": "détection incendie", "coeff": 1},
            {"code": "DEI", "nom": "détection et extinction incendie", "coeff": 2},
            {"code": _code_gtc, "nom": _nom_gtc, "coeff": 1},
        ],
    }
    PS = {
        "code": "PS",
        "nom": "protection de site",
        "coeff": 4,
        "fonctions": [
            {"code": "CA", "nom": "contrôle d'accès", "coeff": 3},
            {"code": "DI", "nom": "détection d'intrusion", "coeff": 3},
            {"code": "VS", "nom": "vidéo surveillance", "coeff": 3},
            {"code": _code_gtc, "nom": _nom_gtc, "coeff": 1},
        ],
    }
    CVC = {
        "code": "CVC",
        "nom": "chauffage, ventilation et climatisation",
        "coeff": 3,
        "fonctions": [
            {"code": "CHA", "nom": "chauffage", "coeff": 1},
            {"code": "ECS", "nom": "eau chaude sanitaire", "coeff": 1},
            {"code": "ECT", "nom": "eau chaude technique", "coeff": 2},
            {"code": "CLI", "nom": "climatisation (confort)", "coeff": 1},
            {"code": "FRI", "nom": "climatisation et froid industriel", "coeff": 3},
            {"code": "VT", "nom": "ventilation et traitement d'air (confort)", "coeff": 1},
            {"code": "VTI", "nom": "ventilation et traitement d'air industriel", "coeff": 3},
            {"code": _code_gtc, "nom": _nom_gtc, "coeff": 1},
        ],
    }
    GF = {
        "code": "GF",
        "nom": "gestion des fluides",
        "coeff": 2,
        "fonctions": [
            {"code": "TF", "nom": "traitement de fluides", "coeff": 2},
            {"code": "PF", "nom": "production de fluides", "coeff": 2},
            {"code": "DF", "nom": "distribution de fluides", "coeff": 2},
            {"code": _code_gtc, "nom": _nom_gtc, "coeff": 1},
        ],
    }
    MA = {
        "code": "MA",
        "nom": "manutention",
        "coeff": 1,
        "fonctions": [
            {"code": "LI", "nom": "levage industriel", "coeff": 1},
            {"code": "ASC", "nom": "ascenseur", "coeff": 1},
            {"code": _code_gtc, "nom": _nom_gtc, "coeff": 1},
        ],
    }
    EN = {
        "code": "EN",
        "nom": "entretien naval",
        "coeff": 3,
        "fonctions": [
            {"code": "MAE", "nom": "assèchement (station de pompage)", "coeff": 3},
            {"code": "MAS", "nom": "maintien à sec (porte de bassin)", "coeff": 3},
            {"code": "REF", "nom": "réfrigération (arrosage de coque)", "coeff": 2},
            {"code": _code_gtc, "nom": _nom_gtc, "coeff": 1},
        ],
    }
    SO = {
        "code": "SO",
        "nom": "sonorisation",
        "coeff": 1,
        "fonctions": [
            {"code": "SO", "nom": "sonorisation", "coeff": 1},
            {"code": _code_gtc, "nom": _nom_gtc, "coeff": 1},
        ],
    }
    EE = {
        "code": "EE",
        "nom": "énergie électrique",
        "coeff": 3,
        "fonctions": [
            {"code": "PEE", "nom": "production d'énergie électrique", "coeff": 3},
            {"code": "CEE", "nom": "conversion d'énergie électrique", "coeff": 2},
            {"code": "TEE", "nom": "transformation d'énergie électrique", "coeff": 2},
            {"code": "DEE", "nom": "distribution d'énergie électrique", "coeff": 2},
            {"code": "SEE", "nom": "stockage d'énergie électrique", "coeff": 2},
            {"code": "ECL", "nom": "éclairage", "coeff": 1},
            {"code": _code_gtc, "nom": _nom_gtc, "coeff": 1},
        ],
    }
    AU = {
        "code": "AU",
        "nom": "autre domaine métier",
        "coeff": 1,
        "fonctions": [
            {"code": "AUT", "nom": "autre fonction métier", "coeff": 1},
            {"code": _code_gtc, "nom": _nom_gtc, "coeff": 1},
        ],
    }

    def __init__(self):
        """Initialisation de l'objet"""
        self.tous_domaines = self._enum_domaines()
        self.fonctions = self._enum_fonctions_par_domaines()

    def _enum_domaines(self) -> list:
        """Renvoi tous les domaines métiers sous forme de liste"""
        return [self.GT, self.SI, self.PS, self.CVC, self.GF, self.MA, self.EN, self.SO, self.EE, self.AU]

    def _enum_fonctions_par_domaines(self) -> dict:
        """Renvoi tous les codes de fonctions métiers associées à un code de domaine métier"""

        return {
            self.GT["code"]: [x["code"] for x in self.GT["fonctions"]],
            self.SI["code"]: [x["code"] for x in self.SI["fonctions"]],
            self.PS["code"]: [x["code"] for x in self.PS["fonctions"]],
            self.CVC["code"]: [x["code"] for x in self.CVC["fonctions"]],
            self.GF["code"]: [x["code"] for x in self.GF["fonctions"]],
            self.MA["code"]: [x["code"] for x in self.MA["fonctions"]],
            self.EN["code"]: [x["code"] for x in self.EN["fonctions"]],
            self.SO["code"]: [x["code"] for x in self.SO["fonctions"]],
            self.EE["code"]: [x["code"] for x in self.EE["fonctions"]],
            self.AU["code"]: [x["code"] for x in self.AU["fonctions"]],
        }

    def affiche_maximum(self) -> tuple:
        """Permet de calculer dans le fichier 'inventaire.models' dans le modèle d'un S2I, la valeur maximum
        que prendra la criticité. Ainsi, il sera possible de la ramener en pourcentage pour plus de lisibilité.

        Renvoi:
            un tuple ( max de la somme des coeff des fct, coeff maximal d'un domaine )
        """
        return (
            max([sum([y["coeff"] for y in x["fonctions"]]) for x in self.tous_domaines]),
            max([x["coeff"] for x in self.tous_domaines]),
        )


class ModeRestriction(IntEnum):
    CONSULTATION = 0
    MODIFICATION = 1


def restreint_zone(user, mode: ModeRestriction) -> list:
    """Renvoi la liste des zones que l'utilisateur peut consulter"""
    zone = []
    for k in ZoneUsid:
        if mode is ModeRestriction.CONSULTATION:
            if user.has_perm(f"inventaire.consult_{k.value}"):
                zone.append(k.value)
        elif mode is ModeRestriction.MODIFICATION:
            if user.has_perm(f"inventaire.modif_{k.value}"):
                zone.append(k.value)
    return zone


class CeleryResultStatus(IntEnum):
    OK = 0
    MINOR = 1
    MAJOR = 2
    FATAL = 3
    CRASH = 4


class CeleryResultMessageType(IntEnum):
    SUCCESS = 0
    INFO = 1
    ERROR = 2


class CeleryResult(BaseModel):
    status: CeleryResultStatus
    messages: list[tuple[CeleryResultMessageType, str]]

    def __repr__(self):
        return "CeleryResult({}, [...({}, {})])".format(
            self.status.name, self.messages[-1][0].name, self.messages[-1][1]
        )
