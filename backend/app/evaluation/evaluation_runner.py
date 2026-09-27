from backend.app.services.agent_service import AgentService
from backend.app.evaluation.evaluation_dataset import (
    EVALUATION_DATASET,
)
from backend.app.evaluation.ground_truth import (
    GroundTruthResolver,
)
from backend.app.evaluation.llm_judge import (
    evaluate_groundedness,
    evaluate_answerability,
)


def evaluate_database_answer(
    question: str,
    actual_answer: str,
    ground_truth: dict,
) -> bool:

    if not ground_truth["available"]:
        return evaluate_unavailable_answer(
            question=question,
            actual_answer=actual_answer,
        )

    employee = ground_truth["data"]

    field = ground_truth.get("field")

    # If the requested field does not exist
    # in the authoritative database record,
    # the correct behavior is to indicate
    # that the information is unavailable.
    if field not in employee:

        return evaluate_unavailable_answer(
            question=question,
            actual_answer=actual_answer,
        )

    expected_value = employee.get(field)

    if expected_value is None:

        return evaluate_unavailable_answer(
            question=question,
            actual_answer=actual_answer,
        )

    answer = actual_answer.lower()

    employee_name = str(
        employee["name"]
    ).lower()

    # For available fields, the answer should
    # refer to the correct employee.
    if employee_name not in answer:
        return False

    # Verify the actual database value dynamically.
    return str(expected_value).lower() in answer

def evaluate_document_answer(
    question: str,
    actual_answer: str,
    ground_truth: dict,
) -> bool:

    if not ground_truth["available"]:
        return False

    result = evaluate_groundedness(
        question=question,
        answer=actual_answer,
        source=ground_truth["data"],
    )

    print(
        f"LLM judge grounded: {result.grounded}"
    )

    print(
        f"LLM judge reason: {result.reason}"
    )

    return result.grounded


def evaluate_combined_answer(
    question: str,
    actual_answer: str,
    database_ground_truth: dict,
    document_ground_truth: dict,
) -> bool:

    if not database_ground_truth["available"]:
        return False

    if not document_ground_truth["available"]:
        return False

    result = evaluate_groundedness(
        question=question,
        answer=actual_answer,
        source=(
            "DATABASE SOURCE:\n"
            f"{database_ground_truth['data']}\n\n"
            "DOCUMENT SOURCE:\n"
            f"{document_ground_truth['data']}"
        ),
    )

    print(
        f"LLM judge grounded: {result.grounded}"
    )

    print(
        f"LLM judge reason: {result.reason}"
    )

    return result.grounded

def evaluate_unavailable_answer(
    question: str,
    actual_answer: str,
) -> bool:

    result = evaluate_answerability(
        question=question,
        answer=actual_answer,
    )

    print(
        f"LLM answerability judge: "
        f"{result.appropriate}"
    )

    print(
        f"LLM answerability reason: "
        f"{result.reason}"
    )

    return result.appropriate

def run_evaluation():

    agent = AgentService()

    ground_truth_resolver = (
        GroundTruthResolver()
    )

    total = len(EVALUATION_DATASET)
    passed = 0
    route_passed = 0
    answer_passed = 0

    print("\n" + "=" * 60)
    print("ENTERPRISE AI AGENT EVALUATION")
    print("=" * 60)

    for index, test_case in enumerate(
        EVALUATION_DATASET,
        start=1,
    ):

        question = test_case["question"]

        ground_truth_config = (
            test_case["ground_truth"]
        )

        source = ground_truth_config[
            "source"
        ]

        print("\n" + "-" * 60)
        print(f"Test Case: {index}")
        print(f"Question: {question}")
        print(
            f"Ground-truth source: {source}"
        )

        try:

            # -----------------------------------------
            # 1. Run the actual agent
            # -----------------------------------------

            result = agent.run_for_evaluation(
                question
            )

            actual_answer = result["answer"]
            actual_route = result["route"]

            # -----------------------------------------
            # 2. Resolve ground truth dynamically
            # -----------------------------------------

            if source == "database":

                employee_name = (
                    ground_truth_config.get(
                        "entity"
                    )
                )

                ground_truth = (
                    ground_truth_resolver
                    .get_database_ground_truth(
                        employee_name
                    )
                )

                ground_truth["field"] = (
                    ground_truth_config.get("field")
                )

            elif source == "document":

                section = (
                    ground_truth_config.get(
                        "section"
                    )
                )

                ground_truth = (
                    ground_truth_resolver
                    .get_document_ground_truth(
                        section
                    )
                )

            elif source == "combined":

                ground_truth = {
                    "available": True,
                    "source": "combined",
                    "data": None,
                }

            else:

                ground_truth = {
                    "available": False,
                    "source": source,
                    "data": None,
                }

            # -----------------------------------------
            # 3. Evaluate answer
            # -----------------------------------------

            if source == "database":

                answer_pass = (
                    evaluate_database_answer(
                        question=question,
                        actual_answer=actual_answer,
                        ground_truth=ground_truth,
                    )
                )

            elif source == "document":

                answer_pass = (
                    evaluate_document_answer(
                        question,
                        actual_answer,
                        ground_truth,
                    )
                )

            elif source == "combined":

                database_ground_truth = (
                    ground_truth_resolver
                    .get_database_ground_truth(
                        ground_truth_config["entity"]
                    )
                )

                document_ground_truth = (
                    ground_truth_resolver
                    .get_document_ground_truth(
                        ground_truth_config["section"]
                    )
                )

                answer_pass = (
                    evaluate_combined_answer(
                        question=question,
                        actual_answer=actual_answer,
                        database_ground_truth=database_ground_truth,
                        document_ground_truth=document_ground_truth,
                    )
                )

            else:

                answer_pass = (
                    evaluate_unavailable_answer(
                        question,
                        actual_answer,
                    )
                )

            # -----------------------------------------
            # 4. Evaluate routing
            # -----------------------------------------

            if source == "document":

                route_pass = (
                    actual_route == "rag"
                )

            elif source == "database":

                route_pass = (
                    actual_route == "database"
                )

            elif source == "combined":

                route_pass = (
                    actual_route == "combined"
                )

            else:

                route_pass = True

            # -----------------------------------------
            # 5. Final result
            # -----------------------------------------

            is_pass = (
                answer_pass
                and route_pass
            )

            print(
                f"Actual answer: {actual_answer}"
            )

            print(
                f"Actual route: {actual_route}"
            )

            print(
                "Answer check: "
                f"{'PASS' if answer_pass else 'FAIL'}"
            )

            print(
                "Route check: "
                f"{'PASS' if route_pass else 'FAIL'}"
            )

            print(
                "Status: "
                f"{'PASS' if is_pass else 'FAIL'}"
            )

            if answer_pass:
                answer_passed += 1

            if route_pass:
                route_passed += 1

            if is_pass:
                passed += 1

        except Exception as error:

            print(f"Error: {error}")
            print("Status: FAIL")

    accuracy = (
        passed / total * 100
        if total
        else 0
    )
    answer_accuracy = (
        answer_passed / total * 100
        if total
        else 0
    )

    route_accuracy = (
        route_passed / total * 100
        if total
        else 0
    )

    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)

    print(f"Total tests : {total}")
    print(f"Passed      : {passed}")
    print(f"Failed      : {total - passed}")
    print(f"Accuracy    : {accuracy:.2f}%")
    print(
        f"Answer accuracy : {answer_accuracy:.2f}%"
    )

    print(
        f"Route accuracy  : {route_accuracy:.2f}%"
    )
    print("=" * 60)


if __name__ == "__main__":
    run_evaluation()