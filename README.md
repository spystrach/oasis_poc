# POC OASIS

Une preuve de concept pour l'inventaire des systèmes industriels.

**Le dossier `env_exemple` fournit un exemple de configuration. Ils ne doivent pas être utilisés tels quels !**

## Déploiement

### Dépendances

Ce projet est conteneurisé, la machine sur lequel sera déployé le projet devra disposer de :
- *Docker Engine*
- Un orchestrateur compatible avec *docker-compose*

### Variables d'environnement

Les variables doivent être créés dans un fichier *env/stack.prod.env*. Les tableaux ci-dessous 
les listent. Les variables en gras sont absolument à changer.
Le dossier *env_exemple* fournit l'ensemble des variables, prêt à fonctionner pour des tests.

#### Serveur web

| Nom de la variable         | explication de la variable                                            |
|----------------------------|-----------------------------------------------------------------------|
| ***SECRET_KEY***           | la clef secrete utilisé par le serveur                                |
| *DEBUG*                    | le serveur est en mode développement                                  |
| ***ALLOWED_HOSTS***        | les hôtes autorisé                                                    |
| ***CSRF_TRUSTED_ORIGINS*** | les hôtes autorisé pour les requêtes CSRF                             | 
| *SQL_ENGINE*               | le moteur de base de donnée utilisé                                   |
| ***SQL_DATABASE***         | le nom de la base de donnée                                           |
| ***SQL_USER***             | le nom de l'utilisateur de la BDD                                     |
| ***SQL_PASSWORD***         | le mot de passe de l'utilisateur de la BDD                            |
| *SQL_HOST*                 | le nom de l'hôte de la base de donnée (**ne pas changer**)            |
| *SQL_PORT*                 | le port d'accès de la base de donnée (**ne pas changer**)             |
| ***MAIL_CONTACT***         | l'adresse mail pour les demandes de contacts                          |
| ***DEMO_BANNER***          | si le site est en mode démonstration (page de login avec un message)  |

#### Base de donnée SQL

| Nom de la variable      | explication de la variable                 |
|-------------------------|--------------------------------------------|
| ***POSTGRES_USER***     | le nom de l'utilisateur de la BDD          |
| ***POSTGRES_PASSWORD*** | le mot de passe de l'utilisateur de la BDD |
| ***POSTGRES_DB***       | le nom de la base de donnée                |

*Nota : ces variables doivent correspondre avec celles définies pour le serveur web.*

#### Base de donnée clef=valeur

| Nom de la variable      | explication de la variable              |
|-------------------------|-----------------------------------------|
| ***REDIS_PASSWORD***    | le mot de passe pour accéder au service |

#### Taches de fond

| Nom de la variable          | explication de la variable                                                 |
|-----------------------------|----------------------------------------------------------------------------|
| ***CELERY_BROKER_URL***     | l'url de connection pour le service de transmission de message             |
| ***CELERY_RESULT_BACKEND*** | l'url de connection vers le service de stockage des résultats              |
| *CELERY_TASK_TRACK_START**  | définit si le service suit plus précisément l'état d'execution d'une tache |

*Nota : ces variables doivent correspondre avec celles définies pour la base de donnée clef=valeur.*

### Lancement

Il suffit de lancer via docker-compose (ou un orchestrateur) le fichier **docker-compose.prod.yml**.
Les images seront téléchargées puis les conteneurs démarrés automatiquement.

```shell
docker-compose -f docker-compose.prod.yml up
```

Pour le déploiement en mode développement et pré-production, consulter 
*[CONTRIBUTING.md](./CONTRIBUTING.md)*.

## Gestion des comptes en production

Dans le panel admin, il est possible de créer des utilisateurs et des groupes.

Le fonctionnement standard est de créer des groupes avec des permissions spécifiques. Il faut
ensuite ajouter des utilisateurs dans les groupes, sans accorder des droits spécifiques aux utilisateurs.

Les permissions spéciales suivantes ont été créées :

| droits en consultations                      | droits en modification                      |
|----------------------------------------------|---------------------------------------------|
| consulter la zone de l'USID d'Angers         | modifier la zone de l'USID d'Angers         | 
| consulter la zone de l'USID de Bourges-Avord | modifier la zone de l'USID de Bourges-Avord |
| consulter la zone de l'USID de Cherbourg     | modifier la zone de l'USID de Cherbourg     |
| consulter la zone de l'USID d'Évreux         | modifier la zone de l'USID d'Évreux         |
| consulter la zone de l'USID de Bricy         | modifier la zone de l'USID de Bricy         |
| consulter la zone de l'USID de Rennes        | modifier la zone de l'USID de Rennes        |
| consulter la zone de l'USID de Tours         | modifier la zone de l'USID de Tours         |

Et des permissions pour l'affichage des statistiques ont aussi été créés :
- afficher des statistiques détaillées de sa zone (optimisée pour les RSSI)
- afficher des statistiques globales de toutes les zones (optimisée pour les BSSI)
- afficher des statistiques anonymes globales (pour les décideurs internes)
- afficher des statistiques anonymes globales censurées (pour les décideurs externes)

L'administrateur voit tous les systèmes automatiquement, car il a automatiquement tous les droits.

### Importation de données

L'administrateur peut via une page spéciale, importer les données depuis les fichiers excels historiques.
Il a la possibilité de nettoyer complètement la zone avant de procéder à l'import.
