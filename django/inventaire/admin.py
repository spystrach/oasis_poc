"""Définition du panneau de contrôle d'administration de l'inventaire"""

from django.contrib import admin

from inventaire.models import (
    Localisation,
    ContratMaintenance,
    DomaineMetier,
    FonctionsMetier,
    SystemeIndustriel,
    Interconnexion,
    MaterielOrdinateur,
    MaterielEffecteur,
    LicenceLogiciel,
)


class FonctionsMetierInline(admin.TabularInline):
    model = FonctionsMetier


class MaterielOrdinateurInline(admin.TabularInline):
    model = MaterielOrdinateur


class MaterielEffecteurInline(admin.TabularInline):
    model = MaterielEffecteur


class LicenceLogicielInline(admin.TabularInline):
    model = LicenceLogiciel


class InterconnexionInline(admin.TabularInline):
    model = Interconnexion
    fk_name = "systeme_from"


@admin.register(Localisation)
class LocalisationAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Périmètre de responsabilité", {"fields": ["zone_usid"]}),
        ("Lieu", {"fields": ["nom_ville", "nom_quartier", "zone_quartier"]}),
        ("Caractéristiques", {"fields": ["protection", "sensibilite"]}),
    ]
    list_display = ["nom_ville", "nom_quartier", "zone_quartier"]
    list_filter = ["zone_usid", "nom_ville", "protection", "sensibilite"]
    ordering = ["zone_usid", "nom_ville", "nom_quartier", "zone_quartier"]


@admin.register(ContratMaintenance)
class ContratMaintenanceAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Généralités", {"fields": ["zone_usid", "numero_marche"]}),
        ("Entreprise titulaire", {"fields": ["nom_societe", "nom_poc"]}),
        ("Statut", {"fields": ["date_fin", "est_actif"]}),
        ("Suppléments", {"classes": ["collapse"], "fields": ["description"]}),
        ("Gestion", {"classes": ["collapse"], "fields": ["fiche_utilisateur", "fiche_corbeille"]}),
    ]
    list_display = ["numero_marche", "nom_societe", "zone_usid", "est_actif"]
    list_filter = ["zone_usid", "nom_societe", "date_fin", "est_actif", "fiche_corbeille"]
    ordering = ["numero_marche"]

    def save_model(self, request, obj, form, change):
        """Ajoute l'id de l'utilisateur effectuant l'enregistrement"""
        obj.fiche_utilisateur = request.user
        super().save_model(request, obj, form, change)


@admin.register(DomaineMetier)
class DomaineMetierAdmin(admin.ModelAdmin):
    fieldsets = [("Généralités", {"fields": ["nom", "code", "coeff_criticite"]})]
    list_display = ["nom", "code", "coeff_criticite"]
    list_filter = ["coeff_criticite"]
    ordering = ["nom"]
    inlines = [FonctionsMetierInline]


@admin.register(SystemeIndustriel)
class SystemeIndustrielAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            "Généralités",
            {
                "fields": [
                    "nom",
                    "localisation",
                    "environnement",
                    "domaine_metier",
                    "fonctions_metiers",
                    "numero_gtp",
                ]
            },
        ),
        (
            "Homologation",
            {
                "classes": ["collapse"],
                "fields": ["homologation_classe", "homologation_responsable", "homologation_fin"],
            },
        ),
        (
            "Maintenance et sauvegardes",
            {
                "classes": ["collapse"],
                "fields": [
                    "contrat_mcs",
                    "date_maintenance",
                    "sauvegarde_config",
                    "sauvegarde_donnees",
                    "sauvegarde_comptes",
                ],
            },
        ),
        ("Suppléments", {"classes": ["collapse"], "fields": ["description"]}),
        ("Gestion", {"classes": ["collapse"], "fields": ["fiche_utilisateur", "fiche_corbeille"]}),
    ]
    list_display = [
        "nom",
        "display_nom_ville",
        "display_nom_quartier",
        "domaine_metier",
        "display_description",
    ]
    list_filter = [
        "localisation__zone_usid",
        "localisation__nom_ville",
        "environnement",
        "domaine_metier",
        "fiche_corbeille",
    ]
    ordering = [
        "localisation__zone_usid",
        "localisation__nom_ville",
        "localisation__nom_quartier",
        "localisation__zone_quartier",
        "nom",
    ]
    inlines = [InterconnexionInline, MaterielOrdinateurInline, MaterielEffecteurInline, LicenceLogicielInline]

    @admin.display(description="Nom de la ville")
    def display_nom_ville(self, obj):
        return obj.localisation.nom_ville

    @admin.display(description="Nom du quartier")
    def display_nom_quartier(self, obj):
        return obj.localisation.nom_quartier

    @admin.display(description="Description / commentaire")
    def display_description(self, obj):
        if len(obj.description) < 40:
            return obj.description
        else:
            return obj.description[:35] + "[...]"

    def save_model(self, request, obj, form, change):
        """Ajoute l'id de l'utilisateur effectuant l'enregistrement"""
        obj.fiche_utilisateur = request.user
        super().save_model(request, obj, form, change)


@admin.register(MaterielOrdinateur)
class MaterielOrdinateurAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Système d'appartenance", {"fields": ["systeme", "nombre"]}),
        (
            "Constructeur",
            {"fields": ["fonction", "marque", "modele"]},
        ),
        (
            "Système d'exploitation",
            {"fields": ["os_famille", "os_version"]},
        ),
        ("Suppléments", {"classes": ["collapse"], "fields": ["description"]}),
    ]
    list_display = ["systeme", "fonction", "marque"]
    list_filter = ["systeme__localisation__zone_usid", "fonction", "os_famille"]
    ordering = [
        "systeme__localisation__zone_usid",
        "systeme__localisation__nom_ville",
        "systeme__localisation__nom_quartier",
        "systeme__localisation__zone_quartier",
        "systeme__nom",
        "fonction",
        "marque",
        "modele",
    ]


@admin.register(MaterielEffecteur)
class MaterielEffecteurAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Système d'appartenance", {"fields": ["systeme", "nombre"]}),
        (
            "Données indispensables",
            {"fields": ["type", "marque", "modele"]},
        ),
        (
            "Données optionnelles",
            {
                "classes": ["collapse"],
                "fields": ["firmware", "cortec", "description"],
            },
        ),
    ]
    list_display = ["systeme", "type"]
    list_filter = ["systeme__localisation__zone_usid", "type"]
    ordering = [
        "systeme__localisation__zone_usid",
        "systeme__localisation__nom_ville",
        "systeme__localisation__nom_quartier",
        "systeme__localisation__zone_quartier",
        "systeme__nom",
        "type",
        "marque",
        "modele",
    ]


@admin.register(LicenceLogiciel)
class LicenceLogicielAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Système d'appartenance", {"fields": ["systeme"]}),
        ("Généralités", {"fields": ["editeur", "logiciel", "version", "licence", "date_fin"]}),
        ("Suppléments", {"classes": ["collapse"], "fields": ["description"]}),
    ]
    list_display = ["systeme", "editeur", "logiciel"]
    list_filter = ["systeme__localisation__zone_usid", "editeur", "date_fin"]
    ordering = [
        "systeme__localisation__zone_usid",
        "systeme__localisation__nom_ville",
        "systeme__localisation__nom_quartier",
        "systeme__localisation__zone_quartier",
        "systeme__nom",
        "editeur",
        "logiciel",
    ]
