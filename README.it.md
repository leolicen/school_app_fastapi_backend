
# School-app Fastapi Backend

> Semplice backend di API REST per l'applicazione di un corso post diploma con gestione dei tirocini

Italian | [English](README.md)

![License](https://img.shields.io/badge/license-MIT-brightgreen)
![FastApi](https://img.shields.io/badge/FastApi-%23009688?logo=fastapi&logoColor=white)
![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)
![MySQL 8.0](https://img.shields.io/badge/MySQL-8.0-%234479A1)
![phpMyAdmin](https://img.shields.io/badge/phpmyadmin-%236C78AF?logo=phpmyadmin&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23FF4438?logo=redis&logoColor=white)
![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-%23E92063?logo=pydantic&logoColor=white)
![SQLModel](https://img.shields.io/badge/SQLModel-%237e56c2)
![Docker](https://img.shields.io/badge/Docker-%232496ED?logo=docker&logoColor=white)

## Panoramica

Progetto personale per imparare le logiche di sviluppo backend, replicando il funzionamento di una applicazione usata 
per tener traccia di un tirocinio svolto durante un corso IT post diploma. In futuro sarà collegata 
a un'applicazione Flutter che, a sua volta, cerca di replicarne l'interfaccia grafica.

#### Obiettivo principale  
Studenti gestiscono tirocini come parte di un corso tecnico post diploma.  
Azioni possibili:
- lettura info del corso frequentato
- registrazione/visualizzazione/eliminazione turni di lavoro
- gestione dati personali 

#### Funzionamento
- **Dati statici** [aziende, corsi, accordi di tirocinio] => creati manualmente nel database (con phpMyAdmin)
- **Dati dinamici** [studenti, turni di lavoro, token] => gestiti da endpoint API

#### Sviluppo locale 
Stack di 4 container Docker (o applicazione singola eseguita con uv in unione a MySQL e Redis)

## Caratteristiche principali

- 🔐 **Autenticazione JWT** => login, autenticazione e logout con:
    - *Access Token* (creazione, validazione e blacklisting tramite redis)
    - *Refresh Token* (creazione, validazione, rotazione e cron job per eliminare i token scaduti)

- 🔧 **Operazioni CRUD**:
    - Studenti => registrazione di nuovi studenti, lettura e aggiornamento dei dati di uno studente, eliminazione di un account (temporanea e definitiva)
    \+ cambio password (come studente autenticato) e reset della password tramite email (come studente non autenticato)
    - Accordi di tirocinio => lettura dell'accordo o degli accordi del singolo studente
    - Turni di tirocinio =>  aggiunta di nuovi turni, lettura e eliminazione dei turni già inseriti  
    - Corsi => lettura dei dati del corso frequentato dallo studente

- 🏢 **Modelli dati** con SQLModel e Pydantic
- 🛡️ **Gestione degli errori** con errori e handler personalizzati 
- 🧪 **Test** con Pytest
- 📚 **Auto-documentazione** con FastApi /docs & /redoc
- 🐳 **Docker Compose** => stack di 4 container Docker (app FastAPI + MySQL + phpMyAdmin + Redis)

## Avvio rapido

### Prerequisiti

- Docker 20.10+ con plugin Docker Compose:
    - **Windows/Mac**: Docker Desktop
    - **Linux**: pacchetti 'docker' + 'docker compose' 

### 1. Clonazione repo & set-up dell'ambiente 

Clona la repository:

```bash
git clone https://github.com/leolicen/school_app_fastapi_backend.git
```

Apri la cartella del progetto:

```bash
cd school-app-fastapi-backend
```

Rinomina il file `.env.example` in `.env`:

```bash
cp .env.example .env
```

Modifica il file `.env` sostituendo i commenti accanto alle variabili con valori personalizzati:

**Es.** *Cancella il commento '# set a secure password'.*
```python
# Database MySQL
DB_USER=root
DB_PASSWORD= # set a secure password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=myapp_db
```

*Imposta la password per il tuo database.*
```python
# Database MySQL
DB_USER=root
DB_PASSWORD=yourSecurePassword
DB_HOST=localhost
DB_PORT=3306
DB_NAME=myapp_db
```

Fai lo stesso per tutte le variabili commentate. Naturalmente, puoi modificare anche i valori già impostati (es. DB_NAME).

### 2. Password-reset tramite email (Facoltativo)

L'applicazione usa Resend per permettere all'utente di resettare la propria password tramite email.

Se vuoi utilizzare questo servizio, [crea un account Resend](https://resend.com/home).

[Aggiungi un dominio](https://resend.com/domains) personale per inviare e ricevere email. Altrimenti, usa l'indirizzo email di test 
(già impostato in `.env`). N.B. L'indirizzo di test funziona solo con l'email fornita in fase di registrazione.

Aggiorna il file `.env` con l'API key di Resend e il dominio che vuoi utilizzare.

### 3. Lancia i container 

Lancia lo stack completo dalla cartella root del progetto:

```bash
docker-compose up -d
```

### 4. Accedi all'applicazione

- **Documentazione API**: http://localhost:8000/docs oppure http://localhost:8000/redoc
- **phpMyAdmin**: http://localhost:8080 (usa le tue credenziali MySQL per effettuare il login)
- **Redis**: http://localhost:6379

## Sviluppo locale (No Docker)

⚠️ **Attenzione**: l'applicazione funziona senza Docker, ma **richiede MySQL 
e Redis attivi** separatamente (credenziali nel file '.env').

### 1. Setup uv 

Installa uv (se necessario): [installazione uv](https://docs.astral.sh/uv/getting-started/installation/).

Scarica le dipendenze del progetto:

```bash
uv sync
```

### 2. Avvia la app

Avvia l'applicazione (con hot-reload):

```bash
uv run python main.py
```

## Esecuzione dei test

I test utilizzano un database SQLite in-memory e un mock di Redis — nessun servizio esterno richiesto.

Esegui tutti i test:

```bash
uv run pytest
```

Esegui solo i test unitari:

```bash
uv run pytest -m unit
```

Esegui solo i test di integrazione:

```bash
uv run pytest -m integration
```

## Struttura del progetto

```bash
school-app-fastapi-backend/
├── app/
│   ├── core/
│   ├── exceptions/
│   ├── models/
│   ├── routers/
│   ├── services/
│   ├── utils/
│   ├── app.py
│   └── dependencies.py
├── test/
│   ├── conftest.py
│   ├── integration/
│   └── unit/
├── .dockerignore
├── .env.example
├── .gitignore
├── .python-version
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── main.py
├── pyproject.toml
├── pytest.ini
├── README.it.md
├── README.md
└── uv.lock

```

## Endpoint API

### 1. Router Auth

| Endpoint | Metodo | Descrizione | Auth | 
| -------- | ------ | ----------- | ---- | 
| /auth/login | POST | Login JWT | No | 
| /auth/register | POST | Registrazione studente | No |
| /auth/password/reset-request | POST | Richiesta reset pwd | No |
| /auth/password/reset-confirm | POST | Conferma reset pwd | No |
| /auth/refresh | POST | Refresh di access & refresh token | Sì |
| /auth/logout | POST | Logout JWT | Sì |

### 2. Router Course

| Endpoint | Metodo | Descrizione | Auth | Account attivo/inattivo |
| -------- | ------ | ----------- | ---- | ----------------------- |
| /courses/ | GET | Lettura lista corsi attivi | No | - |
| /courses/me | GET | Lettura info corso studente | Sì | Attivo, Inattivo |

### 3. Router Internship

| Endpoint | Metodo | Descrizione | Auth | Account attivo/inattivo |
| -------- | ------ | ----------- | ---- | ----------------------- |
| /internship-agreements/ | GET | Lettura info accordo/i di tirocinio | Sì | Attivo, Inattivo |
| /internship-agreements/{agreement_id}/entries | GET | Lettura info turni di tirocinio | Sì | Attivo, Inattivo |
| /internship-agreements/{agreement_id}/entries | POST | Creazione nuovo turno di tirocinio | Sì | Attivo |
| /internship-agreements/{agreement_id}/entries/{entry_id} | DELETE | Eliminazione turno tirocinio | Sì | Attivo |

### 4. Router Student

| Endpoint | Metodo | Descrizione | Auth | Account attivo/inattivo |
| -------- | ------ | ----------- | ---- | ----------------------- |
| /students/me | GET | Lettura info studente | Sì | Attivo, Inattivo |
| /students/me | PATCH | Aggiornamento info studente | Sì | Attivo | 
| /students/me | DELETE | Eliminazione account studente | Sì | Attivo, Inattivo |
| /students/change-password | POST | Modifica pwd studente | Sì | Attivo, Inattivo |

## Roadmap

- [ ] Collegamento a un'app Flutter che replica l'interfaccia originale
- [ ] Aggiunta di un ruolo admin con endpoint per gestire studenti, aziende, corsi e accordi
- [ ] Espansione della copertura dei test

## Simulazione flusso 

Una volta lanciati i 4 container, segui gli step successivi per configurare e utilizzare correttamente l'ambiente. 

### 1. Crea un nuovo corso

Apri il browser e vai su [phpMyAdmin](http://localhost:8080), inserisci le tue credenziali (DB_USER e DB_PASSWORD in `.env`) e seleziona il database 'school_app' dal pannello di sinistra.

Apri la tabella 'courseindb' e clicca su 'Inserisci'.

![Crea un nuovo corso](/assets/screenshots/create_course.png)

Campi da popolare:

| Campo | Tipo | 
| :----- | :---- | 
| *course_type* | ❗obbligatorio | 
| *schedule* | ❎ opzionale | 
| *schedule_type* | ❎ opzionale | 
| *total_hours* | ❗obbligatorio | 
| *internship_total_hours* | ❗obbligatorio | 
| *start_date* |❗obbligatorio | 
| *location* | ❗obbligatorio | 
| *is_active* | ⚙️ default = 1 (True) | 
| *course_id* | ⚡ generato automaticamente | 
| *name* | ❗obbligatorio |
| *created_at* | ⚡ generato automaticamente |

Apri una nuova tab e vai su [API docs](http://localhost:8000/docs).

Scorri fino al router 'courses' e seleziona 'GET /courses/'. 

Clicca su 'Try it out'.

![Leggi la lista dei corsi](/assets/screenshots/get_courses.png)

Questo è un endpoint pubblico e dovrebbe restituire una lista di tutti i corsi attivi disponibili (vengono mostrati solo nome e id del corso). 

![Lista dei corsi](/assets/screenshots/get_courses_response.png)

Copia l'id del corso (course_id) e conservalo.

### 2. Registra un nuovo studente

Seleziona l'endpoint 'POST /auth/register' dal router 'auth'.

Clicca su 'Try it out' e riempi i seguenti campi del request body:

![Registra uno studente](/assets/screenshots/register_student.png)

| Campo | Tipo | Note |
| :----- | :---- | :----- |
| *name* | ❗obbligatorio | - |
| *surname* | ❗obbligatorio | - |
| *email* | ❗obbligatorio | - |
| *course_id* | ❗obbligatorio | incolla il 'course_id' copiato prima |
| *phone* | ❎ opzionale | - |
| *address* | ❎ opzionale | - |
|  *password* | ❗obbligatorio | la password deve essere lunga almeno 8 caratteri e includere almeno una lettera minuscola, una lettera maiuscola, un numero e un carattere speciale |

Copia email e password e conservali.

La response dovrebbe essere simile a questa:

![Response alla registrazione](/assets/screenshots/registration_response.png)

### 3. Effettua il login 

La registrazione comprende sia la creazione di un nuovo studente che il primo login, e restituisce come risposta un access token e un refresh token. 
Solitamente, un'applicazione frontend riceverebbe questa risposta, salverebbe i due token e li userebbe per effettuare richieste alle API.
In questo caso, però, è necessario effettuare il login manualmente attraverso il form OAuth2 all'interno della documentazione automatica di FastApi, così che sia possibile salvare i token e accedere agli endpoint protetti. 

Clicca sul bottone verde 'Authorize' in alto a destra e inserisci email e password dello studente appena creato.

![Form di login](/assets/screenshots/oauth2_form.png)

Vai all'endpoint 'GET /students/me' e prova a effettuare una richiesta.

Dovrebbe restituire qualcosa di simile:

![Info studente](/assets/screenshots/get_student_response.png)

### 4. Crea una nuova azienda 

Torna su [phpMyAdmin](http://localhost:8080) e apri la tabella 'companyindb'.

Crea una nuova azienda con i seguenti campi:

| Campo | Tipo | 
| :----- | :---- | 
| *company_id* | ⚡ generato automaticamente |
| *name* | ❗obbligatorio |
| *city* | ❗obbligatorio |
| *address* | ❗obbligatorio |
| *tutor* | ❎ opzionale |
| *created_at* | ⚡ generato automaticamente |

### 5. Crea un nuovo accordo di tirocinio 

Apri la tabella 'internshipagreementindb' e crea un nuovo accordo con i seguenti campi:

| Campo | Tipo | Note |
| :----- | :---- | :----- |
| *total_hours* | ❗obbligatorio | - |
| *attended_hours* | ❎ opzionale | aggiornato in automatico quando viene creato/eliminato un turno |
| *start_date* | ❗obbligatorio | - |
| *is_active* | ⚙️ default = 0 (False) | impostalo a 1 (True) così che sia possibile creare nuovi turni da subito* |
| *agreement_id* | ⚡ generato automaticamente | - |
| *student_id* | ❗obbligatorio | selezionalo dal dropdown in phpMyAdmin |
| *company_id* | ❗obbligatorio | selezionalo dal dropdown in phpMyAdmin |
| *created_at* | ⚡ generato automaticamente | - |

> **N.B.** Di solito, un accordo si crea in anticipo con una data d'inizio futura, prima della quale lo studente non può creare nuovi turni. L'accordo si attiva automaticamente tramite un cronjob il giorno specificato in 'start_date'. Per questo motivo il valore di default è 0 (False).

Torna su [API docs](http://localhost:8000/docs) e effettua una richiesta all'endpoint 'GET /internship-agreements/'.

Apparirà una lista di accordi appartenenti allo studente:

![Lista di accordi dello studente](/assets/screenshots/get_agreement_list_response.png)

Copia l'id dell'accordo (agreement_id) e conservalo.

⚠️ **Token scaduto?** Clicca 'Authorize', effettua il logout e poi di nuovo il login. Le docs FastAPI non permettono di estrarre manualmente il refresh token (per rinnovare entrambi i token tramite l'endpoint 'POST /auth/refresh'). 

### 6. Crea un nuovo turno di lavoro

Crea un nuovo turno di lavoro mediante l'endpoint 'POST /internship-agreements/{agreement_id}/entries', passando come parametro l'agreement_id.
I campi richiesti sono:

![Crea un nuovo turno](/assets/screenshots/create_entry.png)

| Campo | Tipo | Note |
| :----- | :---- | :----- |
| *entry_date* | ❗obbligatorio | deve corrispondere alla data odierna o a una data non più vecchia di 7 giorni |
| *start_time* | ❗obbligatorio | - |
| *end_time* | ❗obbligatorio | deve essere cronologicamente successiva alla start_time |
| *shift_type* | ❗obbligatorio | scegli fra 'in_office' e 'remote' |
| *description* | ❗obbligatorio |  max 150 caratteri |
| *agreement_id* | ❗obbligatorio  | - |

La risposta dovrebbe essere simile a questa:

![Risposta alla creazione di un turno](/assets/screenshots/create_entry_response.png)

Ora torna all'endpoint 'GET /internship-agreements/{agreement_id}/entries', passa l'agreement_id come parametro e premi 'execute'.
Una lista di turni (per il momento solo quello che abbiamo creato) dovrebbe essere visibile:

![Lista di turni](/assets/screenshots/get_agreem_entries.png)

Copia l'id del turno (entry_id) e conservalo.

### 7. Elimina un turno di lavoro

Vai all'endpoint 'DELETE /internship-agreements/{agreement_id}/entries/{entry_id}' e inserisci agreement_id e entry_id come parametri della richiesta.

![Elimina turno](/assets/screenshots/delete_entry.png)

La risposta dovrebbe essere la seguente:

![Risposta eliminazione turno](/assets/screenshots/delete_entry_response.png)

Ora, se esegui di nuovo una richiesta all'endpoint 'GET /internship-agreements/{agreement_id}/entries', dovresti ricevere una lista vuota:

![Lista di turni vuota](/assets/screenshots/empty_entries_list.png) 

### 8. Effettua il logout

Vai all'endpoint 'POST /auth/logout' e clicca 'execute'.

![Logout](/assets/screenshots/logout.png)

![Risposta logout](/assets/screenshots/logout%20response.png)

🎉 Hai appena completato la simulazione!

## Licenza

Questo progetto è distribuito con licenza [MIT](LICENSE).




