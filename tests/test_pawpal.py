from datetime import date, timedelta, datetime
from pawpal_system import Task, Pet, Owner, Scheduler, ScheduledTask


def test_task_mark_complete():
    task = Task(title="Test task", task_type="feed", duration_minutes=10)
    assert not task.completed
    task.mark_complete()
    assert task.completed


def test_pet_add_task_increases_count():
    pet = Pet(name="Mochi", species="dog")
    initial_count = len(pet.tasks)
    task = Task(title="Walk", task_type="walk", duration_minutes=20)
    pet.add_task(task)
    assert len(pet.tasks) == initial_count + 1
    assert pet.tasks[-1] is task


def test_scheduler_knapsack_chooses_high_priority_best_fit():
    owner = Owner(name="Jordan", available_hours=2.0)
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    pet.add_task(Task(title="Low Priority", task_type="feed", duration_minutes=80, priority="low"))
    pet.add_task(Task(title="High Priority", task_type="walk", duration_minutes=90, priority="high"))
    pet.add_task(Task(title="Medium Priority", task_type="groom", duration_minutes=40, priority="medium"))

    scheduler = Scheduler(owner=owner)
    plan = scheduler.generate_plan()

    assert len(plan) == 1
    assert plan[0].task.title == "High Priority"
    assert plan[0].task.completed
    assert scheduler.score_plan() == 1 / 3


def test_recurring_task_creates_next_occurrence_on_completion():
    owner = Owner(name="Jordan", available_hours=1.5)
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    today = date.today()
    pet.add_task(Task(title="Walk", task_type="walk", duration_minutes=60, priority="high", frequency="daily", deadline=today))

    scheduler = Scheduler(owner=owner)
    plan = scheduler.generate_plan()

    assert len(plan) == 1
    assert plan[0].task.completed

    pending = pet.get_tasks(include_completed=False)
    assert len(pending) == 1
    assert pending[0].title == "Walk"
    assert pending[0].frequency == "daily"
    assert pending[0].deadline == today + timedelta(days=1)


def test_tasks_sorted_returns_chronological_order():
    """Sorting correctness: higher-priority / earlier-deadline tasks come first."""
    owner = Owner(name="Jordan", available_hours=8.0)
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)

    today = date.today()
    pet.add_task(Task(title="Low later", task_type="groom", duration_minutes=20, priority="low", deadline=today + timedelta(days=5)))
    pet.add_task(Task(title="High soon", task_type="walk", duration_minutes=30, priority="high", deadline=today))
    pet.add_task(Task(title="Med mid", task_type="feed", duration_minutes=15, priority="medium", deadline=today + timedelta(days=2)))

    scheduler = Scheduler(owner=owner)
    sorted_tasks = scheduler.get_tasks_sorted()

    titles = [t.title for t in sorted_tasks]
    assert titles.index("High soon") < titles.index("Med mid")
    assert titles.index("Med mid") < titles.index("Low later")


def test_scheduler_detects_conflict_between_overlapping_scheduled_tasks():
    owner = Owner(name="Jordan", available_hours=4.0)
    pet1 = Pet(name="Mochi", species="dog")
    pet2 = Pet(name="Neko", species="cat")
    owner.add_pet(pet1)
    owner.add_pet(pet2)

    task1 = Task(title="Morning walk", task_type="walk", duration_minutes=30, priority="high")
    task2 = Task(title="Feed", task_type="feed", duration_minutes=30, priority="medium")
    pet1.add_task(task1)
    pet2.add_task(task2)

    scheduler = Scheduler(owner=owner)
    start = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    scheduler.scheduled_items = [
        ScheduledTask(task=task1, pet=pet1, start_time=start, end_time=start + timedelta(minutes=30)),
        ScheduledTask(task=task2, pet=pet2, start_time=start, end_time=start + timedelta(minutes=30)),
    ]

    warnings = scheduler.detect_conflicts()
    assert len(warnings) == 1
    assert "Conflict between 'Morning walk'" in warnings[0]
