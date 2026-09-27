from backend.app.services.employee_service import EmployeeService


service = EmployeeService()

employee = service.get_employee("Abarnaa")

print("\nEmployee:")
print(employee)