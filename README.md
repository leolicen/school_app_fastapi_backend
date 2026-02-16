
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

This app was born as a personal project in order to learn how a backend might work whilst having a almost-real-world code to 
show to potential employers. This code is meant to mimic the logic of a real app I used to track a internship I did as
part of a post-diploma IT course. In the future it will be connected to a Flutter app that, again, tries to replicate the UI of the
one I actually used.

The repository is, obviously, free to be cloned and used by anyone who might want to check it out. It is intended to work only
locally by running a 4-containers docker stack, unless otherwise specified within the code itself. 

## Features

- **JWT Authentication** => login, authorization and logout with:
    - *Access Token* (creation, validation and redis blacklisting logic)
    - *Refresh Token* (creation, validation, rotation and cron job to delete expired ones)

- **CRUD operations**:
    - Student => register new student, read student's info, update student's info, delete student's account
    \+ change password (within the app) and reset password by email (from outside the app)
    - Internship agreements => read student agreement/s
    - Intership entries (shifts) =>  create new entries, read entries, delete entries
    - Course => read student's course info

- **Data Models** with SQLModel and Pydantic
- **Error Handling** with custom errors and handlers
- **Testing** with Pytest
- **Auto-documentation** with FastApi /docs & /redoc
- **Docker Compose** => 4-containers stack with FastAPI app + MySQL + phpmyadmin + redis




