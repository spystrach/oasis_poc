# OASIS POC

A proof of concept for industrial systems inventory.

**The `env_example` folder provides a sample configuration. It should **not** be used as-is!**

## Deployment

### Dependencies

This project is containerized. The machine on which the project will be deployed must have:
- *Docker Engine*
- An orchestrator compatible with *docker-compose*

### Environment Variables

Variables must be created in a file at *env/stack.prod.env*. The tables below list them.  
**Bold** variables must absolutely be changed.  
The *env_example* folder provides all variables, ready to use for testing.

#### Web Server

| Variable Name              | Description                                                              |
|---------------------------|--------------------------------------------------------------------------|
| ***SECRET_KEY***          | the secret key used by the server                                        |
| *DEBUG*                   | enables development mode on the server                                   |
| ***ALLOWED_HOSTS***       | allowed hosts                                                            |
| ***CSRF_TRUSTED_ORIGINS***| trusted origins for CSRF requests                                        |
| *SQL_ENGINE*              | the database engine used                                                 |
| ***SQL_DATABASE***        | the name of the database                                                 |
| ***SQL_USER***            | the database user                                                        |
| ***SQL_PASSWORD***        | the database user's password                                             |
| *SQL_HOST*                | the hostname of the database (**do not change**)                         |
| *SQL_PORT*                | the database access port (**do not change**)                             |
| ***MAIL_CONTACT***        | the email address for contact requests                                   |
| ***DEMO_BANNER***         | indicates if the site is in demo mode (login page with a message)        |

#### SQL Database

| Variable Name           | Description                                     |
|------------------------|-------------------------------------------------|
| ***POSTGRES_USER***    | the database user                               |
| ***POSTGRES_PASSWORD***| the database user's password                    |
| ***POSTGRES_DB***      | the name of the database                        |

*Note: These variables must match those defined for the web server.*

#### Key-Value Store (Redis)

| Variable Name         | Description                                         |
|-----------------------|----------------------------------------------------|
| ***REDIS_PASSWORD***  | the password to access the Redis service           |

#### Background Tasks

| Variable Name               | Description                                                       |
|-----------------------------|-------------------------------------------------------------------|
| ***CELERY_BROKER_URL***     | connection URL for the message broker service                     |
| ***CELERY_RESULT_BACKEND*** | connection URL for the result backend service                     |
| *CELERY_TASK_TRACK_START*   | defines whether the service closely tracks task execution status  |

*Note: These variables must match those defined for the key-value store.*

### Launch

Simply run the **docker-compose.prod.yml** file using docker-compose (or an orchestrator).  
The images will be downloaded and the containers started automatically.

```shell
docker-compose -f docker-compose.prod.yml up
```

For deployment in development or pre-production mode, refer to *[CONTRIBUTING.md](./CONTRIBUTING.md)*.

## Account Management in Production

In the admin panel, you can create users and groups.

The standard approach is to create groups with specific permissions, then add users to these groups without assigning individual permissions.

The following special permissions have been created:

| View Permissions              | Edit Permissions              |
|-------------------------------|-------------------------------|
| View the *Angers* area        | Edit the *Angers* area        |
| View the *Bourges-Avord* area | Edit the *Bourges-Avord* area |
| View the *Cherbourg* area     | Edit the *Cherbourg* area     |
| View the *Évreux* area        | Edit the *Évreux* area        |
| View the *Bricy* area         | Edit the *Bricy* area         |
| View the *Rennes* area        | Edit the *Rennes* area        |
| View the *Tours* area         | Edit the *Tours* area         |

Additional permissions have been created for statistics viewing:
- View detailed statistics of one’s zone (optimized for local CISOs)
- View global statistics of all zones (optimized for regional CISOs)
- View anonymized global statistics (for internal decision-makers)
- View censored anonymized global statistics (for external decision-makers)

The administrator automatically sees all systems, as they are granted all permissions by default.

### Data Import

The administrator can, via a special page, import data from historical Excel files.
They also have the option to completely clean a zone before proceeding with the import.
