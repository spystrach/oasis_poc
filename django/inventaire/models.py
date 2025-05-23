"""Définition du contenu de la base de données de l'inventaire"""

# from packaging.version import parse as parse_version
# from packaging.version import Version

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum


class ZoneUsid(models.TextChoices):
    """Les périmètres de responsabilité de chaque USID

    Cette énumération n'est pas contenue dans une classe de modèle, car elle est utilisée dans les modèles :
        - Localisation
        - ContratMaintenance
    """

    AMS = "AMS", "USID d'Angers"
    BGA = "BGA", "USID de Bourges-Avord"
    CBG = "CBG", "USID de Cherbourg"
    EVX = "EVX", "USID d'Évreux"
    OAN = "OAN", "USID de Bricy"
    RVC = "RVC", "USID de Rennes"
    TRS = "TRS", "USID de Tours"


class Droits(models.Model):
    """Faux modèle pour stocker des permissions spécifiques"""

    class Meta:
        managed = False
        default_permissions = ()
        # Ces permissions spéciales permettent de gérer les droits pour les 7 USID.
        # Ils s'écrivent sous la forme (nom de code, nom d'affichage).
        # Les noms de codes sont sous la forme 'droit'+'zone'. Cette codification ne peut être changée
        # qu'à la condition qu'elle soit aussi changée dans les fichiers :
        #   - 'utils.py', la fonction 'restreint_zone'
        #   - 'utils.py', la classe 'DomainesMetiersOfficiels'
        permissions = [
            # consultation et modifications
            ("consult_AMS", "consulter la zone de l'USID d'Angers"),
            ("consult_BGA", "consulter la zone de l'USID de Bourges-Avord"),
            ("consult_CBG", "consulter la zone de l'USID de Cherbourg"),
            ("consult_EVX", "consulter la zone de l'USID d'Évreux"),
            ("consult_OAN", "consulter la zone de l'USID de Bricy"),
            ("consult_RVC", "consulter la zone de l'USID de Rennes"),
            ("consult_TRS", "consulter la zone de l'USID de Tours"),
            ("modif_AMS", "modifier la zone de l'USID d'Angers"),
            ("modif_BGA", "modifier la zone de l'USID de Bourges-Avord"),
            ("modif_CBG", "modifier la zone de l'USID de Cherbourg"),
            ("modif_EVX", "modifier la zone de l'USID d'Évreux"),
            ("modif_OAN", "modifier la zone de l'USID de Bricy"),
            ("modif_RVC", "modifier la zone de l'USID de Rennes"),
            ("modif_TRS", "modifier la zone de l'USID de Tours"),
            # statistiques de la page d'accueil
            ("stat_RSSI", "afficher des statistiques détaillées de sa zone (optimisée pour les RSSI)"),
            ("stat_BSSI", "afficher des statistiques globales de toutes les zone (optimisée pour les BSSI)"),
            ("stat_INT", "afficher des statistiques anonymes globales (pour les décideurs internes)"),
            ("stat_EXT", "afficher des statistiques anonymes globales censurées (pour les décideurs externes)"),
        ]


class Localisation(models.Model):
    """Modèle stockant une emprise"""

    class Meta:
        verbose_name = "Localisation"
        verbose_name_plural = "Localisations"
        db_table = "inventaire_localisation"
        db_table_comment = "Toutes les emprises"
        unique_together = ["zone_usid", "nom_ville", "nom_quartier", "zone_quartier"]

    class Protection(models.TextChoices):
        """Les zones de protection d'une emprise"""

        MC = "MC", "milieu civil"
        TM = "TM", "terrain militaire"
        ZP = "ZP", "zone protégée"
        ZDHS = "ZDHS", "zone de défense hautement sensible"
        ZR = "ZR", "zone réservée"
        ZNAR = "ZNAR", "zone nucléaire d'accès réglementé"
        ZV = "ZV", "zone vitale"

    class Sensibilite(models.TextChoices):
        """Les sensibilités d'une emprise"""

        VITALE = "V", "vitale"
        HAUTE = "H", "haute"
        MOINDRE = "M", "moindre"

    objects = models.Manager()
    # champs du modèle
    zone_usid = models.CharField(verbose_name="Périmètre de l'USID", max_length=3, choices=ZoneUsid)
    nom_ville = models.CharField(verbose_name="Nom de la ville", max_length=50)
    nom_quartier = models.CharField(verbose_name="Nom du quartier", max_length=50)
    zone_quartier = models.CharField(
        verbose_name="Zone dans le quartier",
        max_length=50,
        blank=True,
        default="",
    )
    protection = models.CharField(verbose_name="Niveau de protection de la zone", max_length=4, choices=Protection)
    sensibilite = models.CharField(verbose_name="Sensibilité de la zone", max_length=1, choices=Sensibilite)

    def __str__(self) -> str:
        """Affichage de l'élément"""
        if self.zone_quartier:
            return f"{self.nom_ville} - {self.nom_quartier} - {self.zone_quartier}"
        else:
            return f"{self.nom_ville} - {self.nom_quartier}"


class ContratMaintenance(models.Model):
    """Modèle stockant un contrat de maintenance"""

    class Meta:
        verbose_name = "Contrat MCO/MCS"
        verbose_name_plural = "Contrats MCO/MCS"
        db_table = "inventaire_contrat"
        db_table_comment = "tous les contrats de maintenance"

    objects = models.Manager()
    # champs du modèle
    zone_usid = models.CharField(verbose_name="Périmètre de l'USID", max_length=3, choices=ZoneUsid)
    numero_marche = models.CharField(verbose_name="Numéro du marché", max_length=20, unique=True)
    date_fin = models.DateField(verbose_name="Date de fin du marché")
    nom_societe = models.CharField(verbose_name="Nom de la société", max_length=50)
    nom_poc = models.CharField(verbose_name="Point de contact", max_length=200, blank=True, default="")
    description = models.CharField(verbose_name="Description / commentaire", max_length=300, blank=True, default="")
    est_actif = models.BooleanField(verbose_name="Contrat actif")
    fiche_date = models.DateField(verbose_name="Date mise à jour de la fiche", auto_now=True)
    fiche_utilisateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Utilisateur ayant mis à jour la fiche",
        related_name="contrats_modifies",
    )
    fiche_corbeille = models.BooleanField(verbose_name="Contrat placé dans la corbeille", default=False)

    def __str__(self) -> str:
        """Affichage de l'élément"""
        return f"Contrat avec {self.nom_societe} ({self.numero_marche})"


class DomaineMetier(models.Model):
    """Les domaines métiers d'un S2I (classement du CETID)"""

    class Meta:
        verbose_name = "Domaine métier"
        verbose_name_plural = "Domaines métiers"
        db_table = "inventaire_metier_domaine"
        db_table_comment = "les différents domaines métier"

    objects = models.Manager()
    # champs du modèle
    code = models.CharField(
        max_length=3,
        verbose_name="Acronyme du domaine métier",
        unique=True,
    )
    nom = models.CharField(
        max_length=50,
        verbose_name="Nom du domaine métier",
        unique=True,
    )
    coeff_criticite = models.PositiveSmallIntegerField(
        verbose_name="coefficient multiplicateur (calcul de la criticité)",
        default=1,
    )

    def __str__(self) -> str:
        """Affichage de l'élément"""
        return str(self.nom)


class FonctionsMetier(models.Model):
    """Modèle stockant les fonctions métiers d'un S2I (classement du CETID)"""

    class Meta:
        verbose_name = "Fonction par domaines métiers"
        verbose_name_plural = "Fonctions par domaines métiers"
        db_table = "inventaire_metier_fonctions"
        db_table_comment = "les différentes fonctions par domaines métier"
        unique_together = ["domaine", "nom", "code"]

    objects = models.Manager()
    # champs du modèle
    domaine = models.ForeignKey(
        DomaineMetier,
        on_delete=models.CASCADE,
        verbose_name="Domaine métier de la fonction",
        related_name="fonctions",
    )
    code = models.CharField(
        max_length=3,
        verbose_name="Acronyme de la fonction",
    )
    nom = models.CharField(
        max_length=50,
        verbose_name="Nom de la fonction",
    )
    coeff_criticite = models.PositiveSmallIntegerField(
        verbose_name="coefficient multiplicateur (calcul de la criticité)",
        default=1,
    )

    def __str__(self) -> str:
        """Affichage de l'élément"""
        return str(self.nom)


class SystemeIndustriel(models.Model):
    """Modèle stockant un système industriel d'infrastructure"""

    class Meta:
        verbose_name = "Système industriel"
        verbose_name_plural = "Systèmes industriels"
        db_table = "inventaire_systeme"
        db_table_comment = "tous les systèmes industriels d'infrastructure"
        unique_together = ["localisation", "nom", "environnement", "domaine_metier"]

    class Environnement(models.IntegerChoices):
        """Les missions auxquelles participe le S2I"""

        AUTRE = 0, "autre"
        NUC = 1, "nucléaire"
        CYB = 2, "cyber"
        OPS = 3, "opérationnel"

    class ClasseHomologation(models.IntegerChoices):
        """Les classes d'homologation"""

        # C0 = 0, 'démarche classe 0'
        C1 = 1, "démarche sommaire"
        C2 = 2, "démarche simplifiée"
        C3 = 3, "démarche standard"
        NC = 99, "non homologué"

    class ResponsableHomologation(models.IntegerChoices):
        """Les responsables de l'homologation"""

        NON = 0, "Pas d'entité responsable identifiée"
        SID = 1, "Service infrastructure de la défense"
        SGA = 2, "Secrétariat général pour l'administration"
        DGA = 3, "Direction générale de l'armement"
        DRSD = 4, "Direction du renseignement et de la sécurité de la défense"
        EMA = 5, "État-major des armées"

    objects = models.Manager()
    # champs du modèle
    localisation = models.ForeignKey(
        Localisation,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Localisation du S2I",
        related_name="systemes",
    )
    contrat_mcs = models.ForeignKey(
        ContratMaintenance,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        blank=True,
        verbose_name="Contrat de MCO/MCS",
        related_name="systemes",
    )
    systemes_connectes = models.ManyToManyField(
        "self",
        verbose_name="Systèmes industriels connectés",
        through="Interconnexion",
        blank=True,
    )
    nom = models.CharField(verbose_name="Nom du S2I", max_length=50)
    environnement = models.PositiveSmallIntegerField(verbose_name="Environnement du S2I", choices=Environnement)
    domaine_metier = models.ForeignKey(
        DomaineMetier,
        on_delete=models.CASCADE,
        verbose_name="Domaine métier du S2I",
        related_name="systemes",
    )
    fonctions_metiers = models.ManyToManyField(
        FonctionsMetier,
        verbose_name="Fonctions associées",
        related_name="systemes",
    )
    numero_gtp = models.CharField(
        verbose_name="Numéro d'identification GTP",
        max_length=20,
        blank=True,
        default="",
    )
    homologation_classe = models.PositiveSmallIntegerField(
        verbose_name="Classe d'homologation",
        choices=ClasseHomologation,
        default=ClasseHomologation.NC,
    )
    homologation_responsable = models.PositiveSmallIntegerField(
        verbose_name="Autorité responsable du système",
        choices=ResponsableHomologation,
        default=ResponsableHomologation.NON,
    )
    homologation_fin = models.DateField(
        verbose_name="Date de la fin de l'homologation",
        null=True,
        default=None,
        blank=True,
    )
    sauvegarde_config = models.DateField(
        verbose_name="Date de la dernière sauvegarde des configurations",
        null=True,
        default=None,
        blank=True,
    )
    sauvegarde_donnees = models.DateField(
        verbose_name="Date de la dernière sauvegarde des données metier",
        null=True,
        default=None,
        blank=True,
    )
    sauvegarde_comptes = models.DateField(
        verbose_name="Date de la dernière sauvegarde des comptes",
        null=True,
        default=None,
        blank=True,
    )
    date_maintenance = models.DateField(
        verbose_name="Date de la dernière intervention",
        null=True,
        default=None,
        blank=True,
    )
    description = models.CharField(verbose_name="Description / commentaire", max_length=300, blank=True, default="")
    fiche_date = models.DateField(verbose_name="Date mise à jour de la fiche", auto_now=True)
    fiche_utilisateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Utilisateur ayant mis à jour la fiche",
        related_name="systemes_modifies",
    )
    fiche_corbeille = models.BooleanField(verbose_name="S2I placé dans la corbeille", default=False)

    def __str__(self) -> str:
        """Affichage de l'élément"""
        return f"{self.localisation} - {self.nom}"

    def criticite(self) -> int:
        """Calcule la criticité du S2I, un entier entre 0 et 100 (plus grand = plus critique)

        La formule est la suivante :
        criticite = Somme(coeff_fct_metiers) * coeff_domaine_metier * (coeff_localisation + coeff_sensibilite)

        Returns:
            un entier représentant la criticité du S2I
        """
        maximum_somme_coeff_fonctions = 13
        maximum_coeff_domaine_metier = 4
        coeff_environnement = {
            self.Environnement.NUC: 4,
            self.Environnement.CYB: 3,
            self.Environnement.OPS: 2,
            self.Environnement.AUTRE: 1,
        }
        coeff_localisation = {
            Localisation.Sensibilite.VITALE: 3,
            Localisation.Sensibilite.HAUTE: 2,
            Localisation.Sensibilite.MOINDRE: 1,
        }
        criticite_max = maximum_somme_coeff_fonctions * maximum_coeff_domaine_metier * (4 + 3)
        sum_coeff_fct = self.fonctions_metiers.aggregate(Sum("coeff_criticite"))["coeff_criticite__sum"]
        if sum_coeff_fct is None:
            sum_coeff_fct = 1
        return int(
            (
                sum_coeff_fct
                * self.domaine_metier.coeff_criticite
                * (coeff_environnement[self.environnement] + coeff_localisation[self.localisation.sensibilite])
            )
            / criticite_max
            * 100
        )


class Interconnexion(models.Model):
    """Modèle intermédiaire stockant une interconnexion entre deux S2I"""

    class Meta:
        verbose_name = "Interconnexion"
        verbose_name_plural = "Interconnexions"
        db_table = "inventaire_interconnexion"
        db_table_comment = "toutes les interconnexions entre deux système industriel"
        unique_together = ["systeme_from", "systeme_to"]

    class Reseau(models.IntegerChoices):
        """Les réseaux connectés"""

        A_C = 0, "autre réseau connecté"
        A_I = 1, "autre réseau isolé"
        NP_C = 2, "réseau connecté NP (type internet)"
        NP_I = 3, "réseau isolé NP"
        DR_C = 4, "réseau connecté DR (type intradef)"
        DR_I = 5, "réseau isolé DR"
        S_C = 6, "réseau connecté secret (type intraced)"
        S_I = 7, "réseau isolé S"

    class Liaison(models.IntegerChoices):
        """La couche de transport physique"""

        AUTRE = 0, "autre"
        FIL = 1, "filaire"
        WIFI = 2, "wifi"
        BLUETOOTH = 3, "bluetooth"
        RADIO = 4, "radio"
        FH = 5, "FH"
        GPRS = 6, "GPRS ou 2G"
        MOBILE = 7, "3G, 4G ou 5G"
        INFRAROUGE = 8, "infrarouge"
        RFID = 9, "RFID"

    objects = models.Manager()
    # champ du modèle
    systeme_from = models.ForeignKey(
        SystemeIndustriel,
        on_delete=models.CASCADE,
        related_name="systeme_from",
    )
    systeme_to = models.ForeignKey(
        SystemeIndustriel,
        on_delete=models.CASCADE,
        related_name="systeme_to",
    )
    type_reseau = models.PositiveSmallIntegerField(
        verbose_name="Type de réseau",
        choices=Reseau,
    )
    type_liaison = models.PositiveSmallIntegerField(
        verbose_name="Type de liaison",
        choices=Liaison,
    )
    protocole = models.CharField(
        verbose_name="Protocole utilisé",
        max_length=30,
        blank=True,
        default="",
    )
    description = models.CharField(verbose_name="Description / commentaire", max_length=300, blank=True, default="")

    def __str__(self) -> str:
        """Affichage de l'élément"""
        return f"Liaison {self.get_type_liaison_display()} ({self.get_type_reseau_display()}) de [{self.systeme_from}] vers [{self.systeme_to}]"

    def save(self, *args, recursif=True, **kwargs):
        """Override la fonction de sauvegarde pour enregistrer l'interconnexion symétrique"""
        super().save(*args, **kwargs)
        # puis enregistrement du symétrique
        if recursif:
            try:
                x = Interconnexion.objects.get(
                    systeme_from=self.systeme_to,
                    systeme_to=self.systeme_from,
                )
                x.type_reseau = self.type_reseau
                x.type_liaison = self.type_liaison
                x.protocole = self.protocole
                x.description = self.description
            except Interconnexion.DoesNotExist:
                x = Interconnexion(
                    systeme_from=self.systeme_to,
                    systeme_to=self.systeme_from,
                    type_reseau=self.type_reseau,
                    type_liaison=self.type_liaison,
                    protocole=self.protocole,
                    description=self.description,
                )
            finally:
                x.save(recursif=False)

    def delete(self, *args, recursif=True, **kwargs):
        """Override la fonction de suppression pour supprimer l'interconnexion symétrique"""
        super().delete(*args, **kwargs)
        # puis suppression du symétrique
        if recursif:
            try:
                x = Interconnexion.objects.get(
                    systeme_from=self.systeme_to,
                    systeme_to=self.systeme_from,
                )
                x.delete(recursif=False)
            except Interconnexion.DoesNotExist:
                pass  # un logger d'erreur peut être utile à cet endroit


'''
Requete par version d'os, pour plus tard
class VersionField(models.CharField):
    """Hello"""
    def from_db_value(self, value, expression, connection) -> Version:
        if value is None:
            return value
        return parse_version(value)

    def to_python(self, value) -> Version:
        if isinstance(value, Version) or value is None:
            return value
        return parse_version(value)

    def get_prep_value(self, value) -> str:
        value = super().get_prep_value(value)
        return str(value)
'''


class MaterielOrdinateur(models.Model):
    """Modèle stockant un composant de S2I de type ordinateur ou serveur"""

    class Meta:
        verbose_name = "Ordinateur"
        verbose_name_plural = "Ordinateurs"
        db_table = "inventaire_ordinateur"
        db_table_comment = "tous les ordinateurs et serveurs"

    class Fonction(models.IntegerChoices):
        """Les fonctions principales des matériels IT"""

        MAINT = 0, "poste de maintenance"
        SUPER = 1, "poste de supervision"
        ADMIN = 2, "poste d'administration"
        SU_AD = 3, "poste de supervision et d'administration"
        ANNUA = 4, "serveur d'annuaire"
        TEMPS = 5, "serveur de temps"
        FICHI = 6, "serveur de fichier"
        BASED = 7, "serveur de base de donnée"

    class FamilleOs(models.IntegerChoices):
        """Les types de systèmes d'exploitation"""

        AUTRE = 0, "autre"
        WIN_P_XP = 1, "windows XP"
        WIN_P_VISTA = 2, "windows Vista"
        WIN_P_7 = 3, "windows 7"
        WIN_P_8 = 4, "windows 8"
        WIN_P_10 = 5, "windows 10"
        WIN_P_11 = 6, "windows 11"
        WIN_S_NT = 7, "windows serveur NT"
        WIN_S_00 = 8, "windows serveur 2000"
        WIN_S_03 = 9, "windows serveur 2003"
        WIN_S_081 = 10, "windows serveur 2008"
        WIN_S_082 = 11, "windows serveur 2008 R2"
        WIN_S_121 = 12, "windows serveur 2012"
        WIN_S_122 = 13, "windows serveur 2012 R2"
        WIN_S_16 = 14, "windows serveur 2016"
        WIN_S_19 = 15, "windows serveur 2019"
        WIN_S_22 = 16, "windows serveur 2022"
        LIN_D = 17, "basé sur linux avec UI"
        LIN_S = 18, "basé sur linux sans UI"
        ANDROID = 19, "basé sur Android"
        INDUS = 20, "propriétaire industriel"

    objects = models.Manager()
    # champs du modèle
    systeme = models.ForeignKey(
        SystemeIndustriel,
        on_delete=models.CASCADE,
        verbose_name="Système industriel d'appartenance",
        related_name="materiels_it",
    )
    fonction = models.PositiveSmallIntegerField(
        verbose_name="Fonction principale",
        choices=Fonction,
    )
    marque = models.CharField(
        verbose_name="Nom de la marque",
        max_length=40,
    )
    modele = models.CharField(
        verbose_name="Nom du modèle",
        max_length=40,
    )
    os_famille = models.PositiveSmallIntegerField(
        verbose_name="Famille de système d'exploitation",
        choices=FamilleOs,
    )
    os_version = models.CharField(
        # os_version = VersionField(  # requète par version d'OS, pour plus tard
        verbose_name="Numéro de la version du système d'exploitation",
        max_length=50,
    )
    nombre = models.IntegerField(
        verbose_name="Nombre de machines déployées pour ce S2I",
        default=1,
    )
    description = models.CharField(verbose_name="Description / commentaire", max_length=300, blank=True, default="")

    def __str__(self) -> str:
        """Affichage de l'élément"""
        return f"{self.get_fonction_display()} ({self.marque}) de {self.systeme}"

    '''
    def os_version_cmp(self):
        """Permet la comparaison des numéros de version"""
        return parse_version(self.os_version)
    '''


class MaterielEffecteur(models.Model):
    """Modèle stockant un composant de S2I de type capteur, actionneur ou élément actif de réseau"""

    class Meta:
        verbose_name = "Matériel intelligent"
        verbose_name_plural = "Matériels intelligents"
        db_table = "inventaire_effecteur"
        db_table_comment = "tous les capteurs, actionneurs et éléments actifs de réseau"

    class Type(models.IntegerChoices):
        """Les types d'effecteurs"""

        AUTRE = 0, "autre matériel"
        ACTIONNEUR = 1, "actionneur intelligent"
        ANTENNE = 2, "antenne"
        AUTOMATE = 3, "automate"
        CAMERA = 4, "camera"
        CAPTEUR = 5, "capteur intelligent"
        MESURE = 6, "centrale de mesure"
        ENREGISTREUR = 7, "enregistreur"
        HORLOGE = 8, "horloge"
        HUB = 9, "hub"
        IMPRIMANTE = 10, "imprimante"
        ONDULEUR = 11, "onduleur"
        ROUTEUR = 12, "routeur"
        SONDE = 13, "sonde"
        SWITCH = 14, "switch (passerelle)"
        TELECOMMANDE = 15, "télécommande"
        VARIATEUR = 16, "variateur"

    objects = models.Manager()
    # champs du modèle
    systeme = models.ForeignKey(
        SystemeIndustriel,
        on_delete=models.CASCADE,
        verbose_name="Système industriel d'appartenance",
        related_name="materiels_ot",
    )
    type = models.PositiveSmallIntegerField(
        verbose_name="Type de matériel",
        choices=Type,
    )
    marque = models.CharField(
        verbose_name="Nom de la marque",
        max_length=50,
    )
    modele = models.CharField(
        verbose_name="Nom du modèle",
        max_length=50,
    )
    nombre = models.IntegerField(
        verbose_name="Nombre de machines déployées pour ce S2I",
        default=1,
    )
    firmware = models.CharField(
        verbose_name="Numéro de la version du firmware",
        max_length=50,
        blank=True,
        default="",
    )
    cortec = models.CharField(
        verbose_name="Code CORTEC",
        max_length=50,
        blank=True,
        default="",
    )
    description = models.CharField(verbose_name="Description / commentaire", max_length=300, blank=True, default="")

    def __str__(self) -> str:
        """Affichage de l'élément"""
        return f"{self.get_type_display()} ({self.marque}) de {self.systeme}"


class LicenceLogiciel(models.Model):
    """Modèle stockant une licence de logiciel utilisé par un S2I"""

    class Meta:
        verbose_name = "Licence de logiciel"
        verbose_name_plural = "Licences de logiciels"
        db_table = "inventaire_licence"
        db_table_comment = "toutes les licences utilisées par le S2I"

    objects = models.Manager()
    # champs du modèle
    systeme = models.ForeignKey(
        SystemeIndustriel,
        on_delete=models.CASCADE,
        verbose_name="Système industriel d'appartenance",
        related_name="licences",
    )
    editeur = models.CharField(verbose_name="Nom de l'éditeur", max_length=50)
    logiciel = models.CharField(verbose_name="Nom du logiciel", max_length=50)
    version = models.CharField(verbose_name="Numéro de la version du logiciel", max_length=50)
    licence = models.CharField(verbose_name="Numéro de la licence", max_length=100)
    date_fin = models.DateField(verbose_name="Date d'expiration de la licence")
    description = models.CharField(verbose_name="Description / commentaire", max_length=300, blank=True, default="")

    def __str__(self) -> str:
        """Affichage de l'élément"""
        return f"{self.logiciel} ({self.editeur}) de {self.systeme}"
