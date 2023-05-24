"""
Wrapper around github.com. Contains all the functions related to GitHub API calls.
"""
from typing import List
import json

import arrow
import click
import requests


def get_github_tickets_repos(days_ago: int, till: str, repos: List[str]) -> dict:
    """
    Get closed tickets in repositories from github.com.

    Params:
      days_ago: How many days ago to look for the issues
      till: Limit results to the day set by this argument. Default None will be replaced by `arrow.utcnow()`.
      repos: List of repositories to retrieve tickets for

    Returns:
      Dictionary containing issues with data we care about.

    Example output::
      {
        "repo": {  # repo from the list of repositories
          "issues": [
            {
              "title": "Title", # Title of the issue
              "full_url": "https://pagure.io/project/issue", # Full url to the issue
              "status": "OPEN", # Status of the ticket OPEN/CLOSED
            },
          ],
          "total": 1,  # Total number of issues retrieved
        }
      }
    """
    output = {}

    if till:
        till = arrow.get(till, "DD.MM.YYYY")
    else:
        till = arrow.utcnow()
    since = till.shift(days=-days_ago)

    for repo in repos:
        closed_issues = get_closed_github_tickets_repo(repo, till, since)

        data = {}
        data["issues"] = closed_issues
        data["total"] = len(closed_issues)
        output[repo] = data

    return output


def get_closed_github_tickets_repo(repo: str, till: arrow.Arrow, since: arrow.Arrow) -> dict:
    """
    Get tickets on the repo closed in specified interval
    since < closed_at < till.

    Params:
      repo: Repository to retrieve tickets for
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
    excludes = CONFIG["GitHub"]["excludes"]
    repo_without_prefix = repo.removeprefix("https://github.com/")
    owner = repo_without_prefix.split("/")[0]
    name = repo_without_prefix.split("/")[1]
    # Prepare query for GitHub
    query = f"""
{{
    repository (owner: "{owner}", name: "{name}") {{
        issues (last: 20, states: CLOSED) {{
            edges {{
                node {{
                    title
                    url
                    state
                    closedAt
                }}
            }}
        }}
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
    for edge in json_data["data"]["repository"]["issues"]["edges"]:
        closed_at = arrow.get(edge["node"]["closedAt"])

        # Limit the tickets till and since the date we want
        if closed_at > till or closed_at < since:
            continue

        excluded = False
        for exclude in excludes:
            if edge["node"]["url"].startswith(exclude):
                excluded = True
                break

        if excluded:
            continue

        entry = {
            "title": edge["node"]["title"],
            "full_url": edge["node"]["url"],
            "status": edge["node"]["state"]
        }

        issues.append(entry)

    return issues


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
    excludes = CONFIG["GitHub"]["excludes"]
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

        excluded = False
        for exclude in excludes:
            if edge["node"]["url"].startswith(exclude):
                excluded = True
                break

        if excluded:
            continue

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
    excludes = CONFIG["GitHub"]["excludes"]
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

        excluded = False
        for exclude in excludes:
            if edge["node"]["url"].startswith(exclude):
                excluded = True
                break

        if excluded:
            continue

        entry = {
            "title": edge["node"]["title"],
            "full_url": edge["node"]["url"],
            "status": edge["node"]["state"]
        }

        issues.append(entry)

    return issues


def get_github_pull_requests_repos(days_ago: int, till: str, repos: List[str]) -> dict:
    """
    Get closed pull requests from list of repositories from github.com.

    Params:
      days_ago: How many days ago to look for the pull requests
      till: Limit results to the day set by this argument. Default None will be replaced by `arrow.utcnow()`.
      repos: List of repositories to retrieve tickets for

    Returns:
      Dictionary containing pull requests with data we care about.

    Example output::
      {
        "repo": {  # repo from the list of repositories
          "pull_requests": [
            {
              "title": "Title", # Title of the issue
              "full_url": "https://pagure.io/project/issue", # Full url to the issue
              "status": "OPEN", # Status of the ticket OPEN/CLOSED
            },
          ],
          "total": 1,  # Total number of issues retrieved
        }
      }
    """
    output = {}

    if till:
        till = arrow.get(till, "DD.MM.YYYY")
    else:
        till = arrow.utcnow()
    since = till.shift(days=-days_ago)

    for repo in repos:
        closed_pull_requests = get_closed_github_pull_requests_repo(repo, till, since)

        data = {}
        data["pull_requests"] = closed_pull_requests
        data["total"] = len(closed_pull_requests)
        output[repo] = data

    return output


def get_closed_github_pull_requests_repo(repo: str, till: arrow.Arrow, since: arrow.Arrow) -> dict:
    """
    Get pull requests from repository closed in specified interval
    since < closed_at < till.

    Params:
      repo: Repo to retrieve pull requests for
      till: Till date for closed issues. This will take in account closed_at
            key of the issue.
      since: Since date for closed issues. This will take in account closed_at
            key of the issue.

    Returns:
      Dictionary containing pull requests with data we care about.

    Example output::
      [
        {
          "title": "Title", # Title of the issue
          "full_url": "https://github.com/project/issue", # Full url to the pull request
          "status": "MERGED", # Status of the pull request
        },
      ],
    """
    excludes = CONFIG["GitHub"]["excludes"]
    repo_without_prefix = repo.removeprefix("https://github.com/")
    owner = repo_without_prefix.split("/")[0]
    name = repo_without_prefix.split("/")[1]
    # Prepare query for GitHub
    query = f"""
{{
    repository (owner: "{owner}", name: "{name}") {{
        pullRequests (first: 20, states: MERGED, orderBy: {{field: UPDATED_AT, direction: DESC}}) {{
            edges {{
                node {{
                    title
                    url
                    state
                    closedAt
                }}
            }}
        }}
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

    pull_requests = []
    for edge in json_data["data"]["repository"]["pullRequests"]["edges"]:
        closed_at = arrow.get(edge["node"]["closedAt"])

        # Limit the tickets till and since the date we want
        if closed_at > till or closed_at < since:
            continue

        excluded = False
        for exclude in excludes:
            if edge["node"]["url"].startswith(exclude):
                excluded = True
                break

        if excluded:
            continue

        entry = {
            "title": edge["node"]["title"],
            "full_url": edge["node"]["url"],
            "status": edge["node"]["state"]
        }

        pull_requests.append(entry)

    return pull_requests

def get_github_pull_request(days_ago: int, till: str, users: List[str]) -> dict:
    """
    Get pull requests assigned to list of users from github.com.

    Params:
      days_ago: How many days ago to look for the pull requests
      till: Limit results to the day set by this argument. Default None will be replaced by `arrow.utcnow()`.
      users: List of users to retrieve tickets for

    Returns:
      Dictionary containing pull requests with data we care about.

    Example output::
      {
        "user": {  # username from the list of users
          "pull_requests": [
            {
              "title": "Title", # Title of the issue
              "full_url": "https://pagure.io/project/issue", # Full url to the issue
              "status": "OPEN", # Status of the ticket OPEN/CLOSED
            },
          ],
          "total": 1,  # Total number of issues retrieved
        }
      }
    """
    output = {}

    if till:
        till = arrow.get(till, "DD.MM.YYYY")
    else:
        till = arrow.utcnow()
    since = till.shift(days=-days_ago)

    for user in users:
        open_pull_requests = get_open_github_pull_requests(user)
        closed_pull_requests = get_closed_github_pull_requests(user, till, since)

        user_data = {}
        user_data["pull_requests"] = open_pull_requests + closed_pull_requests
        user_data["total"] = len(open_pull_requests) + len(closed_pull_requests)
        output[user] = user_data

    return output

def get_open_github_pull_requests(user: str) -> dict:
    """
    Get open pull requests created by the user.

    Params:
      user: User to retrieve pull requests for

    Returns:
      Dictionary containing pull requests with data we care about.

    Example output::
       [
          {
            "title": "Title", # Title of the issue
            "full_url": "https://github.com/project/issue", # Full url to the pull request
            "status": "OPEN", # Status of the pull request
          },
        ]
    """
    excludes = CONFIG["GitHub"]["excludes"]
    # Prepare query for GitHub
    query = f"""
{{
    search (query: "author:{user} is:pr is:open", type: ISSUE, first: 50) {{
        edges {{
            node {{
                ... on PullRequest {{
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

    pull_requests = []
    for edge in json_data["data"]["search"]["edges"]:

        excluded = False
        for exclude in excludes:
            if edge["node"]["url"].startswith(exclude):
                excluded = True
                break

        if excluded:
            continue

        entry = {
            "title": edge["node"]["title"],
            "full_url": edge["node"]["url"],
            "status": edge["node"]["state"]
        }

        pull_requests.append(entry)

    return pull_requests


def get_closed_github_pull_requests(user: str, till: arrow.Arrow, since: arrow.Arrow) -> dict:
    """
    Get closed pull requests created by user closed in specified interval
    since < closed_at < till.

    Params:
      user: User to retrieve pull requests for
      till: Till date for closed issues. This will take in account closed_at
            key of the issue.
      since: Since date for closed issues. This will take in account closed_at
            key of the issue.

    Returns:
      Dictionary containing pull requests with data we care about.

    Example output::
      [
        {
          "title": "Title", # Title of the issue
          "full_url": "https://github.com/project/issue", # Full url to the pull request
          "status": "MERGED", # Status of the pull request
        },
      ],
    """
    excludes = CONFIG["GitHub"]["excludes"]
    # Prepare query for GitHub
    query = f"""
{{
    search (query: "author:{user} is:pr closed:>{since.format('YYYY-MM-DD')}", type: ISSUE, first: 50) {{
        edges {{
            node {{
                ... on PullRequest {{
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

    pull_requests = []
    for edge in json_data["data"]["search"]["edges"]:
        closed_at = arrow.get(edge["node"]["closedAt"])

        # Limit the tickets till the date we want
        if closed_at > till:
            continue

        excluded = False
        for exclude in excludes:
            if edge["node"]["url"].startswith(exclude):
                excluded = True
                break

        if excluded:
            continue

        entry = {
            "title": edge["node"]["title"],
            "full_url": edge["node"]["url"],
            "status": edge["node"]["state"]
        }

        pull_requests.append(entry)

    return pull_requests
