from __future__ import annotations

from pydantic import BaseModel, Field


class PluginEntrypoint(BaseModel):
    module: str
    class_name: str = Field(alias="class")

    model_config = {
        "populate_by_name": True,
    }


class PluginManifest(BaseModel):
    name: str
    version: str
    category: str
    entrypoint: PluginEntrypoint
    permissions: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
