"""
Notification delivery.

Push is sent via Firebase Cloud Messaging when FIREBASE_CREDENTIALS_JSON is
configured. Without credentials (dev/staging by default) the sender is a safe
no-op that logs what *would* be sent, so the rest of the system works and is
testable without a real Firebase project.
"""

import logging
from datetime import UTC, datetime

from core.config import settings
from notifications.models import PushToken

logger = logging.getLogger("notifications")

_firebase_app = None  # initialized lazily if credentials exist


def _ensure_firebase() -> bool:
    """Initialize firebase-admin once. Returns True if push can actually be sent."""
    global _firebase_app
    if not settings.firebase_credentials_json:
        return False
    if _firebase_app is not None:
        return True
    try:
        import firebase_admin
        from firebase_admin import credentials

        cred = credentials.Certificate(settings.firebase_credentials_json)
        _firebase_app = firebase_admin.initialize_app(cred)
        return True
    except Exception as exc:  # pragma: no cover - depends on real creds
        logger.warning("Firebase init failed, falling back to no-op: %s", exc)
        return False


async def register_token(branch_id: str, token: str, device_label: str | None) -> PushToken:
    """Idempotently store a device token. Re-registering refreshes the label/timestamp."""
    existing = await PushToken.find_one(PushToken.branch_id == branch_id, PushToken.token == token)
    if existing:
        existing.device_label = device_label
        existing.updated_at = datetime.now(UTC)
        await existing.save()
        return existing
    doc = PushToken(branch_id=branch_id, token=token, device_label=device_label)
    await doc.insert()
    return doc


async def tokens_for_branch(branch_id: str) -> list[str]:
    docs = await PushToken.find(PushToken.branch_id == branch_id).to_list()
    return [d.token for d in docs]


async def send_to_branch(branch_id: str, title: str, body: str) -> int:
    """
    Send a push to all of a branch's devices. Returns the number of tokens
    targeted. Invalid tokens (reported by FCM) are pruned.
    """
    tokens = await tokens_for_branch(branch_id)
    if not tokens:
        return 0

    if not _ensure_firebase():
        # No-op mode: log and return as if delivered.
        logger.info("[push:no-op] branch=%s title=%r body=%r tokens=%d", branch_id, title, body, len(tokens))
        return len(tokens)

    from firebase_admin import messaging  # pragma: no cover - needs real creds

    sent = 0
    for token in tokens:  # pragma: no cover
        try:
            messaging.send(
                messaging.Message(notification=messaging.Notification(title=title, body=body), token=token)
            )
            sent += 1
        except Exception as exc:
            logger.warning("Push to token failed (%s); pruning. err=%s", token[:12], exc)
            doc = await PushToken.find_one(PushToken.token == token)
            if doc:
                await doc.delete()
    return sent
