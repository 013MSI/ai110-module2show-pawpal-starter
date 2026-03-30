from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict


@dataclass
class Task:
    title: str
    task_type: str
    duration_minutes: int
    priority: str = "medium"
    frequency: str = "none"
    deadline: Optional[date] = None
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    def mark_complete(self) -> Optional[Task]:
        pass

    def mark_pending(self) -> None:
        pass

    def update_duration(self, duration_minutes: int) -> None:
        pass

    def update_priority(self, priority: str) -> None:
        pass

    def priority_weight(self) -> int:
        pass

    def value_density(self) -> float:
        pass

    def is_overdue(self, reference: datetime) -> bool:
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int = 0
    health_notes: str = ""
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, title: str) -> None:
        pass

    def get_tasks(self, include_completed: bool = False) -> List[Task]:
        pass

    def summary(self) -> str:
        pass


@dataclass
class Owner:
    name: str
    available_hours: float = 8.0
    preferences: Dict[str, str] = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def remove_pet(self, pet_name: str) -> None:
        pass

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        pass

    def get_all_tasks(self, include_completed: bool = False) -> List[Task]:
        pass


@dataclass
class ScheduledTask:
    task: Task
    pet: Pet
    start_time: datetime
    end_time: datetime
    reason: Optional[str] = None

    def duration(self) -> int:
        pass

    def conflicts_with(self, other: ScheduledTask) -> bool:
        pass


@dataclass
class Scheduler:
    owner: Owner
    date: date = field(default_factory=date.today)
    scheduled_items: List[ScheduledTask] = field(default_factory=list)
    explanation: str = ""

    def get_pending_tasks(self) -> List[Task]:
        pass

    def get_tasks_sorted(self) -> List[Task]:
        pass

    def generate_plan(self, start_time: datetime = None) -> List[ScheduledTask]:
        pass

    def detect_conflicts(self) -> List[str]:
        pass

    def explain_plan(self) -> str:
        pass

    def score_plan(self) -> float:
        pass
