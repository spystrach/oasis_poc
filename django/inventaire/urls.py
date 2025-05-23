"""Définition des urls de l'inventaire"""

from django.contrib.auth.views import LogoutView
from django.urls import path

from inventaire import views


app_name = "inventaire"
urlpatterns = [
    # pages de connection
    path("login", views.LoginView.as_view(), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),

    # pages d'accueil et de compte
    path("", views.HomeView.as_view(), name="accueil"),
    path("compte", views.CompteView.as_view(), name="compte"),

    # les systèmes industriels
    path("systemes", views.SystemesRechercheView.as_view(), name="systemes_recherche"),
    path("systemes/creation", views.SystemesCreationView.as_view(), name="systemes_creation"),
    path("systemes/<int:pk>", views.SystemesDetailsView.as_view(), name="systemes_details"),
    path("systemes/<int:pk>/modification", views.SystemesModificationView.as_view(), name="systemes_modification"),
    path("systemes/<int:pk>/suppression", views.SystemesSuppressionView.as_view(), name="systemes_suppression"),

    # les contrats de maintenance
    path("contrats", views.ContratRechercheView.as_view(), name="contrats_recherche"),
    path("contrats/creation", views.ContratsCreationView.as_view(), name="contrats_creation"),
    path("contrats/<int:pk>", views.ContratsDetailsView.as_view(), name="contrats_details"),
    path("contrats/<int:pk>/modification", views.ContratsModificationView.as_view(), name="contrats_modification"),
    path("contrats/<int:pk>/suppression", views.ContratsSuppressionView.as_view(), name="contrats_suppression"),

    # l'import des systèmes via fichiers excel (fonctionnalité temporaire)
    path("import", views.ImporteExcelView.as_view(), name="import_excel"),
    path("import/<str:task_id>", views.ImporteExcelResultView.as_view(), name="import_excel_resultat"),

    # les chemins d'API pour les requêtes AJAX
    path("api/villes", views.ApiVillesView.as_view(), name="api_villes"),
    path("api/quartiers", views.ApiQuartierView.as_view(), name="api_quartiers"),
    path("api/zones", views.ApiZoneView.as_view(), name="api_zones"),
    path("api/fonctions", views.ApiFonctionsMetierView.as_view(), name="api_fonctions"),
    path("api/import/<str:task_id>", views.ApiImportExcelView.as_view(), name="api_import"),

    # chemin pour la carto
    path("cartographie", views.CartoView.as_view(), name="cartographie_site"),
]
