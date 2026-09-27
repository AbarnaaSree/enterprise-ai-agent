from backend.app.services.agent_service import (
    AgentService,
)


agent = AgentService()


question = (
    "Tell me Abarnaa's remaining vacation and the rules for requesting leave."
)


answer = agent.ask(
    question
)


print("\nQuestion:")
print(question)

print("\nAnswer:")
print(answer)