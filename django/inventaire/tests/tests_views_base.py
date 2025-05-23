"""Définition des tests unitaires de l'inventaire pour les vues de bases"""

import logging

from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse


logger = logging.getLogger(__name__)


@tag("views", "views-base", "views-base-login")
class LoginViewTest(TestCase):
    """Classe de test de la vue de connection"""

    @classmethod
    def setUpTestData(cls):
        # utilisateur pouvant se connecter
        cls.user_lambda = User.objects.create_user(
            username="lambda",
            password="lambda123",
        )

    def tearDown(self) -> None:
        self.client.logout()

    def test_login_affichage_anonyme(self):
        """Un utilisateur non connecté affiche la page"""
        response = self.client.get(reverse("inventaire:login"))
        self.assertEqual(response.status_code, 200)

    def test_login_affichage_deja_connecte(self):
        """Un utilisateur déjà connecté affiche la page et se fait rediriger"""
        self.client.login(username="lambda", password="lambda123")
        response = self.client.get(reverse("inventaire:login"))
        self.assertRedirects(response, reverse("inventaire:accueil"))

    def test_login_connection_mauvais(self):
        """Un utilisateur non connecté veut se connecter et échoue"""
        self.assertFalse(self.client.login(username="lambda", password="lambda"))
        # login par une requête post
        response = self.client.post(
            reverse("inventaire:login"), data={"id_username": "adbmal", "id_password": "lambda"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/login.html")

    def test_login_connection_ok(self):
        """Un utilisateur non connecté veut se connecter et réussit"""
        self.assertTrue(self.client.login(username="lambda", password="lambda123"))
        # login par une requête post
        response = self.client.post(
            reverse("inventaire:login"),
            data={"username": "lambda", "password": "lambda123"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/accueil.html")


@tag("views", "views-base", "views-base-home")
class HomeView(TestCase):
    """Classe de test de la vue de la page d'accueil"""

    @classmethod
    def setUpTestData(cls):
        # utilisateur pouvant se connecter
        cls.user = User.objects.create_user(
            username="lambda",
            password="lambda123",
        )

    def tearDown(self) -> None:
        self.client.logout()

    def test_accueil_anonyme(self):
        """Un utilisateur non connecté sera redirigé vers la page de login"""
        response = self.client.get(reverse("inventaire:accueil"))
        url_attendu = reverse("inventaire:login") + "?next=" + reverse("inventaire:accueil")
        self.assertRedirects(response, url_attendu)

    def test_accueil_connecte(self):
        """Un utilisateur connecté aura sa page d'accueil personnalisée"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("inventaire:accueil"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/accueil.html")


@tag("views", "views-base", "views-base-compte")
class CompteView(TestCase):
    """Classe de test de la vue de la page de détails d'un compte utilisateur"""

    @classmethod
    def setUpTestData(cls):
        # utilisateur pouvant se connecter
        cls.user = User.objects.create_user(
            username="lambda",
            password="lambda123",
        )

    def tearDown(self) -> None:
        self.client.logout()

    def test_compte_anonyme(self):
        """Un utilisateur non connecté sera redirigé vers la page de login"""
        response = self.client.get(reverse("inventaire:compte"))
        url_attendu = reverse("inventaire:login") + "?next=" + reverse("inventaire:compte")
        self.assertRedirects(response, url_attendu)

    def test_compte_connecte(self):
        """Un utilisateur connecté aura sa page de détails de son compte"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("inventaire:compte"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventaire/compte.html")
