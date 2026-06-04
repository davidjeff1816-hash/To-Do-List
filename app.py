import streamlit as st
from supabase import create_client
from groq import Groq
from dotenv import load_dotenv
import os

# -----------------------------
# Load Environment Variables
# -----------------------------
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="AI Todo List",
    page_icon="✅",
    layout="centered"
)

st.title("🤖 AI Todo List App")

# -----------------------------
# AI Task Generator
# -----------------------------
st.subheader("Generate Tasks with AI")

goal = st.text_area(
    "Describe your goal",
    placeholder="Example: Create a movie review website"
)

if st.button("✨ Generate Tasks"):

    if goal.strip():

        prompt = f"""
        Convert the following goal into a practical todo list.

        Goal:
        {goal}

        Return only tasks.
        One task per line.
        No numbering.
        """

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        tasks_text = response.choices[0].message.content

        tasks = [
            t.strip("-• ")
            for t in tasks_text.split("\n")
            if t.strip()
        ]

        for task in tasks:
            supabase.table("todos").insert({
                "task": task,
                "completed": False
            }).execute()

        st.success("AI Tasks Generated!")
        st.rerun()

# -----------------------------
# Manual Task Entry
# -----------------------------
st.subheader("Add Task Manually")

new_task = st.text_input("Task")

if st.button("➕ Add Task"):

    if new_task.strip():

        supabase.table("todos").insert({
            "task": new_task,
            "completed": False
        }).execute()

        st.success("Task Added")
        st.rerun()

# -----------------------------
# Display Tasks
# -----------------------------
st.subheader("My Tasks")

result = (
    supabase
    .table("todos")
    .select("*")
    .order("id")
    .execute()
)

tasks = result.data

for task in tasks:

    task_id = task["id"]
    task_name = task["task"]
    completed = task["completed"]

    col1, col2 = st.columns([8, 1])

    with col1:

        checked = st.checkbox(
            "",
            value=completed,
            key=f"check_{task_id}"
        )

        if checked:
            st.markdown(
                f"~~{task_name}~~ ✅",
                unsafe_allow_html=False
            )
        else:
            st.markdown(task_name)

    with col2:

        if st.button(
            "🗑️",
            key=f"delete_{task_id}"
        ):
            supabase.table("todos")\
                .delete()\
                .eq("id", task_id)\
                .execute()

            st.rerun()

    if checked != completed:

        supabase.table("todos")\
            .update({
                "completed": checked
            })\
            .eq("id", task_id)\
            .execute()

        st.rerun()

# -----------------------------
# Stats
# -----------------------------
completed_count = len(
    [t for t in tasks if t["completed"]]
)

total_tasks = len(tasks)

st.divider()

st.metric(
    "Progress",
    f"{completed_count}/{total_tasks}"
)