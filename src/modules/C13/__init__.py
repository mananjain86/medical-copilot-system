from .login import login_page
from .patient_search import patient_search_page

__all__ = [
    "login_page",
    "patient_search_page",
]

# Optional exports: keep package importable in frontend-only mode when
# backend deps like psycopg2 are not installed.
try:
    from .backend import (
        GeneratedSQL,
        PROJECTDB_SQL_PATH,
        SearchQuery,
        SearchResult,
        create_patient_cohort,
        expand_terms,
        generate_sql,
        get_cohort_members,
        get_cohorts,
        get_connection,
        get_saved_queries,
        get_search_history,
        initialize_projectdb,
        nl_search_pipeline,
        parse_query,
        resolve_diagnosis,
        resolve_symptom,
        run_search,
        save_query,
    )

    __all__ += [
        "GeneratedSQL",
        "PROJECTDB_SQL_PATH",
        "SearchQuery",
        "SearchResult",
        "create_patient_cohort",
        "expand_terms",
        "generate_sql",
        "get_cohort_members",
        "get_cohorts",
        "get_connection",
        "get_saved_queries",
        "get_search_history",
        "initialize_projectdb",
        "nl_search_pipeline",
        "parse_query",
        "resolve_diagnosis",
        "resolve_symptom",
        "run_search",
        "save_query",
    ]
except Exception:
    pass

try:
    from .admin_search import admin_search_page

    __all__.append("admin_search_page")
except Exception:
    pass
