"""Définition des formulaires de l'inventaire"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from inventaire.widgets import (
    BulmaGridCheckboxSelectMultiple,
    QuartierCheckboxSelectMultiple,
    VillesCheckboxSelectMultiple,
)
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
from inventaire.utils import restreint_zone, ModeRestriction


# la connection (déconnection directe avec la vue de contrib.auth)
class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "input"})
        self.fields["password"].widget.attrs.update({"class": "input"})


# les systèmes industriels
class SystemeIndustrielRechercheForm(forms.Form):
    """Formulaire pour rechercher les S2I"""

    template_name = "inventaire/systemes_recherche_formulaire.html"
    # recherche par localisation
    z_usid = forms.MultipleChoiceField(
        label="USID de rattachement",
        required=False,
        widget=BulmaGridCheckboxSelectMultiple,
        choices=(),  # choix dynamique modifié à l'initialisation
    )
    z_ville = forms.MultipleChoiceField(
        label="Ville",
        required=False,
        widget=VillesCheckboxSelectMultiple,
        choices=(),  # choix dynamique modifié à l'initialisation
    )
    z_quartier = forms.MultipleChoiceField(
        label="Quartier",
        required=False,
        widget=QuartierCheckboxSelectMultiple,
        choices=(),  # choix dynamique modifié à l'initialisation
    )
    # recherche par système industriel
    s_nom = forms.CharField(
        label="Nom du S2I",
        required=False,
        widget=forms.TextInput(attrs={"class": "input is-info"}),
        max_length=100,
    )
    s_metier = forms.MultipleChoiceField(
        label="Domaine métier",
        required=False,
        widget=BulmaGridCheckboxSelectMultiple,
        choices=(),  # choix dynamique modifié à l'initialisation
    )
    s_classe = forms.MultipleChoiceField(
        label="Classe d'homologation",
        required=False,
        widget=BulmaGridCheckboxSelectMultiple,
        choices=SystemeIndustriel.ClasseHomologation,
    )
    s_fin = forms.DateField(
        label="Date de fin d'homologation",
        required=False,
        widget=forms.SelectDateWidget,
    )
    # recherche par équipements de type ordinateurs/serveurs
    o_fonction = forms.MultipleChoiceField(
        label="Fonction principale",
        required=False,
        widget=BulmaGridCheckboxSelectMultiple,
        choices=MaterielOrdinateur.Fonction,
    )
    o_famille = forms.MultipleChoiceField(
        label="Famille de système d'exploitation",
        required=False,
        widget=BulmaGridCheckboxSelectMultiple,
        choices=MaterielOrdinateur.FamilleOs,
    )
    o_marque_modele = forms.CharField(
        label="Nom de la marque ou du modèle",
        required=False,
        widget=forms.TextInput(attrs={"class": "input is-info"}),
        max_length=100,
    )
    # recherche par équipements de type effecteur
    e_type = forms.MultipleChoiceField(
        label="Type",
        required=False,
        widget=BulmaGridCheckboxSelectMultiple,
        choices=MaterielEffecteur.Type,
    )
    e_marque_modele = forms.CharField(
        label="Nom de la marque ou du modèle",
        required=False,
        widget=forms.TextInput(attrs={"class": "input is-info"}),
        max_length=100,
    )
    # recherche par licence de logiciel
    l_editeur_logiciel = forms.CharField(
        label="Nom de l'éditeur ou du logiciel",
        required=False,
        widget=forms.TextInput(attrs={"class": "input is-info"}),
        max_length=100,
    )
    l_fin = forms.DateField(
        label="Date d'expiration de la licence",
        required=False,
        widget=forms.SelectDateWidget,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.zones_consultables = restreint_zone(self.user, ModeRestriction.CONSULTATION)
        super().__init__(*args, **kwargs)
        # initialise les choix dynamiques
        self.fields["z_usid"].choices = self._choix_localisation_usid
        self.fields["z_ville"].choices = self._choix_localisation_ville
        self.fields["z_quartier"].choices = self._choix_localisation_quartier
        self.fields["s_metier"].choices = self._choix_domaine_metier

    def _choix_localisation_usid(self):
        """Génère tous les choix possibles pour les USID"""
        return [(k.value, k.label) for k in ZoneUsid if k.value in self.zones_consultables]

    def _choix_localisation_ville(self):
        """Génère tous les choix possibles pour les noms de villes"""
        return (
            Localisation.objects.filter(zone_usid__in=self.zones_consultables)
            .values_list("nom_ville", "nom_ville")
            .distinct()
        )

    def _choix_localisation_quartier(self):
        """Génère tous les choix possibles pour les noms de quartiers"""
        return (
            Localisation.objects.filter(zone_usid__in=self.zones_consultables)
            .values_list("nom_quartier", "nom_quartier")
            .distinct()
        )

    def _choix_domaine_metier(self):
        """Génère les choix possibles pour les domaines métiers"""
        return DomaineMetier.objects.values_list("pk", "nom")


class SystemeIndustrielModificationForm(forms.ModelForm):
    """Formulaire pour modifier un S2I
    Avec ajout de champs de formulaires spécialisés pour la localisation
    """

    z_usid = forms.ChoiceField(
        label="USID de rattachement",
        required=True,
        choices=(),  # choix dynamique modifié à l'initialisation
    )
    z_ville = forms.ChoiceField(
        label="Ville",
        required=True,
        choices=(),  # choix dynamique modifié à l'initialisation
    )
    z_quartier = forms.ChoiceField(
        label="Quartier",
        required=True,
        choices=(),  # choix dynamique modifié à l'initialisation
    )
    z_zone = forms.ChoiceField(
        label="Zone du quartier",
        required=False,
        choices=(),  # choix dynamique modifié à l'initialisation
    )

    class Meta:
        model = SystemeIndustriel
        fields = [
            # le nom du S2I
            "nom",
            # les informations générales
            "environnement",
            "domaine_metier",
            "fonctions_metiers",
            # les informations générales facultatives
            "numero_gtp",
            "description",
            # l'homologation du S2I
            "homologation_classe",
            "homologation_responsable",
            "homologation_fin",
            # la maintenance du S2I
            "contrat_mcs",
            "date_maintenance",
            "sauvegarde_config",
            "sauvegarde_donnees",
            "sauvegarde_comptes",
        ]
        labels = {
            "environnement": "Environnement",
            "domaine_metier": "Domaine métier",
            "fonctions_metiers": "Fonctions du domaine métier",
            "numero_gtp": "Numéro GTP",
            "description": "Description",
            "homologation_classe": "Classe",
            "homologation_responsable": "Responsable",
            "homologation_fin": "Date de fin",
            "contrat_mcs": "N° du marché",
            "date_maintenance": "Dernière intervention",
            "sauvegarde_config": "Configuration",
            "sauvegarde_donnees": "Données",
            "sauvegarde_comptes": "Comptes",
        }
        widgets = {
            "nom": forms.TextInput(
                attrs={
                    "placeholder": "Nom du système industriel",
                    "class": "input is-warning is-normal",
                }
            ),
            "numero_gtp": forms.TextInput(
                attrs={
                    "placeholder": "Numéro du S2I sur GTP",
                    "class": "input is-info is-small",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Description",
                    "class": "input is-info is-small",
                }
            ),
            "homologation_fin": forms.TextInput(
                attrs={
                    "placeholder": "01/01/2025",
                    "class": "input is-info is-small",
                }
            ),
            "date_maintenance": forms.TextInput(
                attrs={
                    "placeholder": "01/01/2025",
                    "class": "input is-info is-small",
                }
            ),
            "sauvegarde_config": forms.TextInput(
                attrs={
                    "placeholder": "01/01/2025",
                    "class": "input is-info is-small",
                }
            ),
            "sauvegarde_donnees": forms.TextInput(
                attrs={
                    "placeholder": "01/01/2025",
                    "class": "input is-info is-small",
                }
            ),
            "sauvegarde_comptes": forms.TextInput(
                attrs={
                    "placeholder": "01/01/2025",
                    "class": "input is-info is-small",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.zones_modifiables = restreint_zone(self.user, ModeRestriction.MODIFICATION)
        super().__init__(*args, **kwargs)
        # filtre les localisations
        self.fields["z_usid"].choices = self._choix_localisation_usid
        self.fields["z_ville"].choices = self._choix_localisation_ville
        self.fields["z_quartier"].choices = self._choix_localisation_quartier
        self.fields["z_zone"].choices = self._choix_localisation_zone
        # filtre les contrats de maintenance
        self.fields["contrat_mcs"].queryset = ContratMaintenance.objects.filter(zone_usid__in=self.zones_modifiables)

    def _choix_localisation_usid(self):
        """Génère tous les choix possibles pour les USID"""
        return [(k.value, k.label) for k in ZoneUsid if k.value in self.zones_modifiables]

    def _choix_localisation_ville(self):
        """Génère tous les choix possibles pour les noms de villes"""
        return (
            Localisation.objects.filter(zone_usid__in=self.zones_modifiables)
            .values_list("nom_ville", "nom_ville")
            .distinct()
        )

    def _choix_localisation_quartier(self):
        """Génère tous les choix possibles pour les noms de quartiers"""
        return (
            Localisation.objects.filter(zone_usid__in=self.zones_modifiables)
            .values_list("nom_quartier", "nom_quartier")
            .distinct()
        )

    def _choix_localisation_zone(self):
        """Génère tous les choix possibles pour les zones d'un quartier"""
        return (
            Localisation.objects.filter(zone_usid__in=self.zones_modifiables)
            .values_list("zone_quartier", "zone_quartier")
            .distinct()
        )

    def clean(self):
        cleaned_data = super().clean()
        # validation de la localisation
        try:
            if cleaned_data.get("z_zone"):  # pas de zone de quartier sélectionnée
                localisation = Localisation.objects.get(
                    zone_usid=cleaned_data.get("z_usid"),
                    nom_ville=cleaned_data.get("z_ville"),
                    nom_quartier=cleaned_data.get("z_quartier"),
                    zone_quartier=cleaned_data.get("z_zone"),
                )
            else:
                localisation = Localisation.objects.get(
                    zone_usid=cleaned_data.get("z_usid"),
                    nom_ville=cleaned_data.get("z_ville"),
                    nom_quartier=cleaned_data.get("z_quartier"),
                )
        except Localisation.DoesNotExist:
            raise forms.ValidationError(
                # impossible d'associer une erreur à un champ un particulier, donc l'envoie dans le général
                "Cette localisation n'existe pas",
                code="invalid_localisation",
            )
        cleaned_data["localisation"] = localisation

        # validation de la concordance entre les fonctions métiers et le domaine métier
        try:
            fonctions_compatibles = FonctionsMetier.objects.filter(domaine=cleaned_data["domaine_metier"])
            fonctions_actuelles = cleaned_data["fonctions_metiers"]
        except KeyError:
            # Le cas ou ces deux variables ne peuvent pas être créées sera géré plus tard. Il est pris en comptes
            # dans le fichier 'views.py' dans les classes de vues 'SystemesModificationView' et 'SystemesCreationView'
            # Dans ce cas, le test formulaire.is_valid sera Faux et la fonction form_invalid sera appelé.
            # On n'a donc rien besoin de faire ici.
            pass
        else:
            for k in fonctions_actuelles:
                if k not in fonctions_compatibles:
                    raise forms.ValidationError("les fonctions métiers doivent correspondre au domaine métier")

        return cleaned_data


class SystemeIndustrielModificationInterconnexionForm(forms.ModelForm):
    """Sous-formulaire lié pour modifier les interconnexions d'un S2I"""

    class Meta:
        model = Interconnexion
        fields = [
            "systeme_to",
            "type_reseau",
            "type_liaison",
            "protocole",
            "description",
        ]
        widgets = {
            "protocole": forms.TextInput(
                attrs={
                    "placeholder": "OPC UA, Modbus, ...",
                    "class": "input is-info is-small",
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "class": "input is-info is-small",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.self_pk = kwargs.pop("self_pk", None)
        self.zones_modifiables = restreint_zone(self.user, ModeRestriction.MODIFICATION)
        super().__init__(*args, **kwargs)
        # filtre les systèmes pouvant s'interconnecter
        if self.self_pk:  # mode de modification de S2I
            self.fields["systeme_to"].queryset = SystemeIndustriel.objects.filter(
                localisation__zone_usid__in=self.zones_modifiables,
                fiche_corbeille=False,
            ).exclude(pk=self.self_pk)
        else:  # mode de création de S2I
            self.fields["systeme_to"].queryset = SystemeIndustriel.objects.filter(
                localisation__zone_usid__in=self.zones_modifiables,
                fiche_corbeille=False,
            )


class SystemeIndustrielModificationOrdinateurForm(forms.ModelForm):
    """Sous-formulaire lié pour modifier les ordinateurs et serveurs d'un S2I"""

    class Meta:
        model = MaterielOrdinateur
        fields = [
            "fonction",
            "marque",
            "modele",
            "nombre",
            "os_famille",
            "os_version",
            "description",
        ]
        widgets = {
            "marque": forms.TextInput(
                attrs={
                    "placeholder": "MGL industries",
                    "class": "input is-info is-small",
                }
            ),
            "modele": forms.TextInput(
                attrs={
                    "placeholder": "BG V8 pro max",
                    "class": "input is-info is-small",
                }
            ),
            "nombre": forms.NumberInput(
                attrs={
                    "class": "input is-info is-small",
                }
            ),
            "os_version": forms.TextInput(
                attrs={
                    "class": "input is-info is-small",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "input is-info is-small",
                }
            ),
        }


class SystemeIndustrielModificationEffecteurForm(forms.ModelForm):
    """Sous-formulaire lié pour modifier les effecteurs intelligents d'un S2I"""

    class Meta:
        model = MaterielEffecteur
        fields = [
            "type",
            "marque",
            "modele",
            "nombre",
            "firmware",
            "cortec",
            "description",
        ]
        widgets = {
            "marque": forms.TextInput(
                attrs={
                    "placeholder": "MGL industries",
                    "class": "input is-info is-small",
                }
            ),
            "modele": forms.TextInput(
                attrs={
                    "placeholder": "BG V8 pro max",
                    "class": "input is-info is-small",
                }
            ),
            "nombre": forms.NumberInput(
                attrs={
                    "class": "input is-info is-small",
                }
            ),
            "firmware": forms.TextInput(
                attrs={
                    "class": "input is-info is-small",
                }
            ),
            "cortec": forms.TextInput(
                attrs={
                    "class": "input is-info is-small",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "input is-info is-small",
                }
            ),
        }


class SystemeIndustrielModificationLicenceForm(forms.ModelForm):
    """Sous-formulaire lié pour modifier les licences de logiciel d'un S2I"""

    class Meta:
        model = LicenceLogiciel
        fields = [
            "editeur",
            "logiciel",
            "version",
            "licence",
            "date_fin",
            "description",
        ]
        widgets = {
            "editeur": forms.TextInput(
                attrs={
                    "placeholder": "MGL industries",
                    "class": "input is-info is-small",
                }
            ),
            "logiciel": forms.TextInput(
                attrs={
                    "placeholder": "PC VOIR pro max",
                    "class": "input is-info is-small",
                }
            ),
            "version": forms.TextInput(
                attrs={
                    "placeholder": "2022 R4.127",
                    "class": "input is-info is-small",
                }
            ),
            "licence": forms.TextInput(
                attrs={
                    "placeholder": "clef de produit",
                    "class": "input is-info is-small",
                }
            ),
            "date_fin": forms.TextInput(
                attrs={
                    "placeholder": "01/01/2025",
                    "class": "input is-info is-small",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "input is-info is-small",
                }
            ),
        }


# les contrats de maintenance
class ContratMaintenanceRechercheForm(forms.ModelForm):
    """Formulaire pour rechercher des contrats de maintenance"""

    template_name = "inventaire/contrats_recherche_formulaire.html"

    # ces deux champs ne peuvent être initiés par le ModelForm car :
    #  - zone_usid: champ multiple (et non unique comme dans le modèle)
    #  - date_fin: champ non obligatoire (bug ? ne fonctionne pas si fait dans la fonction __init__)
    zone_usid = forms.MultipleChoiceField(  # recherche par localisation (impossible
        label="USID de rattachement",
        required=False,
        widget=BulmaGridCheckboxSelectMultiple,
        choices=(),  # choix dynamique modifié à l'initialisation
    )
    date_fin = forms.DateField(
        label="Date de fin du marché",
        required=False,
        widget=forms.SelectDateWidget,
    )

    class Meta:
        model = ContratMaintenance
        fields = [
            "numero_marche",
            "nom_societe",
            "est_actif",
        ]
        labels = {
            "est_actif": "Affiche aussi les marchés archivés",
        }
        widgets = {
            "zone_usid": BulmaGridCheckboxSelectMultiple(),
            "numero_marche": forms.TextInput(attrs={"class": "input is-info is-small"}),
            "nom_societe": forms.TextInput(attrs={"class": "input is-info is-small"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.zones_consultables = restreint_zone(self.user, ModeRestriction.CONSULTATION)
        super().__init__(*args, **kwargs)
        # filtre les localisations
        self.fields["zone_usid"].choices = self._choix_zone_usid()
        # rend les champs restants non obligatoires
        self.fields["numero_marche"].required = False
        self.fields["nom_societe"].required = False
        self.fields["est_actif"].required = False

    def _choix_zone_usid(self) -> list[tuple]:
        """La liste des zones usid affichables en fonction des droits de l'utilisateur"""
        return [(k.value, k.label) for k in ZoneUsid if k.value in self.zones_consultables]


class ContratMaintenanceModificationForm(forms.ModelForm):
    """Formulaire pour modifier des contrats de maintenance"""

    class Meta:
        model = ContratMaintenance
        fields = [
            # le numéro du marché
            "numero_marche",
            # les généralités
            "zone_usid",
            "date_fin",
            "est_actif",
            # l'entreprise titulaire
            "nom_societe",
            "nom_poc",
            "description",
        ]
        labels = {
            "zone_usid": "USID",
            "date_fin": "Date d'expiration",
            "est_actif": "Actif",
            "nom_societe": "Entreprise",
            "nom_poc": "Point de contact",
            "description": "Description",
        }
        widgets = {
            "numero_marche": forms.TextInput(
                attrs={
                    "placeholder": "Numéro du marché",
                    "class": "input is-warning is-normal",
                }
            ),
            "date_fin": forms.TextInput(
                attrs={
                    "placeholder": "01/01/2025",
                    "class": "input is-warning is-small",
                }
            ),
            "nom_societe": forms.TextInput(
                attrs={
                    "placeholder": "SOS MCS Ouest",
                    "class": "input is-warning is-small",
                }
            ),
            "nom_poc": forms.TextInput(
                attrs={
                    "placeholder": "M. Lucien Cheval - 0102030405",
                    "class": "input is-info is-small",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Tout commentaire utile",
                    "class": "input is-info is-small",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.zones_modifiables = restreint_zone(self.user, ModeRestriction.MODIFICATION)
        super().__init__(*args, **kwargs)
        # filtre les localisations
        self.fields["zone_usid"].choices = self._choix_zone_usid()

    def _choix_zone_usid(self) -> list[tuple]:
        """La liste des zones usid affichables en fonction des droits de l'utilisateur"""
        return [(k.value, k.label) for k in ZoneUsid if k.value in self.zones_modifiables]


class ImporteExcelForm(forms.Form):
    """Import des données via un fichier excel (fonctionnalité temporaire)"""

    zone = forms.ChoiceField(
        label="USID",
        required=True,
        choices=ZoneUsid,
    )
    fichier = forms.FileField(
        label="fichier excel",
        required=True,
        widget=forms.FileInput(
            attrs={"class": "file-input"},
        ),
    )
    nettoie = forms.BooleanField(
        label="nettoyer la zone avant d'importer le fichier",
        required=False,
    )


# les api pour les requêtes AJAX
class ApiListeVillesForm(forms.Form):
    """Formulaire pour l'API qui liste toutes les villes"""

    usid = forms.MultipleChoiceField(
        required=True,
        choices=ZoneUsid,
    )


class ApiListeQuartiersForm(forms.Form):
    """Formulaire pour l'API qui liste tous les quartiers"""

    ville = forms.MultipleChoiceField(
        required=True,
        choices=(),  # choix dynamique modifié à l'initialisation
    )

    @staticmethod
    def _obtient_toutes_villes():
        """La liste des choix dépendant des informations en base, il faut l'isoler dans une fonction"""
        return Localisation.objects.values_list("nom_ville", "nom_ville").distinct()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.fields["ville"].choices = self._obtient_toutes_villes  # pas d'appel de la fonction


class ApiListeZoneForm(forms.Form):
    """Formulaire pour l'API qui liste toutes les zones d'un quartier"""

    quartier = forms.MultipleChoiceField(
        required=True,
        choices=(),  # choix dynamique modifié à l'initialisation
    )

    @staticmethod
    def _obtient_tous_quartiers():
        """La liste des choix dépendant des informations en base, il faut l'isoler dans une fonction"""
        return Localisation.objects.values_list("nom_quartier", "nom_quartier").distinct()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.fields["quartier"].choices = self._obtient_tous_quartiers  # pas d'appel de la fonction


class ApiListeFonctionsMetierForm(forms.Form):
    """Formulaire pour l'API qui liste toutes les fonctions métiers liées à un domaine métier"""

    domaine = forms.ChoiceField(
        required=True,
        choices=(),  # choix dynamique modifié à l'initialisation
    )

    @staticmethod
    def _obtient_tous_domaines():
        """La liste des choix dépendant des informations en base, il faut l'isoler dans une fonction"""
        return DomaineMetier.objects.values_list("pk", "nom")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.fields["domaine"].choices = self._obtient_tous_domaines  # pas d'appel de la fonction


# création des sous-formulaires liés (formsets) des systèmes
InterconnexionFormset = forms.inlineformset_factory(
    SystemeIndustriel,
    Interconnexion,
    form=SystemeIndustrielModificationInterconnexionForm,
    extra=1,
    can_delete=True,
    fk_name="systeme_from",
)
SystemeIndustrielModificationOrdinateurFormset = forms.inlineformset_factory(
    SystemeIndustriel,
    MaterielOrdinateur,
    form=SystemeIndustrielModificationOrdinateurForm,
    extra=1,
    can_delete=True,
)
SystemeIndustrielModificationEffecteurFormset = forms.inlineformset_factory(
    SystemeIndustriel,
    MaterielEffecteur,
    form=SystemeIndustrielModificationEffecteurForm,
    extra=1,
    can_delete=True,
)
SystemeIndustrielModificationLicenceFormset = forms.inlineformset_factory(
    SystemeIndustriel,
    LicenceLogiciel,
    form=SystemeIndustrielModificationLicenceForm,
    extra=1,
    can_delete=True,
)


class CartoForm(forms.Form):
    """Formulaire pour la cartographie de site"""

    usid = forms.ChoiceField(
        label="USID",
        required=True,
        choices=(),  # choix dynamique modifié à l'initialisation
    )
    ville = forms.ChoiceField(
        label="Ville",
        required=True,
        choices=(),  # choix dynamique modifié à l'initialisation
    )
    quartier = forms.ChoiceField(
        label="Quartier",
        required=True,
        choices=(),  # choix dynamique modifié à l'initialisation
    )
    moteur = forms.ChoiceField(
        label="moteur de rendu",
        required=True,
        choices=((0, "MermaidJS"), (1, "GoJS")),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.zones_consultables = restreint_zone(self.user, ModeRestriction.CONSULTATION)
        super().__init__(*args, **kwargs)
        # initialise les choix dynamiques
        self.fields["usid"].choices = self._choix_localisation_usid
        self.fields["ville"].choices = self._choix_localisation_ville
        self.fields["quartier"].choices = self._choix_localisation_quartier

    def _choix_localisation_usid(self):
        """Génère tous les choix possibles pour les USID"""
        return [(k.value, k.label) for k in ZoneUsid if k.value in self.zones_consultables]

    def _choix_localisation_ville(self):
        """Génère tous les choix possibles pour les noms de villes"""
        return (
            Localisation.objects.filter(zone_usid__in=self.zones_consultables)
            .values_list("nom_ville", "nom_ville")
            .distinct()
        )

    def _choix_localisation_quartier(self):
        """Génère tous les choix possibles pour les noms de quartiers"""
        return (
            Localisation.objects.filter(zone_usid__in=self.zones_consultables)
            .values_list("nom_quartier", "nom_quartier")
            .distinct()
        )
