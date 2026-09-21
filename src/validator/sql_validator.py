import re
from typing import Tuple

class SQLValidator:
    FORBIDDEN_KEYWORDS = [
        r"\bDROP\b",
        r"\bDELETE\b",
        r"\bUPDATE\b",
        r"\bINSERT\b",
        r"\bALTER\b",
        r"\bTRUNCATE\b",
        r"\bEXEC\b",
        r"\bCREATE\b",
        r"\bREPLACE\b",
        r"\bGRANT\b",
        r"\bREVOKE\b"
    ]

    @classmethod
    def is_safe_query(cls, sql_query: str) -> Tuple[bool, str]:
        """
        Validates that the SQL query is a read-only SELECT query and does not contain dangerous modifications.
        Returns (is_safe: bool, reason: str).
        """
        cleaned_query = sql_query.strip()

        # Remove trailing semicolon if present
        if cleaned_query.endswith(";"):
            cleaned_query = cleaned_query[:-1].strip()

        # Check for multiple SQL statements (semicolon separation)
        if ";" in cleaned_query:
            return False, "Multiple SQL statements detected. Only single SELECT statements are permitted."

        # Verify query starts with SELECT or WITH (CTEs)
        upper_query = cleaned_query.upper()
        if not (upper_query.startswith("SELECT") or upper_query.startswith("WITH")):
            return False, "Query must start with a SELECT or WITH statement."

        # Check for forbidden mutation keywords
        for pattern in cls.FORBIDDEN_KEYWORDS:
            if re.search(pattern, upper_query):
                return False, f"Forbidden keyword detected in query matching pattern: {pattern}"

        return True, "Query passed security validation."
