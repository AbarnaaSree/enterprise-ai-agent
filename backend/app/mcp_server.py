from mcp.server.mcpserver import MCPServer

from backend.app.services.employee_service import (
    EmployeeService,
)


mcp = MCPServer(
    "Enterprise AI Data Server"
)

employee_service = EmployeeService()


@mcp.tool()
def get_employee(name: str) -> dict:
    """
    Get employee information from the company database.
    """

    employee = employee_service.get_employee(name)

    if employee is None:
        return {
            "found": False,
            "message": f"Employee '{name}' was not found.",
        }

    return {
        "found": True,
        "employee": employee,
    }


if __name__ == "__main__":
    mcp.run()