import logging
from typing import Any, TypedDict

import reflex as rx
from sqlalchemy import text


class AdvisoryArticle(TypedDict):
    id: int
    title: str
    title_te: str
    summary: str
    summary_te: str
    source: str
    url: str
    topic: str
    season: str
    reviewed: str


class AdvisoryState(rx.State):
    articles: list[AdvisoryArticle] = []
    topics: list[str] = []
    search: str = ""
    topic: str = "all"
    season: str = "all"
    loading: bool = False
    error: str = ""

    @rx.event
    def set_search(self, value: str):
        self.search = value

    @rx.event
    def set_topic(self, value: str):
        self.topic = value
        return AdvisoryState.load_articles

    @rx.event
    def set_season(self, value: str):
        self.season = value
        return AdvisoryState.load_articles

    @rx.event
    def submit_search(self, form_data: dict[str, Any]):
        self.search = str(form_data.get("search", "")).strip()
        self.topic = str(form_data.get("topic", "all") or "all")
        self.season = str(form_data.get("season", "all") or "all")
        return AdvisoryState.load_articles

    @rx.event(background=True)
    async def load_articles(self):
        async with self:
            self.loading = True
            search = self.search.strip().lower()
            topic = self.topic
            season = self.season
        try:
            sql = """
                SELECT id, title_en, COALESCE(title_te, ''),
                       COALESCE(summary_en, ''), COALESCE(summary_te, ''),
                       COALESCE(source_name, ''), COALESCE(source_url, ''),
                       COALESCE(topic, 'general'), season, reviewed_on
                FROM advisory_entry
                WHERE is_published = true
            """
            params: dict[str, str] = {}
            if search:
                sql += (
                    " AND (LOWER(title_en) LIKE :q"
                    " OR LOWER(COALESCE(crop_name_en, '')) LIKE :q"
                    " OR LOWER(COALESCE(crop_slug, '')) LIKE :q"
                    " OR LOWER(COALESCE(topic, '')) LIKE :q)"
                )
                params["q"] = f"%{search}%"
            if topic != "all":
                sql += " AND LOWER(COALESCE(topic, '')) = :topic"
                params["topic"] = topic.lower()
            if season != "all":
                sql += " AND season = :season"
                params["season"] = season.upper()
            sql += " ORDER BY reviewed_on DESC NULLS LAST LIMIT 60"

            async with rx.asession() as asession:
                rows = (await asession.execute(text(sql), params)).all()
                topic_rows = (
                    await asession.execute(
                        text(
                            "SELECT DISTINCT LOWER(COALESCE(topic, 'general')) "
                            "FROM advisory_entry WHERE is_published = true "
                            "ORDER BY 1 LIMIT 20"
                        )
                    )
                ).all()
            async with self:
                self.articles = [
                    {
                        "id": int(r[0]),
                        "title": str(r[1]),
                        "title_te": str(r[2]),
                        "summary": str(r[3]),
                        "summary_te": str(r[4]),
                        "source": str(r[5]),
                        "url": str(r[6]),
                        "topic": str(r[7]),
                        "season": str(r[8]).lower().replace("_", " "),
                        "reviewed": str(r[9] or "pending"),
                    }
                    for r in rows
                ]
                self.topics = [str(t[0]) for t in topic_rows]
                self.error = ""
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = "Advisories are temporarily unavailable."
        finally:
            async with self:
                self.loading = False
