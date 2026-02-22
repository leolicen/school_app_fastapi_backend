
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
| /courses | GET | Leggi info sul corso dello studente | Sì | Attivo, Inattivo |

### 3. Router Internship

| Endpoint | Metodo | Descrizione | Auth | Account attivo/inattivo |
| -------- | ------ | ----------- | ---- | ----------------------- |
| /internship-agreements | GET | Leggi info accordo/i di tirocinio | Sì | Attivo, Inattivo |
| /internship-agreements/{agreement_id}/entries | GET | Leggi info turni di tirocinio | Sì | Attivo, Inattivo |
| /internship-agreements/{agreement_id}/entries | POST | Crea nuovo turno di tirocinio | Sì | Attivo |
| /internship-agreements/{agreement_id}/entries/{entry_id} | DELETE | Elimina turno tirocinio | Sì | Attivo |

### 4. Router Student

| Endpoint | Metodo | Descrizione | Auth | Account attivo/inattivo |
| -------- | ------ | ----------- | ---- | ----------------------- |
| /students/me | GET | Leggi info studente | Sì | Attivo, Inattivo |
| /students/me | PATCH | Aggiorna info studente | Sì | Attivo | 
| /students/me | DELETE | Elimina account studente | Sì | Attivo, Inattivo |
| /students/change-password | Cambia pwd studente | POST | Sì | Attivo, Inattivo |





