"""The one place this package touches the real Anthropic SDK / network.

Kept separate from `advisor.py` so that module only ever depends on the
narrow `MessagesClient` protocol, not on `anthropic` itself — tests for the
prompt/parsing logic construct a stub directly and never import this module.
"""

from __future__ import annotations

from typing import cast

import anthropic

from .advisor import MessagesClient


def default_client() -> MessagesClient:
    """Reads `ANTHROPIC_API_KEY` from the environment (the SDK's own default
    lookup) — raises `anthropic.AuthenticationError` on first real call if unset,
    rather than failing here, so importing this module never requires a key.

    A user-scoped key (as opposed to a key generated for a specific workspace)
    gets a 400 from the API ("not scoped to a workspace") unless the request
    carries an `anthropic-workspace-id` header. The SDK already reads that from
    `ANTHROPIC_CUSTOM_HEADERS` (one "Header: value" per line) with no code needed
    here — see the README's install section — so this function doesn't special-case
    it itself."""
    # anthropic.Messages.create is a multi-overload signature (streaming vs not);
    # our narrower MessagesClient protocol is what advisor.py actually calls it
    # with, so this is a real runtime match even though mypy can't verify the
    # overloaded SDK type against a plain **kwargs Protocol.
    return cast(MessagesClient, anthropic.Anthropic().messages)
