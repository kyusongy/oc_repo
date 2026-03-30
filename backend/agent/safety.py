import re

from openai import AsyncOpenAI

# Patterns for safe commands (auto-execute)
SAFE_PATTERNS = [
    r"^(npm|yarn|pnpm)\s+(install|ci|run build|run lint)\b",
    r"^pip3?\s+install\b",
    r"^uv\s+(sync|run|pip install)\b",
    r"^brew\s+install\b",
    r"^cargo\s+(build|install)\b",
    r"^(ls|head|tail|wc|find|which|type|file|stat)\b",
    r"^cat\s+[^>|]",  # cat for reading only, not redirecting
    r"^(python3?|node|ruby|go|java|cargo)\s+(-[vV]|--version)",
    r"^mkdir\b",
    r"^(cp|mv)\b",
    r"^git\s+(clone|status|log|diff|branch)\b",
    r"^curl\s+-[sS]",  # silent curl (GET checks)
    r"^curl\s+.*-I\b",  # HEAD requests
    r"^(lsof|ps|whoami|hostname|uname|sysctl|sw_vers)\b",
    r"^(sleep|true|false)\b",
    r"^test\s",
    r"^\.\s",  # source/dot commands
    r"^source\b",
    r"^(pip3?|npm)\s+list\b",
    r"^python3?\s+-m\s+(pip|venv|ensurepip)\b",
]

# Patterns for dangerous commands (always block)
DANGEROUS_PATTERNS = [
    r"\brm\s+-rf\s+/",
    r"\bsudo\s+rm\b",
    r"\bmkfs\b",
    r"\bchmod\s+777\b",
    r"\bcurl\s+.*\|\s*(ba)?sh\b",  # curl | bash
    r"\bwget\s+.*\|\s*(ba)?sh\b",  # wget | sh
    r"\beval\b.*\$",
    r"\b>\s*/dev/",
    r"\bdd\s+if=",
    r"`[^`]+`",  # backtick command substitution
    r"\$\([^)]+\)",  # $() subshell
]

# Patterns for sensitive commands (ask user)
SENSITIVE_PATTERNS = [
    r"\bnohup\b",
    r"&\s*$",  # background process
    r"\b(flask\s+run|uvicorn|gunicorn|npm\s+run\s+dev|npm\s+start|node\s+\S+\.js)\b",
    r"\bsudo\b",
    r"\bkill\b",
    r"\bdocker\s+(run|compose|build)\b",
    r"^(python3?|node)\s+-c\s+",  # inline scripts can do anything
    r"^echo\b.*[>|]",  # echo with redirect or pipe
]

# echo without redirect/pipe is safe
SAFE_PATTERNS.append(r"^echo\b")


def classify_rule_based(command: str) -> str | None:
    """Classify a command using regex patterns. Returns 'safe', 'sensitive', 'dangerous', or None if ambiguous."""
    cmd = command.strip()
    if not cmd:
        return None

    # Handle bash -c or bash -lc wrappers
    for prefix in ["bash -c ", "bash -lc ", "sh -c "]:
        if cmd.startswith(prefix):
            cmd = cmd[len(prefix) :].strip("'\"")
            break

    # Check dangerous first (highest priority)
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd):
            return "dangerous"

    # Check sensitive
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, cmd):
            return "sensitive"

    # Check safe
    for pattern in SAFE_PATTERNS:
        if re.search(pattern, cmd):
            return "safe"

    # Check multi-command chains
    if "&&" in cmd:
        parts = [p.strip() for p in cmd.split("&&")]
        results = [classify_rule_based(p) for p in parts]
        if "dangerous" in results:
            return "dangerous"
        if "sensitive" in results:
            return "sensitive"
        if all(r == "safe" for r in results):
            return "safe"

    # Semicolon chains
    if ";" in cmd:
        parts = [p.strip() for p in cmd.split(";")]
        results = [classify_rule_based(p) for p in parts]
        if "dangerous" in results:
            return "dangerous"
        if "sensitive" in results:
            return "sensitive"

    return None  # ambiguous — falls through to LLM


async def classify_with_llm(command: str, client: AsyncOpenAI, model: str) -> str:
    """Fallback: use LLM to classify an ambiguous command."""
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Classify this shell command as SAFE, SENSITIVE, or DANGEROUS.\n"
                        f"SAFE = read-only or standard install/build operations.\n"
                        f"SENSITIVE = starts services, writes credentials, or has side effects beyond the project.\n"
                        f"DANGEROUS = destructive or potentially harmful.\n"
                        f"Command: {command}\n"
                        f"Reply with one word: SAFE, SENSITIVE, or DANGEROUS."
                    ),
                }
            ],
        )
        result = response.choices[0].message.content.strip().upper()
        if result in ("SAFE", "SENSITIVE", "DANGEROUS"):
            return result.lower()
        return "sensitive"
    except Exception:
        return "sensitive"


async def classify_command(
    command: str, client: AsyncOpenAI | None = None, model: str | None = None
) -> str:
    """Classify a command's safety level. Returns 'safe', 'sensitive', or 'dangerous'."""
    result = classify_rule_based(command)
    if result is not None:
        return result
    if client and model:
        return await classify_with_llm(command, client, model)
    return "sensitive"
