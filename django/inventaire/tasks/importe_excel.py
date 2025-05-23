"""Permet d'importer les systèmes depuis un fichier excel (version excel 2.X)"""

import logging
from csv import reader
from datetime import datetime
from pathlib import Path
from base64 import b64decode
from tempfile import TemporaryDirectory

from celery import shared_task
from django.db.utils import IntegrityError
from xlsx2csv import Xlsx2csv

from inventaire.models import (
    DomaineMetier,
    FonctionsMetier,
    # LicenceLogiciel,
    Localisation,
    MaterielOrdinateur,
    MaterielEffecteur,
    SystemeIndustriel,
    ZoneUsid,
)
from inventaire.utils import DomainesMetiersOfficiels, CeleryResult, CeleryResultStatus, CeleryResultMessageType


logger = logging.getLogger(__name__)


class ImporteExcelError(Exception):
    pass


class StructureLocalisation:
    """Traduction des informations de localisation du fichier csv vers le modèle Localisation"""

    _zone_usid = 3
    _nom_ville = 4
    _nom_quartier = 5
    _zone_quartier = 6
    _protection = 7
    _sensibilite = 8

    def get_zone_usid(self, ligne: list) -> ZoneUsid:
        """Obtient le champ zone_usid dans le fichier csv"""
        zone = ligne[self._zone_usid].upper()
        if zone == "USID_ANGERS":
            return ZoneUsid.AMS
        elif zone == "USID_AVORD":
            return ZoneUsid.BGA
        elif zone == "USID_BRICY":
            return ZoneUsid.OAN
        elif zone == "USID_CHERBOURG":
            return ZoneUsid.CBG
        elif zone == "USID_EVREUX":
            return ZoneUsid.EVX
        elif zone == "USID_RENNES":
            return ZoneUsid.RVC
        elif zone == "USID_TOURS":
            return ZoneUsid.TRS
        else:
            raise ImporteExcelError("Colonne %s : la zone_usid '%s' est inconnue" % (self._zone_usid + 1, zone))

    def get_nom_ville(self, ligne: list) -> str:
        """Obtient le champ nom_ville dans le fichier csv"""
        return ligne[self._nom_ville].lower().replace("_", "-")

    def get_nom_quartier(self, ligne: list) -> str:
        """Obtient le champ nom_quartier dans le fichier csv"""
        return ligne[self._nom_quartier].lower()

    def get_zone_quartier(self, ligne: list) -> str:
        """Obtient le champ zone_quartier dans le fichier csv"""
        return ligne[self._zone_quartier].lower()

    def get_protection(self, ligne: list) -> Localisation.Protection:
        """Obtient le champ protection dans le fichier csv"""
        protection = ligne[self._protection].upper()
        if protection == "MC":
            return Localisation.Protection.MC
        elif protection == "TM":
            return Localisation.Protection.TM
        elif protection == "ZP":
            return Localisation.Protection.ZP
        elif protection == "ZDHS":
            return Localisation.Protection.ZDHS
        elif protection == "ZR":
            return Localisation.Protection.ZR
        elif protection == "ZNAR":
            return Localisation.Protection.ZNAR
        elif protection == "ZV":
            return Localisation.Protection.ZV
        else:
            raise ImporteExcelError(
                "Colonne %s : le niveau de protection périmétrique '%s' est inconnu"
                % (self._protection + 1, protection)
            )

    def get_sensibilite(self, ligne: list) -> Localisation.Sensibilite:
        """Obtient le champ sensibilite dans le fichier csv"""
        sensibilite = ligne[self._sensibilite].upper()
        if sensibilite == "VITALE":
            return Localisation.Sensibilite.VITALE
        elif sensibilite == "HAUTE":
            return Localisation.Sensibilite.HAUTE
        elif sensibilite == "MOINDRE":
            return Localisation.Sensibilite.MOINDRE
        else:
            raise ImporteExcelError(
                "Colonne %s : le niveau de sensibilité '%s' est inconnu" % (self._sensibilite + 1, sensibilite)
            )


class StructureDomaineMetier:
    """Traduction des informations du système industriel du fichier csv S2I vers le modèle DomaineMetier"""

    _domaine_metier = 10
    _domaines = DomainesMetiersOfficiels()

    def get_domaine_metier(self, ligne: list) -> DomaineMetier:
        """Obtient le champ domaine_metier dans le fichier csv

        Cette fonction se base sur les domaines métiers déclarés dans la commande 'db_metiers'
        """
        code_domaine_metier = ligne[self._domaine_metier].split("_")[0].upper()
        try:
            return DomaineMetier.objects.get(code=code_domaine_metier)
        except DomaineMetier.DoesNotExist:
            raise ImporteExcelError(
                "Colonne %s: l'acronyme du domaine métier '%s' est inconnu"
                % (self._domaine_metier + 1, code_domaine_metier)
            )


class StructureFonctionMetier:
    """Traduction des informations du système industriel du fichier csv S2I vers le modèle FonctionMetier"""

    _nom = 11
    _domaines = DomainesMetiersOfficiels()

    def get_fonctions_metiers(self, ligne: list, domaine=None) -> list[str]:
        """Obtient les champs fonctions_metiers dans le fichier csv"""
        fonctions_metiers = ligne[self._nom].split("(")[-1][:-1].split("-")
        fonctions_a_renvoyer = []
        # nota : le domaine métier est forcément connu, car validé par sa structure dédiée

        for k in fonctions_metiers:
            if k in self._domaines.fonctions.get(domaine, None):
                fonctions_a_renvoyer.append(k)
            else:
                raise ImporteExcelError(
                    "Colonne %s : la fonction de domaine métier '%s' est inconnue ou ne correspond pas au domaine métier inscrit"
                    % (self._nom + 1, k)
                )
        return fonctions_a_renvoyer


class StructureSystemeIndustriel:
    """Traduction des informations du système industriel du fichier csv vers le modèle SystemeIndustriel"""

    _excel_id = 0
    # la localisation est gérée par la StructureLocalisation
    _nom = 1
    _environnement = 9
    # le domaine métier est géré par la StructureDomaineMetier
    # les fonctions métiers sont gérées par la StructureFonctionMetier
    _numero_gtp = 2
    _homologation_fin = 13
    _homologation_classe = 14
    # _homologation_responsable n'est pas présent dans le ficher excel
    _description = 26

    def get_id_excel(self, ligne: list) -> str | None:
        """Obtient le champ de l'ID excel (hors BDD, correspondance entre les onglets)"""
        try:
            return ligne[self._excel_id].lower()
        except IndexError:
            return None

    def get_nom(self, ligne: list) -> str:
        """Obtient le champ nom dans le fichier csv"""
        return ligne[self._nom].lower()

    def get_environnement(self, ligne: list) -> SystemeIndustriel.Environnement:
        """Obtient le champ environnement dans le fichier csv"""
        environnement = ligne[self._environnement].lower()
        if environnement == "autre":
            return SystemeIndustriel.Environnement.AUTRE
        elif environnement == "nucleaire":
            return SystemeIndustriel.Environnement.NUC
        elif environnement == "cyber":
            return SystemeIndustriel.Environnement.CYB
        elif environnement == "operationnel":
            return SystemeIndustriel.Environnement.OPS
        else:
            raise ImporteExcelError(
                "Colonne %s : l'environnement '%s' est inconnu" % (self._environnement + 1, environnement)
            )

    def get_numero_gtp(self, ligne: list) -> str:
        """Obtient le champ numero_gtp dans le fichier csv"""
        return ligne[self._numero_gtp]

    def get_homologation_fin(self, ligne: list) -> None | datetime:
        """Obtient le champ homologation_fin dans le fichier csv"""
        homologation_fin = ligne[self._homologation_fin]
        if homologation_fin:
            try:
                return datetime.strptime(homologation_fin, "%d/%M/%Y")
            except ValueError:
                raise ImporteExcelError(
                    "Colonne %s : impossible de convertir la date '%s'" % (self._homologation_fin + 1, homologation_fin)
                )
        else:
            return None

    def get_homologation_classe(self, ligne: list) -> None | SystemeIndustriel.ClasseHomologation:
        """Obtient le champ homologation_classe dans le fichier csv"""
        homologation_classe = ligne[self._homologation_classe].lower()
        if not homologation_classe or homologation_classe == "?":
            return SystemeIndustriel.ClasseHomologation.NC
        elif homologation_classe == "sommaire (1)":
            return SystemeIndustriel.ClasseHomologation.C1
        elif homologation_classe == "simplifiée (2)":
            return SystemeIndustriel.ClasseHomologation.C2
        elif homologation_classe == "standard (3)":
            return SystemeIndustriel.ClasseHomologation.C3
        else:
            raise ImporteExcelError(
                "Colonne %s : la classe d'homologation '%s' est inconnue"
                % (self._homologation_classe + 1, homologation_classe)
            )

    def get_description(self, ligne: list) -> str:
        """Obtient le champ description dans le fichier csv"""
        return ligne[self._description]


class StructureMaterielOrdinateur:
    """Traduction des informations des ordinateurs du fichier csv vers le modèle MaterielOrdinateur"""

    _excel_id = 0
    _fonction = 8
    _marque = 9
    _modele = 10
    _os_famille = 11
    _os_version = 12
    _nombre = 13
    _description = 14

    def get_id_excel(self, ligne: list) -> str:
        """Obtient le champ de l'ID excel (hors BDD, correspondance entre les onglets)"""
        return ligne[self._excel_id].lower()

    def get_fonction(self, ligne: list) -> MaterielOrdinateur.Fonction:
        """Obtient le champ fonction dans le fichier csv"""
        fonction = ligne[self._fonction].lower()
        if fonction == "poste de maintenance":
            return MaterielOrdinateur.Fonction.MAINT
        elif fonction == "poste de supervision":
            return MaterielOrdinateur.Fonction.SUPER
        elif fonction == "poste d'administration" or fonction == "poste d’administration":
            return MaterielOrdinateur.Fonction.ADMIN
        elif (
            fonction == "poste de supervision et d'administration"
            or fonction == "poste de supervision et d’administration"
        ):
            return MaterielOrdinateur.Fonction.SU_AD
        elif fonction == "serveur de temps":
            return MaterielOrdinateur.Fonction.TEMPS
        elif fonction == "serveur de fichier":
            return MaterielOrdinateur.Fonction.FICHI
        elif fonction == "serveur de base de données":
            return MaterielOrdinateur.Fonction.BASED
        elif fonction == "serveur d'annuaire" or fonction == "serveur d’annuaire":
            return MaterielOrdinateur.Fonction.ANNUA
        else:
            raise ImporteExcelError("Colonne %s : la fonction '%s' est inconnue" % (self._fonction + 1, fonction))

    def get_marque(self, ligne: list) -> str:
        """Obtient le champ marque dans le fichier csv"""
        return ligne[self._marque].lower()

    def get_modele(self, ligne: list) -> str:
        """Obtient le champ modele dans le fichier csv"""
        return ligne[self._modele].lower()

    def get_os_famille(self, ligne: list) -> MaterielOrdinateur.FamilleOs:
        """Obtient le champ os_famille dans le fichier csv"""
        os_famille = ligne[self._os_famille].lower()
        if os_famille == "autre":
            return MaterielOrdinateur.FamilleOs.AUTRE
        elif os_famille == "windows xp":
            return MaterielOrdinateur.FamilleOs.WIN_P_XP
        elif os_famille == "windows vista":
            return MaterielOrdinateur.FamilleOs.WIN_P_VISTA
        elif os_famille == "windows 7":
            return MaterielOrdinateur.FamilleOs.WIN_P_7
        elif os_famille == "windows 8":
            return MaterielOrdinateur.FamilleOs.WIN_P_8
        elif os_famille == "windows 10":
            return MaterielOrdinateur.FamilleOs.WIN_P_10
        elif os_famille == "windows 11":
            return MaterielOrdinateur.FamilleOs.WIN_P_11
        elif os_famille == "windows serveur nt":
            return MaterielOrdinateur.FamilleOs.WIN_S_NT
        elif os_famille == "windows serveur 2000":
            return MaterielOrdinateur.FamilleOs.WIN_S_00
        elif os_famille == "windows serveur 2003":
            return MaterielOrdinateur.FamilleOs.WIN_S_03
        elif os_famille == "windows serveur 2008":
            return MaterielOrdinateur.FamilleOs.WIN_S_081
        elif os_famille == "windows serveur 2008 r2":
            return MaterielOrdinateur.FamilleOs.WIN_S_082
        elif os_famille == "windows serveur 2012":
            return MaterielOrdinateur.FamilleOs.WIN_S_121
        elif os_famille == "windows serveur 2012 r2":
            return MaterielOrdinateur.FamilleOs.WIN_S_122
        elif os_famille == "windows serveur 2016":
            return MaterielOrdinateur.FamilleOs.WIN_S_16
        elif os_famille == "windows serveur 2019":
            return MaterielOrdinateur.FamilleOs.WIN_S_19
        elif os_famille == "windows serveur 2022":
            return MaterielOrdinateur.FamilleOs.WIN_S_22
        elif os_famille == "linux (mode bureau)":
            return MaterielOrdinateur.FamilleOs.LIN_D
        elif os_famille == "linux (mode serveur)":
            return MaterielOrdinateur.FamilleOs.LIN_S
        elif os_famille == "android":
            return MaterielOrdinateur.FamilleOs.ANDROID
        elif os_famille == "propriétaire industriel":
            return MaterielOrdinateur.FamilleOs.INDUS
        else:
            raise ImporteExcelError(
                "Colonne %s : la famille d'OS '%s' est inconnue" % (self._os_famille + 1, os_famille)
            )

    def get_os_version(self, ligne: list) -> str:
        """Obtient le champ os_version dans le fichier csv"""
        return ligne[self._os_version].lower()

    def get_nombre(self, ligne: list) -> int:
        """Obtient le champ nombre dans le fichier csv"""
        try:
            return int(ligne[self._nombre])
        except ValueError:
            raise ImporteExcelError(
                "Colonne %s : impossible de convertir le nombre '%s'" % (self._nombre + 1, ligne[self._nombre])
            )

    def get_description(self, ligne: list) -> str:
        """Obtient le champ description dans le fichier csv"""
        return ligne[self._description]


class StructureMaterielEffecteur:
    """Traduction des informations des ordinateurs du fichier csv vers le modèle MaterielOrdinateur"""

    _excel_id = 0
    _type = 7
    _marque = 8
    _modele = 9
    _nombre = 13
    _firmware = 10
    _cortec = 11
    _description = 14

    def get_id_excel(self, ligne: list) -> str:
        """Obtient le champ de l'ID excel (hors BDD, correspondance entre les onglets)"""
        return ligne[self._excel_id].lower()

    def get_type(self, ligne: list) -> MaterielEffecteur.Type:
        """Obtient le champ type dans le fichier csv"""
        type_m = ligne[self._type].lower()
        if type_m == "autre matériel":
            return MaterielEffecteur.Type.AUTRE
        elif type_m == "capteur intelligent":
            return MaterielEffecteur.Type.CAPTEUR
        elif type_m == "actionneur intelligent":
            return MaterielEffecteur.Type.ACTIONNEUR
        elif type_m == "routeur":
            return MaterielEffecteur.Type.ROUTEUR
        elif type_m == "switch":
            return MaterielEffecteur.Type.SWITCH
        elif type_m == "automate":
            return MaterielEffecteur.Type.AUTOMATE
        elif type_m == "antenne":
            return MaterielEffecteur.Type.ANTENNE
        elif type_m == "caméra":
            return MaterielEffecteur.Type.CAMERA
        elif type_m == "centrale de mesure":
            return MaterielEffecteur.Type.MESURE
        elif type_m == "imprimante":
            return MaterielEffecteur.Type.IMPRIMANTE
        elif type_m == "onduleur":
            return MaterielEffecteur.Type.ONDULEUR
        elif type_m == "sonde":
            return MaterielEffecteur.Type.SONDE
        elif type_m == "télécommande":
            return MaterielEffecteur.Type.TELECOMMANDE
        elif type_m == "variateur":
            return MaterielEffecteur.Type.VARIATEUR
        elif type_m == "enregistreur":
            return MaterielEffecteur.Type.ENREGISTREUR
        elif type_m == "horloge":
            return MaterielEffecteur.Type.HORLOGE
        elif type_m == "hub":
            return MaterielEffecteur.Type.HUB
        else:
            raise ImporteExcelError("Colonne %s : le type '%s' est inconnu" % (self._type + 1, type_m))

    def get_marque(self, ligne: list) -> str:
        """Obtient le champ marque dans le fichier csv"""
        return ligne[self._marque].lower()

    def get_modele(self, ligne: list) -> str:
        """Obtient le champ modele dans le fichier csv"""
        return ligne[self._modele].lower()

    def get_nombre(self, ligne: list) -> int:
        """Obtient le champ nombre dans le fichier csv"""
        try:
            return int(ligne[self._nombre])
        except ValueError:
            raise ImporteExcelError(
                "Colonne %s : impossible de convertir le nombre '%s'" % (self._nombre + 1, ligne[self._nombre])
            )

    def get_firmware(self, ligne: list) -> str:
        """Obtient le champ firmware dans le fichier csv"""
        return ligne[self._firmware].lower()

    def get_cortec(self, ligne: list) -> str:
        """Obtient le champ cortec dans le fichier csv"""
        return ligne[self._cortec].lower()

    def get_description(self, ligne: list) -> str:
        """Obtient le champ description dans le fichier csv"""
        return ligne[self._description]


class ImporteExcel:
    """Commande d'import des données du S2I"""

    # constantes de structures du fichier excel
    struct_localisation = StructureLocalisation()
    struct_domaine = StructureDomaineMetier()
    struct_fonction = StructureFonctionMetier()
    struct_systeme = StructureSystemeIndustriel()
    struct_ordinateur = StructureMaterielOrdinateur()
    struct_materiel = StructureMaterielEffecteur()
    # struct_licence = StructureLicence()

    # paramétrage de la lecture du fichier
    onglet_S2I_ignore_lignes_debut = 3  # Compter lignes à partir de 1 (et non de 0)
    onglet_ordi_ignore_lignes_debut = 3
    onglet_mate_ignore_lignes_debut = 3

    # constates
    nom_excel = "base.xlsx"
    nom_csv_systeme = "S2I.csv"
    nom_csv_ordinateur = "ordinateur.csv"
    nom_csv_materiel = "materiel.csv"
    nom_csv_license = "license.csv"

    def __init__(self, zone: ZoneUsid, encoded_fichier: bytes, verbosity=0, nettoie=False):
        """Initialisation de la commande"""
        self.zone_usid = zone
        self.encoded_fichier = encoded_fichier
        self.pre_nettoie = nettoie

        # gestion du logging
        if verbosity == 0:
            logger.setLevel(logging.ERROR)
        elif verbosity == 1:
            logger.setLevel(logging.WARNING)
        elif verbosity == 2:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.DEBUG)

        # variables utilisés par l'objet
        self.memoire_systemes = {}
        self.traceback = []

    def _decode_excel(self, chemin_sortie: Path) -> None:
        """décodage du fichier excel"""
        with open(chemin_sortie, "wb+") as f:
            f.write(b64decode(self.encoded_fichier))

    def _nettoyage(self) -> None:
        """Effectue les actions de nettoyage préliminaires sur la base de donnée"""
        # suppression
        MaterielOrdinateur.objects.filter(systeme__localisation__zone_usid=self.zone_usid).delete()
        MaterielEffecteur.objects.filter(systeme__localisation__zone_usid=self.zone_usid).delete()
        # LicenceLogiciel.objects.filter(systeme__localisation__zone_usid=self.zone_usid).delete()
        SystemeIndustriel.objects.filter(localisation__zone_usid=self.zone_usid).delete()
        Localisation.objects.filter(zone_usid=self.zone_usid).delete()
        self.traceback.append((CeleryResultMessageType.SUCCESS, f"zone {self.zone_usid} nettoyée de la base de donnée"))

    def _traite_ligne_csv_s2i(self, numero: int, ligne: list) -> None:
        """Traite chaque ligne pour l'onglet S2I"""
        # si la ligne est vide
        if not self.struct_systeme.get_id_excel(ligne):
            return None

        logger.info("S2I - ligne n°%s" % numero)
        # la localisation du S2I
        try:
            temp_localisation = Localisation.objects.filter(
                zone_usid=self.struct_localisation.get_zone_usid(ligne),
                nom_ville=self.struct_localisation.get_nom_ville(ligne),
                nom_quartier=self.struct_localisation.get_nom_quartier(ligne),
                zone_quartier=self.struct_localisation.get_zone_quartier(ligne),
            ).get()
        except Localisation.DoesNotExist:
            temp_localisation = Localisation(
                zone_usid=self.struct_localisation.get_zone_usid(ligne),
                nom_ville=self.struct_localisation.get_nom_ville(ligne),
                nom_quartier=self.struct_localisation.get_nom_quartier(ligne),
                zone_quartier=self.struct_localisation.get_zone_quartier(ligne),
                protection=self.struct_localisation.get_protection(ligne),
                sensibilite=self.struct_localisation.get_sensibilite(ligne),
            )
            temp_localisation.save()
            logger.info("création de la localisation '%s'" % temp_localisation)
            self.traceback.append((CeleryResultMessageType.INFO, f"localisation {temp_localisation} créée"))

        # les informations principales du S2I
        try:
            temp_systeme = SystemeIndustriel.objects.filter(
                localisation=temp_localisation,
                nom=self.struct_systeme.get_nom(ligne),
                environnement=self.struct_systeme.get_environnement(ligne),
                domaine_metier=self.struct_domaine.get_domaine_metier(ligne),
            ).get()
            temp_systeme.numero_gtp = self.struct_systeme.get_numero_gtp(ligne)
            temp_systeme.homologation_fin = self.struct_systeme.get_homologation_fin(ligne)
            temp_systeme.homologation_classe = self.struct_systeme.get_homologation_classe(ligne)
            temp_systeme.description = self.struct_systeme.get_description(ligne)
        except SystemeIndustriel.DoesNotExist:
            temp_systeme = SystemeIndustriel(
                localisation=temp_localisation,
                nom=self.struct_systeme.get_nom(ligne),
                environnement=self.struct_systeme.get_environnement(ligne),
                domaine_metier=self.struct_domaine.get_domaine_metier(ligne),
                numero_gtp=self.struct_systeme.get_numero_gtp(ligne),
                homologation_fin=self.struct_systeme.get_homologation_fin(ligne),
                homologation_classe=self.struct_systeme.get_homologation_classe(ligne),
                description=self.struct_systeme.get_description(ligne),
            )
        try:
            temp_systeme.save()
            logger.info("création du système industriel '%s'" % temp_systeme)
            self.traceback.append((CeleryResultMessageType.INFO, f"système industriel {temp_systeme} créé"))
        except IntegrityError:
            raise ImporteExcelError("Impossible de sauvegarder le système '%s'" % temp_systeme)
        # ajout des fonctions métiers
        temp_systeme.fonctions_metiers.add(
            *FonctionsMetier.objects.filter(
                code__in=self.struct_fonction.get_fonctions_metiers(ligne, domaine=temp_systeme.domaine_metier.code)
            )
        )

        # Cette ligne sert à la correspondance entre la clef primaire de la BDD et les ID du fichier excel,
        # pour pouvoir lier les futurs ordinateurs, matériels et licences du fichier excel, aux systèmes qu'on vient
        # de créer dans la base de donnée.
        self.memoire_systemes[self.struct_systeme.get_id_excel(ligne)] = temp_systeme.pk

    def _traite_ligne_csv_ordinateur(self, numero: int, ligne: list) -> None:
        """Traite chaque ligne pour l'onglet PC - SERVEUR"""
        # si la ligne est vide
        if not self.struct_ordinateur.get_id_excel(ligne):
            return None

        logger.info("Ordinateurs - ligne n°%s" % numero)
        # les informations du matériel ordinateur / serveur
        temp_systeme_lie_pk = self.memoire_systemes.get(self.struct_ordinateur.get_id_excel(ligne), None)
        if temp_systeme_lie_pk is None:
            raise ImporteExcelError("impossible de créer le matériel car le système lié est introuvable")
        else:
            temp_materiel_ordinateur_serveur = MaterielOrdinateur(
                systeme=SystemeIndustriel.objects.get(pk=temp_systeme_lie_pk),
                fonction=self.struct_ordinateur.get_fonction(ligne),
                marque=self.struct_ordinateur.get_marque(ligne),
                modele=self.struct_ordinateur.get_modele(ligne),
                os_famille=self.struct_ordinateur.get_os_famille(ligne),
                os_version=self.struct_ordinateur.get_os_version(ligne),
                nombre=self.struct_ordinateur.get_nombre(ligne),
                description=self.struct_ordinateur.get_description(ligne),
            )
            try:
                temp_materiel_ordinateur_serveur.save()
            except Exception as e:
                raise ImporteExcelError("Erreur inconnue : %s" % e)

    def _traite_ligne_csv_materiel(self, numero: int, ligne: list) -> None:
        """Traite chaque ligne pour l'onglet EQUIPEMENTS DIVERS"""
        # si la ligne est vide
        if not self.struct_materiel.get_id_excel(ligne):
            return None

        logger.info("Matériels intelligents - ligne n°%s" % numero)
        # les informations du matériel ordinateur / serveur
        temp_systeme_lie_pk = self.memoire_systemes.get(self.struct_materiel.get_id_excel(ligne), None)
        if temp_systeme_lie_pk is None:
            raise ImporteExcelError("impossible de créer le matériel car le système lié est introuvable")
        else:
            temp_materiel_effecteur = MaterielEffecteur(
                systeme=SystemeIndustriel.objects.get(pk=temp_systeme_lie_pk),
                type=self.struct_materiel.get_type(ligne),
                marque=self.struct_materiel.get_marque(ligne),
                modele=self.struct_materiel.get_modele(ligne),
                nombre=self.struct_materiel.get_nombre(ligne),
                firmware=self.struct_materiel.get_firmware(ligne),
                cortec=self.struct_materiel.get_cortec(ligne),
                description=self.struct_materiel.get_description(ligne),
            )
            try:
                temp_materiel_effecteur.save()
            except Exception as e:
                raise ImporteExcelError("Erreur inconnue : %s" % e)

    def main(self) -> CeleryResult:
        """Import d'un fichier excel dans la base de donnée.
        Renvoi True si l'import s'est correctement déroulé.
        """

        # création d'un répertoire temporaire
        with TemporaryDirectory() as temp_dossier:
            temp_path = Path(temp_dossier)
            logger.debug("temp_dossier: %s" % temp_path)

            # enregistrement du fichier excel fournit
            try:
                self._decode_excel(temp_path / self.nom_excel)
            except Exception as e:
                logger.critical("Erreur dans le décodage du fichier excel : %s" % e)
                self.traceback.append((CeleryResultMessageType.ERROR, f"erreur dans la lecture du fichier excel : {e}"))
                return CeleryResult(status=CeleryResultStatus.FATAL, messages=self.traceback)

            # nettoyage de la base de donnée si demandé
            if self.pre_nettoie:
                try:
                    self._nettoyage()
                except Exception as e:
                    logger.critical("Erreur dans le nettoyage de la base de donnée:  %s" % e)
                    self.traceback.append(
                        (CeleryResultMessageType.ERROR, f"erreur dans le nettoyage de la base de donnée : {e}")
                    )
                    return CeleryResult(status=CeleryResultStatus.FATAL,messages=self.traceback)

            # conversion du fichier excel en plusieurs CSV
            excel = Xlsx2csv(temp_path / self.nom_excel, outputencoding="utf-8", delimiter=";", dateformat="%d/%m/%Y")
            excel.convert(str(temp_path / self.nom_csv_systeme), sheetname="S2I")
            excel.convert(str(temp_path / self.nom_csv_ordinateur), sheetname="PC - SERVEUR")
            excel.convert(str(temp_path / self.nom_csv_materiel), sheetname="EQUIPEMENTS DIVERS")
            # excel.convert(str(temp_path / self.nom_csv_license), sheetname="LICENCES")

            # traitement du fichier csv des S2I
            erreur_s2i = False
            with open(temp_path / self.nom_csv_systeme, "r", encoding="utf-8") as f:
                fichier_csv_s2i = reader(f, delimiter=";")
                i = 1
                for row in fichier_csv_s2i:
                    if i > self.onglet_S2I_ignore_lignes_debut:
                        try:
                            self._traite_ligne_csv_s2i(i, row)
                        except ImporteExcelError as e:
                            logger.info(str(e))
                            logger.warning("Import S2I - Erreur pour la ligne n° %s" % i)
                            self.traceback.append(
                                (CeleryResultMessageType.ERROR, f"import S2I - erreur pour la ligne n°{i} : {e}")
                            )
                            erreur_s2i = True
                    i += 1

            # s'il y a des erreurs dans l'importation des S2I, on annule la suite
            if erreur_s2i:
                logger.warning("Il y a eu des erreurs dans l'import des S2I, fin du programme")
                self.traceback.append(
                    (CeleryResultMessageType.ERROR, f"Il y a eu des erreurs dans l'import des S2I, fin du programme")
                )
                return CeleryResult(status=CeleryResultStatus.MAJOR, messages=self.traceback)
            else:
                self.traceback.append(
                    (CeleryResultMessageType.SUCCESS, f"importation réussie des S2I dans la base de donnée")
                )
                logger.warning("Importation réussie des S2I dans la base de donnée")

            # traitement du fichier des ordinateurs
            erreur_mineure = False
            with open(temp_path / self.nom_csv_ordinateur, "r", encoding="utf-8") as f:
                fichier_csv_ordi = reader(f, delimiter=";")
                i = 1
                for row in fichier_csv_ordi:
                    if i > self.onglet_ordi_ignore_lignes_debut:
                        try:
                            self._traite_ligne_csv_ordinateur(i, row)
                        except ImporteExcelError as e:
                            erreur_mineure = True
                            logger.debug(str(e))
                            logger.warning("Import ordinateur/serveur - Erreur pour la ligne n° %s" % i)
                            self.traceback.append(
                                (
                                    CeleryResultMessageType.ERROR,
                                    f"import ordinateur/serveur - erreur pour la ligne n°{i} : {e}",
                                )
                            )
                    i += 1
            logger.info("Importation terminée des ordinateurs/serveurs dans la base de donnée")
            self.traceback.append(
                (CeleryResultMessageType.SUCCESS, f"importation terminée des ordinateurs/serveurs dans la base de donnée")
            )

            # traitement du fichier des effecteurs intelligents
            with open(temp_path / self.nom_csv_materiel, "r", encoding="utf-8") as f:
                fichier_csv_materiel = reader(f, delimiter=";")
                i = 1
                for row in fichier_csv_materiel:
                    if i > self.onglet_mate_ignore_lignes_debut:
                        try:
                            self._traite_ligne_csv_materiel(i, row)
                        except ImporteExcelError as e:
                            erreur_mineure = True
                            logger.debug(str(e))
                            logger.warning("Import matériels intelligents - Erreur pour la ligne n° %s" % i)
                            self.traceback.append(
                                (CeleryResultMessageType.ERROR, f"matériels intelligents - erreur pour la ligne n°{i} : {e}")
                            )
                    i += 1
            logger.info("Importation terminée des matériels intelligents dans la base de donnée")
            self.traceback.append(
                (CeleryResultMessageType.SUCCESS, f"importation terminée des matériels intelligents dans la base de donnée")
            )

            if erreur_mineure:
                return CeleryResult(status=CeleryResultStatus.MINOR, messages=self.traceback)
            else:
                return CeleryResult(status=CeleryResultStatus.OK, messages=self.traceback)


@shared_task(pydantic=True)
def importe_excel(zone_usid: ZoneUsid, encoded_fichier: bytes, verbosity: int, nettoie: bool) -> CeleryResult:
    logger.info("début de l'import du fichier excel")
    importeur = ImporteExcel(zone_usid, encoded_fichier, verbosity=verbosity, nettoie=nettoie)
    return importeur.main()

