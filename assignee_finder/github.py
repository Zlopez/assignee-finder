"""
Wrapper around github.com. Contains all the functions related to GitHub API calls.
"""
from typing import List
import json

import arrow
import requests


def get_github_tickets(days_ago: int, till: str, users: List[str]) -> dict:
    """
    Get tickets assigned to list of users from github.com.

    Params:
      days_ago: How many days ago to look for the issues
      till: Limit results to the day set by this argument. Default None will be replaced by `arrow.utcnow()`.
      users: List of users to retrieve tickets for

    Returns:
      Dictionary containing issues with data we care about.

    Example output::
      {
        "issues": [
          {
            "title": "Title", # Title of the issue
            "full_url": "https://pagure.io/project/issue", # Full url to the issue
            "status": "OPEN", # Status of the ticket OPEN/CLOSED
          },
        ],
        "total": 1,  # Total number of issues retrieved
      }
    """
    output = {}

    if till:
        till = arrow.get(till, "DD.MM.YYYY")
    else:
        till = arrow.utcnow()
    since = till.shift(days=-days_ago)

    for user in users:
        open_issues = get_open_github_tickets(user)
        closed_issues = get_closed_github_tickets(user, till, since)

        user_data = {}
        user_data["issues"] = open_issues + closed_issues
        user_data["total"] = len(open_issues) + len(closed_issues)
        output[user] = user_data

    return output

def get_open_github_tickets(user: str) -> dict:
    """
    Get open tickets assigned to user.

    Params:
      user: User to retrieve tickets for

    Returns:
      Dictionary containing issues with data we care about.

    Example output::
       [
          {
            "title": "Title", # Title of the issue
            "full_url": "https://github.com/project/issue", # Full url to the issue
            "status": "OPEN", # Status of the ticket
          },
        ]
    """
    # Prepare query for GitHub
    query = f"""
{{
    search (query: "assignee:{user} is:issue is:open", type: ISSUE, first: 50) {{
        edges {{
            node {{
                ... on Issue {{
                    title
                    url
                    state
                }}
            }}
        }}
        issueCount
    }}
}}
    """

    headers = {"Authorization": f"bearer {CONFIG['GitHub']['github_api_token']}"}
    resp = requests.post(
        CONFIG["GitHub"]["github_api_url"],
        json={"query": query},
        headers=headers
    )
    if resp.ok:
        json_data = resp.json()
    else:
        click.echo(
            f"Github request failed with status '{resp.status_code}': '{resp.reason}'",
            err=True
        )
        return []

    issues = []
    for edge in json_data["data"]["search"]["edges"]:
        entry = {
            "title": edge["node"]["title"],
            "full_url": edge["node"]["url"],
            "status": edge["node"]["state"]
        }

        issues.append(entry)

    return issues


def get_closed_github_tickets(user: str, till: arrow.Arrow, since: arrow.Arrow) -> dict:
    """
    Get closed tickets assigned to user closed in specified interval
    since < closed_at < till.

    Params:
      user: User to retrieve tickets for
      till: Till date for closed issues. This will take in account closed_at
            key of the issue.
      since: Since date for closed issues. This will take in account closed_at
            key of the issue.

    Returns:
      Dictionary containing issues with data we care about.

    Example output::
      [
        {
          "title": "Title", # Title of the issue
          "full_url": "https://github.com/project/issue", # Full url to the issue
          "status": "CLOSED", # Status of the ticket
        },
      ],
    """
    # Prepare query for GitHub
    query = f"""
{{
    search (query: "assignee:{user} is:issue closed:>{since.format('YYYY-MM-DD')}", type: ISSUE, first: 50) {{
        edges {{
            node {{
                ... on Issue {{
                    title
                    url
                    state
                    closedAt
                }}
            }}
        }}
        issueCount
    }}
}}
    """

    headers = {"Authorization": f"bearer {CONFIG['GitHub']['github_api_token']}"}
    resp = requests.post(
        CONFIG["GitHub"]["github_api_url"],
        json={"query": query},
        headers=headers
    )
    if resp.ok:
        json_data = resp.json()
    else:
        click.echo(
            f"Github request failed with status '{resp.status_code}': '{resp.reason}'",
            err=True
        )
        return []

    issues = []
    for edge in json_data["data"]["search"]["edges"]:
        closed_at = arrow.get(edge["node"]["closedAt"])

        # Limit the tickets till the date we want
        if closed_at > till:
            continue

        entry = {
            "title": edge["node"]["title"],
            "full_url": edge["node"]["url"],
            "status": edge["node"]["state"]
        }

        issues.append(entry)

    return issues
