from datetime import datetime, timezone
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from .client import RoxClient
from .resolver import Resolver
from .utils import jitter


class ProfileCollector:
    def __init__(self, client: RoxClient):
        self.client = client
        self.resolver = Resolver(client)

    def _user_basic(self, user_id: int) -> Optional[dict]:
        return self.client.get_json(f"{self.client.BASE_USERS}/v1/users/{user_id}")

    def _count(self, user_id: int, kind: str) -> int:
        data = self.client.get_json(
            f"{self.client.BASE_FRIENDS}/v1/users/{user_id}/{kind}/count"
        )
        return int(data.get("count", 0)) if data else 0

    def _username_history(self, user_id: int) -> List[dict]:
        data = self.client.get_json(
            f"{self.client.BASE_USERS}/v1/users/{user_id}/username-history",
            params={"limit": 100, "sortOrder": "Asc"},
        )
        if not data:
            return []
        return [
            {"name": e.get("name"), "changed": e.get("created")}
            for e in data.get("data", []) if e.get("name")
        ]

    def _groups(self, user_id: int) -> List[dict]:
        data = self.client.get_json(
            f"{self.client.BASE_GROUPS}/v2/users/{user_id}/groups/roles"
        )
        if not data:
            return []
        out = []
        for entry in data.get("data", []):
            g = entry.get("group", {})
            role = entry.get("role", {})
            out.append({
                "id": g.get("id"),
                "name": g.get("name"),
                "description": g.get("description"),
                "owner": (g.get("owner") or {}).get("username"),
                "members": g.get("memberCount"),
                "role": role.get("name"),
                "rank": role.get("rank"),
                "link": f"https://www.roblox.com/groups/{g.get('id')}",
            })
        return out

    def _collect_ids(self, user_id: int, kind: str) -> List[int]:
        ordered: List[int] = []
        seen = set()
        cursor = ""
        pages = 0
        while True:
            data = self.client.get_json(
                f"{self.client.BASE_FRIENDS}/v1/users/{user_id}/{kind}",
                params={"limit": 100, "cursor": cursor},
            )
            if not data:
                break
            for entity in data.get("data", []):
                nested = entity.get("user") if isinstance(entity.get("user"), dict) else None
                eid = nested.get("id") if nested else entity.get("id")
                if eid and eid not in seen:
                    seen.add(eid)
                    ordered.append(int(eid))
            cursor = data.get("nextPageCursor") or ""
            pages += 1
            if not cursor:
                break
            jitter(0.35)
        return ordered

    def _social_list(self, user_id: int, kind: str) -> List[dict]:
        ids = self._collect_ids(user_id, kind)
        if not ids:
            return []
        resolved = self.resolver.resolve_users(ids)
        return [resolved[i] for i in ids if i in resolved]

    def _about_me(self, user_id: int) -> str:
        r = self.client.get_raw(f"{self.client.BASE_WEB}/users/{user_id}/profile")
        if r is None or not hasattr(r, "text"):
            return ""
        soup = BeautifulSoup(r.text, "html.parser")
        node = soup.find("span", class_="profile-about-content-text linkify")
        if node:
            return node.get_text(strip=True)
        container = soup.find("div", class_="profile-about-content")
        if container:
            span = container.find("span")
            if span:
                return span.get_text(strip=True)
        return ""

    def _avatar(self, user_id: int) -> dict:
        data = self.client.get_json(
            f"{self.client.BASE_THUMBS}/v1/users/avatar",
            params={"userIds": user_id, "size": "420x420", "format": "Png", "isCircular": "false"},
        )
        if data and data.get("data"):
            entry = data["data"][0]
            return {"image_url": entry.get("imageUrl"), "state": entry.get("state")}
        return {}

    def _avatar_bust(self, user_id: int) -> dict:
        data = self.client.get_json(
            f"{self.client.BASE_THUMBS}/v1/users/avatar-bust",
            params={"userIds": user_id, "size": "420x420", "format": "Png", "isCircular": "false"},
        )
        if data and data.get("data"):
            entry = data["data"][0]
            return {"image_url": entry.get("imageUrl"), "state": entry.get("state")}
        return {}

    def _presence(self, user_id: int) -> dict:
        data = self.client.post_json(
            f"{self.client.BASE_PRESENCE}/v1/presence/users",
            {"userIds": [user_id]},
        )
        if data and data.get("userPresences"):
            p = data["userPresences"][0]
            return {
                "user_presence_type": p.get("userPresenceType"),
                "last_online": p.get("lastOnline"),
                "last_location": p.get("lastLocation"),
                "place_id": p.get("placeId"),
                "root_place_id": p.get("rootPlaceId"),
                "universe_id": p.get("universeId"),
            }
        return {}

    def _badges(self, user_id: int) -> List[dict]:
        data = self.client.get_json(
            f"{self.client.BASE_USERS}/v1/users/{user_id}/badges",
            params={"limit": 100, "sortOrder": "Desc"},
        )
        if not data:
            return []
        return [{"id": b.get("id"), "name": b.get("name"), "awarded": b.get("awardedDate")}
                for b in data.get("data", [])]

    def _social_links(self, user_id: int) -> List[dict]:
        data = self.client.get_json(
            f"{self.client.BASE_ACCOUNT}/v1/users/{user_id}/promotion-channels"
        )
        if not data:
            return []
        mapping = {
            "twitter": "Twitter/X",
            "youtube": "YouTube",
            "twitch": "Twitch",
            "guilded": "Guilded",
            "facebook": "Facebook",
        }
        links = []
        for key, label in mapping.items():
            val = data.get(key)
            if val:
                links.append({"platform": label, "url": val})
        if data.get("discord"):
            links.append({"platform": "Discord", "url": data["discord"]})
        return links

    def _created_games(self, user_id: int) -> List[dict]:
        data = self.client.get_json(
            f"{self.client.BASE_GAMES}/v2/users/{user_id}/games",
            params={"limit": 50, "sortOrder": "Desc"},
        )
        if not data:
            return []
        out = []
        for g in data.get("data", []):
            root = g.get("rootPlace") or {}
            out.append({
                "id": g.get("id"),
                "name": g.get("name"),
                "description": g.get("description"),
                "created": g.get("created"),
                "updated": g.get("updated"),
                "visits": g.get("placeVisits"),
                "url": f"https://www.roblox.com/games/{root.get('id')}" if root.get("id") else None,
            })
        return out

    def _favorite_games(self, user_id: int) -> List[dict]:
        data = self.client.get_json(
            f"{self.client.BASE_GAMES}/v2/users/{user_id}/favorite/games",
            params={"limit": 50},
        )
        if not data:
            return []
        out = []
        for g in data.get("data", []):
            root = g.get("rootPlace") or {}
            out.append({
                "id": g.get("id"),
                "name": g.get("name"),
                "url": f"https://www.roblox.com/games/{root.get('id')}" if root.get("id") else None,
            })
        return out

    def _collectibles(self, user_id: int) -> List[dict]:
        data = self.client.get_json(
            f"{self.client.BASE_INVENTORY}/v2/users/{user_id}/inventory",
            params={"assetTypes": "8,41,42,43,44,45,46,47", "limit": 100, "sortOrder": "Desc"},
        )
        if not data:
            return []
        return [
            {"asset_id": item.get("assetId"), "name": item.get("name"),
             "asset_type": item.get("assetType"), "created": item.get("created")}
            for item in data.get("data", [])
        ]

    def collect_full(self, user_id: int) -> Optional[dict]:
        basic = self._user_basic(user_id)
        if not basic:
            return None

        profile = {
            "id": basic.get("id"),
            "username": basic.get("name"),
            "display_name": basic.get("displayName"),
            "description": basic.get("description", ""),
            "created": basic.get("created"),
            "is_banned": basic.get("isBanned", False),
            "has_verified_badge": basic.get("hasVerifiedBadge", False),
            "external_app_display_name": basic.get("externalAppDisplayName"),
            "about_me": self._about_me(user_id),
            "avatar": self._avatar(user_id),
            "avatar_bust": self._avatar_bust(user_id),
            "presence": self._presence(user_id),
            "username_history": self._username_history(user_id),
            "social_links": self._social_links(user_id),
            "counts": {
                "friends": self._count(user_id, "friends"),
                "followers": self._count(user_id, "followers"),
                "followings": self._count(user_id, "followings"),
            },
        }

        profile["friends"] = self._social_list(user_id, "friends")
        profile["followers"] = self._social_list(user_id, "followers")
        profile["followings"] = self._social_list(user_id, "followings")
        profile["groups"] = self._groups(user_id)
        profile["badges"] = self._badges(user_id)
        profile["created_games"] = self._created_games(user_id)
        profile["favorite_games"] = self._favorite_games(user_id)
        profile["collectibles"] = self._collectibles(user_id)
        profile["collected_at"] = datetime.now(timezone.utc).isoformat()
        return profile