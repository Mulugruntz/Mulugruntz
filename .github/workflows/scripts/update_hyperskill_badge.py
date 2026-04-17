# /// script
# requires-python = "==3.14"
# dependencies = [
#   "httpx==0.28.1",
#   "pydantic==2.12.5",
# ]
# ///

import json
import os
from pathlib import Path
from typing import Final

import httpx
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


DEFAULT_TIMEOUT: Final[float] = 30.0
DEFAULT_LABEL: Final[str] = "Hyperskill"
DEFAULT_LABEL_COLOR: Final[str] = "8C5AFF"
DEFAULT_COLOR: Final[str] = "grey"
DEFAULT_NAMED_LOGO: Final[str] = "hyperskill"
DEFAULT_LOGO_COLOR: Final[str] = "white"


class GamificationPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    active_days: int
    daily_step_completed_count: int
    passed_problems: int
    passed_projects: int
    passed_topics: int
    progress_updated_at: str


class UserPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    id: int
    fullname: str
    username: str
    gamification: GamificationPayload
    timezone: str
    is_premium: bool


class HyperskillResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    users: list[UserPayload]


class BadgePayload(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        alias_generator=to_camel,
    )

    schemaVersion: int
    label: str
    message: str
    labelColor: str
    color: str
    namedLogo: str
    logoColor: str


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def fetch_user_payload(user_id: str, timeout: float = DEFAULT_TIMEOUT) -> UserPayload:
    url = f"https://hyperskill.org/api/users/{user_id}"

    with httpx.Client(
        timeout=timeout,
        headers={"User-Agent": "mulugruntz-hyperskill-badge/1.0"},
        follow_redirects=True,
    ) as client:
        response = client.get(url)
        response.raise_for_status()
        payload = HyperskillResponse.model_validate(response.json())

    if not payload.users:
        raise RuntimeError(
            f"No users found in Hyperskill response for user_id={user_id}"
        )

    return payload.users[0]


def build_badge(user: UserPayload) -> BadgePayload:
    gamification = user.gamification

    return BadgePayload(
        schemaVersion=1,
        label=DEFAULT_LABEL,
        message=(
            f"{gamification.passed_problems}✔ "
            f"{gamification.passed_topics}📚 "
            f"{gamification.active_days}🔥"
        ),
        labelColor=DEFAULT_LABEL_COLOR,
        color=DEFAULT_COLOR,
        namedLogo=DEFAULT_NAMED_LOGO,
        logoColor=DEFAULT_LOGO_COLOR,
    )


def main() -> int:
    user_id = require_env("HYPERSKILL_USER_ID")
    output_path = Path(require_env("OUTPUT_FILE"))

    user = fetch_user_payload(user_id=user_id)
    badge = build_badge(user)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        badge.model_dump_json(ensure_ascii=False, indent=4) + "\n", encoding="utf-8"
    )

    # print(f"Updated badge: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
