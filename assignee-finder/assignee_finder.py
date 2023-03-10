"""
This script will obtain all issues assigned to list of users.
"""
from typing import List
import json

import click
import requests


PAGURE_URL="https://pagure.io/"


@click.group()
def cli():
    pass


@click.command()
def get_tickets():
    """
    Get open tickets assigned to list of users.
    """
    pagure_users = ["zlopez"]
    get_pagure_tickets(pagure_users)

def get_pagure_tickets(users: List[str]) -> dict:
    """
    Get tickets assigned to list of users from pagure.io.
    """
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

        click.echo("Issues assigned to '{}' ({}):".format(user, data["total"]))
        for issue in data["issues"]:
            click.echo("* [{}]({})".format(issue["title"], issue["full_url"]))


def get_page_data(url: str):
    """
    Gets data from the current page returned by pagination.

    Params:
      url: Url for the page

    Returns:
      Dictionary containing issues with data we care about.

    Example output::
      # if closed is set to True
      {
        "issues": [
          {
            0: { # Id of the issue
              "title": "Title", # Title of the issue
              "full_url": "https://pagure.io/project/issue", # Full url to the issue
            },
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
