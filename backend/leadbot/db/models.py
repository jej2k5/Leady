"""Pydantic models and enums used by the persistence layer."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RunStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class SourceType(str, Enum):
    website = "website"
    linkedin = "linkedin"
    directory = "directory"
    api = "api"


class SignalType(str, Enum):
    funding = "funding"
    hiring = "hiring"
    technology = "technology"
    intent = "intent"


class ContactType(str, Enum):
    email = "email"
    phone = "phone"
    linkedin = "linkedin"


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    username: str | None = None
    email: EmailStr
    name: str | None = None
    password_hash: str | None = None
    provider: str = "local"
    google_sub: str | None = None
    role: str = "viewer"
    created_at: datetime | None = None
    last_login_at: datetime | None = None


class Company(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    run_id: int | None = None
    name: str
    domain: str | None = None
    industry: str | None = None
    employee_count: int | None = None
    location: str | None = None
    score: float = 0.0
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Signal(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    company_id: int
    signal_type: SignalType
    source_id: int | None = None
    value: str
    confidence: float = 0.0
    observed_at: datetime | None = None
    created_at: datetime | None = None


class Contact(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    company_id: int
    full_name: str
    title: str | None = None
    contact_type: ContactType
    contact_value: str
    is_primary: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RawCandidate(BaseModel):
    company_name: str
    domain: str | None = None
    source_type: SourceType
    source_url: str | None = None
    signals: list[Signal] = Field(default_factory=list)
    contacts: list[Contact] = Field(default_factory=list)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class RunSummary(BaseModel):
    run_id: int
    status: RunStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    companies_discovered: int = 0
    signals_collected: int = 0
    contacts_collected: int = 0
