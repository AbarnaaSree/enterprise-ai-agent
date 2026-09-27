from typing import TypedDict

from pydantic import BaseModel

from langgraph.graph import (
    StateGraph,
    START,
    END,
)
from langfuse import observe, propagate_attributes

from backend.app.services.retriever_service import (
    RetrieverService,
)

from backend.app.services.llm_service import (
    generate_response,
    generate_structured_response,
)
from backend.app.services.mcp_client_service import (
    MCPClientService,
)

from backend.app.services.response_validator import (
    ResponseValidator,
)

class RouteDecision(BaseModel):
    needs_rag: bool
    needs_database: bool
    employee_name: str | None
    rag_query: str | None = None

class AgentState(TypedDict):

    question: str
    context: str
    answer: str
    route: str
    employee_data: dict
    employee_name: str | None
    rag_query: str | None


class AgentService:

    def __init__(self):

        self.retriever_service = (
            RetrieverService()
        )
        self.mcp_client = MCPClientService()
        self.response_validator = ResponseValidator()

        self.graph = self._build_graph()
    
    def validate_node(
        self,
        state: AgentState,
    ) -> AgentState:

        answer = state["answer"]

        validation = self.response_validator.validate(
            answer,
            state,
        )

        if not validation["valid"]:
            answer = (
                "I could not safely validate the generated "
                "response."
            )

        return {
            **state,
            "answer": answer,
        }   

    def route_question(
        self,
        state: AgentState,
    ) -> AgentState:

        question = state["question"]

        prompt = f"""
You are a routing agent for an enterprise AI assistant.

Analyze the user's question and determine which data sources are required.

Available sources:

1. DATABASE
   Use for employee-specific structured information such as:
   - employee name
   - department
   - role
   - leave balance
   - location
   - other fields available in the employee database

2. DOCUMENT / RAG
   Use for information contained in company documents such as:
   - policies
   - rules
   - procedures
   - guidelines
   - company knowledge

Routing rules:

- Set needs_database=true when the question requires employee-specific
  information from the database.
- Set needs_rag=true when the question requires information from company
  documents.
- Both can be true when the question requires information from both sources.
- Extract the employee name when an employee-specific database lookup is
  required.
- If no employee name is required, set employee_name to null.

RAG QUERY RULE:

When needs_rag=true, generate rag_query as a concise, standalone question
containing ONLY the part of the user's question that should be answered
using the company documents.

Do not include database-specific information in rag_query.

When needs_rag=false, set rag_query to null.

The rag_query must be generated dynamically from the user's question.
Do not assume fixed questions, employee names, or fixed values.

Return only the structured response.

User question:
{state["question"]}
"""

        decision = generate_structured_response(
            prompt,
            RouteDecision,
        )

        print("\nDEBUG ROUTER DECISION:")
        print(decision)

        if decision.needs_rag and decision.needs_database:
            route = "combined"

        elif decision.needs_rag:
            route = "rag"

        elif decision.needs_database:
            route = "database"

        else:
            route = "direct"

        return {
            **state,
            "route": route,
            "employee_name": decision.employee_name,
            "rag_query": decision.rag_query,
        }

    def retrieve_node(
        self,
        state: AgentState,
    ) -> AgentState:

        question = (
            state.get("rag_query")
            or state["question"]
        )

        documents = (
            self.retriever_service.retrieve(
                question
            )
        )

        context = "\n\n".join(
            result["document"].page_content
            for result in documents
        )

        return {
            **state,
            "context": context,
        }
    def database_node(
        self,
        state: AgentState,
    ) -> AgentState:

        question = state["question"]

        employee_name = ""

        employee_name = state.get("employee_name")

        if not employee_name:
            return {
                **state,
                "employee_data": {
                    "found": False,
                    "message": (
                        "Could not identify an employee name."
                    ),
                },
            }

        employee_data = self.mcp_client.get_employee(
            employee_name
        )

        return {
            **state,
            "employee_data": employee_data,
        }
    def generate_node(
        self,
        state: AgentState,
    ) -> AgentState:

        print("\nDEBUG generate_node state:")
        print(state)

        question = state["question"]
        context = state["context"]
        employee_data = state["employee_data"]
        route = state["route"]

        # Database response
        if route == "database":

            if not employee_data.get("found"):
                return {
                    **state,
                    "answer": employee_data.get(
                        "message",
                        "Employee information was not found.",
                    ),
                }

            employee = employee_data["employee"]

            prompt = f"""
        You are an enterprise employee data assistant.

        Your job is to answer the user's question using
        the employee data retrieved from the company database.

        IMPORTANT RULES:

        1. The employee data is the source of truth.
        2. Do not invent any employee information.
        3. Do not change, calculate, or modify database values.
        4. Answer only using the provided employee data.
        5. Give a short, natural-language answer.
        6. If the requested information is not present,
        say that it is not available.

        Retrieved employee data:
        {employee}

        User question:
        {question}

        Answer:
        """

            answer = generate_response(prompt)

            return {
                **state,
                "answer": answer,
            }
        if route == "combined":

            if not context and not employee_data.get("found"):
                return {
                    **state,
                    "answer": (
                        "The requested information is not "
                        "available."
                    ),
                }

            prompt = f"""
        You are an enterprise AI assistant.

        Answer the user's question using ONLY the
        retrieved company information provided below.

        You have two trusted sources:

        1. Company knowledge retrieved from the
        company documents.
        2. Employee data retrieved from the company
        database through an MCP tool.

        IMPORTANT RULES:

        - Use the company document context for company
        policies and general company information.
        - Use the employee data for employee-specific
        information.
        - Treat the retrieved employee data as the
        source of truth.
        - Do not invent any information.
        - Do not change or modify database values.
        - Do not use outside knowledge.
        - If information is missing from the provided
        sources, clearly say that it is not available.

        Company knowledge:
        {context}

        Employee data:
        {employee_data}

        User question:
        {question}

        Answer:
        """

            answer = generate_response(prompt)

            return {
                **state,
                "answer": answer,
            }
        # RAG response
        if route == "rag":

            if not context:

                return {
                    **state,
                    "answer": (
                        "The information is not "
                        "available in the provided "
                        "documents."
                    ),
                }

            prompt = f"""
    You are an enterprise knowledge assistant.

    Answer the user's question using ONLY
    the provided context.

    If the answer cannot be found in the
    context, say that the information is not
    available in the provided documents.

    Do not use outside knowledge.

    Context:
    {context}

    Question:
    {question}

    Answer:
    """

            answer = generate_response(prompt)

            return {
                **state,
                "answer": answer,
            }

        # Direct response
        prompt = f"""
    Answer the user's question directly.

    Question:
    {question}

    Answer:
    """

        answer = generate_response(prompt)

        return {
            **state,
            "answer": answer,
        }
    def combined_node(
        self,
        state: AgentState,
    ) -> AgentState:

        # Retrieve company information from RAG
        rag_state = self.retrieve_node(state)

        # Retrieve employee information through MCP
        database_state = self.database_node(state)

        return {
            **state,
            "context": rag_state["context"],
            "employee_data": database_state["employee_data"],
        }
    def direct_node(
        self,
        state: AgentState,
    ) -> AgentState:

        question = state["question"]

        prompt = f"""
Answer the user's question directly.

Question:
{question}

Answer:
"""

        answer = generate_response(
            prompt
        )

        return {
            **state,
            "answer": answer,
        }

    def _build_graph(self):

        workflow = StateGraph(
            AgentState
        )

        workflow.add_node(
            "router",
            self.route_question,
        )

        workflow.add_node(
            "retrieve",
            self.retrieve_node,
        )
        workflow.add_node(
            "database",
            self.database_node,
        )
        workflow.add_node(
            "combined",
            self.combined_node,
        )

        workflow.add_node(
            "generate",
            self.generate_node,
        )
        workflow.add_node(
            "validate",
            self.validate_node,
        )

        workflow.add_node(
            "direct",
            self.direct_node,
        )

        workflow.add_edge(
            START,
            "router",
        )

        workflow.add_conditional_edges(
            "router",
            lambda state: state["route"],
            {
                "rag": "retrieve",
                "database": "database",
                "combined": "combined",
                "direct": "direct",
            },
        )

        workflow.add_edge(
            "retrieve",
            "generate",
        )
        workflow.add_edge(
            "database",
            "generate",
        )
        workflow.add_edge(
            "combined",
            "generate",
        )

        workflow.add_edge(
            "generate",
            "validate",
        )

        workflow.add_edge(
            "validate",
            END,
        )

        workflow.add_edge(
            "direct",
            "validate",
        )

        return workflow.compile()

    @observe(name="enterprise_ai_agent", as_type="agent")
    def ask(
        self,
        question: str,
    ) -> str:

        with propagate_attributes(
            trace_name="enterprise_ai_agent",
            metadata={
                "workflow": "rag_mcp_langgraph",
            },
            tags=[
                "langgraph",
                "rag",
                "mcp",
                "llm",
            ],
        ):

            result = self.graph.invoke(
                {
                    "question": question,
                    "context": "",
                    "answer": "",
                    "route": "",
                    "employee_data": {},
                    "employee_name": None,
                }
            )

            return result["answer"]
    def run_for_evaluation(
        self,
        question: str,
    ) -> AgentState:

        result = self.graph.invoke(
            {
                "question": question,
                "context": "",
                "answer": "",
                "route": "",
                "employee_data": {},
                "employee_name": None,
            }
        )

        return result