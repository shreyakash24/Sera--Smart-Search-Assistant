import streamlit as st
import time
import os
from src.planner1 import planner
from src.executor import Executor
from src.supervisor import Supervisor

BROWSER_SNAPSHOT = "post_ss.png"

st.set_page_config(page_title="Sera", page_icon="🤖", layout="centered")

st.title("🤖 Sera — Smart Search Assistant")
st.caption("A multi-agent system with Planner, Executor, and Supervisor")
st.markdown("---")
st.caption("Built with ❤️ by Sera team")
user_task = st.chat_input(
    "Enter your task (e.g. Find cheapest flight from Mumbai to Delhi for 2 adults on 5th September)"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "image" in msg:
            st.image(msg["image"], caption="Browser snapshot")

def run_pipeline(user_task):

    messages = [{"role": "user", "content": user_task}]
    step = 1

    while True:
        planner_output = planner.generate_reply(messages)
        messages.append(planner_output)
        yield "planner", f"🧭 **Step {step} – Planner:**\n\n{planner_output}",None
        time.sleep(0.3)

        executor_output = Executor.generate_reply(messages)
        messages.append(executor_output)
        if os.path.exists("post_ss.png"):
            BROWSER_SNAPSHOT = "post_ss.png"
        else:
            BROWSER_SNAPSHOT = None

        yield "executor", f"⚙️ **Step {step} – Executor:**\n\n{executor_output}", BROWSER_SNAPSHOT
        time.sleep(0.3)

        supervisor_feedback = Supervisor.generate_reply(messages)
        messages.append(supervisor_feedback)
        yield "supervisor", f"🧩 **Step {step} – Supervisor:**\n\n{supervisor_feedback}",None
        time.sleep(0.3)

        if supervisor_feedback["content"]["is_terminate"]:
            yield "system", "✅ Supervisor has terminated the process. Pipeline complete!",None
            break

        step += 1


if user_task:
    st.session_state.messages.append({"role": "user", "content": user_task})
    with st.chat_message("user"):
        st.markdown(user_task)

    with st.spinner("Running pipeline..."):
        for role, content, image_path in run_pipeline(user_task):
            with st.chat_message(role, avatar="🤖" if role != "user" else "🧑"):
                st.markdown(content)
                if image_path:
                    st.image(image_path, caption="🌐 Browser snapshot")
            st.session_state.messages.append(
                {"role": role, "content": content, **({"image": BROWSER_SNAPSHOT} if BROWSER_SNAPSHOT else {})}
            )


