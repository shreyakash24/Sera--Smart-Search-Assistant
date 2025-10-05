import streamlit as st
import time
from planner1 import planner
from executor import Executor
from supervisor import Supervisor

st.set_page_config(page_title="Sera", page_icon="🤖", layout="centered")

st.title("🤖 Sera — Smart Search Assistant")
st.caption("A multi-agent system with Planner, Executor, and Supervisor")

user_task = st.chat_input(
    "Enter your task (e.g. Find cheapest flight from Mumbai to Delhi for 2 adults on 5th September)"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


def run_pipeline(user_task):
    """Generator that yields (role, content)."""
    messages = [{"role": "user", "content": user_task}]
    step = 1

    while True:
        planner_output = planner.generate_reply(messages)
        messages.append(planner_output)
        yield "planner", f"🧭 **Step {step} – Planner:**\n\n{planner_output}"
        time.sleep(0.3)

        executor_output = Executor.generate_reply(messages)
        messages.append(executor_output)
        yield "executor", f"⚙️ **Step {step} – Executor:**\n\n{executor_output}"
        time.sleep(0.3)

        supervisor_feedback = Supervisor.generate_reply(messages)
        messages.append(supervisor_feedback)
        yield "supervisor", f"🧩 **Step {step} – Supervisor:**\n\n{supervisor_feedback}"
        time.sleep(0.3)

        if supervisor_feedback["content"]["is_terminate"]:
            yield "system", "✅ Supervisor has terminated the process. Pipeline complete!"
            break

        step += 1


if user_task:
    st.session_state.messages.append({"role": "user", "content": user_task})
    with st.chat_message("user"):
        st.markdown(user_task)

    with st.spinner("Running pipeline..."):
        for role, content in run_pipeline(user_task):
            with st.chat_message(role, avatar="🤖" if role != "user" else "🧑"):
                st.markdown(content)
            st.session_state.messages.append({"role": role, "content": content})

st.markdown("---")
st.caption("Built with ❤️ by Sera team")
