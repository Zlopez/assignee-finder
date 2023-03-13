"""
This script will obtain all issues assigned to list of users.
"""
from typing import List
import json

import click
import requests


PAGURE_URL="https://pagure.io/"
GITHUB_API_URL="https://api.github.com/graphql"
GITHUB_API_TOKEN=""


@click.group()
def cli():
    pass


@click.command()
def get_tickets():
    """
    Get open tickets assigned to list of users.
    """
    pagure_users = ["zlopez"]
    pagure_users_tickets = get_pagure_tickets(pagure_users)

    for user in pagure_users_tickets.keys():
        click.echo("Issues assigned to '{}' ({}):".format(user, pagure_users_tickets[user]["total"]))
        for issue in pagure_users_tickets[user]["issues"]:
            click.echo("* [{}]({})".format(issue["title"], issue["full_url"]))

    github_users = ["zlopez"]
    github_users_tickets = get_github_tickets(github_users)
    for user in github_users_tickets.keys():
        click.echo("Issues assigned to '{}' ({}):".format(user, github_users_tickets[user]["total"]))
        for issue in github_users_tickets[user]["issues"]:
            click.echo("* [{}]({})".format(issue["title"], issue["full_url"]))


def get_pagure_tickets(users: List[str]) -> dict:
    """
    Get tickets assigned to list of users from pagure.io.

    Params:
      users: List of users to retrieve tickets for

    Returns:
      Dictionary containing issues with data we care about.

    Example output::
      {
        "user": {  # username from the list of users
          "issues": [
            {
              0: { # Id of the issue
                "title": "Title", # Title of the issue
                "full_url": "https://pagure.io/project/issue", # Full url to the issue
              },
            },
          ],
          "total": 1,  # Total number of issues retrieved
        }
      }
    """
    output = {}
    for user in users:
        next_page = PAGURE_URL + "api/0/user/" + user + "/issues?status=Open&author=False"

        data = {
            "issues": [],
            "total": 0
        }

        while next_page:
            page_data = get_page_data(next_page)
            data["issues"] = data["issues"] + page_data["issues"]
            data["total"] = data["total"] + page_data["total"]
            next_page = page_data["next_page"]

        output[user] = data

    return output


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

        headers = {"Authorization": f"bearer {GITHUB_API_TOKEN}"}
        resp = requests.post(
            GITHUB_API_URL,
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


def get_page_data(url: str):
    """
    Gets data from the current page returned by pagination.

    Params:
      url: Url for the page

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
        "next_page": "https://pagure.io/next_page" # URL for next page
      }
    """
    r = requests.get(url)
    data = {
        "issues": [],
        "next_page": None,
    }

    if r.status_code == requests.codes.ok:
        page = r.json()
        #click.echo(json.dumps(page, indent=2))
        for issue in page["issues_assigned"]:
            entry = {
                "title": issue["title"],
                "full_url": issue["full_url"],
            }

            data["issues"].append(entry)
        data["next_page"] = page["pagination_issues_assigned"]["next"]
        data["total"] = len(data["issues"])

    return data


def main():
    cli.add_command(get_tickets)
    cli()

if __name__ == "__main__":
    main()
