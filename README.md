
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

Personal project to learn backend development, replicating the logic of a real internship tracking app I used during 
a 2-year IT course. In the future it will be connected to a Flutter app that, similarly, replicates the UI of the
one I actually used.

#### Main goal
Students manage internships as part of a technical post-diploma course.
They can:
- read info about their course
- register/visualize/delete shifts
- manage personal data

#### How it works
- **Static data** [companies, courses, internship agreements] => manually created in DB (through phpMyAdmin)
- **Dynamic data** [students, internship entries (shifts), tokens] => handled by API endpoints

#### Local-only  
4-containers Docker stack (or uv run with separate MySQL and Redis)

---

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

- ⏰ **Cron Jobs** (via APScheduler):
    - Delete expired refresh tokens from DB
    - Delete expired soft-deleted student accounts from DB
    - Activate internship agreements when their start date is reached

- 🚦 **Rate Limiting** (via SlowAPI) on sensitive endpoints (login, register, password reset)
- 📝 **Logging** with Python's built-in logging module
- 🏢 **Data Models** with SQLModel and Pydantic
- 🛡️ **Error Handling** with custom errors and handlers
- 🧪 **Testing** with Pytest
- 📚 **Auto-documentation** with FastApi /docs & /redoc
- 🐳 **Docker Compose** => 4-containers Docker stack (FastAPI app + MySQL + phpMyAdmin + Redis)

---

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

**E.g.** *Cancel '# set a secure password' comment.*
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

### 2. Password-reset via email (Optional)

The app makes use of Resend to allow users to reset their password by email.

If you want to use this feature, first [create a Resend account](https://resend.com/home).

[Add a domain](https://resend.com/domains) you own to be able to send and receive emails. Otherwise, just use Resend test domain (already set
in `.env`). Please note that the test domain only works with the address used during registration.

Update `.env` file with resend API key and the domain you would like to use.

### 3. Launch docker containers

Launch the full stack from the project's root folder:

```bash
docker-compose up -d
```

### 4. Access application

- **API Docs**: http://localhost:8000/docs or http://localhost:8000/redoc
- **phpMyAdmin**: http://localhost:8080 (use your MySQL credentials to login)
- **Redis**: http://localhost:6379

---

## Local development (No Docker)

⚠️ **Warning**: the application runs without Docker, but still **requires separate MySQL 
and Redis** (using '.env' credentials).

### 1. uv Setup

Install uv (if needed): [uv installation](https://docs.astral.sh/uv/getting-started/installation/).

Install project dependencies:

```bash
uv sync
```
### 2. Run the app

Run the app (with hot-reload):

```bash
uv run python main.py
```

---

## Running Tests

Tests use an in-memory SQLite database and a Redis mock — no external services required.

Run all tests:

```bash
uv run pytest
```

Run only unit tests:

```bash
uv run pytest -m unit
```

Run only integration tests:

```bash
uv run pytest -m integration
```

---

## Project Structure

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

---

## API Endpoints

### 1. Auth Router

| Endpoint | Method | Description | Auth | 
| -------- | ------ | ----------- | ---- | 
| /auth/login | POST | Login JWT | No | 
| /auth/register | POST | Register student | No |
| /auth/password/reset-request | POST | Request pwd reset | No |
| /auth/password/reset-confirm | POST | Confirm pwd reset | No |
| /auth/refresh | POST | Refresh access & refresh tokens | Yes |
| /auth/logout | POST | Logout JWT | Yes |

### 2. Course Router

| Endpoint | Method | Description | Auth | Active/Inactive account |
| -------- | ------ | ----------- | ---- | ----------------------- |
| /courses/ | GET | Read list of active courses | No | - |
| /courses/me | GET | Read student course info | Yes | Active, Inactive |

### 3. Internship Router

| Endpoint | Method | Description | Auth | Active/Inactive account |
| -------- | ------ | ----------- | ---- | ----------------------- |
| /internship-agreements/ | GET | Read student agreement/s info | Yes | Active, Inactive |
| /internship-agreements/{agreement_id}/entries | GET | Read agreement entries | Yes | Active, Inactive |
| /internship-agreements/{agreement_id}/entries | POST | Create new internship entry | Yes | Active |
| /internship-agreements/{agreement_id}/entries/{entry_id} | DELETE | Delete internship entry | Yes | Active |

### 4. Student Router

| Endpoint | Method | Description | Auth | Active/Inactive account |
| -------- | ------ | ----------- | ---- | ----------------------- |
| /students/me | GET | Read student info | Yes | Active, Inactive |
| /students/me | PATCH | Update student info | Yes | Active | 
| /students/me | DELETE | Delete student account | Yes | Active, Inactive |
| /students/change-password | Change student pwd | POST | Yes | Active, Inactive |

---

## Roadmap

- [ ] Connect to a Flutter frontend app replicating the original UI
- [ ] Add admin role with endpoints to manage students, companies, courses, and agreements
- [ ] Expand test coverage

---

## Demo Flow

When all 4 containers are up and running, follow the next steps to correctly set up and test the environment.

### 1. Create a new course

Open your browser and go to [phpMyAdmin](http://localhost:8080), enter your credentials (DB_USER and DB_PASSWORD in `.env`) and select 'school_app' db from the panel on your left.

Open 'courseindb' table and click on 'insert'.

![Create new course](/assets/screenshots/create_course.png)

Fields population:

| Field | Type | 
| :----- | :---- | 
| *course_type* | ❗required | 
| *schedule* | ❎ optional | 
| *schedule_type* | ❎ optional | 
| *total_hours* | ❗required | 
| *internship_total_hours* | ❗required | 
| *start_date* |❗required | 
| *location* | ❗required | 
| *is_active* | ⚙️ default value = 1 (True) | 
| *course_id* | ⚡ automatically generated | 
| *name* | ❗required |
| *created_at* | ⚡ automatically generated |

Open a new tab and go to the [API docs](http://localhost:8000/docs) page.

Scroll to 'courses' router and select 'GET /courses/'. 

Click on 'Try it out'.

![Get courses list](/assets/screenshots/get_courses.png)

This endpoint is public and should return a list of all active courses available (only course name and id are shown). 

![Courses list](/assets/screenshots/get_courses_response.png)

Copy the 'course_id' and save it somewhere.

### 2. Register a new student

Select 'POST /auth/register' endpoint within the 'auth' router.

Click on 'Try it out' and fill in the following fields of the request body:

![Register student](/assets/screenshots/register_student.png)

| Field | Type | Notes |
| :----- | :---- | :----- |
| *name* | ❗required | - |
| *surname* | ❗required | - |
| *email* | ❗required | - |
| *course_id* | ❗required | paste your saved 'course_id' here |
| *phone* | ❎ optional | - |
| *address* | ❎ optional | - |
|  *password* | ❗required | password must be at least 8 characters long and include at least a lowercase letter, a uppercase letter, a number and a special character |

Copy email and password and save them.

The response should look like this:

![registration response](/assets/screenshots/registration_response.png)

### 3. Log in 

The registration process includes both the creation of a new student and their first login, returning access and refresh tokens as response.
Normally, a frontend application would take this response, store both tokens and use them to make requests to the API.
In this case, though, it is necessary to manually login through the OAuth2 form in the FastApi docs, in order to let it save the tokens and be able to use protected endpoints.

Click on the green 'Authorize' button on the top right corner and enter email and password of your newly created student.

![Login form](/assets/screenshots/oauth2_form.png)

Go to 'GET /students/me' endpoint and try to make a request.

It should return something like this:

![Student info](/assets/screenshots/get_student_response.png)

### 4. Create a new company 

Go back to [phpMyAdmin](http://localhost:8080) and open 'companyindb' table.

Create a new company with the following fields:

| Field | Type | 
| :----- | :---- | 
| *company_id* | ⚡ automatically generated |
| *name* | ❗required |
| *city* | ❗required |
| *address* | ❗required |
| *tutor* | ❎ optional |
| *created_at* | ⚡ automatically generated |

### 5. Create an internship agreement

Open the 'internshipagreementindb' table and create a new agreement with the following fields:

| Field | Type | Notes |
| :----- | :---- | :----- |
| *total_hours* | ❗required | - |
| *attended_hours* | ❎ optional | automatically updated whenever a new entry is created/deleted |
| *start_date* | ❗required | - |
| *is_active* | ⚙️ default value = 0 (False) | set it to 1 (True) so that it is already possible to create new entries* |
| *agreement_id* | ⚡ automatically generated | - |
| *student_id* | ❗required | manually select from phpMyAdmin dropdown |
| *company_id* | ❗required | manually select from phpMyAdmin dropdown |
| *created_at* | ⚡ automatically generated | - |

> **Note:** Usually, a new agreement is created in advance with a future start date, until which it is not possible for the student to create new entries. The agreement automatically activates via cronjob at the start date. That is why the default value is 0 (False).

Go back to the [API docs](http://localhost:8000/docs) page and execute a request to the 'GET /internship-agreements/' endpoint.

A list with agreements owned by the student should be returned:

![Student agreements list](/assets/screenshots/get_agreement_list_response.png)

Copy the agreement_id and save it.

⚠️ **Token expired?** Click 'Authorize', logout and login again. The FastAPI docs don't allow extracting the refresh token manually (in order to refresh both tokens through the 'POST /auth/refresh' endpoint). 

### 6. Create an internship entry 

Create a new internship entry at 'POST /internship-agreements/{agreement_id}/entries' endpoint, passing the agreement_id as a parameter.
The required fields are:

![Create new entry](/assets/screenshots/create_entry.png)

| Field | Type | Notes |
| :----- | :---- | :----- |
| *entry_date* | ❗required | must be previous or equal to the current date and not go back more than 7 days |
| *start_time* | ❗required | - |
| *end_time* | ❗required | must be greater than the start time |
| *shift_type* | ❗required | choose between 'in_office' or 'remote' |
| *description* | ❗required |  max_length=150 |
| *agreement_id* | ❗required  | - |

The response should be:

![Entry creation response](/assets/screenshots/create_entry_response.png)

Now check the 'GET /internship-agreements/{agreement_id}/entries' endpoint, passing in the agreement id and pressing 'execute'.
A list of entries (just the one we created, for now) should be available:

![Entries list](/assets/screenshots/get_agreem_entries.png)

Copy the entry id and save it.

### 7. Delete an internship entry

Go to the 'DELETE /internship-agreements/{agreement_id}/entries/{entry_id}' endpoint and pass both the agreement_id and the entry_id parameters.

![Delete entry](/assets/screenshots/delete_entry.png)

The response is the following:

![Entry deletion response](/assets/screenshots/delete_entry_response.png)

Now, if you go back and check again 'GET /internship-agreements/{agreement_id}/entries' endpoint, you should find an empty list:

![Empty entries list](/assets/screenshots/empty_entries_list.png) 

### 8. Log out

Go to the 'POST /auth/logout' endpoint in the docs and click 'execute'.

![Logout](/assets/screenshots/logout.png)

![Logout response](/assets/screenshots/logout%20response.png)

🎉 You've just completed the full demo flow!

---

## License

This project is licensed under the [MIT License](LICENSE).
