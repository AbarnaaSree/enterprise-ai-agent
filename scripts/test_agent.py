from backend.app.services.agent_service import (
    AgentService,
)


agent = AgentService()


question = (
    "Tell me Abarnaa's remaining vacation and the rules for requesting leave."
)


result = agent.run_for_evaluation(
    question
)


print("\nQuestion:")
print(question)

print("\nExecution Steps:")
print(result["execution_steps"])

print("\nRoute:")
print(result["route"])

print("\nAnswer:")
print(result["answer"])
print("\nQuestion:")
print(question)

print("\nExecution Steps:")
print(result["execution_steps"])

print("\nRoute:")
print(result["route"])

print("\nWorkflow:")
print(result["workflow"])

print("\nAnswer:")
print(result["answer"])