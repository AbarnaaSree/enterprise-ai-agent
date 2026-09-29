import json
from typing import Any

from langfuse import observe
from pydantic import BaseModel

from backend.app.services.llm_service import (
    generate_structured_response,
)


class EmployeeClaim(BaseModel):
    field: str
    claimed_value: str


class EmployeeClaims(BaseModel):
    claims: list[EmployeeClaim]


class ResponseValidator:

    @observe(
        name="response_validation",
        as_type="guardrail",
    )
    def validate(
        self,
        answer: str,
        state: dict[str, Any],
    ) -> dict[str, Any]:

        errors = []
        warnings = []

        # -------------------------------------------------
        # 1. Basic empty-response validation
        # -------------------------------------------------

        if not answer or not answer.strip():

            errors.append(
                "LLM returned an empty response."
            )

            return {
                "valid": False,
                "answer": "",
                "errors": errors,
                "warnings": warnings,
            }

        # -------------------------------------------------
        # 2. Get trusted employee data
        # -------------------------------------------------

        employee_data = state.get(
            "employee_data",
            {},
        )

        if not employee_data.get("found"):

            return {
                "valid": True,
                "answer": answer.strip(),
                "errors": errors,
                "warnings": warnings,
            }

        employee = employee_data.get(
            "employee",
            {},
        )

        if not employee:

            return {
                "valid": True,
                "answer": answer.strip(),
                "errors": errors,
                "warnings": warnings,
            }

        # -------------------------------------------------
        # 3. Get all available database fields dynamically
        # -------------------------------------------------

        available_fields = {
            key: value
            for key, value in employee.items()
            if value is not None
        }

        # -------------------------------------------------
        # 4. Extract employee-related claims from answer
        # -------------------------------------------------

        extraction_prompt = f"""
You are validating an enterprise AI assistant response.

Your task is to extract ONLY facts about the specific employee
that come from the trusted employee database.

Trusted employee data:

{json.dumps(available_fields, indent=2, default=str)}

Generated answer:

{answer}

IMPORTANT DISTINCTION:

The generated answer may contain TWO types of information:

1. EMPLOYEE-SPECIFIC FACTS
   These describe the specific employee and must be checked
   against the trusted employee database.

   Example:
   "Abarnaa has 12 days of leave remaining."

   This is an employee-specific fact.

2. COMPANY POLICY / GENERAL INFORMATION
   These describe company-wide rules or policies and must NOT
   be checked against the employee database.

   Examples:
   "Employees receive 18 days of annual leave per year."
   "Leave requests should be submitted 3 working days in advance."
   "Emergency leave does not require advance notice."

   These are NOT employee database claims.

CRITICAL RULE:

Do NOT interpret a company-policy value as an employee value.

For example, if the answer says:

"Abarnaa has 12 days remaining. Employees receive 18 days
of annual leave per year."

Extract ONLY:

{{
  "field": "leave_balance",
  "claimed_value": "12"
}}

Do NOT extract:

{{
  "field": "leave_balance",
  "claimed_value": "18"
}}

Only extract a claim when the answer clearly states that
the value belongs to the specific employee.

Additional rules:

- field must be one of the fields in the trusted employee data.
- claimed_value must be the value explicitly stated for that employee.
- Do not infer values.
- Do not extract company policies.
- Do not extract general rules.
- Do not extract general eligibility information.
- Do not extract annual entitlement unless it is explicitly
  stated as this employee's personal entitlement.
- Ignore opinions and explanations.
- If there are no employee-specific claims, return an empty claims array.

Return exactly this JSON structure:

{{
  "claims": [
    {{
      "field": "leave_balance",
      "claimed_value": "12"
    }}
  ]
}}

The top-level response MUST be an object containing a "claims" array.
"""

        try:

            extracted = generate_structured_response(
                extraction_prompt,
                EmployeeClaims,
            )

        except Exception as error:

            warnings.append(
                "Could not extract employee claims "
                f"for validation: {error}"
            )

            return {
                "valid": True,
                "answer": answer.strip(),
                "errors": errors,
                "warnings": warnings,
            }

        # -------------------------------------------------
        # 5. Compare claims with trusted database values
        # -------------------------------------------------

        for claim in extracted.claims:

            field = claim.field

            if field not in available_fields:
                continue

            expected_value = str(
                available_fields[field]
            ).strip().lower()

            claimed_value = str(
                claim.claimed_value
            ).strip().lower()

            if expected_value != claimed_value:

                errors.append(
                    "LLM generated an incorrect value "
                    f"for '{field}'. "
                    f"Generated value: "
                    f"'{claim.claimed_value}', "
                    f"database value: "
                    f"'{available_fields[field]}'."
                )

        # -------------------------------------------------
        # 6. Return validation result
        # -------------------------------------------------

        return {
            "valid": len(errors) == 0,
            "answer": answer.strip(),
            "errors": errors,
            "warnings": warnings,
        }