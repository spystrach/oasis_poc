# Contributing on POC OASIS

## Installation

### Clonage et environnement

Il faut commencer par cloner le répertoire avec *git*. 
Puis créer un environnement virtuel python avec `python -m venv venv`.
Activer l'environnement virtuel avec `source venv/bin/activate` (pour linux) ou
`venv/bin/activate.bat` (pour windows).

Installer les dépendances avec `pip install -r django/requirements.txt`.

### Setup initial de base de donnée de dev

En version de développement, le moteur de base de donnée est géré dans un fichier *db.sqlite*.
Cette base de donnée est créée par les commandes suivantes dans le dossier *django/*. 
Elle est persistante durant le développement.

Les commandes suivantes permettent de la configurer.

```shell
python django/manage.py makemigrations inventaire
python django/manage.py migrate
python django/manage.py createsuperuser
```

Puis, certaines données persistantes peuvent être ajoutée avec :

```shell
python django/manage.py loaddata django/inventaire/fixtures/inventaire/metiers.json
python django/manage.py loaddata django/inventaire/fixtures/inventaire/groupes.json
```

### Lancer le serveur de dev

La variable d'environnement **DEBUG=true** doit exister, sinon les fichiers statiques
ne seront pas gérés par le serveur. 

Pour lancer le serveur, il faut utiliser `python django/manage.py runserver`

## Tests unitaires et d'intégrations

Ce projet comporte toutes sortes de tests qui sont dans le dossier *django/tests*. 
Chaque commit dans le dossier doit être vérifié en utilisant ces tests.

La commande est `python django/manage.py tests inventaire`

Il est possible de ne lancer qu'une partie des tests avec ajoutant l'argument 
`--tag nomDuTag` à la fin.

Les principaux tags disponibles sont :

| nom du tag   | explications                                    |
|--------------|-------------------------------------------------|
| models       | teste les modèles de la base de donnée          |
| views        | teste les pages html                            |
| utils        | teste les fonctions utilitaires                 |
| templatetags | teste les fonctions utilisés dans les templates |


## Déploiement en pré-production

La phase de pré-production est aussi conteneurisée, mais le DEBUG est activé. 
La base de donnée est nettoyée à chaque redémarrage des conteneurs et un administrateur 
est créé automatiquement.

### Variables d'environnement

Les variables doivent être créés dans un fichier *env/stack.pre-prod.env*. Les tableaux 
ci-dessous les listent. Les variables en gras sont absolument à changer. 
Le dossier *env_exemple* fournit l'ensemble des variables, prêt à fonctionner pour des tests.

#### Serveur web

| Nom de la variable              | explication de la variable                                            |
|---------------------------------|-----------------------------------------------------------------------|
| ***SECRET_KEY***                | la clef secrete utilisé par le serveur                                |
| *DEBUG*                         | le serveur est en mode développement                                  |
| ***ALLOWED_HOSTS***             | les hôtes autorisé                                                    |
| ***CSRF_TRUSTED_ORIGINS***      | les hôtes autorisé pour les requêtes CSRF                             |
| *SQL_ENGINE*                    | le moteur de base de donnée utilisé                                   |
| ***SQL_DATABASE***              | le nom de la base de donnée                                           |
| ***SQL_USER***                  | le nom de l'utilisateur de la BDD                                     |
| ***SQL_PASSWORD***              | le mot de passe de l'utilisateur de la BDD                            |
| *SQL_HOST*                      | le nom de l'hôte de la base de donnée (**ne pas changer**)            |
| *SQL_PORT*                      | le port d'accès de la base de donnée (**ne pas changer**)             |
| ***MAIL_CONTACT***              | l'adresse mail pour les demandes de contacts                          |
| ***DEMO_BANNER***               | si le site est en mode démonstration (page de login avec un message)  |
| ***DJANGO_SUPERUSER_USERNAME*** | le nom de l'administrateur                                            |
| ***DJANGO_SUPERUSER_PASSWORD*** | le mot de passe de l'administrateur                                   |
| ***DJANGO_SUPERUSER_EMAIL***    | l'email de l'administrateur                                           |

#### Base de donnée

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
| *CELERY_TASK_TRACK_STARTE** | définit si le service suit plus précisément l'état d'execution d'une tache |

*Nota : ces variables doivent correspondre avec celles définies pour la base de donnée clef=valeur.*

### Lancement

Il suffit de lancer via *docker-compose* (ou un autre orchestrateur) le fichier **docker-compose.pre-prod.yml**.
Les images seront construites automatiquement puis les conteneurs démarrés.

`docker-compose -f docker-compose.pre-prod.yml up --build`
