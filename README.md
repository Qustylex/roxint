# Roxint

Roblox OSINT toolkit. Resolves a Roblox username or user ID, collects the full
public social graph and profile data, correlates the results, and exports
everything in JSON, CSV and plain-text formats.

Roxint only uses public, unauthenticated Roblox endpoints. It performs read-only
requests. It does not log in, does not modify anything, and does not bypass any
access control.

---

## Table of contents

1. Features
2. Project structure
3. Requirements
4. Installation
5. Commands
6. Command-line options
7. Interactive mode
8. Output layout
9. What is extracted
10. Correlations
11. Example session
12. Troubleshooting
13. Legal and ethical notice

---

## 1. Features

- Resolve a Roblox username to a numeric user ID, or accept an ID directly.
- Collect the complete list of friends, followers and following, paginated to
  the end with no artificial cap.
- Resolve every social entry to a full user record: id, username, display name,
  account creation date, ban status, verified badge status and profile URL.
- Collect the target profile: description, About Me, avatar, avatar bust,
  presence, username history, groups with roles and ranks, badges, created
  games, favorite games, collectibles and linked social accounts.
- Correlate the data: followers who are not friends, following who are not
  friends, friends who are not followed back, owned groups, high-rank groups,
  top groups by member count, most visited created game, username change count,
  and a presence snapshot.
- Export results in three formats:
  - JSON: full nested data, suitable for further processing.
  - CSV: one file per collection, suitable for spreadsheets and analysis.
  - Plain text: human-readable report and a full connection list.
- Automatic retry with exponential backoff on transient errors.
- Automatic handling of rate limiting using the `Retry-After` header.
- Randomized User-Agent per request.
- Request throttling to keep the client polite.
- Verbose logging mode for debugging.

---

## 2. Project structure

```
roxint/
├── cli.py
├── requirements.txt
├── README.md
└── roxint/
    ├── __init__.py
    ├── client.py
    ├── collectors.py
    ├── correlator.py
    ├── exporter.py
    ├── resolver.py
    └── utils.py
```

Module responsibilities:

- `cli.py`: argument parsing, interactive prompt, orchestration, console output.
- `roxint/client.py`: HTTP session, retries, throttling, headers, JSON helpers.
- `roxint/resolver.py`: username to ID resolution, batch user record resolution.
- `roxint/collectors.py`: all data collection methods and the `collect_full` pipeline.
- `roxint/correlator.py`: cross-referencing and derived metrics.
- `roxint/exporter.py`: JSON, CSV and text writers.
- `roxint/utils.py`: logging, User-Agent pool, throttling helpers, chunking.

---

## 3. Requirements

- Python 3.8 or newer.
- Internet access to reach Roblox public endpoints.
- The following Python packages:
  - `requests`
  - `beautifulsoup4`

No API key, no cookie, no authentication token is required.

---

## 4. Installation

Step 1. Copy the project into a folder, for example:

```
C:\Users\<you>\Downloads\roxint
```

Step 2. Open a terminal in that folder:

```powershell
cd C:\Users\<you>\Downloads\roxint
```

Step 3. Install the dependencies:

```bash
pip install -r requirements.txt
```

If you do not have `requirements.txt`, install directly:

```bash
pip install requests beautifulsoup4
```

Step 4. Verify the layout matches section 2. In particular, ensure the folder
`roxint/` (the package) sits next to `cli.py`, and inside it every `.py` file
listed above exists.

---

## 5. Commands

All commands must be run from the project folder, the one that contains
`cli.py`.

| Goal                                                       | Command                                                              |
|------------------------------------------------------------|----------------------------------------------------------------------|
| Collect data for a username                                | `python cli.py builderman`                                           |
| Collect data for a user ID                                 | `python cli.py 1`                                                    |
| Prompt for the target                                      | `python cli.py`                                                      |
| Write output to a custom folder                            | `python cli.py builderman -o reports`                                |
| Show progress while running                                | `python cli.py builderman -v`                                        |
| Skip CSV files                                             | `python cli.py builderman --no-csv`                                  |
| Skip the plain-text report                                 | `python cli.py builderman --no-summary`                              |
| Increase HTTP timeout                                      | `python cli.py builderman --timeout 40`                              |
| Increase the retry count                                   | `python cli.py builderman --retries 10`                              |
| Everything combined                                        | `python cli.py builderman -o reports -v --timeout 40 --retries 10`   |
| Show usage                                                 | `python cli.py -h`                                                   |
| Run from another folder using an absolute path             | `python C:\Users\<you>\Downloads\roxint\cli.py builderman`           |
| Run with an absolute output path                           | `python cli.py builderman -o C:\Users\<you>\Desktop\reports`         |

Equivalent on macOS and Linux:

| Goal                                                       | Command                                                              |
|------------------------------------------------------------|----------------------------------------------------------------------|
| Collect data for a username                                | `python3 cli.py builderman`                                          |
| Collect data for a user ID                                 | `python3 cli.py 1`                                                   |
| Prompt for the target                                      | `python3 cli.py`                                                     |
| Write output to a custom folder                            | `python3 cli.py builderman -o reports`                               |
| Show progress while running                                | `python3 cli.py builderman -v`                                       |
| Everything combined                                        | `python3 cli.py builderman -o reports -v --timeout 40 --retries 10`  |
| Show usage                                                 | `python3 cli.py -h`                                                  |

### 5.1 Walkthrough of the most common command

```bash
python cli.py builderman
```

Step by step:

1. Roxint resolves `builderman` to its numeric user ID.
2. It collects friends, followers and following, paginated to the end.
3. It resolves each entry to a full user record.
4. It collects the profile, groups, badges, games, social links and collectibles.
5. It computes the correlations.
6. It writes everything under `output/<user_id>/`.

### 5.2 Walkthrough of the interactive command

```bash
python cli.py
```

Output:

```
Target:
```

Type the username or the user ID and press Enter. Everything else is identical
to the non-interactive run.

### 5.3 Walkthrough of the verbose command

```bash
python cli.py builderman -v
```

Adds timestamped log lines to the console so you can follow each phase:

```
[12:00:01] Resolving target: builderman
[12:00:01] User ID: 1
[12:00:02] Collecting friends...
[12:00:04]   -> 512 friends
[12:00:06] Collecting followers...
[12:00:09]   -> 1084312 followers
[12:00:15] Collecting following...
[12:00:17]   -> 3 following
[12:00:18] Collecting profile data...
[12:00:22] Analyzing correlations...
[12:00:22] JSON        -> output/1/profile.json
```

### 5.4 What to do after a run

| Step | Action                                                                   |
|------|--------------------------------------------------------------------------|
| 1    | Open the folder `output/<user_id>/`.                                     |
| 2    | Open `report.txt` for the human-readable summary.                        |
| 3    | Open `connections.txt` to see every friend, follower and following.      |
| 4    | Open `profile.json` for the full nested record.                          |
| 5    | Open the CSV files with Excel, LibreOffice, Sheets or pandas.            |
| 6    | Read the "Correlations" section in `report.txt` for derived metrics.     |

---

## 6. Command-line options

| Option             | Default   | Description                                              |
|--------------------|-----------|----------------------------------------------------------|
| `identifier`       | none      | Roblox username or numeric user ID.                      |
| `-o`, `--output`   | `output`  | Base directory for all exported files.                   |
| `--no-csv`         | off       | Skip CSV exports.                                        |
| `--no-summary`     | off       | Skip the plain-text report.                              |
| `--timeout`        | `25`      | HTTP timeout in seconds for each request.                |
| `--retries`        | `6`       | Maximum number of retries per request.                   |
| `-v`, `--verbose`  | off       | Enable verbose logging.                                  |
| `-h`, `--help`     | off       | Print usage information and exit.                        |

---

## 7. Interactive mode

When you run Roxint without a positional argument, it prompts for one. An empty
value aborts the run.

```bash
python cli.py
```

```
Target:
```

This is identical to `python cli.py <username_or_id>`, only the identifier is
read from standard input instead of the command line.

---

## 8. Output layout

All files are written under `<output>/<user_id>/`.

```
output/
└── <user_id>/
    ├── profile.json
    ├── report.txt
    ├── connections.txt
    ├── groups.csv
    ├── friends.csv
    ├── followers.csv
    ├── followings.csv
    ├── username_history.csv
    ├── badges.csv
    ├── created_games.csv
    ├── favorite_games.csv
    ├── social_links.csv
    └── collectibles.csv
```

File descriptions:

- `profile.json`: the full record, including all collections and correlations.
- `report.txt`: human-readable summary of the target.
- `connections.txt`: friends, followers and following, listed one by one with
  id, username, display name and profile URL.
- `groups.csv`: every group with role, rank, owner, member count and link.
- `friends.csv`, `followers.csv`, `followings.csv`: one row per user with id,
  username, display name, creation date, ban flag, verified flag and URL.
- `username_history.csv`: previous usernames ordered by change date.
- `badges.csv`: every badge with id, name and award date.
- `created_games.csv`: every created game with id, name, visits, dates and URL.
- `favorite_games.csv`: favorite games with id, name and URL.
- `social_links.csv`: linked external platforms and URLs.
- `collectibles.csv`: limited items with asset id, name, type and acquisition date.

---

## 9. What is extracted

Target profile:

- User id.
- Username.
- Display name.
- Description.
- About Me.
- Account creation date.
- Ban status.
- Verified badge status.
- External app display name.
- Avatar image URL.
- Avatar bust image URL.
- Presence: presence type, last online, last location, place id, universe id.

Social graph:

- Every friend: id, username, display name, creation date, ban flag, verified
  flag, profile URL.
- Every follower: same fields.
- Every following: same fields.

History and activity:

- Full username history, each entry with the username and the date it changed.
- Every group membership with group id, name, description, owner, member count,
  assigned role, rank, and group URL.
- Every badge with id, name and award date.
- Every created game with id, name, description, creation date, last update
  date, visit count and game URL.
- Every favorite game with id, name and URL.
- Every collectible item with asset id, name, asset type and acquisition date.
- Every linked external account: Twitter/X, YouTube, Twitch, Guilded, Facebook
  and Discord when available.

---

## 10. Correlations

After collection, Roxint computes derived metrics and lists:

- `friend_count`, `follower_count`, `following_count`.
- `mutual_friends_with_followers`.
- `friends_not_followed_back` and the full list of names and ids.
- `following_not_friends` and the full list of names and ids.
- `followers_not_friends` and the full list of names and ids.
- `following_only` and `followers_only` counts.
- `group_count` and `group_names`.
- `top_groups_by_members`: the ten largest groups the target belongs to.
- `owned_groups`: groups where the target's rank equals 255.
- `high_rank_groups`: groups where the target's rank is 100 or higher, with
  the role name.
- `social_platforms`: which external platforms are linked.
- `created_games_count`.
- `total_game_visits`: sum of visits across created games.
- `most_visited_game`: name, visit count and URL.
- `username_changes`: number of username changes (history length minus one).
- `presence_type`, `last_online`, `last_location`: snapshot of presence.

These values are written to `profile.json` and to `report.txt`.

---

## 11. Example session

Command:

```bash
python cli.py builderman -v
```

Console output (abridged):

```
[12:00:01] Resolving target: builderman
[12:00:01] User ID: 1
[12:00:02] Collecting friends...
[12:00:04]   -> 512 friends
[12:00:06] Collecting followers...
[12:00:09]   -> 1084312 followers
[12:00:15] Collecting following...
[12:00:17]   -> 3 following
[12:00:18] Collecting profile data...
[12:00:22] Analyzing correlations...
[12:00:22] JSON        -> output/1/profile.json
[12:00:22] Connections -> output/1/connections.txt
[12:00:22] CSV         -> output/1/groups.csv (groups)
[12:00:22] CSV         -> output/1/friends.csv (friends)
[12:00:22] CSV         -> output/1/followers.csv (followers)
[12:00:22] CSV         -> output/1/followings.csv (followings)
[12:00:22] CSV         -> output/1/username_history.csv (username_history)
[12:00:22] CSV         -> output/1/badges.csv (badges)
[12:00:22] CSV         -> output/1/created_games.csv (created_games)
[12:00:22] CSV         -> output/1/favorite_games.csv (favorite_games)
[12:00:22] CSV         -> output/1/social_links.csv (social_links)
[12:00:22] CSV         -> output/1/collectibles.csv (collectibles)
[12:00:22] Report      -> output/1/report.txt

Target        : builderman (1)
Display Name  : builderman
Created       : 2006-02-27T21:06:40.3Z
Friends       : 512
Followers     : 1084312
Following     : 3
Groups        : 21
Badges        : 47
Created Games : 12
Social Links  : 2
Output        : output/1/
```

What you do next: open `output/1/connections.txt` and `output/1/report.txt`.

---

## 12. Troubleshooting

| Error                                                        | Cause                                                  | Fix                                                                        |
|--------------------------------------------------------------|--------------------------------------------------------|----------------------------------------------------------------------------|
| `ImportError: cannot import name 'Correlator' from 'roxint'` | Missing `correlator.py` or missing import in `__init__`| Create the file, add the import, delete `roxint/__pycache__`, run again.   |
| `Target not found`                                           | Username misspelled or account deleted                 | Check the spelling or pass the numeric user ID directly.                   |
| `usage: cli.py ...` and no target                            | You ran `python cli.py` without arguments              | That is the prompt. Type the target at `Target:` or pass it directly.      |
| Empty CSV files                                              | Account is private or banned                           | Expected behavior. The public API does not expose those lists.             |
| Very slow run                                                | Account has hundreds of thousands of followers         | Expected. Use `-v` to see progress. Do not lower the internal throttle.    |
| Frequent rate limiting                                       | Too many requests too fast                             | Increase `--timeout` and `--retries`, then run again later.                |

---

## 13. Legal and ethical notice

Roxint is intended for educational and research use, and for inspecting
accounts you own or are explicitly authorized to investigate.

- Only public endpoints are used.
- No authentication, no cookies, no tokens.
- No write operations, no mutations, no bypass of privacy controls.
- The tool must be used in compliance with the Roblox Terms of Service and
  with all applicable laws, including data protection regulations.

The author assumes no responsibility for misuse. You are solely responsible
for how you use this tool and for any consequences that follow.
