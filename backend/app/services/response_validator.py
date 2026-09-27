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
You are extracting factual claims from an
enterprise employee-data response.

Trusted employee data:

{json.dumps(available_fields, indent=2, default=str)}

Generated answer:

{answer}

Identify only the employee-data facts that the
generated answer explicitly claims.

For every claim:

- field must be one of the fields present in
  the trusted employee data.
- claimed_value must contain the value stated
  by the generated answer.
- Do not invent claims.
- Do not infer information that is not explicitly
  stated.
- Ignore company policies.
- Ignore general explanations.
- Ignore opinions.

Return only the structured response.
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