"""Définition des vues publiques de l'inventaire"""

import logging
from base64 import b64encode
from io import BytesIO
from json import dumps
from subprocess import call

from celery.result import AsyncResult
from celery import states
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as BaseLoginView
from django.db.models import Case, CharField, Count, Value, When, Q
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from inventaire.forms import (
    CustomAuthenticationForm,
    SystemeIndustrielRechercheForm,
    SystemeIndustrielModificationForm,
    SystemeIndustrielModificationOrdinateurFormset,
    SystemeIndustrielModificationEffecteurFormset,
    SystemeIndustrielModificationLicenceFormset,
    ContratMaintenanceRechercheForm,
    ContratMaintenanceModificationForm,
    ImporteExcelForm,
    ApiListeVillesForm,
    ApiListeQuartiersForm,
    ApiListeZoneForm,
    ApiListeFonctionsMetierForm,
    InterconnexionFormset,
    CartoForm,
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
)
from inventaire.tasks import importe_excel
from inventaire.utils import (
    restreint_zone,
    ModeRestriction,
    CeleryResult,
    CeleryResultStatus,
    CeleryResultMessageType,
)

logger = logging.getLogger(__name__)


# la connection (déconnection directe avec la vue de contrib.auth)
class LoginView(BaseLoginView):
    template_name = "inventaire/login.html"
    redirect_authenticated_user = True
    form_class = CustomAuthenticationForm

    def form_invalid(self, form):
        errors = self.get_context_data()["form"].errors.as_data()
        # les erreurs peuvent être globales (et non liées à un champ particulier)
        if "__all__" in errors:
            for error in errors["__all__"]:
                messages.add_message(self.request, messages.ERROR, error.messages[0])
        else:
            messages.add_message(self.request, messages.ERROR, "Impossible de se connecter")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["demo"] = settings.DEMO_BANNER
        return data


# l'accueil et le compte
class HomeView(LoginRequiredMixin, generic.View):
    """Page d'accueil d'un utilisateur"""

    template_name = "inventaire/accueil.html"
    menu_actif = "accueil"

    def _graph_domaine_metier(self) -> tuple[list, list]:
        """Récupère les données pour le graphique de répartition des domaines métiers"""
        query = (
            DomaineMetier.objects.filter(systemes__localisation__zone_usid__in=self.zones_consultables)
            .annotate(nb=Count("systemes"))
            .values("nom", "nb")
        )
        label = [k["nom"] for k in query]
        data = [k["nb"] for k in query]
        return label, data

    def _graph_nom_ville(self) -> tuple[list, list]:
        """Récupère les données pour le graphique de répartition par ville"""
        query = (
            Localisation.objects.filter(zone_usid__in=self.zones_consultables)
            .values("nom_ville")
            .annotate(nb=Count("systemes"))
            .order_by("nom_ville")
        )
        label = [k["nom_ville"] for k in query]
        data = [k["nb"] for k in query]
        return label, data

    def _graph_homologation_classe(self) -> tuple[list, list]:
        """Récupère les données pour le graphique de répartition des homologations"""
        homologations = [(k.value, k.label) for k in SystemeIndustriel.ClasseHomologation]
        whens = [When(homologation_classe=k[0], then=Value(k[1])) for k in homologations]
        query = (
            SystemeIndustriel.objects.filter(localisation__zone_usid__in=self.zones_consultables)
            .values("homologation_classe")
            .annotate(nb=Count("homologation_classe"))
            .annotate(humain_homologation=Case(*whens, output_field=CharField()))
            .order_by("homologation_classe")
        )

        label = [k["humain_homologation"] for k in query]
        data = [k["nb"] for k in query]
        return label, data

    def get(self, request):
        # nombre de S2I et de contrats total pour les zones consultables
        self.zones_consultables = restreint_zone(request.user, ModeRestriction.CONSULTATION)
        nb_systeme_total = SystemeIndustriel.objects.filter(localisation__zone_usid__in=self.zones_consultables).count()
        nb_contrat_total = ContratMaintenance.objects.filter(zone_usid__in=self.zones_consultables).count()

        # les données pour les graphiques
        stat = {}
        stat_domaine_metier = self._graph_domaine_metier()
        stat["pie_domaine_metier"] = {"label": stat_domaine_metier[0], "data": stat_domaine_metier[1]}
        stat_nom_ville = self._graph_nom_ville()
        stat["pie_nom_ville"] = {"label": stat_nom_ville[0], "data": stat_nom_ville[1]}
        stat_homologation = self._graph_homologation_classe()
        stat["pie_homologation_classe"] = {"label": stat_homologation[0], "data": stat_homologation[1]}

        return render(
            request,
            self.template_name,
            {
                "user": request.user,
                "actif": self.menu_actif,
                "total_systemes": nb_systeme_total,
                "total_contrats": nb_contrat_total,
                "stat": stat,
            },
        )


class CompteView(LoginRequiredMixin, generic.View):
    """Page de visualisation des détails de son compte utilisateur"""

    template_name = "inventaire/compte.html"
    menu_actif = "compte"

    def get(self, request):
        contexte = {
            "actif": self.menu_actif,
            "user": request.user,
            "zones_consultation": restreint_zone(request.user, ModeRestriction.CONSULTATION),
            "zones_modification": restreint_zone(request.user, ModeRestriction.MODIFICATION),
            "groupes_fct": request.user.groups.values_list("name", flat=True),
        }

        return render(request, self.template_name, contexte)


# les systèmes industriels
class SystemesRechercheView(LoginRequiredMixin, generic.ListView):
    """Page de recherche des systèmes industriels"""

    template_name = "inventaire/systemes_recherche.html"
    menu_actif = "systemes"
    context_object_name = "tous_sys_indus"
    paginate_by = 50

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._form = None

    def get_queryset(self):
        # restreint les systèmes par rapport aux droits de l'utilisateur
        query = SystemeIndustriel.objects.filter(
            localisation__zone_usid__in=restreint_zone(self.request.user, ModeRestriction.CONSULTATION),
            fiche_corbeille=False,
        )
        self._form = SystemeIndustrielRechercheForm(self.request.GET, user=self.request.user)
        if not self._form.is_valid():
            messages.add_message(self.request, messages.WARNING, "La recherche contient des paramètres invalides")
        else:
            # par la table de localisation
            if self._form.cleaned_data["z_usid"]:
                query = query.filter(localisation__zone_usid__in=self._form.cleaned_data["z_usid"])
            if self._form.cleaned_data["z_ville"]:
                query = query.filter(localisation__nom_ville__in=self._form.cleaned_data["z_ville"])
            if self._form.cleaned_data["z_quartier"]:
                query = query.filter(localisation__nom_quartier__in=self._form.cleaned_data["z_quartier"])
            # par la table des systèmes industriels
            if self._form.cleaned_data["s_nom"]:
                query = query.filter(nom__icontains=self._form.cleaned_data["s_nom"])
            if self._form.cleaned_data["s_metier"]:
                query = query.filter(domaine_metier__in=self._form.cleaned_data["s_metier"])
            if self._form.cleaned_data["s_classe"]:
                query = query.filter(homologation_classe__in=self._form.cleaned_data["s_classe"])
            if self._form.cleaned_data["s_fin"]:
                query = query.filter(homologation_fin__lt=self._form.cleaned_data["s_fin"])
            # par la table des ordinateurs et serveurs
            if self._form.cleaned_data["o_fonction"]:
                query = query.filter(materiels_it__fonction__in=self._form.cleaned_data["o_fonction"])
            if self._form.cleaned_data["o_famille"]:
                query = query.filter(materiels_it__os_famille__in=self._form.cleaned_data["o_famille"])
            if self._form.cleaned_data["o_marque_modele"]:
                query = query.filter(
                    Q(materiels_it__marque__icontains=self._form.cleaned_data["o_marque_modele"])
                    | Q(materiels_it__modele__icontains=self._form.cleaned_data["o_marque_modele"])
                )
            if self._form.cleaned_data["e_type"]:
                query = query.filter(materiels_ot__type__in=self._form.cleaned_data["e_type"])
            if self._form.cleaned_data["e_marque_modele"]:
                query = query.filter(
                    Q(materiels_ot__marque__icontains=self._form.cleaned_data["e_marque_modele"])
                    | Q(materiels_ot__modele__icontains=self._form.cleaned_data["e_marque_modele"])
                )
            # par la table des licences de logiciels
            if self._form.cleaned_data["l_editeur_logiciel"]:
                query = query.filter(
                    Q(licences__editeur__icontains=self._form.cleaned_data["l_editeur_logiciel"])
                    | Q(licences__logiciel__icontains=self._form.cleaned_data["l_editeur_logiciel"])
                )
            if self._form.cleaned_data["l_fin"]:
                query = query.filter(licences__date_fin__lt=self._form.cleaned_data["l_fin"])

        # trie et renvoi les systèmes
        return query.order_by(
            "localisation__zone_usid",
            "localisation__nom_ville",
            "localisation__nom_quartier",
            "localisation__zone_quartier",
            "nom",
        ).distinct()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["actif"] = self.menu_actif
        data["recherche_systemes_form"] = self._form
        data["droit_modification"] = restreint_zone(self.request.user, ModeRestriction.MODIFICATION) != []
        return data


class SystemesDetailsView(LoginRequiredMixin, generic.DetailView):
    """Page de vue des détails d'un système industriel"""

    template_name = "inventaire/systemes_details.html"
    menu_actif = "systemes"
    context_object_name = "systeme"

    def get_queryset(self):
        return SystemeIndustriel.objects.filter(
            localisation__zone_usid__in=restreint_zone(self.request.user, ModeRestriction.CONSULTATION),
            fiche_corbeille=False,
        )  # permet de restreindre aux seuls systèmes dans la zone, car affichera un 404 sinon

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["actif"] = self.menu_actif
        data["interconnexions"] = Interconnexion.objects.filter(
            systeme_from=self.kwargs["pk"], systeme_to__fiche_corbeille=False
        ).order_by("systeme_to__localisation", "systeme_to__nom")
        data["ordis"] = MaterielOrdinateur.objects.filter(systeme=self.kwargs["pk"]).order_by(
            "fonction", "marque", "modele"
        )
        data["effecteurs"] = MaterielEffecteur.objects.filter(systeme=self.kwargs["pk"]).order_by(
            "type", "marque", "modele"
        )
        data["licences"] = LicenceLogiciel.objects.filter(systeme=self.kwargs["pk"]).order_by("editeur", "logiciel")
        data["droit_modification"] = self.object.localisation.zone_usid in restreint_zone(
            self.request.user, ModeRestriction.MODIFICATION
        )
        return data


class SystemesCreationView(LoginRequiredMixin, CreateView):
    """Page de création d'un systeme industriel"""

    model = SystemeIndustriel
    template_name = "inventaire/systemes_modification.html"
    menu_actif = "systemes"
    form_class = SystemeIndustrielModificationForm
    mode = "création"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["actif"] = self.menu_actif
        data["mode"] = self.mode
        if self.request.POST:
            data["interconnexions"] = InterconnexionFormset(self.request.POST, form_kwargs={"user": self.request.user})
            data["ordis"] = SystemeIndustrielModificationOrdinateurFormset(self.request.POST)
            data["effecteurs"] = SystemeIndustrielModificationEffecteurFormset(self.request.POST)
            data["licences"] = SystemeIndustrielModificationLicenceFormset(self.request.POST)
        else:
            data["interconnexions"] = InterconnexionFormset(form_kwargs={"user": self.request.user})
            data["ordis"] = SystemeIndustrielModificationOrdinateurFormset()
            data["effecteurs"] = SystemeIndustrielModificationEffecteurFormset()
            data["licences"] = SystemeIndustrielModificationLicenceFormset()
        return data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        # récupération dans le contexte des formset des matériels liés
        context = self.get_context_data()
        interconnexions = context["interconnexions"]
        ordis = context["ordis"]
        effecteurs = context["effecteurs"]
        licences = context["licences"]

        if (
            not interconnexions.is_valid()
            or not ordis.is_valid()
            or not effecteurs.is_valid()
            or not licences.is_valid()
        ):
            return self.form_invalid(form)

        # sauvegarde du S2I
        self.object = form.save(commit=False)
        self.object.fiche_utilisateur = self.request.user
        self.object.localisation = form.cleaned_data["localisation"]
        self.object.save()
        form.save_m2m()  # obligatoire pour enregistrer les clefs 'Many to Many' car commit=False ne le fait pas
        # sauvegarde des interconnexions
        interconnexions.instance = self.object
        interconnexions.save()
        # sauvegarde des ordinateurs et serveurs liés
        ordis.instance = self.object
        ordis.save()
        # sauvegarde des effecteurs liés
        effecteurs.instance = self.object
        effecteurs.save()
        # sauvegarde des licences liées
        licences.instance = self.object
        licences.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        if "__all__" in form.errors.as_data():
            for error in form.errors.as_data()["__all__"]:
                messages.add_message(self.request, messages.ERROR, error.messages[0])
        else:
            messages.add_message(self.request, messages.ERROR, "Impossible d'enregistrer le système industriel")
        return super().form_invalid(form)

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Nouveau système industriel enregistré")
        return reverse("inventaire:systemes_details", args=[self.object.pk])


class SystemesModificationView(LoginRequiredMixin, UpdateView):
    """Page de modification d'un système industriel"""

    template_name = "inventaire/systemes_modification.html"
    menu_actif = "systemes"
    form_class = SystemeIndustrielModificationForm
    mode = "modification"

    def get_queryset(self):
        return SystemeIndustriel.objects.filter(
            localisation__zone_usid__in=restreint_zone(self.request.user, ModeRestriction.MODIFICATION),
            fiche_corbeille=False,
        )  # permet de restreindre aux seuls systèmes dans la zone, car affichera un 404 sinon

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["actif"] = self.menu_actif
        data["mode"] = self.mode
        if self.request.POST:
            data["interconnexions"] = InterconnexionFormset(
                self.request.POST,
                instance=self.object,
                form_kwargs={"user": self.request.user, "self_pk": self.object.pk},
                queryset=Interconnexion.objects.filter(systeme_to__fiche_corbeille=False),
            )
            data["ordis"] = SystemeIndustrielModificationOrdinateurFormset(self.request.POST, instance=self.object)
            data["effecteurs"] = SystemeIndustrielModificationEffecteurFormset(self.request.POST, instance=self.object)
            data["licences"] = SystemeIndustrielModificationLicenceFormset(self.request.POST, instance=self.object)
        else:
            data["interconnexions"] = InterconnexionFormset(
                instance=self.object,
                form_kwargs={"user": self.request.user, "self_pk": self.object.pk},
                queryset=Interconnexion.objects.filter(systeme_to__fiche_corbeille=False),
            )
            data["ordis"] = SystemeIndustrielModificationOrdinateurFormset(instance=self.object)
            data["effecteurs"] = SystemeIndustrielModificationEffecteurFormset(instance=self.object)
            data["licences"] = SystemeIndustrielModificationLicenceFormset(instance=self.object)
            # pré-chargement des localisations du formulaire
            data["form"]["z_usid"].initial = self.object.localisation.zone_usid
            data["form"]["z_ville"].initial = self.object.localisation.nom_ville
            data["form"]["z_quartier"].initial = self.object.localisation.nom_quartier
            data["form"]["z_zone"].initial = self.object.localisation.zone_quartier
        return data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        # récupération dans le contexte des formset des matériels liés
        context = self.get_context_data()
        interconnexions = context["interconnexions"]
        ordis = context["ordis"]
        effecteurs = context["effecteurs"]
        licences = context["licences"]

        if (
            not interconnexions.is_valid()
            or not ordis.is_valid()
            or not effecteurs.is_valid()
            or not licences.is_valid()
        ):
            return self.form_invalid(form)

        # sauvegarde du S2I
        self.object = form.save(commit=False)
        self.object.fiche_utilisateur = self.request.user
        self.object.localisation = form.cleaned_data["localisation"]
        self.object.save()
        form.save_m2m()  # obligatoire pour enregistrer les clefs 'Many to Many' car commit=False ne le fait pas
        # sauvegarde des interconnexions
        interconnexions.instance = self.object
        interconnexions.save()
        # sauvegarde des ordinateurs et serveurs liés
        ordis.instance = self.object
        ordis.save()
        # sauvegarde des effecteurs liés
        effecteurs.instance = self.object
        effecteurs.save()
        # sauvegarde des licences liées
        licences.instance = self.object
        licences.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        if "__all__" in form.errors.as_data():
            for error in form.errors.as_data()["__all__"]:
                messages.add_message(self.request, messages.ERROR, error.messages[0])
        else:
            messages.add_message(self.request, messages.ERROR, "Impossible de modifier le système industriel")
        return super().form_invalid(form)

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Système industriel modifié")
        return reverse("inventaire:systemes_details", args=[self.object.pk])


class SystemesSuppressionView(LoginRequiredMixin, DeleteView):
    """Page de suppression d'un système industriel"""

    template_name = "inventaire/systemes_suppression.html"
    menu_actif = "systemes"
    model = SystemeIndustriel

    def get_queryset(self):
        return SystemeIndustriel.objects.filter(
            localisation__zone_usid__in=restreint_zone(self.request.user, ModeRestriction.CONSULTATION),
            fiche_corbeille=False,
        )  # permet de restreindre aux seuls systèmes dans la zone, car affichera un 404 sinon

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["actif"] = self.menu_actif
        return data

    def form_valid(self, form):
        """Override de la fonction originelle, car on implémente une corbeille"""
        self.object.fiche_corbeille = True
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Système industriel supprimé")
        return reverse("inventaire:systemes_recherche")


# les contrats de maintenance
class ContratRechercheView(LoginRequiredMixin, generic.ListView):
    """Page de recherche des contrats de maintenance"""

    template_name = "inventaire/contrats_recherche.html"
    menu_actif = "contrats"
    context_object_name = "tous_contrats"
    paginate_by = 50

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._form = None

    def get_queryset(self):
        # restreint les contrats par rapport aux droits de l'utilisateur
        query = ContratMaintenance.objects.filter(
            zone_usid__in=restreint_zone(self.request.user, ModeRestriction.CONSULTATION),
            fiche_corbeille=False,
        )
        self._form = ContratMaintenanceRechercheForm(self.request.GET, user=self.request.user)
        if not self._form.is_valid():
            messages.add_message(self.request, messages.WARNING, "La recherche contient des paramètres invalides")
            query = query.filter(est_actif=True)
        else:
            # par les localisations
            if self._form.cleaned_data["zone_usid"]:
                query = query.filter(zone_usid__in=self._form.cleaned_data["zone_usid"])
            # par les généralités
            if self._form.cleaned_data["numero_marche"]:
                query = query.filter(numero_marche__icontains=self._form.cleaned_data["numero_marche"])
            if self._form.cleaned_data["nom_societe"]:
                query = query.filter(nom_societe__icontains=self._form.cleaned_data["nom_societe"])
            if self._form.cleaned_data["date_fin"]:
                query = query.filter(date_fin__lt=self._form.cleaned_data["date_fin"])
            if not self._form.cleaned_data["est_actif"]:  # vaut True si la case est cochée
                query = query.filter(est_actif=True)

        # trie et renvoi les systèmes
        return query.order_by(
            "zone_usid",
            "numero_marche",
        ).distinct()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["actif"] = self.menu_actif
        data["recherche_contrats_form"] = self._form
        data["droit_modification"] = restreint_zone(self.request.user, ModeRestriction.MODIFICATION) != []
        return data


class ContratsDetailsView(LoginRequiredMixin, generic.DetailView):
    """Page de vue des détails d'un contrat de maintenance"""

    template_name = "inventaire/contrats_details.html"
    menu_actif = "contrats"
    context_object_name = "contrat"

    def get_queryset(self):
        return ContratMaintenance.objects.filter(
            zone_usid__in=restreint_zone(self.request.user, ModeRestriction.CONSULTATION),
            fiche_corbeille=False,
        )  # permet de restreindre aux seuls contrats dans la zone, car affichera un 404 sinon

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["actif"] = self.menu_actif
        data["tous_systemes_lies"] = SystemeIndustriel.objects.filter(
            contrat_mcs=self.kwargs["pk"], fiche_corbeille=False
        )
        data["droit_modification"] = self.object.zone_usid in restreint_zone(
            self.request.user, ModeRestriction.MODIFICATION
        )
        return data


class ContratsCreationView(LoginRequiredMixin, CreateView):
    """Page de création d'un contrat de maintenance"""

    model = ContratMaintenance
    template_name = "inventaire/contrats_modification.html"
    menu_actif = "contrats"
    form_class = ContratMaintenanceModificationForm
    mode = "création"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["actif"] = self.menu_actif
        data["mode"] = self.mode
        return data

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.fiche_utilisateur = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        if "__all__" in form.errors.as_data():
            for error in form.errors.as_data()["__all__"]:
                messages.add_message(self.request, messages.ERROR, error.messages[0])
        else:
            messages.add_message(self.request, messages.ERROR, "Impossible d'enregistrer le contrat de maintenance")
        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Nouveau contrat de maintenance enregistré")
        return reverse("inventaire:contrats_details", args=[self.object.pk])


class ContratsModificationView(LoginRequiredMixin, UpdateView):
    """Page de modification d'un contrat de maintenance"""

    template_name = "inventaire/contrats_modification.html"
    menu_actif = "contrats"
    form_class = ContratMaintenanceModificationForm
    mode = "modification"

    def get_queryset(self):
        return ContratMaintenance.objects.filter(
            zone_usid__in=restreint_zone(self.request.user, ModeRestriction.MODIFICATION),
            fiche_corbeille=False,
        )  # permet de restreindre aux seuls systèmes dans la zone, car affichera un 404 sinon

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["actif"] = self.menu_actif
        data["mode"] = self.mode
        return data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.fiche_utilisateur = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        if "__all__" in form.errors.as_data():
            for error in form.errors.as_data()["__all__"]:
                messages.add_message(self.request, messages.ERROR, error.messages[0])
        else:
            messages.add_message(self.request, messages.ERROR, "Impossible de modifier le contrat de maintenance")
        return super().form_invalid(form)

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Contrat de maintenance modifié")
        return reverse("inventaire:contrats_details", args=[self.object.pk])


class ContratsSuppressionView(LoginRequiredMixin, DeleteView):
    """Page de suppression d'un contrat de maintenance"""

    template_name = "inventaire/contrats_suppression.html"
    menu_actif = "contrats"
    model = ContratMaintenance

    def get_queryset(self):
        return ContratMaintenance.objects.filter(
            zone_usid__in=restreint_zone(self.request.user, ModeRestriction.MODIFICATION),
            fiche_corbeille=False,
        )  # permet de restreindre aux seuls systèmes dans la zone, car affichera un 404 sinon

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["actif"] = self.menu_actif
        return data

    def form_valid(self, form):
        """Override de la fonction originelle, car on implémente une corbeille"""
        self.object.fiche_corbeille = True
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Contrat de maintenance supprimé")
        return reverse("inventaire:contrats_recherche")


# gestion en masse avec des fichiers Excel
class ImporteExcelView(LoginRequiredMixin, generic.View):
    template_name = "inventaire/importe_excel.html"
    menu_actif = "import"

    def get(self, request):
        contexte = {
            "actif": self.menu_actif,
            "form": ImporteExcelForm(),
        }
        return render(request, self.template_name, contexte)

    def post(self, request):
        contexte = {
            "actif": self.menu_actif,
        }
        mon_form = ImporteExcelForm(request.POST, request.FILES)
        if not mon_form.is_valid():
            messages.add_message(self.request, messages.ERROR, "Impossible de lancer l'importation")
            contexte["form"] = mon_form
            return render(request, self.template_name, contexte)

        else:
            # chargement du fichier en mémoire
            with BytesIO() as f:
                for chunk in request.FILES["fichier"].chunks():
                    f.write(chunk)
                f.seek(0)
                encoded_excel = b64encode(f.read())
            # lancement de la tache asynchrone
            task = importe_excel.delay(
                mon_form.cleaned_data["zone"],
                encoded_excel,
                verbosity=0,
                nettoie=mon_form.cleaned_data["nettoie"],
            )

        # renvoi la réponse
        return HttpResponseRedirect(reverse("inventaire:import_excel_resultat", args=[task.id]))


class ImporteExcelResultView(LoginRequiredMixin, generic.View):
    template_name = "inventaire/importe_excel_resultat.html"
    menu_actif = "import"

    def get(self, request, task_id):
        task = AsyncResult(task_id)
        contexte = {"state": task.state, "state_str": "", "task_id": task_id, "result": None}
        match task.state:
            case states.PENDING:
                contexte["state_str"] = "Importation en attente"
            case states.RETRY:
                contexte["state_str"] = "Importation en attente"
            case states.STARTED:
                contexte["state_str"] = "Importation démarrée"
            case states.FAILURE:
                contexte["state_str"] = "Importation échouée"
                contexte["result"] = CeleryResult(
                    status=CeleryResultStatus.CRASH,
                    messages=[
                        (CeleryResultMessageType.ERROR,
                        "Crash inattendu, consulter les logs pour plus de détails")
                    ],
                )
            case states.SUCCESS:
                contexte["state_str"] = "Importation terminée"
                contexte["result"] = CeleryResult.model_validate(task.result)

        return render(request, self.template_name, context=contexte)


# les api pour les requêtes AJAX
class ApiVillesView(LoginRequiredMixin, generic.View):
    """Page d'accès API pour obtenir les villes des zones USID sélectionnées"""

    def get(self, request):
        mon_form = ApiListeVillesForm(self.request.GET)

        if mon_form.is_valid():
            query = (
                Localisation.objects.filter(zone_usid__in=restreint_zone(request.user, ModeRestriction.CONSULTATION))
                .filter(zone_usid__in=mon_form.cleaned_data["usid"])
                .values_list("nom_ville", flat=True)
                .distinct()
            )
            return JsonResponse({"villes": list(query)})
        return JsonResponse({"villes": []})


class ApiQuartierView(LoginRequiredMixin, generic.View):
    """Page d'accès API pour obtenir les quartiers des villes sélectionnées"""

    def get(self, request):
        mon_form = ApiListeQuartiersForm(self.request.GET)
        if mon_form.is_valid():
            query = (
                Localisation.objects.filter(zone_usid__in=restreint_zone(request.user, ModeRestriction.CONSULTATION))
                .filter(nom_ville__in=mon_form.cleaned_data["ville"])
                .values_list("nom_quartier", flat=True)
                .distinct()
            )
            return JsonResponse({"quartiers": list(query)})
        return JsonResponse({"quartiers": []})


class ApiZoneView(LoginRequiredMixin, generic.View):
    """Page d'accès API pour obtenir les zones des quartiers sélectionnées"""

    def get(self, request):
        mon_form = ApiListeZoneForm(request.GET)
        if mon_form.is_valid():
            query = (
                Localisation.objects.filter(zone_usid__in=restreint_zone(request.user, ModeRestriction.CONSULTATION))
                .filter(nom_quartier__in=mon_form.cleaned_data["quartier"])
                .values_list("zone_quartier", flat=True)
                .distinct()
            )
            return JsonResponse({"zones": list(query)})
        return JsonResponse({"zones": []})


class ApiFonctionsMetierView(LoginRequiredMixin, generic.View):
    """Page d'accès API pour obtenir les fonctions associées au domaine métier sélectionné"""

    def get(self, request):
        mon_form = ApiListeFonctionsMetierForm(request.GET)
        if mon_form.is_valid():
            query = (
                FonctionsMetier.objects.filter(domaine=mon_form.cleaned_data["domaine"])
                .order_by("pk")
                .values_list("pk", flat=True)
            )

            return JsonResponse({"fonctions": list(query)})
        return JsonResponse({"fonctions": []})


class ApiImportExcelView(LoginRequiredMixin, generic.View):
    """Page d'accès API pour obtenir le status de la commande d'import excel"""

    def get(self, request, task_id):
        if request.user.is_staff:
            task = AsyncResult(task_id)
            return JsonResponse({"status": task.state})
        return JsonResponse({"status": None})


# test de cartographie de site
class CartoView(LoginRequiredMixin, generic.View):
    """Page de visualisation de la cartographie d'un site"""

    template_name = "inventaire/cartographie_site.html"
    menu_actif = "carto"

    def get(self, request):
        mon_form = CartoForm(request.GET, user=self.request.user)
        dessin, mode, localisation = "", "", ""
        if not mon_form.is_valid():
            if request.GET:  # si des paramètres GET sont présents
                messages.add_message(self.request, messages.WARNING, "La requête contient des paramètres invalides")
        else:
            localisation_usid = mon_form.cleaned_data["usid"]
            localisation_ville = mon_form.cleaned_data["ville"]
            localisation_quartier = mon_form.cleaned_data["quartier"]
            toutes_localisations = Localisation.objects.filter(
                zone_usid=localisation_usid, nom_ville=localisation_ville, nom_quartier=localisation_quartier
            )
            if toutes_localisations:
                localisation = f"{toutes_localisations[0].get_zone_usid_display()} - {localisation_ville} - {localisation_quartier}"
                mode = int(mon_form.cleaned_data["moteur"])

                tous_systemes_locaux = set(
                    SystemeIndustriel.objects.filter(localisation__in=toutes_localisations, fiche_corbeille=False)
                )
                tous_systemes_distants = set()
                for temp_sys_local in tous_systemes_locaux:
                    for temp_sys_connecte in temp_sys_local.systemes_connectes.all():
                        if (
                            temp_sys_connecte.localisation not in toutes_localisations
                            and not temp_sys_connecte.fiche_corbeille
                        ):
                            tous_systemes_distants.add(temp_sys_connecte)
                tous_systemes = {}
                for temp_sys in tous_systemes_locaux.union(tous_systemes_distants):
                    if temp_sys.localisation in tous_systemes:
                        tous_systemes[temp_sys.localisation].append(temp_sys)
                    else:
                        tous_systemes[temp_sys.localisation] = [temp_sys]

                # dessin avec GoJS
                if mode == 1:
                    dessin = {"class": "GraphLinksModel", "nodeDataArray": [], "linkDataArray": []}
                    dessin["nodeDataArray"].append(
                        {"key": "base", "text": localisation, "color": "#fcecea", "isGroup": True}
                    )
                    for temp_lieu in tous_systemes:
                        if (
                            temp_lieu.nom_ville == localisation_ville
                            and temp_lieu.nom_quartier == localisation_quartier
                        ):
                            is_local = True
                            group_color = "DarkRed"
                            box_color = "LightCoral"
                        else:
                            is_local = False
                            group_color = "RoyalBlue"
                            box_color = "SkyBlue"

                        if is_local:
                            dessin["nodeDataArray"].append(
                                {
                                    "key": f"loc_{temp_lieu.pk}",
                                    "text": str(temp_lieu),
                                    "color": group_color,
                                    "isGroup": True,
                                    "group": "base",
                                }
                            )
                        else:
                            dessin["nodeDataArray"].append(
                                {
                                    "key": f"loc_{temp_lieu.pk}",
                                    "text": str(temp_lieu),
                                    "color": group_color,
                                    "isGroup": True,
                                }
                            )
                        for temp_sys in tous_systemes[temp_lieu]:
                            dessin["nodeDataArray"].append(
                                {
                                    "key": temp_sys.pk,
                                    "text": temp_sys.nom,
                                    "color": box_color,
                                    "group": f"loc_{temp_lieu.pk}",
                                }
                            )

                    for i in Interconnexion.objects.filter(systeme_from__in=tous_systemes_locaux):
                        # retire les doublons dans les interconnections des systèmes locaux entre eux
                        if (
                            not {"from": i.systeme_to.pk, "to": i.systeme_from.pk, "text": i.get_type_liaison_display()}
                            in dessin["linkDataArray"]
                        ):
                            dessin["linkDataArray"].append(
                                {"from": i.systeme_from.pk, "to": i.systeme_to.pk, "text": i.get_type_liaison_display()}
                            )
                    dessin = dumps(dessin)

                # dessin avec MermaidJS
                elif mode == 0:
                    mermaid_local = ["graph TB", f"subgraph C[{localisation_ville} - {localisation_quartier}]"]
                    mermaid_distant = []
                    mermaid_liens = []
                    mermaid_color = ["style C fill:#fcecea, stroke: DarkRed"]
                    for temp_lieu in tous_systemes:
                        if (
                            temp_lieu.nom_ville == localisation_ville
                            and temp_lieu.nom_quartier == localisation_quartier
                        ):
                            is_local = True
                            group_color = "LightCoral"
                            box_color = "MistyRose"
                            stroke_color = "DarkRed"
                        else:
                            is_local = False
                            group_color = "LightBlue"
                            box_color = "LightCyan"
                            stroke_color = "RoyalBlue"
                        if is_local:
                            mermaid_local.append(f"subgraph B{temp_lieu.pk}[{str(temp_lieu)}]")
                        else:
                            mermaid_distant.append(f"subgraph B{temp_lieu.pk}[{str(temp_lieu)}]")
                        mermaid_color.append(f"style B{temp_lieu.pk} fill: {group_color}, stroke: {stroke_color}")
                        for temp_sys in tous_systemes[temp_lieu]:
                            if is_local:
                                mermaid_local.append(f'A{temp_sys.pk}("{temp_sys.nom}")')
                            else:
                                mermaid_distant.append(f'A{temp_sys.pk}("{temp_sys.nom}")')
                            mermaid_color.append(f"style A{temp_sys.pk} fill: {box_color}, stroke: {stroke_color}")
                        if is_local:
                            mermaid_local.append("end")
                        else:
                            mermaid_distant.append("end")

                    for i in Interconnexion.objects.filter(systeme_from__in=tous_systemes_locaux):
                        # retire les doublons dans les interconnections des systèmes locaux entre eux
                        if (
                            not f"A{i.systeme_to.pk} <-- {i.get_type_liaison_display()} --> A{i.systeme_from.pk}"
                            in mermaid_liens
                        ):
                            mermaid_liens.append(
                                f"A{i.systeme_from.pk} <-- {i.get_type_liaison_display()} --> A{i.systeme_to.pk}"
                            )
                    dessin = "\n".join(mermaid_local + ["end"] + mermaid_distant + mermaid_liens + mermaid_color)

        contexte = {
            "actif": self.menu_actif,
            "user": request.user,
            "site_choisi": localisation,
            "mon_form": mon_form,
            "page_vide": localisation == "",
            "mode": mode,
            "dessin": dessin,
        }
        return render(request, self.template_name, contexte)
