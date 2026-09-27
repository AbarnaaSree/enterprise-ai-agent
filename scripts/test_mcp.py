from backend.app.services.mcp_client_service import (
    MCPClientService,
)


service = MCPClientService()

result = service.get_employee("Abarnaa")

print("\nMCP Client Service Result:")
print(result)