EVALUATION_DATASET = [

    # --------------------------------------------------
    # DATABASE TESTS
    # --------------------------------------------------

    {
        "question": "What is Abarnaa's leave balance?",
        "ground_truth": {
            "source": "database",
            "entity": "Abarnaa",
            "field": "leave_balance",
        },
    },

    {
        "question": "Which department does Abarnaa work in?",
        "ground_truth": {
            "source": "database",
            "entity": "Abarnaa",
            "field": "department",
        },
    },

    {
        "question": "What is Abarnaa's role?",
        "ground_truth": {
            "source": "database",
            "entity": "Abarnaa",
            "field": "role",
        },
    },

    {
        "question": "Where is Abarnaa located?",
        "ground_truth": {
            "source": "database",
            "entity": "Abarnaa",
            "field": "location",
        },
    },

    {
        "question": "What is Abarnaa's salary?",
        "ground_truth": {
            "source": "database",
            "entity": "Abarnaa",
            "field": "salary",
        },
    },

    {
        "question": "What is Rahul's leave balance?",
        "ground_truth": {
            "source": "database",
            "entity": "Rahul",
            "field": "leave_balance",
        },
    },

    {
        "question": "What is Priya's role?",
        "ground_truth": {
            "source": "database",
            "entity": "Priya",
            "field": "role",
        },
    },

    {
        "question": "What is Arun's location?",
        "ground_truth": {
            "source": "database",
            "entity": "Arun",
            "field": "location",
        },
    },


    # --------------------------------------------------
    # DOCUMENT / RAG TESTS
    # --------------------------------------------------

    {
        "question": (
            "How many days of annual leave are "
            "full-time employees eligible for?"
        ),
        "ground_truth": {
            "source": "document",
            "section": "Annual Leave Policy",
        },
    },

    {
        "question": (
            "How early should planned leave "
            "be requested?"
        ),
        "ground_truth": {
            "source": "document",
            "section": "Annual Leave Policy",
        },
    },

    {
        "question": (
            "Can emergency leave be requested "
            "without advance notice?"
        ),
        "ground_truth": {
            "source": "document",
            "section": "Annual Leave Policy",
        },
    },

    {
        "question": (
            "Who needs to approve a leave request?"
        ),
        "ground_truth": {
            "source": "document",
            "section": "Annual Leave Policy",
        },
    },

    {
        "question": (
            "How many days per week can employees "
            "work from home?"
        ),
        "ground_truth": {
            "source": "document",
            "section": "Work From Home Policy",
        },
    },

    {
        "question": (
            "What must remote employees do during "
            "their working hours?"
        ),
        "ground_truth": {
            "source": "document",
            "section": "Work From Home Policy",
        },
    },

    {
        "question": (
            "Can company confidential information "
            "be shared externally?"
        ),
        "ground_truth": {
            "source": "document",
            "section": "Information Security Policy",
        },
    },

    {
        "question": (
            "How should company credentials be stored?"
        ),
        "ground_truth": {
            "source": "document",
            "section": "Information Security Policy",
        },
    },


    # --------------------------------------------------
    # COMBINED RAG + DATABASE TESTS
    # --------------------------------------------------

    {
        "question": (
            "Tell me Abarnaa's leave balance and "
            "the rules for requesting annual leave."
        ),
        "ground_truth": {
            "source": "combined",
            "entity": "Abarnaa",
            "field": "leave_balance",
            "section": "Annual Leave Policy",
        },
    },

    {
        "question": (
            "What is Abarnaa's role and can employees "
            "work from home?"
        ),
        "ground_truth": {
            "source": "combined",
            "entity": "Abarnaa",
            "field": "role",
            "section": "Work From Home Policy",
        },
    },


    # --------------------------------------------------
    # UNAVAILABLE / OUT-OF-SCOPE TESTS
    # --------------------------------------------------

    {
        "question": "What is Abarnaa's salary?",
        "ground_truth": {
            "source": "database",
            "entity": "Abarnaa",
            "field": "salary",
        },
    },

    {
        "question": (
            "What is the company's stock price?"
        ),
        "ground_truth": {
            "source": "none",
        },
    },

    {
        "question": (
            "What is Abarnaa's personal phone number?"
        ),
        "ground_truth": {
            "source": "database",
            "entity": "Abarnaa",
            "field": "phone_number",
        },
    },

]