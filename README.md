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
5. Usage
6. Interactive mode
7. Command-line options
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
