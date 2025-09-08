import re

# Optional: could be extended to support pronoun resolution, etc.
def rewrite_followup(current_input, last_query_info):
    if not last_query_info:
        return current_input

    rewritten = current_input

    if "level" in last_query_info and "level" not in current_input:
        rewritten += f" for {last_query_info['level']} level"
    if "department" in last_query_info and "department" not in current_input:
        rewritten += f" in {last_query_info['department']} department"

    return rewritten
