from pathlib import Path
import re

from backend.app.services.employee_service import EmployeeService
from backend.app.services.document_processor import load_document


class GroundTruthResolver:

    def __init__(self):

        self.employee_service = EmployeeService()

        self.handbook_path = (
            "data/documents/company_handbook.txt"
        )

    def get_database_ground_truth(
        self,
        employee_name: str,
    ) -> dict:

        employee = (
            self.employee_service.get_employee(
                employee_name
            )
        )

        if employee is None:
            return {
                "available": False,
                "source": "database",
                "data": None,
            }

        return {
            "available": True,
            "source": "database",
            "data": employee,
        }

    def get_document_ground_truth(
        self,
        section: str | None = None,
    ) -> dict:

        path = Path(self.handbook_path)

        if not path.exists():
            return {
                "available": False,
                "source": "document",
                "data": None,
            }

        content = load_document(
            self.handbook_path
        )

        if section is None:
            return {
                "available": True,
                "source": "document",
                "data": content,
            }

        section_text = self._extract_section(
            content,
            section,
        )

        if section_text is None:
            return {
                "available": False,
                "source": "document",
                "data": None,
            }

        return {
            "available": True,
            "source": "document",
            "section": section,
            "data": section_text,
        }

    def _extract_section(
        self,
        content: str,
        section: str,
    ) -> str | None:

        lines = content.splitlines()

        section_start = None

        for index, line in enumerate(lines):

            if line.strip() == section:
                section_start = index + 1
                break

        if section_start is None:
            return None

        section_lines = []

        for line in lines[section_start:]:

            stripped = line.strip()

            # A new top-level policy section begins
            # when we encounter a known heading-style line
            # followed by content.
            if (
                stripped
                and stripped != section
                and stripped in {
                    "Annual Leave Policy",
                    "Work From Home Policy",
                    "Information Security Policy",
                }
            ):
                break

            section_lines.append(line)

        section_text = "\n".join(
            section_lines
        ).strip()

        if not section_text:
            return None

        return section_text