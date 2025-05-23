"""Définition de l'application django pour l'inventaire des S2I"""

from django.apps import AppConfig


class InventaireConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inventaire"
