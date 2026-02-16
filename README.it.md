
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

Questa applicazione nasce come un progetto personale col principale obiettivo di imparare le logiche di funzionamento di un'applicazione
backend, oltre che per avere un progetto completo che possa avvicinarsi agli standard del mondo IT. 
Con questo codice ho cercato di emulare la logica di una app che ho usato per tener traccia di un tirocinio svolto nell'ambito di 
un corso IT post diploma. In futuro è mia intenzione collegarla a un'applicazione Flutter che, a sua volta, cerca di replicarne 
l'interfaccia grafica.

Questa repository è, chiaramente, clonabile e utilizzabile da chiunque sia interessato a provarla. L'applicazione è stata pensata per essere
eseguita in locale attraverso uno stack di 4 container Docker, ma può essere ovviamente modificata a piacimento.

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
- 🐳 **Docker Compose** => stack di 4 container Docker (app FastAPI + MySQL + phpmyadmin + redis)

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

*Cancella il commento '# set a secure password'.*
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

### 2. Lancia i container 

Lancia lo stack completo dalla cartella root del progetto:

```bash
docker-compose up -d
```

### 3. Accedi all'applicazione

- **Documentazione API**: http://localhost:8000/docs oppure http://localhost:8000/redoc
- **phpMyAdmin**: http://localhost:8080 (usa le tue credenziali MySql per effettuare il login)
- **Redis**: http://localhost:6379




