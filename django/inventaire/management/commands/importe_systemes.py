"""Commandes administrateurs personnalisées pour l'inventaire

Permet d'importer les systèmes depuis un fichier excel (version excel 2.X)
"""

from base64 import b64encode
from time import sleep

from celery.result import AsyncResult
from celery.states import PENDING, SUCCESS, ALL_STATES
from django.core.management.base import BaseCommand

from inventaire.models import ZoneUsid
from inventaire.tasks import importe_excel
from inventaire.utils import CeleryResult, CeleryResultStatus, CeleryResultMessageType


class Command(BaseCommand):
    """Commande d'import des données du S2I"""

    help = "Permet d'importer les données csv des S2I"
    zone_usid = None

    def add_arguments(self, parser):
        """Arguments pris par la commande"""
        parser.add_argument(
            "-z",
            "--zone-usid",
            action="store",
            dest="zone_usid",
            choices=["AMS", "BGA", "CBG", "EVX", "OAN", "RVC", "TRS"],
            help="l'USID concerné par le fichier excel",
            required=True,
        )
        parser.add_argument(
            "-f",
            "--fichier",
            action="store",
            dest="fichier_excel",
            help="fichier excel d'une zone",
            required=True,
        )
        parser.add_argument(
            "--nettoie",
            action="store_true",
            dest="nettoie",
            help="supprime tous ce qui est déjà enregistré pour cette zone",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            dest="no_input",
            help="ne demande aucune confirmation pour effectuer les actions",
        )

    def _verifie_excel(self, nom_fichier: str, no_input: bool) -> bool:
        # vérification de la cohérence avec la zone d'USID donnée
        label_usid = getattr(ZoneUsid, self.zone_usid).label
        if "'" in label_usid:
            ville_usid = label_usid[label_usid.rfind("'") + 1:]
        elif "-" in label_usid:
            ville_usid = label_usid[label_usid.rfind("-") + 1:]
        else:
            ville_usid = label_usid[label_usid.rfind(" ") + 1:]

        if not ville_usid.lower() in nom_fichier.lower():
            self.stdout.write(
                self.style.WARNING("Le nom du fichier excel n'a pas l'air de correspondre à l'%s" % label_usid)
            )
            # si mode "sans utilisateur", on valide directement
            if no_input:
                x_input = "y"
            else:
                x_input = input(self.style.WARNING("Tapez [y] ou [o] pour confirmer vos choix: ")).lower()
            if x_input != "y" and x_input != "o":
                self.stdout.write(self.style.ERROR("Annulation"))
                return False

        return True

    def handle(self, *args, **options):
        """Action réalisée par la commande"""
        # conversion de la zone d'USID
        self.zone_usid = getattr(ZoneUsid, options["zone_usid"], None)

        # vérification du fichier excel puis décodage
        if not self._verifie_excel(options["fichier_excel"], options["no_input"]):
            return None
        with open(options["fichier_excel"], "rb") as f:
            encoded_excel = b64encode(f.read())

        # lancement de la tache asynchrone
        task = importe_excel.delay(
            self.zone_usid,
            encoded_excel,
            verbosity=options["verbosity"],
            nettoie=options["nettoie"],
        )
        self.stdout.write(self.style.SUCCESS("task started with id: %s" % task.id))

        # attente puis affichage du resultat global
        while not task.ready():
            sleep(1)
        if task.failed():
            self.stderr.write(
                self.style.ERROR(
                    "importation échouée, erreur inconnue. Vérifiez les logs Celery pour plus d'informations"
                )
            )
        if task.successful():
            result = CeleryResult.model_validate(task.result)
            match result.status:
                case result.status.OK:
                    func = self.stdout.write
                    func(self.style.SUCCESS("importation réussie"))
                case result.status.MINOR:
                    func = self.stdout.write
                    func(self.style.WARNING("importation réussie avec des erreurs mineures"))
                case result.status.MAJOR:
                    func = self.stdout.write
                    func(self.style.WARNING("importation réussie avec des erreurs majeures"))
                case result.status.FATAL:
                    func = self.stderr.write
                    func(self.style.ERROR("importation échouée"))
                case result.status.CRASH:
                    func = self.stderr.write
                    func(self.style.ERROR("importation échée, crash inattendu"))

            # affichage des détails de la tâche
            for status, msg in result.messages:
                if status == CeleryResultMessageType.SUCCESS:
                    func(self.style.SUCCESS(msg))
                elif status == CeleryResultMessageType.ERROR:
                    func(self.style.ERROR(msg))
                else:
                    func(msg)
