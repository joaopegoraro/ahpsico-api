from enum import StrEnum


class SessionStatus(StrEnum):
    CONFIRMED = "CONFIRMED"
    NOT_CONFIRMED = "NOT_CONFIRMED"
    CANCELED = "CANCELED"
    CONCLUDED = "CONCLUDED"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class SessionType(StrEnum):
    MONTHLY = "MONTHLY"
    INDIVIDUAL = "INDIVIDUAL"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class AssignmentStatus(StrEnum):
    PENDING = "PENDING"
    DONE = "DONE"
    MISSED = "MISSED"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]
