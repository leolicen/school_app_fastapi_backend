
# School-app Fastapi Backend
---
> Simple REST API backend for a post-diploma technical course app with internship management

English | [Italian](README.it.md)

![License](https://img.shields.io/badge/license-MIT-brightgreen)
![FastApi](https://img.shields.io/badge/FastApi-%23009688?logo=fastapi&logoColor=white)
![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)
![MySQL 8.0](https://img.shields.io/badge/MySQL-8.0-%234479A1)
![phpMyAdmin](https://img.shields.io/badge/phpmyadmin-%236C78AF?logo=phpmyadmin&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23FF4438?logo=redis&logoColor=white)
![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-%23E92063?logo=pydantic&logoColor=white)
![SQLModel](https://img.shields.io/badge/SQLModel-%237e56c2)
![Docker](https://img.shields.io/badge/Docker-%232496ED?logo=docker&logoColor=white)

## Overview

This app was born as a personal project with the aim of learning how a backend might work whilst having a code that could be close to 
IT world standards. This code is meant to mimic the logic of a real app I used to track a internship I did as
part of a post-diploma IT course. In the future it will be connected to a Flutter app that, again, tries to replicate the UI of the
one I actually used.

The repository is, obviously, free to be cloned and used by anyone who might want to check it out. It is intended to work only
locally by running a 4-containers Docker stack, unless otherwise specified within the code itself. 

## Features

- 🔐 **JWT Authentication** => login, authorization and logout with:
    - *Access Token* (creation, validation and redis blacklisting logic)
    - *Refresh Token* (creation, validation, rotation and cron job to delete expired ones)

- 🔧 **CRUD operations**:
    - Student => register new student, read and update student's info, delete student's account (soft & hard)
    \+ change password (as a authenticated student) and reset password by email (as a unauthenticated student)
    - Internship agreements => read student agreement/s
    - Internship entries (shifts) =>  create new entries, read and delete existing entries
    - Course => read student's course info

- 🏢 **Data Models** with SQLModel and Pydantic
- 🛡️ **Error Handling** with custom errors and handlers
- 🧪 **Testing** with Pytest
- 📚 **Auto-documentation** with FastApi /docs & /redoc
- 🐳 **Docker Compose** => 4-containers Docker stack (FastAPI app + MySQL + phpmyadmin + redis)

## Quick Start

### Prerequisites

- Docker 20.10+ with Docker Compose plugin:
    - **Windows/Mac**: Docker Desktop
    - **Linux**: 'docker' + 'docker compose' packages

### 1. Clone & environment set-up

Clone the repository:

```bash
git clone https://github.com/leolicen/school_app_fastapi_backend.git
```

Open project folder:

```bash
cd school-app-fastapi-backend
```

Rename `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` file by replacing comments next to variables with custom values:

*Cancel '# set a secure password' comment.*
```python
# Database MySQL
DB_USER=root
DB_PASSWORD= # set a secure password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=myapp_db
```

*Set the password you want your database to have.*
```python
# Database MySQL
DB_USER=root
DB_PASSWORD=yourSecurePassword
DB_HOST=localhost
DB_PORT=3306
DB_NAME=myapp_db
```

Do the same for all commented variables. You can, of course, modify existing values as well (e.g. DB_NAME).

### 2. Launch docker containers

Launch the full stack from the project's root folder:

```bash
docker-compose up -d
```

### 3. Access application

- **API Docs**: http://localhost:8000/docs or http://localhost:8000/redoc
- **phpMyAdmin**: http://localhost:8080 (use your MySql credentials to login)
- **Redis**: http://localhost:6379


## API Endpoints

### 1. Auth Router

| Endpoint | Method | Description | Auth | 
| -------- | ------ | ----------- | ---- | 
| /auth/login | POST | Login JWT | No | 
| /auth/register | POST | Register student | No |
| /auth/password/reset-request | POST | Request pwd reset | No |
| /auth/password/reset-confirm | POST | Confirm pwd reset | No |
| /auth/refresh | POST | Refresh access & refresh tokens | Yes |
| /auth/logout | POST | Logout | Yes |

### 2. Course Router

| Endpoint | Method | Description | Auth | Active/Inactive account |
| -------- | ------ | ----------- | ---- | ----------------------- |
| /courses | GET | Read student course info | Yes | A,I |

### 3. Internship Router

| Endpoint | Method | Description | Auth | Active/Inactive account |
| -------- | ------ | ----------- | ---- | ----------------------- |
| /internship-agreements | GET | Read student agreement/s info | Yes | A,I |
| /internship-agreements/{agreement_id}/entries | GET | Read agreement entries | Yes | A,I |
| /internship-agreements/{agreement_id}/entries | POST | Create new internship entry | Yes | A |
| /internship-agreements/{agreement_id}/entries/{entry_id} | DELETE | Delete internship entry | Yes | A |

### 4. Student Router

| Endpoint | Method | Description | Auth | Active/Inactive account |
| -------- | ------ | ----------- | ---- | ----------------------- |
| /students/me | GET | Read student info | Yes | A,I |
| /students/me | PATCH | Update student info | Yes | A | 
| /students/me | DELETE | Delete student account | Yes | A,I |
| /students/change-password | POST | Yes | A,I |















