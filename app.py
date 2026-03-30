import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to **PawPal+** — a pet care planning assistant that helps busy pet owners stay on top
of daily care tasks for their pets.
"""
)

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
**PawPal+** helps a pet owner plan care tasks (walks, feeding, meds, grooming, enrichment)
based on constraints like available time, task priority, and deadlines.
The scheduler selects and orders tasks to maximise priority value within the owner's daily budget.
"""
    )

# ── Session state: keep Owner alive across reruns ─────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_hours=8.0)

owner: Owner = st.session_state.owner

# ── Owner profile ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)
owner.available_hours = st.number_input(
    "Available hours today", min_value=1.0, max_value=24.0, value=float(owner.available_hours)
)

# ── Add pet ───────────────────────────────────────────────────────────────────
st.divider()
st.subheader("Add Pet")
new_pet_name = st.text_input("Pet name", value="", key="new_pet_name")
new_pet_species = st.selectbox("Species", ["dog", "cat", "other"], key="new_pet_species")
new_pet_age = st.number_input("Age", min_value=0, max_value=30, value=0, key="new_pet_age")

if st.button("Add pet"):
    if new_pet_name.strip():
        if owner.get_pet(new_pet_name.strip()) is None:
            owner.add_pet(Pet(name=new_pet_name.strip(), species=new_pet_species, age=int(new_pet_age)))
            st.success(f"Added pet: {new_pet_name.strip()}")
        else:
            st.warning(f"A pet named '{new_pet_name.strip()}' already exists.")
    else:
        st.error("Pet name cannot be empty.")

pet_names = [pet.name for pet in owner.pets]
if pet_names:
    st.write("**Current pets:**")
    for pet in owner.pets:
        st.write(f"- {pet.summary()} — {len(pet.get_tasks())} pending task(s)")
else:
    st.info("No pets added yet.")

# ── Add task ──────────────────────────────────────────────────────────────────
st.divider()
st.subheader("Add Task")
if pet_names:
    selected_pet_name = st.selectbox("Assign to pet", pet_names, key="task_pet")
    task_title = st.text_input("Task title", value="Morning walk", key="task_title")
    task_type = st.selectbox("Task type", ["walk", "feed", "meds", "groom", "enrich"], key="task_type")
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20, key="task_dur")
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=1, key="task_pri")
    frequency = st.selectbox("Frequency", ["none", "daily", "weekly"], key="task_freq")

    if st.button("Add task"):
        pet = owner.get_pet(selected_pet_name)
        if pet is not None:
            pet.add_task(
                Task(
                    title=task_title,
                    task_type=task_type,
                    duration_minutes=int(duration),
                    priority=priority,
                    frequency=frequency,
                )
            )
            st.success(f"Task '{task_title}' added to {selected_pet_name}.")

    selected_pet = owner.get_pet(selected_pet_name)
    if selected_pet and selected_pet.tasks:
        st.write(f"**Tasks for {selected_pet.name}:**")
        st.table(
            [
                {
                    "Title": t.title,
                    "Type": t.task_type,
                    "Min": t.duration_minutes,
                    "Priority": t.priority,
                    "Frequency": t.frequency,
                    "Done": t.completed,
                }
                for t in selected_pet.tasks
            ]
        )
else:
    st.info("Add a pet first before adding tasks.")

# ── Build schedule ────────────────────────────────────────────────────────────
st.divider()
st.subheader("Build Schedule")
if st.button("Generate schedule"):
    scheduler = Scheduler(owner=owner)

    pending = scheduler.get_tasks_sorted()
    if pending:
        st.markdown("#### Pending tasks (sorted by deadline → priority)")
        st.table(
            [
                {
                    "Pet": next((p.name for p in owner.pets if t in p.tasks), "—"),
                    "Title": t.title,
                    "Type": t.task_type,
                    "Min": t.duration_minutes,
                    "Priority": t.priority,
                    "Deadline": str(t.deadline) if t.deadline else "—",
                    "Frequency": t.frequency,
                }
                for t in pending
            ]
        )
    else:
        st.info("No pending tasks found.")

    plan = scheduler.generate_plan()

    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.warning("⚠️ Conflicts detected in your schedule:")
        for warn in conflicts:
            st.warning(warn)
    else:
        st.success("✅ No conflicts detected in the planned schedule.")

    if not plan:
        st.info(scheduler.explain_plan())
    else:
        st.success(f"Today's Schedule — {len(plan)} task(s) scheduled")
        st.table(
            [
                {
                    "Start": item.start_time.strftime("%H:%M"),
                    "End": item.end_time.strftime("%H:%M"),
                    "Pet": item.pet.name,
                    "Task": item.task.title,
                    "Type": item.task.task_type,
                    "Priority": item.task.priority,
                    "Reason": item.reason,
                }
                for item in plan
            ]
        )
        st.metric("Plan score", f"{scheduler.score_plan():.0%}")
        st.write("**Explanation:**", scheduler.explain_plan())
