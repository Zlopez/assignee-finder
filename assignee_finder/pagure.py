"""
Wrapper around pagure.io. Contains all the functions related to Pagure API calls.
"""
from typing import List
import json

import arrow
import requests


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
    excludes = CONFIG["Pagure"]["excludes"]
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

            excluded = False
            for exclude in excludes:
                if issue["full_url"].startswith(exclude):
                    excluded = True
                    break

            if excluded:
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
