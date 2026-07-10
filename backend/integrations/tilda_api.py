from __future__ import annotations

import os
from dataclasses import dataclass

import requests
from dotenv import load_dotenv


load_dotenv()

API_BASE = "https://api.tildacdn.info/v1"


class TildaAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class TildaProject:
    id: str
    title: str
    description: str


class TildaAPIClient:
    def __init__(
        self,
        public_key: str | None = None,
        secret_key: str | None = None,
        timeout: int = 30,
    ) -> None:
        self.public_key = public_key or os.getenv("TILDA_PUBLIC_KEY", "")
        self.secret_key = secret_key or os.getenv("TILDA_SECRET_KEY", "")
        self.timeout = timeout

        if not self.public_key or not self.secret_key:
            raise TildaAPIError(
                "Не заданы TILDA_PUBLIC_KEY и TILDA_SECRET_KEY в файле .env"
            )

    def _request(self, method: str, **params: str) -> dict:
        query = {
            "publickey": self.public_key,
            "secretkey": self.secret_key,
            **params,
        }

        response = requests.get(
            f"{API_BASE}/{method}/",
            params=query,
            timeout=self.timeout,
        )
        response.raise_for_status()

        payload = response.json()

        if payload.get("status") != "FOUND":
            message = (
                payload.get("message")
                or payload.get("error")
                or "Tilda API вернул ошибку"
            )
            raise TildaAPIError(str(message))

        return payload

    def get_projects(self) -> list[TildaProject]:
        payload = self._request("getprojectslist")
        result = payload.get("result", [])

        return [
            TildaProject(
                id=str(item.get("id", "")),
                title=str(item.get("title", "")),
                description=str(item.get("descr", "")),
            )
            for item in result
        ]

    def get_pages(self, project_id: str) -> list[dict]:
        payload = self._request(
            "getpageslist",
            projectid=str(project_id),
        )
        return list(payload.get("result", []))

    def get_page(self, page_id: str) -> dict:
        payload = self._request(
            "getpage",
            pageid=str(page_id),
        )
        return dict(payload.get("result", {}))


def print_projects() -> None:
    client = TildaAPIClient()
    projects = client.get_projects()

    if not projects:
        print("Проекты не найдены.")
        return

    print("Проекты Tilda:")
    print("=" * 70)

    for project in projects:
        print(f"ID: {project.id}")
        print(f"Название: {project.title}")
        if project.description:
            print(f"Описание: {project.description}")
        print("-" * 70)


if __name__ == "__main__":
    print_projects()
