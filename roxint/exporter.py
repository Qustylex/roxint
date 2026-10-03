import csv
import json
import os
from typing import Any, Dict


class Exporter:
    def __init__(self, base_dir: str = "output"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _dir(self, user_id: Any) -> str:
        d = os.path.join(self.base_dir, str(user_id))
        os.makedirs(d, exist_ok=True)
        return d

    def write_json(self, data: Dict[str, Any], user_id: Any) -> str:
        path = os.path.join(self._dir(user_id), "profile.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path

    def _csv(self, rows, header, path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)

    def write_csvs(self, data: Dict[str, Any], user_id: Any) -> Dict[str, str]:
        out_dir = self._dir(user_id)
        paths = {}

        p = os.path.join(out_dir, "groups.csv")
        self._csv(
            [[g.get("id"), g.get("name"), g.get("role"), g.get("rank"),
              g.get("members"), g.get("owner"), g.get("link")]
             for g in data.get("groups", [])],
            ["id", "name", "role", "rank", "members", "owner", "link"],
            p,
        )
        paths["groups"] = p

        for key in ("friends", "followers", "followings"):
            p = os.path.join(out_dir, f"{key}.csv")
            self._csv(
                [[e.get("id"), e.get("name"), e.get("display_name"),
                  e.get("created"), e.get("is_banned"),
                  e.get("has_verified_badge"), e.get("url")]
                 for e in data.get(key, [])],
                ["id", "name", "display_name", "created", "is_banned",
                 "has_verified_badge", "url"],
                p,
            )
            paths[key] = p

        p = os.path.join(out_dir, "username_history.csv")
        self._csv(
            [[i + 1, h.get("name"), h.get("changed")]
             for i, h in enumerate(data.get("username_history", []))],
            ["index", "username", "changed"],
            p,
        )
        paths["username_history"] = p

        p = os.path.join(out_dir, "badges.csv")
        self._csv(
            [[b.get("id"), b.get("name"), b.get("awarded")] for b in data.get("badges", [])],
            ["id", "name", "awarded"],
            p,
        )
        paths["badges"] = p

        p = os.path.join(out_dir, "created_games.csv")
        self._csv(
            [[g.get("id"), g.get("name"), g.get("visits"), g.get("created"),
              g.get("updated"), g.get("url")]
             for g in data.get("created_games", [])],
            ["id", "name", "visits", "created", "updated", "url"],
            p,
        )
        paths["created_games"] = p

        p = os.path.join(out_dir, "favorite_games.csv")
        self._csv(
            [[g.get("id"), g.get("name"), g.get("url")]
             for g in data.get("favorite_games", [])],
            ["id", "name", "url"],
            p,
        )
        paths["favorite_games"] = p

        p = os.path.join(out_dir, "social_links.csv")
        self._csv(
            [[s.get("platform"), s.get("url")] for s in data.get("social_links", [])],
            ["platform", "url"],
            p,
        )
        paths["social_links"] = p

        p = os.path.join(out_dir, "collectibles.csv")
        self._csv(
            [[c.get("asset_id"), c.get("name"), c.get("asset_type"), c.get("created")]
             for c in data.get("collectibles", [])],
            ["asset_id", "name", "asset_type", "created"],
            p,
        )
        paths["collectibles"] = p

        return paths

    def write_connections(self, data: Dict[str, Any], user_id: Any) -> str:
        path = os.path.join(self._dir(user_id), "connections.txt")
        lines = []

        lines.append(f"TARGET: {data.get('username')} ({data.get('id')})")
        lines.append("")

        lines.append(f"FRIENDS ({len(data.get('friends', []))})")
        lines.append("-" * 60)
        for i, f in enumerate(data.get("friends", []), 1):
            lines.append(
                f"{i:>4}. {f.get('name')}  |  display: {f.get('display_name')}  "
                f"|  id: {f.get('id')}  |  {f.get('url')}"
            )
        lines.append("")

        lines.append(f"FOLLOWERS ({len(data.get('followers', []))})")
        lines.append("-" * 60)
        for i, f in enumerate(data.get("followers", []), 1):
            lines.append(
                f"{i:>4}. {f.get('name')}  |  display: {f.get('display_name')}  "
                f"|  id: {f.get('id')}  |  {f.get('url')}"
            )
        lines.append("")

        lines.append(f"FOLLOWING ({len(data.get('followings', []))})")
        lines.append("-" * 60)
        for i, f in enumerate(data.get("followings", []), 1):
            lines.append(
                f"{i:>4}. {f.get('name')}  |  display: {f.get('display_name')}  "
                f"|  id: {f.get('id')}  |  {f.get('url')}"
            )
        lines.append("")

        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
        return path

    def write_report(self, data: Dict[str, Any], user_id: Any) -> str:
        path = os.path.join(self._dir(user_id), "report.txt")
        corr = data.get("correlations", {}) or {}
        presence = data.get("presence", {}) or {}
        counts = data.get("counts", {}) or {}

        lines = [
            "ROBLOX OSINT REPORT",
            "===================",
            f"User ID            : {data.get('id')}",
            f"Username           : {data.get('username')}",
            f"Display Name       : {data.get('display_name')}",
            f"Created            : {data.get('created')}",
            f"Banned             : {data.get('is_banned')}",
            f"Verified Badge     : {data.get('has_verified_badge')}",
            f"External Name      : {data.get('external_app_display_name')}",
            "",
            "COUNTS",
            "------",
            f"Friends            : {counts.get('friends')}",
            f"Followers          : {counts.get('followers')}",
            f"Following          : {counts.get('followings')}",
            f"Groups             : {len(data.get('groups', []))}",
            f"Badges             : {len(data.get('badges', []))}",
            f"Created Games      : {len(data.get('created_games', []))}",
            f"Favorite Games     : {len(data.get('favorite_games', []))}",
            f"Collectibles       : {len(data.get('collectibles', []))}",
            f"Username Changes   : {corr.get('username_changes')}",
            "",
            "PRESENCE",
            "--------",
            f"Type               : {presence.get('user_presence_type')}",
            f"Last Online        : {presence.get('last_online')}",
            f"Last Location      : {presence.get('last_location')}",
            f"Place ID           : {presence.get('place_id')}",
            f"Universe ID        : {presence.get('universe_id')}",
            "",
            "SOCIAL LINKS",
            "------------",
        ]
        for s in data.get("social_links", []):
            lines.append(f"{s.get('platform'):<18} : {s.get('url')}")
        if not data.get("social_links"):
            lines.append("(none)")

        lines += ["", "USERNAME HISTORY", "----------------"]
        for i, h in enumerate(data.get("username_history", []), 1):
            lines.append(f"{i:>3}. {h.get('name')}  ({h.get('changed')})")
        if not data.get("username_history"):
            lines.append("(none)")

        lines += ["", "GROUPS", "------"]
        for g in data.get("groups", []):
            lines.append(
                f"- {g.get('name')} | role={g.get('role')} | rank={g.get('rank')} "
                f"| members={g.get('members')} | owner={g.get('owner')}"
            )
        if not data.get("groups"):
            lines.append("(none)")

        lines += ["", "CORRELATIONS", "------------"]
        for k, v in corr.items():
            if isinstance(v, (list, dict)):
                lines.append(f"{k}:")
                lines.append(json.dumps(v, indent=2, ensure_ascii=False))
            else:
                lines.append(f"{k:<30} : {v}")

        lines += ["", "DESCRIPTION", "-----------", data.get("description") or "(empty)"]
        lines += ["", "ABOUT ME", "--------", data.get("about_me") or "(empty)"]
        lines += ["", f"Collected at: {data.get('collected_at')}"]

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return path