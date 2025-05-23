"""Commandes administrateurs personnalisées pour l'inventaire

Permet de créer un fichier de pré-configuration de la base de donnée pour les groupes fonctionnels et
leurs droits associés
"""

import logging
from json import dump

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth.models import Permission


logger = logging.getLogger(__name__)


# Les groupes fonctionnels pour pouvoir travailler efficacement dans l'application
# fmt: off
GROUPES = {
    # groupes utilisateurs standard de type RSSI
    "RSSI-A Angers": [
        "consult_AMS",
        "modif_AMS",
        "stat_RSSI",
    ],
    "RSSI-A Avord": [
        "consult_BGA",
        "modif_BGA",
        "stat_RSSI",
    ],
    "RSSI-A Cherbourg": [
        "consult_CBG",
        "modif_CBG",
        "stat_RSSI",
    ],
    "RSSI-A Evreux": [
        "consult_EVX",
        "modif_EVX",
        "stat_RSSI",
    ],
    "RSSI-A Bricy": [
        "consult_OAN",
        "modif_OAN",
        "stat_RSSI",
    ],
    "RSSI-A Rennes": [
        "consult_RVC",
        "modif_RVC",
        "stat_RSSI",
    ],
    "RSSI-A Tours": [
        "consult_TRS",
        "modif_TRS",
        "stat_RSSI",
    ],
    # groupes utilisateurs standard d'un autre type
    "Direction centrale": [
        "stat_EXT",
    ],
    "Décideurs locaux": [
        "stat_INT"
    ],
    "BSSI Rennes": [
        "consult_AMS",
        "consult_BGA",
        "consult_CBG",
        "consult_EVX",
        "consult_OAN",
        "consult_RVC",
        "consult_TRS",
        "stat_BSSI",
    ],
    # groupes d'administrateur locaux
    "Super utilisateur BSSI Rennes": [
        # les lieux
        "add_localisation",
        "change_localisation",
        "delete_localisation",
        "view_localisation",
        # les contrats de maintenance
        "add_contratmaintenance",
        "change_contratmaintenance",
        "delete_contratmaintenance",
        "view_contratmaintenance",
        # les systèmes industriels (et les éléments liés)
        "add_systemeindustriel",
        "change_systemeindustriel",
        "delete_systemeindustriel",
        "view_systemeindustriel",
        "add_interconnexion",
        "change_interconnexion",
        "delete_interconnexion",
        "view_interconnexion",
        "add_materielordinateur",
        "change_materielordinateur",
        "delete_materielordinateur",
        "view_materielordinateur",
        "add_materieleffecteur",
        "change_materieleffecteur",
        "delete_materieleffecteur",
        "view_materieleffecteur",
        "view_materielordinateur",
        "add_licencelogiciel",
        "change_licencelogiciel",
        "delete_licencelogiciel",
        "view_licencelogiciel",
    ],
}
# fmt: on


class Command(BaseCommand):
    """Commande de pré-remplissage de la base de données des différentes fonctions par domaines métiers"""

    help = (
        "Permet de générer une fixture (pré-remplissage de la base de donnée)"
        " pour tous les groupes fonctionnels nécessaire au fonctionnement de l'application"
    )
    chemin_json = settings.BASE_DIR / "inventaire" / "fixtures" / "inventaire" / "groupes.json"

    def add_arguments(self, parser):
        """Arguments pris par la commande"""
        parser.add_argument(
            "--enregistre",
            action="store_true",
            dest="enregistre",
            help="applique la fixture nouvellement crée sur la base de données",
        )

    def handle(self, *args, **options):
        """Action réalisée par la commande"""
        if options["verbosity"] == 0:
            logger.setLevel(logging.ERROR)
        elif options["verbosity"] == 1:
            logger.setLevel(logging.WARNING)
        elif options["verbosity"] == 2:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.DEBUG)

        # constantes
        fixture = []
        i = 1

        # création du fichier json, 1 enregistrement pour chaque possibilité
        for groupe in GROUPES:
            logger.info("%s" % groupe)
            # Impossible d'utiliser directement l'objet 'django.contrib.auth.models.Group' sans sauvegarder
            # dans la base de donnée à cause du champ ManyToMany. On va donc créer directement l'objet serializable
            # qui résulterait de l'appel à la fonction 'serialize("json", groupe1)' avec type(groupe1) = Group
            temp_groupe_serializable = {
                "model": "auth.group",
                "pk": i,
                "fields": {
                    "name": groupe,
                    "permissions": list(
                        Permission.objects.filter(codename__in=GROUPES[groupe])
                        .order_by("pk")
                        .values_list("pk", flat=True)
                    ),
                },
            }
            fixture.append(temp_groupe_serializable)
            i += 1

        # enregistrement du fichier json
        try:
            self.chemin_json.parent.mkdir(parents=True, exist_ok=True)
            with open(self.chemin_json, "w+", encoding="utf-8") as f:
                dump(fixture, f)
            self.stdout.write(self.style.SUCCESS("fichier json des groupes fonctionnels créé"))
        except PermissionError:
            logger.critical(self.chemin_json)
            self.stderr.write(self.style.ERROR("impossible d'enregistrer le fichier car les droits sont insuffisants"))
            return None

        # applique dans la base de données
        if options["enregistre"]:
            try:
                call_command("loaddata", f"{self.chemin_json.parent.name}/{self.chemin_json.name}", verbosity=0)
                self.stdout.write(self.style.SUCCESS("groupes fonctionnels importés dans la base de données"))
            except CommandError as e:
                logging.critical(str(e))
                self.stderr.write(self.style.ERROR("impossible d'importer le fichier dans la base de donnée"))
