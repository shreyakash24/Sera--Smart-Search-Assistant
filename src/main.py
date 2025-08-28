from src.user import user
from src.planner import planner
from src.executor import executor
from src.supervisor import supervisor

def main():
    messages=[]
    
    user_input=user.get("Enter your task:")
    messages.append({
        "role": "Supervisor",
        "content": user_input,
        "metadata": {"from_user": True}
    })
    
    while True:
        
        planner_output=planner.step(messages)
        messages.append({"role": "Planner", "content": planner_output})
        
        executor_output = executor.step(messages)
        messages.append({"role": "Executor", "content": executor_output})

        supervisor_feedback = supervisor.step(messages)
        messages.append({
                "role": "Supervisor",
                "content": supervisor_feedback,
                "metadata": {"from_user": False}
            })
        
        if "terminate" in supervisor_feedback["feedback"].lower():
            break



if __name__ == "__main__":
    main()