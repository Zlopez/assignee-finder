"""
Wrapper around github.com. Contains all the functions related to GitHub API calls.
"""
from typing import List
import json

import arrow
import requests


def get_github_tickets(users: List[str]) -> dict:
    """
    Get tickets assigned to list of users from github.com.

    Params:
      users: List of users to retrieve tickets for

    Returns:
      Dictionary containing issues with data we care about.

    Example output::
      {
        "issues": [
          {
            "title": "Title", # Title of the issue
            "full_url": "https://pagure.io/project/issue", # Full url to the issue
          },
        ],
        "total": 1,  # Total number of issues retrieved
      }
    """
    output = {}
    for user in users:
        # Prepare query for GitHub
        query = f"""
{{
    search (query: "assignee:{user} is:issue is:open", type: ISSUE, first: 50) {{
        edges {{
            node {{
                ... on Issue {{
                    title
                    url
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
            return output

        user_data = {}
        issues = []
        for edge in json_data["data"]["search"]["edges"]:
            entry = {
                "title": edge["node"]["title"],
                "full_url": edge["node"]["url"]
            }

            issues.append(entry)
        user_data["issues"] = issues
        user_data["total"] = len(issues)
        output[user] = user_data

    return output
