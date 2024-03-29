# Description

This script will help you find to what tickets the provided users are assigned.
Currently supports: https://github.com and https://pagure.io

# Installation

NOTE: For installation you need to have [poetry](https://python-poetry.org/) installed.

1. Clone this repository
`git clone https://github.com/Zlopez/assignee-finder.git`

2. Go to the directory
`cd assignee-finder`

3. Install the dependencies with poetry
`poetry install`

# Configuration

To configure the script you need to create a configuration file. You can find a [example configuration file](https://github.com/Zlopez/assignee-finder/blob/main/config.example.toml) in this repository.

1. Fill in your [GitHub API token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) or disable the
GitHub backend

2. Fill in usernames and the corresponding mapping for Pagure and GitHub

# Usage

Script is executed using poetry.

`poetry run python assignee_finder/main.py get-tickets --config <path_to_your_config_file>`

The output of the script is [Markdown](https://www.markdownguide.org/) compliant:
```
# Issues assigned to 'zlopez'

## Pagure (6)

* [Rebasing Fedora Linux 38 Silverblue](https://pagure.io/fedora-magazine-newsroom/issue/175) - Open
* [Duplicating pungi-fedora config for Bodhi in infra ansible makes it outdated and confusing](https://pagure.io/fedora-infrastructure/issue/10779) - Open
* [Not able to close PR using API](https://pagure.io/pagure-dist-git/issue/144) - Open
* [Use Anitya to help Copr with automatic builds](https://pagure.io/cpe-planning/issue/30) - Open
* [Add support for flathub flatpaks to Anitya and the-new-hotness](https://pagure.io/cpe-planning/issue/25) - Open
* [Publish to maven](https://pagure.io/pagure-java-client/issue/2) - Closed

## GitHub (2)

* [High priority test issue](https://github.com/Test-zlopez/test_repo/issues/2) - OPEN
* [File pull requests instead of attaching patches to Bugzilla](https://github.com/fedora-infra/the-new-hotness/issues/189) - CLOSED
```

To specify the closed tickets interval use `--days-ago` and `till` parameters:
`poetry run python assignee_finder/main.py get-tickets --days-ago 7 --till "2023-03-07" --config <path_to_your_config_file>`

# Commands

The script supports following commands:

* `poetry run python assignee_finder/main.py get-tickets`

  Retrieve tickets assigned to list of configured users.

* `poetry run python assignee_finder/main.py get-pull-requests`

  Retrieve pull-requests authored by list of configured users.

* `poetry run python assignee_finder/main.py get-repos`

  Retrieve closed tickets/pull requests for list of configured repositories.
