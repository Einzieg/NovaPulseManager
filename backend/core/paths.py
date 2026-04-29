import sys
from pathlib import Path
from typing import Optional, Union

_STATIC_DIR: Optional[Path] = None
_SHARED_TEMPLATES_DIR: Optional[Path] = None


def get_static_dir() -> Path:
    """返回静态资源目录（兼容源码运行与 PyInstaller）。"""

    global _STATIC_DIR
    if _STATIC_DIR is not None:
        return _STATIC_DIR

    meipass = getattr(sys, "_MEIPASS", None)
    candidates: list[Path] = []
    if meipass:
        candidates.append(Path(meipass) / "static")

    backend_dir = Path(__file__).resolve().parents[1]
    candidates.append(backend_dir / "static")

    for candidate in candidates:
        if candidate.exists():
            _STATIC_DIR = candidate
            return candidate

    candidate_str = ", ".join(str(p) for p in candidates)
    raise FileNotFoundError(f"Static directory not found (tried: {candidate_str})")


def get_shared_templates_dir() -> Path:
    """返回共享模板目录（兼容源码运行与 PyInstaller）。"""

    global _SHARED_TEMPLATES_DIR
    if _SHARED_TEMPLATES_DIR is not None:
        return _SHARED_TEMPLATES_DIR

    meipass = getattr(sys, "_MEIPASS", None)
    candidates: list[Path] = []
    if meipass:
        candidates.append(Path(meipass) / "shared_templates")

    backend_dir = Path(__file__).resolve().parents[1]
    candidates.append(backend_dir / "shared_templates")

    for candidate in candidates:
        if candidate.exists():
            _SHARED_TEMPLATES_DIR = candidate
            return candidate

    candidate_str = ", ".join(str(p) for p in candidates)
    raise FileNotFoundError(
        f"Shared templates directory not found (tried: {candidate_str})"
    )


def resolve_static_path(relative_path: Union[str, Path]) -> Path:
    """基于 static 目录解析资源路径。"""

    return get_static_dir() / Path(relative_path)


def resolve_template_path(
    template_relpath: Union[str, Path],
    *,
    plugin_dir: Optional[Path] = None,
) -> Path:
    """解析模板图片路径。

    查找顺序：
    1) 插件内 `templates/`
    2) `backend/shared_templates/`

    参数:
      template_relpath: 相对模板根目录的路径，例如 `identify_in/in_menu.png`。
      plugin_dir: 插件目录（如 `backend/plugins/order_task`），存在时会优先尝试：
        `<plugin_dir>/templates/<template_relpath>`
    """

    rel = Path(template_relpath)

    tried: list[Path] = []

    if plugin_dir is not None:
        candidate = plugin_dir / "templates" / rel
        tried.append(candidate)
        if candidate.exists():
            return candidate

    shared_dir = get_shared_templates_dir()
    candidate = shared_dir / rel
    tried.append(candidate)
    if candidate.exists():
        return candidate

    tried_str = ", ".join(str(p) for p in tried)
    raise FileNotFoundError(f"Template not found: {rel} (tried: {tried_str})")
