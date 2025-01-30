"""
Wrapper around pagure.io. Contains all the functions related to Pagure API calls.
"""
from typing import List
import json

import arrow
import requests

def get_pagure_pull_requests_repos(days_ago: int, till: str, repos: List[str]) -> dict:
    """
    Get closed pull requests on the repositories.

    Params:
      days_ago: How many days ago to look for the pull requests
      till: Limit results to the day set by this argument. Default None will be replaced by `arrow.utcnow()`.
      repos: List of repos to retrieve pull requests for

    Returns:
      Dictionary containing pull requests with data we care about.

    Example output::
      {
        "repo": {  # repo from the list of repositories
          "pull_requests": [
            {
              "title": "Title", # Title of the pull_request
              "full_url": "https://pagure.io/project/issue", # Full url to the pull_request
              "status": Open, # Status of the pull request Open/Closed
            },
          ],
          "total": 1,  # Total number of pull requests retrieved
        }
      }
    """
    output = {}

    if till:
        till = arrow.get(till, "DD.MM.YYYY")
    else:
        till = arrow.utcnow()
    since_arg = till.shift(days=-days_ago)

    # Get open pull requests first
    for repo in repos:
        next_page = CONFIG["Pagure"]["pagure_url"] + "api/0/" + repo.removeprefix(CONFIG["Pagure"]["pagure_url"]) + "/pull-requests?status=Merged"

        data = {
            "pull_requests": [],
            "total": 0
        }

        while next_page:
            page_data = get_pull_requests_page_data(next_page, till, since_arg)
            data["pull_requests"] = data["pull_requests"] + page_data["pull_requests"]
            data["total"] = data["total"] + page_data["total"]
            next_page = page_data["next_page"]

        output[repo] = data

    return output


def get_pagure_pull_requests(days_ago: int, till: str, users: List[str]) -> dict:
    """
    Get pull requests created by the list of users from pagure.io.

    Params:
      days_ago: How many days ago to look for the pull requests
      till: Limit results to the day set by this argument. Default None will be replaced by `arrow.utcnow()`.
      users: List of users to retrieve pull requests for

    Returns:
      Dictionary containing pull requests with data we care about.

    Example output::
      {
        "user": {  # username from the list of users
          "pull_requests": [
            {
              "title": "Title", # Title of the pull_request
              "full_url": "https://pagure.io/project/issue", # Full url to the pull_request
              "status": Open, # Status of the pull request Open/Closed
            },
          ],
          "total": 1,  # Total number of pull requests retrieved
        }
      }
    """
    output = {}

    if till:
        till = arrow.get(till, "DD.MM.YYYY")
    else:
        till = arrow.utcnow()
    since_arg = till.shift(days=-days_ago)

    # Get open pull requests first
    for user in users:
        next_page = CONFIG["Pagure"]["pagure_url"] + "api/0/user/" + user + "/requests/filed?status=all"

        data = {
            "pull_requests": [],
            "total": 0
        }

        while next_page:
            page_data = get_pull_requests_page_data(next_page, till, since_arg)
            data["pull_requests"] = data["pull_requests"] + page_data["pull_requests"]
            data["total"] = data["total"] + page_data["total"]
            next_page = page_data["next_page"]

        output[user] = data

    return output


def get_pull_requests_page_data(url: str, till: arrow.Arrow, since: arrow.Arrow) -> dict:
    """
    Gets data from the current pull requests page returned by pagination.

    Params:
      url: Url for the page
      till: Till date for closed issues. This will take in account closed_at
            key of the issue.
      since: Since date for closed issues. This will take in account closed_at
            key of the issue.

    Returns:
      Dictionary containing pull requests with data we care about.

    Example output::
      {
        "pull_requests": [
          {
            "title": "Title", # Title of the pull request
            "full_url": "https://pagure.io/project/issue", # Full url to the pull request
            "status": "Closed", # Status of the pull request Open/Closed
          },
        ],
        "total": 1,  # Total number of issues retrieved
        "next_page": "https://pagure.io/next_page" # URL for next page
      }
    """
    excludes = CONFIG["Pagure"]["excludes"]
    r = requests.get(url)
    data = {
        "pull_requests": [],
        "next_page": None,
    }

    if r.status_code == requests.codes.ok:
        page = r.json()
        #click.echo(json.dumps(page, indent=2))
        for pull_request in page["requests"]:
            excluded = False
            full_url = CONFIG["Pagure"]["pagure_url"] + pull_request["project"]["url_path"] + "/pull-request/" + str(pull_request["id"])
            for exclude in excludes:
                if full_url.startswith(exclude):
                    excluded = True
                    break

            if excluded:
                continue

            if pull_request["closed_at"]:
                # Check if the issue is in relevant time range if closed_at is filled
                closed_at = arrow.Arrow.fromtimestamp(pull_request["closed_at"])

                if closed_at < since or closed_at > till:
                    continue

            entry = {
                "title": pull_request["title"],
                "full_url": full_url,
                "status": pull_request["status"]
            }

            data["pull_requests"].append(entry)
        data["next_page"] = page["pagination"]["next"]
        data["total"] = len(data["pull_requests"])

    return data


def get_pagure_tickets_repos(days_ago: int, till: str, repos: List[str]) -> dict:
    """
    Get closed tickets on repositories from pagure.io.

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
              "status": Open, # Status of the ticket Open/Closed
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

    for repo in repos:
        next_page = CONFIG["Pagure"]["pagure_url"] + "api/0/" + repo.removeprefix(CONFIG["Pagure"]["pagure_url"]) + "/issues?status=Closed&since=" + str(since_arg.int_timestamp)

        data = {
            "issues": [],
            "total": 0
        }

        while next_page:
            page_data = get_issues_page_data(next_page, till, since_arg)
            data["issues"] = data["issues"] + page_data["issues"]
            data["total"] = data["total"] + page_data["total"]
            next_page = page_data["next_page"]

        output[repo] = data

    return output


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
              "title": "Title", # Title of the issue
              "full_url": "https://pagure.io/project/issue", # Full url to the issue
              "status": Open, # Status of the ticket Open/Closed
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
        next_page = CONFIG["Pagure"]["pagure_url"] + "api/0/user/" + user + "/issues?status=all&author=False"

        data = {
            "issues": [],
            "total": 0
        }

        while next_page:
            page_data = get_issues_page_data(next_page, till, since_arg)
            data["issues"] = data["issues"] + page_data["issues"]
            data["total"] = data["total"] + page_data["total"]
            next_page = page_data["next_page"]

        output[user] = data

    return output


def get_issues_page_data(url: str, till: arrow.Arrow, since: arrow.Arrow) -> dict:
    """
    Gets data from the current issues page returned by pagination.
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
        if "issues_assigned" in page:
            issues = page["issues_assigned"]
        else:
            issues = page["issues"]
        for issue in issues:
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
            if issue["status"] == "Closed":
                if issue["closed_at"]:
                    # Check if the issue is in relevant time range if closed_at is filled
                    closed_at = arrow.Arrow.fromtimestamp(issue["closed_at"])

                    if closed_at < since or closed_at > till:
                        continue
                else:
                    continue

            # Find the date the user was assigned to issue
            assigned_at = None
            for comment in reversed(issue["comments"]):
                if comment["notification"]:
                    if "assigned" in comment["comment"]:
                        assigned_at = comment["date_created"]
                        break

            # Set assigned_at to creation date of the ticket if not set
            # We will show it up only for tickets assigned to user anyway
            # so if missing it means that the user was assigned when ticket
            # was created
            if not assigned_at:
                assigned_at = issue["date_created"]

            entry = {
                "title": issue["title"],
                "full_url": issue["full_url"],
                "status": issue["status"],
                "assigned": assigned_at,
            }

            data["issues"].append(entry)
        if "pagination_issues_assigned" in page:
            data["next_page"] = page["pagination_issues_assigned"]["next"]
        else:
            data["next_page"] = page["pagination"]["next"]
    data["total"] = len(data["issues"])

    return data
