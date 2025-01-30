"""
This script will obtain all issues assigned to list of users.
"""
import tomllib

import arrow
import click

from assignee_finder import github, pagure

# Global variable containing config
CONFIG = {}

@click.group()
def cli():
    pass


@click.command()
@click.option("--days-ago", default=7, help="How many days ago to look for closed issues/pull-requests in the repo.")
@click.option("--till", default=None, help="Show results till this date. Expects date in DD.MM.YYYY format (31.12.2021).")
@click.option("--config", default="config.toml", help="Path to configuration file to use")
def get_repos(days_ago: int, till: str, config: str):
    """
    Get closed pull requests/issues on the specified repositories.

    Params:
      days_ago: How many days ago to look for closed issues/pull-requests in the repo
      till: Limit results to the day set by this argument. Default None will be replaced by `arrow.utcnow()`
      config: Path to configuration file
    """
    global CONFIG

    with open(config, "rb") as config_file:
        CONFIG = tomllib.load(config_file)

    pagure.CONFIG = CONFIG
    github.CONFIG = CONFIG

    pagure_enabled = CONFIG["Pagure"]["enable"]
    github_enabled = CONFIG["GitHub"]["enable"]

    if pagure_enabled:
        pagure_repos = CONFIG["Pagure"]["repositories"]
        pagure_issues = pagure.get_pagure_tickets_repos(days_ago, till, pagure_repos)
        pagure_prs = pagure.get_pagure_pull_requests_repos(days_ago, till, pagure_repos)

    if github_enabled:
        github_repos = CONFIG["GitHub"]["repositories"]
        github_issues = github.get_github_tickets_repos(days_ago, till, github_repos)
        github_prs = github.get_github_pull_requests_repos(days_ago, till, github_repos)

    if pagure_enabled:
        for repo in pagure_repos:
            click.echo("# Issues/pull requests on '{}'\n".format(repo))
            click.echo("## Issues ({})\n".format(pagure_issues[repo]["total"]))
            for issue in pagure_issues[repo]["issues"]:
                click.echo("* [{}]({})".format(issue["title"], issue["full_url"]))
            click.echo("")
            click.echo("## Pull requests ({})\n".format(pagure_prs[repo]["total"]))
            for pr in pagure_prs[repo]["pull_requests"]:
                click.echo("* [{}]({})".format(pr["title"], pr["full_url"]))
            click.echo("")

        click.echo("")

    if github_enabled:
        for repo in github_repos:
            click.echo("# Issues/pull requests on '{}'\n".format(repo))
            click.echo("## Issues ({})\n".format(github_issues[repo]["total"]))
            for issue in github_issues[repo]["issues"]:
                click.echo("* [{}]({})".format(issue["title"], issue["full_url"]))
            click.echo("")
            click.echo("## Pull requests ({})\n".format(github_prs[repo]["total"]))
            for pr in github_prs[repo]["pull_requests"]:
                click.echo("* [{}]({})".format(pr["title"], pr["full_url"]))
            click.echo("")

        click.echo("")


@click.command()
@click.option("--days-ago", default=7, help="How many days ago to look for issues.")
@click.option("--till", default=None, help="Show results till this date. Expects date in DD.MM.YYYY format (31.12.2021).")
@click.option("--config", default="config.toml", help="Path to configuration file to use")
def get_pull_requests(days_ago: int, till: str, config: str):
    """
    Get open and closed pull requests created by list of users.

    Params:
      days_ago: How many days ago to look for the issues
      till: Limit results to the day set by this argument. Default None will be replaced by `arrow.utcnow()`.
      config: Path to configuration file
    """
    global CONFIG

    with open(config, "rb") as config_file:
        CONFIG = tomllib.load(config_file)

    pagure.CONFIG = CONFIG
    github.CONFIG = CONFIG

    pagure_enabled = CONFIG["Pagure"]["enable"]
    if pagure_enabled:
        pagure_users = CONFIG["Pagure"]["usernames"].values()
        pagure_users_prs = pagure.get_pagure_pull_requests(days_ago, till, pagure_users)

    github_enabled = CONFIG["GitHub"]["enable"]
    if github_enabled:
        github_users = CONFIG["GitHub"]["usernames"].values()
        github_users_prs = github.get_github_pull_request(days_ago, till, github_users)

    for user in CONFIG["General"]["usernames"]:
        click.echo("# Pull requests authored by '{}'\n".format(user))
        if pagure_enabled:
            pagure_user = CONFIG["Pagure"]["usernames"][user]
            click.echo("## Pagure ({})\n".format(pagure_users_prs[pagure_user]["total"]))
            for issue in pagure_users_prs[pagure_user]["pull_requests"]:
                if issue["status"] == "Open":
                    click.echo("* [{}]({}) - {}".format(issue["title"], issue["full_url"], issue["status"]))
            for issue in pagure_users_prs[pagure_user]["pull_requests"]:
                if issue["status"] != "Open":
                    click.echo("* [{}]({}) - {}".format(issue["title"], issue["full_url"], issue["status"]))

            click.echo("")

        if github_enabled:
            github_user = CONFIG["GitHub"]["usernames"][user]
            click.echo("## GitHub ({})\n".format(github_users_prs[github_user]["total"]))
            for issue in github_users_prs[github_user]["pull_requests"]:
                click.echo("* [{}]({}) - {}".format(issue["title"], issue["full_url"], issue["status"]))
            click.echo("")

        click.echo("")


@click.command()
@click.option("--days-ago", default=7, help="How many days ago to look for pull requests.")
@click.option("--till", default=None, help="Show results till this date. Expects date in DD.MM.YYYY format (31.12.2021).")
@click.option("--config", default="config.toml", help="Path to configuration file to use")
def get_tickets(days_ago: int, till: str, config: str):
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

    pagure.CONFIG = CONFIG
    github.CONFIG = CONFIG

    pagure_enabled = CONFIG["Pagure"]["enable"]
    if pagure_enabled:
        pagure_users = CONFIG["Pagure"]["usernames"].values()
        pagure_users_tickets = pagure.get_pagure_tickets(days_ago, till, pagure_users)

    github_enabled = CONFIG["GitHub"]["enable"]
    if github_enabled:
        github_users = CONFIG["GitHub"]["usernames"].values()
        github_users_tickets = github.get_github_tickets(days_ago, till, github_users)

    for user in CONFIG["General"]["usernames"]:
        click.echo("# Issues assigned to '{}'\n".format(user))
        if pagure_enabled:
            pagure_user = CONFIG["Pagure"]["usernames"][user]
            click.echo("## Pagure ({})\n".format(pagure_users_tickets[pagure_user]["total"]))
            for issue in pagure_users_tickets[pagure_user]["issues"]:
                if issue["status"] == "Open":
                    click.echo("* [{}]({}) - {} - Assigned on: {}".format(issue["title"], issue["full_url"], issue["status"], arrow.Arrow.fromtimestamp(issue["assigned"]) if issue["assigned"] else "No date"))
            for issue in pagure_users_tickets[pagure_user]["issues"]:
                if issue["status"] != "Open":
                    click.echo("* [{}]({}) - {} - Assigned on: {}".format(issue["title"], issue["full_url"], issue["status"], arrow.Arrow.fromtimestamp(issue["assigned"]) if issue["assigned"] else "No date"))
            click.echo("")

        if github_enabled:
            github_user = CONFIG["GitHub"]["usernames"][user]
            click.echo("## GitHub ({})\n".format(github_users_tickets[github_user]["total"]))
            for issue in github_users_tickets[github_user]["issues"]:
                click.echo("* [{}]({}) - {} - Assigned on: {}".format(issue["title"], issue["full_url"], issue["status"], issue["assigned"]))

        click.echo("")


def main():
    cli.add_command(get_repos)
    cli.add_command(get_tickets)
    cli.add_command(get_pull_requests)
    cli()

if __name__ == "__main__":
    main()
