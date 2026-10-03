from typing import Dict, List, Optional

from .client import RoxClient
from .utils import chunked


class Resolver:
    def __init__(self, client: RoxClient):
        self.client = client
        self._cache: Dict[int, dict] = {}

    def username_to_id(self, username: str) -> Optional[int]:
        if username.isdigit():
            return int(username)

        data = self.client.get_json(
            f"{self.client.BASE_USERS}/v1/users/search",
            params={"keyword": username, "limit": 10},
        )
        if data:
            for entry in data.get("data", []):
                if entry.get("name", "").lower() == username.lower():
                    return entry.get("id")

        raw = self.client.get_raw(
            f"{self.client.BASE_WEB}/users/profile",
            params={"username": username},
        )
        if raw is not None and hasattr(raw, "url"):
            parts = raw.url.split("/")
            for i, part in enumerate(parts):
                if part == "users" and i + 1 < len(parts):
                    if parts[i + 1].isdigit():
                        return int(parts[i + 1])
        return None

    def resolve_users(self, ids: List[int]) -> Dict[int, dict]:
        result: Dict[int, dict] = {}
        for uid in ids:
            if uid in self._cache:
                result[uid] = self._cache[uid]

        pending = [i for i in ids if i not in self._cache]
        for batch in chunked(pending, 100):
            payload = {"userIds": batch, "excludeBannedUsers": False}
            data = self.client.post_json(f"{self.client.BASE_USERS}/v1/users", payload)
            if not data:
                for uid in batch:
                    fallback = {"id": uid, "name": str(uid),
                                "display_name": str(uid), "created": None}
                    self._cache[uid] = fallback
                    result[uid] = fallback
                continue
            for u in data.get("data", []):
                uid = u.get("id")
                if not uid:
                    continue
                info = {
                    "id": uid,
                    "name": u.get("name"),
                    "display_name": u.get("displayName"),
                    "created": u.get("created"),
                    "is_banned": u.get("isBanned", False),
                    "has_verified_badge": u.get("hasVerifiedBadge", False),
                    "description": u.get("description", ""),
                    "url": f"https://www.roblox.com/users/{uid}/profile",
                }
                self._cache[uid] = info
                result[uid] = info

            missing = [b for b in batch if b not in self._cache]
            for uid in missing:
                fallback = {"id": uid, "name": str(uid),
                            "display_name": str(uid), "created": None,
                            "is_banned": False, "has_verified_badge": False,
                            "description": "", 
                            "url": f"https://www.roblox.com/users/{uid}/profile"}
                self._cache[uid] = fallback
                result[uid] = fallback
        return result