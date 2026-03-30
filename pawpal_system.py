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
        """Mark this task complete and return the next occurrence for recurring tasks."""
        self.completed = True
        if self.frequency not in {"daily", "weekly"}:
            return None
        days = 1 if self.frequency == "daily" else 7
        next_date = (self.deadline if self.deadline else date.today()) + timedelta(days=days)
        return Task(
            title=self.title,
            task_type=self.task_type,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            deadline=next_date,
            completed=False,
            created_at=datetime.now(),
        )

    def mark_pending(self) -> None:
        """Mark this task as pending/incomplete."""
        self.completed = False

    def update_duration(self, duration_minutes: int) -> None:
        """Update task duration in minutes."""
        self.duration_minutes = duration_minutes

    def update_priority(self, priority: str) -> None:
        """Set task priority."""
        self.priority = priority

    def priority_weight(self) -> int:
        """Return numeric score for task priority."""
        return {"high": 100, "medium": 50, "low": 20}.get(self.priority, 50)

    def value_density(self) -> float:
        """Return priority-weight per minute; used for schedule fitness scoring."""
        if self.duration_minutes <= 0:
            return float("inf")
        return self.priority_weight() / self.duration_minutes

    def is_overdue(self, reference: datetime) -> bool:
        """Return True if the task deadline has passed relative to reference."""
        if self.deadline is None:
            return False
        return reference.date() > self.deadline


@dataclass
class Pet:
    name: str
    species: str
    age: int = 0
    health_notes: str = ""
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove a task by title."""
        self.tasks = [t for t in self.tasks if t.title != title]

    def get_tasks(self, include_completed: bool = False) -> List[Task]:
        """Return tasks, optionally including completed ones."""
        return [t for t in self.tasks if include_completed or not t.completed]

    def summary(self) -> str:
        """Return a short human-readable description of this pet."""
        return f"{self.name} ({self.species}, age {self.age})"


@dataclass
class Owner:
    name: str
    available_hours: float = 8.0
    preferences: Dict[str, str] = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Return a pet by name, or None if not found."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def get_all_tasks(self, include_completed: bool = False) -> List[Task]:
        """Return all tasks across all pets, optionally including completed tasks."""
        tasks: List[Task] = []
        for pet in self.pets:
            tasks.extend(pet.get_tasks(include_completed=include_completed))
        return tasks


@dataclass
class ScheduledTask:
    task: Task
    pet: Pet
    start_time: datetime
    end_time: datetime
    reason: Optional[str] = None

    def duration(self) -> int:
        """Return scheduled duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() // 60)

    def conflicts_with(self, other: ScheduledTask) -> bool:
        """Return True if this slot overlaps with another scheduled task."""
        return not (self.end_time <= other.start_time or self.start_time >= other.end_time)


@dataclass
class Scheduler:
    owner: Owner
    date: date = field(default_factory=date.today)
    scheduled_items: List[ScheduledTask] = field(default_factory=list)
    explanation: str = ""

    def get_pending_tasks(self) -> List[Task]:
        """Return all incomplete tasks across the owner's pets."""
        return self.owner.get_all_tasks(include_completed=False)

    def get_tasks_sorted(self) -> List[Task]:
        """Return pending tasks sorted by deadline, priority, duration, and creation time."""
        priority_rank = {"high": 1, "medium": 2, "low": 3}
        return sorted(
            self.get_pending_tasks(),
            key=lambda t: (
                t.deadline or date.max,
                priority_rank.get(t.priority, 2),
                -t.duration_minutes,
                t.created_at,
            ),
        )

    def _select_tasks_for_capacity(self, tasks: List[Task], capacity_minutes: int) -> List[Task]:
        """Use a 0/1 knapsack to choose the highest-value subset of tasks within capacity."""
        if capacity_minutes <= 0 or not tasks:
            return []

        dp: List[tuple] = [(0.0, []) for _ in range(capacity_minutes + 1)]

        for idx, task in enumerate(tasks):
            dur = task.duration_minutes
            if dur > capacity_minutes or dur <= 0:
                continue
            value = task.priority_weight()
            for cap in range(capacity_minutes, dur - 1, -1):
                prev_score, prev_indices = dp[cap - dur]
                candidate = prev_score + value
                if candidate > dp[cap][0]:
                    dp[cap] = (candidate, prev_indices + [idx])

        _, best_indices = max(dp, key=lambda x: x[0])
        return [tasks[i] for i in best_indices]

    def generate_plan(self, start_time: datetime = None) -> List[ScheduledTask]:
        """Build a schedule using knapsack-based selection to maximize priority value."""
        if start_time is None:
            start_time = datetime.combine(self.date, datetime.min.time()).replace(hour=8, minute=0)

        self.scheduled_items = []
        remaining = int(self.owner.available_hours * 60)
        current = start_time

        sorted_tasks = self.get_tasks_sorted()
        selected = self._select_tasks_for_capacity(sorted_tasks, remaining)

        if not selected:
            self.explanation = "No tasks could be scheduled within available hours."
            return self.scheduled_items

        # Re-apply sort order so the timeline is human-friendly.
        selected = [t for t in sorted_tasks if t in selected]

        for task in selected:
            if task.duration_minutes > remaining:
                continue
            end = current + timedelta(minutes=task.duration_minutes)
            pet = next((p for p in self.owner.pets if task in p.tasks), None)
            if pet is None:
                continue
            self.scheduled_items.append(
                ScheduledTask(task=task, pet=pet, start_time=current, end_time=end, reason=f"Priority {task.priority}")
            )
            current = end
            remaining -= task.duration_minutes
            next_task = task.mark_complete()
            if next_task:
                pet.add_task(next_task)

        if not self.scheduled_items:
            self.explanation = "No tasks could be scheduled within available hours."
        else:
            used = int(self.owner.available_hours * 60) - remaining
            self.explanation = (
                f"Scheduled {len(self.scheduled_items)} tasks using {used} min "
                f"with {remaining} min remaining."
            )

        conflicts = self.detect_conflicts()
        if conflicts:
            self.explanation += " WARNING: " + " | ".join(conflicts)

        return self.scheduled_items

    def detect_conflicts(self) -> List[str]:
        """Return warning strings for any overlapping scheduled tasks."""
        warnings: List[str] = []
        n = len(self.scheduled_items)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = self.scheduled_items[i], self.scheduled_items[j]
                if a.conflicts_with(b):
                    warnings.append(
                        f"Conflict between '{a.task.title}' (pet {a.pet.name}) "
                        f"and '{b.task.title}' (pet {b.pet.name}) at {a.start_time.strftime('%H:%M')}."
                    )
        return warnings

    def explain_plan(self) -> str:
        """Return a human-friendly explanation of the generated plan."""
        return self.explanation

    def score_plan(self) -> float:
        """Score the plan as the fraction of total tasks that were scheduled."""
        if not self.scheduled_items:
            return 0.0
        total = len(self.owner.get_all_tasks(include_completed=True))
        if total == 0:
            return 1.0
        return len(self.scheduled_items) / total
