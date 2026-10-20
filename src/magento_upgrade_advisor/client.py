"""The one place this package touches the real Anthropic SDK / network.

Kept separate from `advisor.py` so that module only ever depends on the
narrow `MessagesClient` protocol, not on `anthropic` itself — tests for the
prompt/parsing logic construct a stub directly and never import this module.
"""

from __future__ import annotations

import os
from typing import cast

import anthropic

from .advisor import MessagesClient


def default_client() -> MessagesClient:
    """Reads `ANTHROPIC_API_KEY` from the environment (the SDK's own default
    lookup) — raises `anthropic.AuthenticationError` on first real call if unset,
    rather than failing here, so importing this module never requires a key.

    A user-scoped key (as opposed to a key generated for a specific workspace)
    gets a 400 from the API ("not scoped to a workspace") unless the request
    carries an `anthropic-workspace-id` header — read from `ANTHROPIC_WORKSPACE_ID`
    if set, omitted otherwise (a normal workspace-scoped key doesn't need it)."""
    workspace_id = os.environ.get("ANTHROPIC_WORKSPACE_ID")
    default_headers = {"anthropic-workspace-id": workspace_id} if workspace_id else None

    # anthropic.Messages.create is a multi-overload signature (streaming vs not);
    # our narrower MessagesClient protocol is what advisor.py actually calls it
    # with, so this is a real runtime match even though mypy can't verify the
    # overloaded SDK type against a plain **kwargs Protocol.
    return cast(MessagesClient, anthropic.Anthropic(default_headers=default_headers).messages)
