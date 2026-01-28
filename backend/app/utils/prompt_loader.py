from pathlib import Path
from typing import Union
import json
import os
import re

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_PROMPT_DIR = _PROJECT_ROOT / "app" / "services" / "transform2tidy" / "prompts"
PROMPT_DIR = Path(os.environ.get("PROMPT_DIR", str(_DEFAULT_PROMPT_DIR))).resolve()


class PromptRenderError(Exception):
    pass


def load_prompt(prompt_name: Union[str, Path]) -> str:
    """
    Load a prompt template from the prompts directory.
    """
    path = PROMPT_DIR / Path(prompt_name)
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def to_pretty_json(obj) -> str:
    """
    Convert Python object to pretty JSON string (Unicode-safe).
    """
    return json.dumps(obj, indent=2, ensure_ascii=False)


def wrap_json_block(json_str: str) -> str:
    """
    Wrap JSON string in markdown fenced code block.
    """
    return f"```json\n{json_str}\n```"


def render_prompt(
    prompt_template: str,
    variables: dict,
    strict: bool = True
) -> str:
    """
    Render a prompt template by replacing placeholders.

    Placeholders must be written as <PLACEHOLDER_NAME>

    Args:
        prompt_template: str
        variables: dict[str, Any] (auto JSON serialized)
        strict: fail if placeholders are missing or unused

    Returns:
        Rendered prompt string
    """
    rendered = prompt_template

    # Replace placeholders
    for key, value in variables.items():
        placeholder = f"<{key}>"

        if strict and placeholder not in rendered:
            raise PromptRenderError(
                f"Placeholder {placeholder} not found in prompt template"
            )

        if not isinstance(value, str):
            value = wrap_json_block(to_pretty_json(value))

        rendered = rendered.replace(placeholder, value)

    # Detect unreplaced placeholders
    if strict:
        leftovers = re.findall(r"<[A-Z0-9_]+>", rendered)
        if leftovers:
            raise PromptRenderError(
                f"Unreplaced placeholders found: {leftovers}"
            )

    return rendered
