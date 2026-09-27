from sqlalchemy import text

from backend.app.db.database import engine


class EmployeeService:

    def get_employee(self, name: str) -> dict | None:

        query = text("""
            SELECT
                id,
                name,
                department,
                role,
                leave_balance,
                location
            FROM employees
            WHERE name = :name
        """)

        with engine.connect() as connection:

            result = connection.execute(
                query,
                {"name": name},
            )

            row = result.mappings().first()

            if row is None:
                return None

            return dict(row)