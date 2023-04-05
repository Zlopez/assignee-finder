"""
This script will obtain all issues assigned to list of users.
"""
import tomllib

import click

from assignee_finder import github, pagure

# Global variable containing config
CONFIG = {}

@click.group()
def cli():
    pass


@click.command()
@click.option("--days-ago", default=7, help="How many days ago to look for open issues.")
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
                    click.echo("* [{}]({}) - {}".format(issue["title"], issue["full_url"], issue["status"]))
            for issue in pagure_users_tickets[pagure_user]["issues"]:
                if issue["status"] != "Open":
                    click.echo("* [{}]({}) - {}".format(issue["title"], issue["full_url"], issue["status"]))
            click.echo("")

        if github_enabled:
            github_user = CONFIG["GitHub"]["usernames"][user]
            click.echo("## GitHub ({})\n".format(github_users_tickets[github_user]["total"]))
            for issue in github_users_tickets[github_user]["issues"]:
                click.echo("* [{}]({}) - {}".format(issue["title"], issue["full_url"], issue["status"]))

        click.echo("")


def main():
    cli.add_command(get_tickets)
    cli()

if __name__ == "__main__":
    main()
