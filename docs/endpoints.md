# Index
1. [Authentication](#authentication)
    2. [POST /login](#auth1)
    3. [POST /signup](#auth2)
2. [Doctors](#doctors)
    1. [GET /doctors/{id}](#doc1)
    2. [PUT /doctors/{id}](#doc2)
3. [Patients](#patients)
    1. [GET /patients/{id}](#doc1)
    2. [PUT /patients/{id}](#doc2)
    3. [GET /doctors/{id}/patients](#pat3)
4. [Sessions](#sessions)
    1. [GET /sessions/{id}](#sess1)
    2. [POST /sessions](#sess2)
    3. [PUT /sessions/{id}](#sess3)
    4. [DELETE /sessions/{id}](#sess4)
    5. [GET /doctors/{id}/sessions](#sess5)
    6. [GET /patients/{id}/sessions](#sess6)
5. [Assignments](#assignments)
    1. [GET /assignments/{id}](#ass1)
    2. [POST /assignments](#ass2)
    3. [PUT /assignments/{id}](#ass3)
    4. [DELETE /assignments/{id}](#ass4)
    5. [GET /patients/{id}/assignments](#ass5)
6. [Advices](#advices)
    1. [GET /advices/{id}](#adv1)
    2. [POST /advices](#adv2)
    3. [PUT /advices/{id}](#adv3)
    4. [DELETE /advices/{id}](#adv4)
    5. [GET /doctors/{id}/advices ](#adv5)
    5. [GET /patients/{id}/advices](#adv6)
<br></br>

# Authentication <a name="authentication"></a>

## `@POST` /login <a name="auth1"></a>
### Autenticação: **Token**;
### Response body:
```json
{
    "user_uuid": str,
    "is_doctor": bool,
}
```

- Valida se o token é valido,
    - Se sim, retorna se o usuário é doutor ou não e seu uuid;
<br></br>

## `@POST` /signup <a name="auth2"></a>
### Autenticação: **Token**;
### Request body:
```json
{
    "name": str,
    "is_doctor": bool,
}
```
### Response body:
```json
{
    "user_uuid": str,
}
```
- Valida se o token é valido,
    - Se sim, cria um usuário e retorna uuid
<br></br>

# Doctors <a name="doctors"></a>

## `@GET` /doctors/`{id}` <a name="doc1"></a>
### Autenticação: **Token**;
### Response body:
```json
{
    "uuid": str,
    "photo": str,
    "name": str,
    "phone_number": str,
    "description": str,
    "crp": str,
    "addresses": [str],
    "pix_key": str,
    "payment_details": str,
    "tags": [str],
}
```

 - Retorna o perfil do doutor onde `doctor.uuid = $id`;
<br></br>

## `@PUT` /doctors/`{id}` <a name="doc2"></a>
### Autenticação: **Token**;
### Request body:
```json
{
    "photo": str,
    "name": str,
    "phone_number": str,
    "description": str,
    "crp": str,
    "addresses": [str],
    "pix_key": str,
    "payment_details": str,
    "tags": [str],
}
```
### Response body:
```json
{
    "uuid": str,
    "photo": str,
    "name": str,
    "phone_number": str,
    "description": str,
    "crp": str,
    "addresses": [str],
    "pix_key": str,
    "payment_details": str,
    "tags": [str],
}
```

- Valida se o usuario atrelado ao token enviado possui `id` igual à `$id`;
    - Se não for, retorna 401;
- Altera doutor onde `doctor.uuid = $id`;
- Retorna o perfil do doutor alterado;
<br></br>

# Patients <a name="patients"></a>

## `@GET` /patients/`{id}` <a name="pat1"></a>
### Autenticação: **Token**;
### Response body:
```json
{
    "uuid": str,
    "name": str,
    "phone_number": str,
    "doctor_ids": str[];
}
```

 - Retorna o perfil do paciente onde `patient.uuid = $id`;
<br></br>

## `@PUT` /patients/`{id}` <a name="pat2"></a>
### Autenticação: **Token**;
### Request body:
```json
{
    "name": str,
    "phone_number": str,
    "doctor_ids": str[];
}
### Response body:
```json
{
    "uuid": str,
    "name": str,
    "phone_number": str,
    "doctor_ids": str[];
}
```

- Valida se o usuario atrelado ao token enviado possui `id` igual à `$id`;
    - Se não for, retorna 401;
- Altera paciente onde `patient.uuid = $id`;
- Retorna o perfil do paciente alterado;
<br></br>

## `@GET` /doctors/`{id}`/patients <a name="pat3"></a>
### Autenticação: **Token**;
### Response body:
```json
{
    "patients": [
        {
           "uuid": str,
           "name": str,
           "phone_number": str,
           "doctor_ids": str[];
        }
    ]
}
```
- Valida se o usuário atrelado ao token enviado possui `id` igual à `$id`, 
    - Se não possuir, retorna 401;
- Retorna os pacientes que possuem `$id` em `patient.doctor_ids`.
<br></br>

# Sessions <a name="sessions"></a>

## `@GET` /sessions/`{id}` <a name="sess1"></a>
### Autenticação: **Token**;
### Response body:
```json
{
    "id": str,
    "doctor_id": str,
    "doctor_name": str,
    "patient_id": str,
    "patient_name": str,
    "status": str, // CONFIRMED, NOT_CONFIRMED, CANCELED, CONCLUDED, BLOCKED
    "type": str, // MONTHLY, INDIVIDUAL
    "date": str,
    "group_id": str,
    "group_index": int, // index of the session in the session group (ex: index 1 means session 1 of 4)
}
```
- Valida se o usuário atrelado ao token enviado possui `id` igual à `session.doctor_id` ou 
`session.patient_id`, onde `session.id = $id`;
    - Se não possuir, retorna 401;
- Retorna a sessão onde `session.id = $id`;
<br></br>

## `@POST` /sessions` <a name="sess2"></a>
### Autenticação: **Token**;
### Request body:
```json
{
    "doctor_id": str,
    "doctor_name": str,
    "patient_id": str,
    "patient_name": str,
    "status": str, // CONFIRMED, NOT_CONFIRMED, CANCELED, CONCLUDED, BLOCKED
    "type": str, // MONTHLY, INDIVIDUAL
    "date": str,
    "group_id": str,
    "group_index": int, // index of the session in the session group (ex: index 1 means session 1 of 4)
}
```
### Response body:
```json
{
    "id": str,
    "doctor_id": str,
    "doctor_name": str,
    "patient_id": str,
    "patient_name": str,
    "status": str, // CONFIRMED, NOT_CONFIRMED, CANCELED, CONCLUDED, BLOCKED
    "type": str, // MONTHLY, INDIVIDUAL
    "date": str,
    "group_id": str,
    "group_index": int, // index of the session in the session group (ex: index 1 means session 1 of 4)
}
```
- Valida se o usuário atrelado ao token enviado possui `id` igual à `doctor_id` ou 
`patient_id` passados no request body;
    - Se não possuir, retorna 401;
- Cria a sessão usando os dados do request body;
- Retorna a sessão criada;
<br></br>

## `@PUT` /sessions/`{id}` <a name="sess3"></a>
### Autenticação: **Token**;
### Request body:
```json
{
    "doctor_id": str,
    "doctor_name": str,
    "patient_id": str,
    "patient_name": str,
    "status": str, // CONFIRMED, NOT_CONFIRMED, CANCELED, CONCLUDED, BLOCKED
    "type": str, // MONTHLY, INDIVIDUAL
    "date": str,
    "group_id": str,
    "group_index": int, // index of the session in the session group (ex: index 1 means session 1 of 4)
}
```
### Response body:
```json
{
    "id": str,
    "doctor_id": str,
    "doctor_name": str,
    "patient_id": str,
    "patient_name": str,
    "status": str, // CONFIRMED, NOT_CONFIRMED, CANCELED, CONCLUDED, BLOCKED
    "type": str, // MONTHLY, INDIVIDUAL
    "date": str,
    "group_id": str,
    "group_index": int, // index of the session in the session group (ex: index 1 means session 1 of 4)
}
```
- Valida se o usuário atrelado ao token enviado possui `id` igual à `session.doctor_id` ou 
`session.patient_id`, onde `session.id = $id`;
    - Se não possuir, retorna 401;
- Altera sessão onde `session.id = $id`;
- Retorna a sessão alteada;
<br></br>

## `@DELETE` /sessions/`{id}` <a name="sess4"></a>
### Autenticação: **Token**;

- Valida se o usuário atrelado ao token enviado possui `id` igual à `session.doctor_id` ou 
`session.patient_id`, onde `session.id = $id`;
    - Se não possuir, retorna 401;
- Deleta a sessão onde `session.id = $id`;
<br></br>

## `@GET` /doctors/`{id}`/sessions?date=`{date}` <a name="sess5"></a>
### Autenticação: **Token**;
### Response body:
```json
{
    "sessions": [
        {
            "id": str,
            "doctor_id": str,
            "doctor_name": str,
            "patient_id": str,
            "patient_name": str,
            "status": str, // CONFIRMED, NOT_CONFIRMED, CANCELED, CONCLUDED, BLOCKED
            "type": str, // MONTHLY, INDIVIDUAL
            "date": str,
            "group_id": str,
            "group_index": int, // index of the session in the session group (ex: index 1 means session 1 of 4)
        }
    ]
}
```

- Valida se o usuario atrelado ao token enviado possui `id` igual à `$id`;
    - Se não for, retorna 401;
- Retorna as sessões que possuem `session.doctor_id = $id`, 
- E caso `$date` seja passado, filtra também onde `session.date = $date`;
<br></br>


## `@GET` /patients/`{id}`/sessions?upcoming=`{upcoming}` <a name="sess6"></a>
### Autenticação: **Token**;
### Response body:
```json
{
    "sessions": [
        {
            "id": str,
            "doctor_id": str,
            "doctor_name": str,
            "patient_id": str,
            "patient_name": str,
            "status": str, // CONFIRMED, NOT_CONFIRMED, CANCELED, CONCLUDED, BLOCKED
            "type": str, // MONTHLY, INDIVIDUAL
            "date": str,
            "group_id": str,
            "group_index": int, // index of the session in the session group (ex: index 1 means session 1 of 4)
        }
    ]
}
```
- Valida se o usuário atrelado ao token enviado possui `id` igual à `$id`, 
    - Ou se possui `id` em `patient.doctor_ids` onde `patient.uuid = $id`,
    - Se não for pra nenhum, retorna 401;
- Caso seja válido para o paciente, retorna as sessões que 
possuem `session.patient_id = $id`.
- Caso o usuário atrelado ao token seja doutor, retorna as sessões que 
possuem `session.patient_id = $id` e `session.doctor_id = doutor.id`.
- Caso `$upcoming` seja `true`, também filtra apenas as sessões futuras que 
possuem `session.status = "CONFIRMED"` ou `session.status = "NOT_CONFIRMED"`;
<br></br>

# Assignments <a name="assignments"></a>


## `@GET` /assignments/`{id}` <a name="ass1"></a>
### Autenticação: **Token**;
### Response body:
```json
{
    "id": str,
    "title": str,
    "description": str,
    "doctor_id": str,
    "patient_id": str,
    "status": str, /// PENDING, DONE, MISSED
    "delivery_session_id": str;
    
}
```
- Valida se o usuário atrelado ao token enviado possui `id` igual à 
`assignment.doctor_id` ou igual à `assignment.patient_id`, 
onde `asignment.id = $id`,
    - Se não possuir, retorna 401;
- Retorna tarefa onde `asignment.id = $id`;
<br></br>

## `@POST` /assignments` <a name="ass2"></a>
### Autenticação: **Token**;
### Request body:
```json
{
    "title": str,
    "description": str,
    "doctor_id": str,
    "patient_id": str,
    "status": str, /// PENDING, DONE, MISSED
    "delivery_session_id": str;
}
```
### Response body:
```json
{
    "id": str,
    "title": str,
    "description": str,
    "doctor_id": str,
    "patient_id": str,
    "status": str, /// PENDING, DONE, MISSED
    "delivery_session_id": str;
}
```
- Valida se o usuário atrelado ao token enviado possui `id` igual à 
`$doctor_id` ou igual à `$patient_id` presentes no request body, 
    - Se não possuir, retorna 401;
- Cria tarefa;
- Retorna tarefa criada;
<br></br>

## `@PUT` /assignments/`{id}` <a name="ass3"></a>
### Autenticação: **Token**;
### Request body:
```json
{
    "title": str,
    "description": str,
    "doctor_id": str,
    "patient_id": str,
    "status": str, /// PENDING, DONE, MISSED
    "delivery_session_id": str;
}
```
### Response body:
```json
{
    "id": str,
    "title": str,
    "description": str,
    "doctor_id": str,
    "patient_id": str,
    "status": str, /// PENDING, DONE, MISSED
    "delivery_session_id": str;
}
```
- Valida se o usuário atrelado ao token enviado possui `id` igual à 
`assignment.doctor_id` ou igual à `assignment.patient_id`, 
onde `asignment.id = $id`,
    - Se não possuir, retorna 401;
- Altera tarefa onde `asignment.id = $id`;
- Retorna tarefa alterada;
<br></br>

## `@DELETE` /assignments/`{id}` <a name="ass4"></a>
### Autenticação: **Token**;

- Valida se o usuário atrelado ao token enviado possui `id` igual à 
`assignment.doctor_id` ou igual à `assignment.patient_id`, 
onde `asignment.id = $id`,
    - Se não possuir, retorna 401;
- Deleta tarefa do banco, onde `asignment.id = $id`;
<br></br>

## `@GET` /patients/`{id}`/assignments?pending=`{upcoming} <a name="ass5"></a>
### Autenticação: **Token**;
### Response body:
```json
{
    "assignments": [
        {
            "id": str,
            "title": str,
            "description": str,
            "doctor_id": str,
            "patient_id": str,
            "status": str, /// PENDING, DONE, MISSED
            "delivery_session_id": str;
        }
    ]
}
```
- Valida se o usuário atrelado ao token enviado possui `id` igual à `$id`, 
    - Ou se possui `id` em `patient.doctor_ids` onde `patient.uuid = $id`,
    - Se não for pra nenhum, retorna 401;
- Caso seja válido para o paciente, retorna as tarefas que 
possuem `assignment.patient_id = $id`.
- Caso o usuário atrelado ao token seja doutor, retorna as tarefas que 
possuem `assignment.patient_id = $id` e `assignment.doctor_id = doutor.id`.
- Caso `$pending` seja `true`, também filtra apenas as tarefas que possuem 
`assignment.status = "PENDING";
<br></br>

# Advices <a name="advices"></a>

## `@GET` /advices/`{id}` <a name="adv1"></a>
### Autenticação: **Token**;
### Response body:
```json
{
    "id": str,
    "message": str,
    "doctor_id": str,
    "doctor_name": str,
    "patient_ids": str[];
}
```
- Valida se o usuário atrelado ao token enviado possui `id` igual à 
`advice.doctor_id` ou em `advice.patient_ids`, onde `advice.id = $id`,
    - Se não for pra nenhum, retorna 401;
- Retorna a dica onde `advice.id = $id`;
<br></br>

## `@POST` /advices` <a name="adv2"></a>
### Autenticação: **Token**;
### Request body:
```json
{
    "message": str,
    "doctor_id": str,
    "doctor_name": str,
    "patient_ids": str[];
}
```
### Response body:
```json
{
    "id": str,
    "message": str,
    "doctor_id": str,
    "doctor_name": str,
    "patient_ids": str[];
}
```
- Valida se o usuário atrelado ao token enviado possui `id` igual à 
`doctor_id` ou em `patient_ids` passados pelo request body;
    - Se não possuir, retorna 401;
- Cria a dica com os dados passados pelo request body;
- Retorna a dica criada;
<br></br>

## `@PUT` /advices/`{id}` <a name="adv2"></a>
### Autenticação: **Token**;
### Request body:
```json
{
    "message": str,
    "doctor_id": str,
    "doctor_name": str,
    "patient_ids": str[];
}
```
### Response body:
```json
{
    "id": str,
    "message": str,
    "doctor_id": str,
    "doctor_name": str,
    "patient_ids": str[];
}
```
- Valida se o usuário atrelado ao token enviado possui `id` igual à 
`advice.doctor_id` ou em `advice.patient_ids`, onde `advice.id = $id`,
    - Se não for pra nenhum, retorna 401;
- Altera a dica onde `advice.id = $id`;
- Retorna a dica alterada;
<br></br>

## `@DELETE` /advices/`{id}` <a name="adv4"></a>
### Autenticação: **Token**;

- Valida se o usuário atrelado ao token enviado possui `id` igual à 
`advice.doctor_id` ou em `advice.patient_ids`, onde `advice.id = $id`,
    - Se não for pra nenhum, retorna 401;
- Deleta a dica onde `advice.id = $id`;
<br></br>

## `@GET` /doctors/`{id}`/advices <a name="adv5"></a>
### Autenticação: **Token**;
### Response body:
```json
{
    "advices": [
        {
           "id": str,
           "message": str,
           "doctor_id": str,
           "doctor_name": str,
           "patient_ids": str[];
        }
    ]
}
```
- Valida se o usuário atrelado ao token enviado possui `id` igual à `$id`, 
    - Se não possuir, retorna 401;
- Retorna as dicas que possuem `advice.doctor_id = $id`.
<br></br>

## `@GET` /patients/`{id}`/advices <a name="adv6"></a>
### Autenticação: **Token**;
### Response body:
```json
{
    "advices": [
        {
           "id": str,
           "message": str,
           "doctor_id": str,
           "doctor_name": str,
           "patient_ids": str[];
        }
    ]
}
```
- Valida se o usuário atrelado ao token enviado possui `id` igual à `$id`, 
    - Ou se possui `id` em `patient.doctor_ids` onde `patient.uuid = $id`,
    - Se não for pra nenhum, retorna 401;
- Caso seja válido para o paciente, retorna as dicas que 
possuem `$id` em `advice.patient_ids`.
- Caso o usuário atrelado ao token seja doutor, retorna as dicas que 
possuem `$id` em `advice.patient_ids` e `advice.doctor_id = doutor.id`.
<br></br>