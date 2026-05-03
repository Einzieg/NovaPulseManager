from __future__ import annotations

import inspect
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel


OUTPUT_PATH = Path(__file__).resolve().parents[1] / "frontend" / "src" / "types" / "api.generated.ts"
SCHEMAS_MODULE = "backend.core.api.schemas"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _try_run_pydantic2ts_cli(output_path: Path) -> bool:
    exe = shutil.which("pydantic2ts")
    if not exe:
        return False

    cmd = [
        exe,
        "--module",
        SCHEMAS_MODULE,
        "--output",
        str(output_path),
    ]

    try:
        subprocess.run(cmd, check=True)
        return True
    except Exception:
        return False


def _ts_type(annotation: Any) -> str:
    if annotation is Any:
        return "any"

    if annotation is str:
        return "string"
    if annotation is int or annotation is float:
        return "number"
    if annotation is bool:
        return "boolean"

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin in (list,):
        inner = _ts_type(args[0]) if args else "any"
        return f"{inner}[]"

    if origin in (dict,):
        return "Record<string, any>"

    if origin is Union:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and len(non_none) != len(args):
            return f"{_ts_type(non_none[0])} | null"
        return " | ".join(_ts_type(a) for a in args) or "any"

    if origin is Literal:
        return " | ".join(
            f"{v!r}" if isinstance(v, str) else str(v)
            for v in args
        )

    if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
        return annotation.__name__

    return "any"


def _collect_models(module) -> list[type[BaseModel]]:
    models: list[type[BaseModel]] = []
    for _, obj in vars(module).items():
        if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj is not BaseModel:
            models.append(obj)
    models.sort(key=lambda m: m.__name__)
    return models


def _render_interface(model: type[BaseModel]) -> str:
    lines: list[str] = [f"export interface {model.__name__} {{"]

    for field_name, field in model.model_fields.items():
        optional_mark = "" if field.is_required() else "?"
        ts_t = _ts_type(field.annotation)
        lines.append(f"  {field_name}{optional_mark}: {ts_t};")

    lines.append("}")
    return "\n".join(lines)


def _render_type_aliases(module) -> list[str]:
    aliases: list[str] = []
    if hasattr(module, "WorkflowStatus"):
        aliases.append(f"export type WorkflowStatus = {_ts_type(getattr(module, 'WorkflowStatus'))};")
    return aliases


def _generate_fallback(output_path: Path) -> None:
    from backend.core.api import schemas

    models = _collect_models(schemas)
    aliases = _render_type_aliases(schemas)

    chunks: list[str] = [
        "/* eslint-disable */",
        "// This file is generated from backend/core/api/schemas.py",
        "// Run: python scripts/generate_frontend_types.py",
        "",
    ]

    chunks.extend(aliases)
    if aliases:
        chunks.append("")

    for model in models:
        chunks.append(_render_interface(model))
        chunks.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(chunks).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    if _try_run_pydantic2ts_cli(OUTPUT_PATH):
        print(f"Generated via pydantic2ts: {OUTPUT_PATH}")
        return

    _generate_fallback(OUTPUT_PATH)
    print(f"Generated via fallback generator: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
