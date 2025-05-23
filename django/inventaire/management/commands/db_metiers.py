"""Commandes administrateurs personnalisées pour l'inventaire

Permet de créer un fichier de pré-configuration de la base de donnée pour les domaines métiers et leurs
fonctions associées
"""

import logging

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.core.serializers import serialize
from django.conf import settings

from inventaire.models import DomaineMetier, FonctionsMetier
from inventaire.utils import DomainesMetiersOfficiels


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Commande de pré-remplissage de la base de données des différentes fonctions par domaines métiers"""

    help = (
        "Permet de générer une fixture (pré-remplissage de la base de donnée)"
        " pour tous les domaines métiers et leurs fonctions associées"
    )
    chemin_json = settings.BASE_DIR / "inventaire" / "fixtures" / "inventaire" / "metiers.json"

    # Les domaines métiers et leurs fonctions sont fixés par une note et énumérés dans 'DomainesMetiersOfficiels'
    domaines = DomainesMetiersOfficiels()

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
        i_d = 1
        i_f = 1

        # création du fichier json, 1 enregistrement pour chaque possibilité
        for domaine in self.domaines.tous_domaines:
            logger.info("%s" % domaine["nom"])
            temp_domaine = DomaineMetier(
                pk=i_d,
                code=domaine["code"],
                nom=domaine["nom"],
                coeff_criticite=domaine["coeff"],
            )
            fixture.append(temp_domaine)
            for fonction in domaine["fonctions"]:
                logger.debug("  - %s" % fonction)
                temp_fonction = FonctionsMetier(
                    pk=i_f,
                    domaine=temp_domaine,
                    code=fonction["code"],
                    nom=fonction["nom"],
                    coeff_criticite=fonction["coeff"],
                )
                fixture.append(temp_fonction)
                i_f += 1
            i_d += 1

        # enregistrement du fichier json
        try:
            self.chemin_json.parent.mkdir(parents=True, exist_ok=True)
            with open(self.chemin_json, "w+", encoding="utf-8") as f:
                f.write(serialize("json", fixture))
            self.stdout.write(self.style.SUCCESS("fichier json des domaines métiers créé"))
        except PermissionError:
            logger.critical(self.chemin_json)
            self.stderr.write(self.style.ERROR("impossible d'enregistrer le fichier car les droits sont insuffisants"))
            return None

        # applique dans la base de données
        if options["enregistre"]:
            try:
                call_command("loaddata", f"{self.chemin_json.parent.name}/{self.chemin_json.name}", verbosity=0)
                self.stdout.write(self.style.SUCCESS("domaines métiers importés dans la base de données"))
            except CommandError as e:
                logging.critical(str(e))
                self.stderr.write(self.style.ERROR("impossible d'importer le fichier dans la base de donnée"))
