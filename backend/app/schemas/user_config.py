from pydantic import BaseModel, field_validator
import re


_HEX_RE = re.compile(r'^#[0-9A-Fa-f]{6}$')


class ThemeColorsSchema(BaseModel):
    primary:      str = "#6366f1"
    secondary:    str = "#10b981"
    accent:       str = "#f59e0b"
    danger:       str = "#ef4444"
    background:   str = "#f4f5f8"
    surface:      str = "#ffffff"
    text_primary: str = "#1f2937"
    text_muted:   str = "#9ca3af"
    border:       str = "#e5e7eb"

    @field_validator(
        "primary", "secondary", "accent", "danger",
        "background", "surface", "text_primary", "text_muted", "border",
        mode="before",
    )
    @classmethod
    def must_be_valid_hex(cls, v: str) -> str:
        if not _HEX_RE.match(v):
            raise ValueError(f"'{v}' is not a valid hex color (#rrggbb)")
        return v


class AppearanceConfigSchema(BaseModel):
    language:     str               = "es"
    density:      str               = "normal"
    global_theme: ThemeColorsSchema = ThemeColorsSchema()
    view_themes:  dict              = {}

    @field_validator("language", mode="before")
    @classmethod
    def valid_language(cls, v: str) -> str:
        if v not in ("es", "en", "pt"):
            raise ValueError("language must be 'es', 'en', or 'pt'")
        return v

    @field_validator("density", mode="before")
    @classmethod
    def valid_density(cls, v: str) -> str:
        if v not in ("compact", "normal", "comfortable"):
            raise ValueError("density must be 'compact', 'normal', or 'comfortable'")
        return v


class UserConfigResponse(BaseModel):
    user_id: str
    config:  AppearanceConfigSchema
