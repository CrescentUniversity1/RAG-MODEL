import datetime
import os

def log_query(query, score, log_file="query_log.txt"):
    """Logs the query and similarity score with timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"{timestamp} | Query: {query} | Score: {score:.4f}\n"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_line)
