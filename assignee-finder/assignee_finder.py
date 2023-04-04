"""
This script will obtain all issues assigned to list of users.
"""
from typing import List
import json
import tomllib

import arrow
import click
import requests

# Global variable containing config
CONFIG = {}

@click.group()
def cli():
    pass


@click.command()
@click.option("--days-ago", default=7, help="How many days ago to look for open issues.")
@click.option("--till", default=None, help="Show results till this date. Expects date in DD.MM.YYYY format (31.12.2021).")
@click.option("--config", default="config.toml", help="Path to configuration file to use")
def get_tickets(days_ago: int, till: str, config: dict):
    """
    Get open and closed tickets assigned to list of users.

    Params:
      days_ago: How many days ago to look for the issues
      till: Limit results to the day set by this argument. Default None will be replaced by `arrow.utcnow()`.
      config: Path to configuration file
    """
    global CONFIG

    with open(config, "rb") as config_file:
        CONFIG = tomllib.load(config_file)

    pagure_enabled = CONFIG["Pagure"]["enable"]
    if pagure_enabled:
        pagure_users = CONFIG["Pagure"]["usernames"].values()
        pagure_users_tickets = get_pagure_tickets(days_ago, till, pagure_users)

    github_enabled = CONFIG["GitHub"]["enable"]
    if github_enabled:
        github_users = CONFIG["GitHub"]["usernames"].values()
        github_users_tickets = get_github_tickets(github_users)

    for user in CONFIG["General"]["usernames"]:
        click.echo("# Issues assigned to '{}'\n".format(user))
        if pagure_enabled:
            pagure_user = CONFIG["Pagure"]["usernames"][user]
            click.echo("## Pagure ({})\n".format(pagure_users_tickets[pagure_user]["total"]))
            for issue in pagure_users_tickets[pagure_user]["issues"]:
                if issue["status"] == "Open":
                    click.echo("* [{}]({}) - {}".format(issue["title"], issue["full_url"], issue["status"]))
            for issue in pagure_users_tickets[pagure_user]["issues"]:
                if issue["status"] != "Open":
                    click.echo("* [{}]({}) - {}".format(issue["title"], issue["full_url"], issue["status"]))
            click.echo("")

        if github_enabled:
            github_user = CONFIG["GitHub"]["usernames"][user]
            click.echo("## GitHub ({})\n".format(github_users_tickets[github_user]["total"]))
            for issue in github_users_tickets[github_user]["issues"]:
                click.echo("* [{}]({})".format(issue["title"], issue["full_url"]))

        click.echo("")

def get_pagure_tickets(days_ago: int, till: str, users: List[str]) -> dict:
    """
    Get tickets assigned to list of users from pagure.io.

    Params:
      days_ago: How many days ago to look for the issues
      till: Limit results to the day set by this argument. Default None will be replaced by `arrow.utcnow()`.
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
                "status": Open, # Status of the ticket Open/Closed
              },
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
    since_arg = till.shift(days=-days_ago)

    for user in users:
        next_page = CONFIG["Pagure"]["pagure_url"] + "api/0/user/" + user + "/issues?status=all&author=False&since=" + str(since_arg.int_timestamp)

        data = {
            "issues": [],
            "total": 0
        }

        while next_page:
            page_data = get_page_data(next_page, till, since_arg)
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


def get_page_data(url: str, till: arrow.Arrow, since: arrow.Arrow):
    """
    Gets data from the current page returned by pagination.
    It will filter any issue not closed at time interval specified
    by since and till parameters.
    since < closed_at < till

    Params:
      url: Url for the page
      till: Till date for closed issues. This will take in account closed_at
            key of the issue.
      since: Since date for closed issues. This will take in account closed_at
            key of the issue.

    Returns:
      Dictionary containing issues with data we care about.

    Example output::
      {
        "issues": [
          {
            "title": "Title", # Title of the issue
            "full_url": "https://pagure.io/project/issue", # Full url to the issue
            "status": "Closed", # Status of the issue Open/Closed
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
            # Skip the ticket if any of the dates is not filled
            if not issue["date_created"]:
                continue
            if issue["closed_at"]:
                # Check if the issue is in relevant time range if closed_at is filled
                closed_at = arrow.Arrow.fromtimestamp(issue["closed_at"])

                if closed_at < since or closed_at > till:
                    continue
            entry = {
                "title": issue["title"],
                "full_url": issue["full_url"],
                "status": issue["status"]
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
