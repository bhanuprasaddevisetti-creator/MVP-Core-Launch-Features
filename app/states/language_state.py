import reflex as rx


class LanguageState(rx.State):
    """Bilingual toggle shared by every page of the marketplace."""

    language: str = "en"

    @rx.var
    def is_telugu(self) -> bool:
        return self.language == "te"

    @rx.var
    def switch_label(self) -> str:
        return (
            "English"
            if self.language == "te"
            else "\u0c24\u0c46\u0c32\u0c41\u0c17\u0c41"
        )

    @rx.event
    def toggle_language(self):
        self.language = "te" if self.language == "en" else "en"

    @rx.event
    def set_language(self, value: str):
        self.language = value if value in {"en", "te"} else "en"
