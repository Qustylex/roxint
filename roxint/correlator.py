from typing import Dict


class Correlator:
    def analyze(self, data: Dict) -> Dict:
        correlations = {}

        friends = data.get("friends", [])
        followers = data.get("followers", [])
        followings = data.get("followings", [])
        groups = data.get("groups", [])

        friend_ids = {f["id"] for f in friends}
        follower_ids = {f["id"] for f in followers}
        following_ids = {f["id"] for f in followings}

        mutual_friends = friend_ids & follower_ids
        not_following_back = friend_ids - following_ids
        follows_not_friend = following_ids - friend_ids
        only_followers = follower_ids - friend_ids
        only_following = following_ids - friend_ids

        def name_map(lst):
            return {u["id"]: (u.get("name") or u.get("display_name") or str(u["id"]))
                    for u in lst}

        fmap = name_map(friends)
        flmap = name_map(followers)
        fgmap = name_map(followings)

        correlations["friend_count"] = len(friend_ids)
        correlations["follower_count"] = len(follower_ids)
        correlations["following_count"] = len(following_ids)
        correlations["mutual_friends_with_followers"] = len(mutual_friends)
        correlations["friends_not_followed_back"] = len(not_following_back)
        correlations["following_not_friends"] = len(follows_not_friend)
        correlations["followers_not_friends"] = len(only_followers)
        correlations["following_only"] = len(only_following)

        correlations["followers_not_friends_list"] = [
            {"id": i, "name": flmap.get(i, str(i))} for i in sorted(only_followers)
        ]
        correlations["following_not_friends_list"] = [
            {"id": i, "name": fgmap.get(i, str(i))} for i in sorted(only_following)
        ]
        correlations["friends_not_followed_back_list"] = [
            {"id": i, "name": fmap.get(i, str(i))} for i in sorted(not_following_back)
        ]

        group_names = [g.get("name") for g in groups if g.get("name")]
        correlations["group_count"] = len(group_names)
        correlations["group_names"] = group_names

        top_groups = sorted(
            [g for g in groups if isinstance(g.get("members"), int)],
            key=lambda g: g["members"],
            reverse=True,
        )[:10]
        correlations["top_groups_by_members"] = [
            {"name": g.get("name"), "members": g.get("members")} for g in top_groups
        ]

        owned_groups = [g for g in groups if g.get("rank") == 255]
        correlations["owned_groups"] = [g.get("name") for g in owned_groups]

        high_rank_groups = [g for g in groups if isinstance(g.get("rank"), int) and g["rank"] >= 100]
        correlations["high_rank_groups"] = [
            {"name": g.get("name"), "rank": g.get("rank"), "role": g.get("role")}
            for g in high_rank_groups
        ]

        social_links = data.get("social_links", [])
        correlations["social_platforms"] = [s.get("platform") for s in social_links]

        games = data.get("created_games", [])
        correlations["created_games_count"] = len(games)
        if games:
            total_visits = sum(g.get("visits") or 0 for g in games)
            correlations["total_game_visits"] = total_visits
            best = max(games, key=lambda g: g.get("visits") or 0)
            correlations["most_visited_game"] = {
                "name": best.get("name"),
                "visits": best.get("visits"),
                "url": best.get("url"),
            }

        username_history = data.get("username_history", [])
        correlations["username_changes"] = max(0, len(username_history) - 1)

        presence = data.get("presence", {}) or {}
        correlations["presence_type"] = presence.get("user_presence_type")
        correlations["last_online"] = presence.get("last_online")
        correlations["last_location"] = presence.get("last_location")

        return correlations