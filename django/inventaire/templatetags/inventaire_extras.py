"""Définition des balises et filtres de gabarits pour l'inventaire"""

from django import template
from django.conf import settings
from django.template.defaultfilters import date as _date

register = template.Library()


@register.simple_tag(takes_context=True)
def lien_pagination(context, value):
    """Ajoute le paramètre de pagination en conservant les paramètres actuels"""
    get_params = context.request.GET.copy()
    get_params["page"] = value
    return get_params.urlencode()


@register.simple_tag(takes_context=True)
def get_mailto_contact(context):
    """Récupère le mail de contact pour afficher dans la barre de navigation"""
    if context.request.user.is_authenticated:
        return f"mailto:{settings.MAIL_CONTACT}?subject=Oasis - demande de {context.request.user.get_full_name()}"
    else:
        return f"mailto:{settings.MAIL_CONTACT}?subject=Oasis - demande de création de compte"


@register.filter(is_safe=True)
def nom_ville_humain(value):
    """Affiche les noms de villes de manière lisible par un humain"""
    return value[0].upper() + value[1:].replace("-", " ")


@register.filter(is_dafe=True)
def format_date_heure_court(value):
    """Affiche une date et une heure de manière esthétique"""
    return _date(value, "d/m/Y à H\hi")


@register.filter(is_safe=True)
def format_date_court(value):
    """Affiche une date de manière brève"""
    return _date(value, "d/m/Y")


@register.filter(is_safe=True)
def format_date_long(value):
    """Affiche une date de manière esthétique"""
    return _date(value, "j F Y")


@register.filter(is_safe=True)
def bulma_form_label(value, arg=None):
    if not arg:
        arg = "normal"
    return value.label_tag(attrs={"class": f"label is-{arg}"})


@register.filter(is_safe=True)
def bulma_form_label_checkbox(value, arg=None):
    if not arg:
        arg = "normal"
    return value.label_tag(attrs={"class": f"checkbox label is-display-inline-block is-{arg}"})


@register.filter(is_safe=True)
def bulma_menu_actif(value, arg):
    """Permet d'afficher le menu courant comme celui qui est sélectionné"""
    if value == arg:
        return "is-active "
    else:
        return ""


@register.filter(is_safe=True)
def bulma_message_tag_couleur(value):
    """Permet de changer le tag d'un message en couleur bulma"""
    if value == "info":
        return "is-info"
    elif value == "success":
        return "is-success"
    elif value == "warning":
        return "is-warning"
    elif value == "error":
        return "is-danger"
    else:
        return ""
