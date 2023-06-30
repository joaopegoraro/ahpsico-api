## Usuário
```dart
User {
    String uuid;
    String phone_number;
    bool is_doctor;
}
```

## Doutor
```dart
Doctor {
    String uuid;
    String photo;
    String name;
    String phone_number;
    String description;
    String crp;
    String pix_key;
    String payment_details;
}
```

## Paciente
```dart
Patient {
    String uuid;
    String name;
    String phone_number;
    List<String> doctor_ids;
}
```

## Convite
```dart
Invite {
    String doctor_id,
    String patient_id,
    String phone_number;
}
```

## Dica
- É deletado após 7 dias de ser criado
```dart
Advice {
    String message;
    String doctor_id;
    String doctor_name;
    List<String> patient_id;
}
```

## Grupo de sessões
```dart
SessionGroup {
    String doctor_id;
}
```

## Sessão
```dart
Session {
    String doctor_id;
    String doctor_name;
    String patient_id;
    String patient_name;
    /// CONFIRMED, NOT_CONFIRMED, CANCELED, CONCLUDED, BLOCKED
    String status; 
    /// MONTHLY, INDIVIDUAL
    String type; 
    String date;
    String group_id;
    /// index of the session in the session 
    /// group (ex: index 1 means session 1 of 4)
    int group_index;
}
```

## Tarefa
```dart
Assignment {
    String title;
    String description;
    String doctor_id;
    String patient_id;
    /// PENDING, DONE, MISSED
    String status; 
    String delivery_session_id;
}
```
