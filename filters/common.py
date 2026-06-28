"""Shared helpers used by all filters."""
import os
import re
import sys

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

# Token counting. If `tiktoken` is installed we use a real BPE tokenizer
# (a close approximation of Claude's); otherwise we fall back to the chars/4
# heuristic. We probe lazily and cache the result.
_ENCODER = None
_ENCODER_TRIED = False
_TOKENIZER_NAME = "estimate (~4 chars/token)"


def _get_encoder():
    global _ENCODER, _ENCODER_TRIED, _TOKENIZER_NAME
    if not _ENCODER_TRIED:
        _ENCODER_TRIED = True
        try:
            # In the bundled .exe, read the vocab from the cache we shipped so we
            # never hit the network. (PyInstaller extracts data to sys._MEIPASS.)
            if getattr(sys, "frozen", False):
                bundled = os.path.join(getattr(sys, "_MEIPASS", ""), "tiktoken_cache")
                if os.path.isdir(bundled):
                    os.environ.setdefault("TIKTOKEN_CACHE_DIR", bundled)
            import tiktoken
            _ENCODER = tiktoken.get_encoding("o200k_base")
            _TOKENIZER_NAME = "tiktoken o200k_base"
        except Exception:
            _ENCODER = None
    return _ENCODER


def estimate_tokens(text: str) -> int:
    """Count tokens with tiktoken if available, else the ~4 chars/token heuristic."""
    enc = _get_encoder()
    if enc is not None:
        return max(1, len(enc.encode(text)))
    return max(1, len(text) // 4)


def tokenizer_name() -> str:
    """Human-readable name of the active token counter (for `gain`/`doctor`)."""
    _get_encoder()
    return _TOKENIZER_NAME


def is_real_tokenizer() -> bool:
    return _get_encoder() is not None


def strip_ansi(text: str) -> str:
    """Remove ANSI color/escape codes (npm/git color output is pure noise to an LLM)."""
    return ANSI_RE.sub("", text)


def dedupe_consecutive(lines):
    """Collapse runs of identical lines into 'line  (xN)'."""
    out = []
    i = 0
    while i < len(lines):
        j = i
        while j + 1 < len(lines) and lines[j + 1] == lines[i]:
            j += 1
        count = j - i + 1
        if count > 1:
            out.append(f"{lines[i]}  (x{count})")
        else:
            out.append(lines[i])
        i = j + 1
    return out


def truncate_middle(lines, head=20, tail=10):
    """Keep the start and end of a long block, drop the redundant middle."""
    if len(lines) <= head + tail:
        return lines
    hidden = len(lines) - head - tail
    return lines[:head] + [f"... ({hidden} lines hidden by slim) ..."] + lines[-tail:]
