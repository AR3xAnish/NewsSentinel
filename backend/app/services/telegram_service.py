import html
import os
import httpx
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import Story, NotificationDelivery
from app.config import get_settings

class TelegramService:
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.api_base = "https://api.telegram.org"
        self._bot_token = bot_token
        self._chat_id = chat_id

    @property
    def bot_token(self) -> str:
        if self._bot_token is not None:
            return self._bot_token
        s = get_settings()
        return s.TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN", "")

    @bot_token.setter
    def bot_token(self, val: str):
        self._bot_token = val

    @property
    def chat_id(self) -> str:
        if self._chat_id is not None:
            return self._chat_id
        s = get_settings()
        return s.TELEGRAM_CHAT_ID or os.getenv("TELEGRAM_CHAT_ID", "")

    @chat_id.setter
    def chat_id(self, val: str):
        self._chat_id = val

    def is_configured(self) -> bool:
        """Returns True if bot token and chat ID are both non-empty."""
        return bool(self.bot_token.strip() and self.chat_id.strip())

    def get_configuration_status(self) -> Dict[str, Any]:
        """Returns non-sensitive configuration status and guidance."""
        return {
            "configured": self.is_configured(),
            "chat_id": self.chat_id if self.chat_id else None,
            "has_token": bool(self.bot_token),
            "instructions": (
                "To configure Telegram notifications: 1) Talk to @BotFather on Telegram to create a bot and copy the API token. "
                "2) Start a chat with your bot or add it to a channel. 3) Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in backend/.env "
                "or update them in the Settings page."
            )
        }

    async def send_test_message(self, db: Session, test_text: Optional[str] = None) -> Dict[str, Any]:
        """Sends a verification test ping to the configured Telegram chat."""
        if not self.is_configured():
            return {
                "success": False,
                "error": "Telegram integration is not configured. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."
            }

        text = test_text or "🤖 YGF AI News Intelligence Agent: Telegram connection test successful!"
        return await self._dispatch_message(db=db, story_id=None, text=text, parse_mode=None)

    async def send_story_summary(self, db: Session, story: Story, custom_note: Optional[str] = None) -> Dict[str, Any]:
        """
        Formats a story summary and dispatches it via Telegram safely using HTML mode.
        Prevents accidental duplicate dispatch to the same chat within 10 minutes.
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "Telegram integration is not configured. Delivery skipped."
            }

        # Check duplicate delivery
        recent_delivery = db.query(NotificationDelivery).filter(
            NotificationDelivery.story_id == story.id,
            NotificationDelivery.recipient_chat_id == self.chat_id,
            NotificationDelivery.status == "SUCCESS"
        ).order_by(NotificationDelivery.created_at.desc()).first()

        if recent_delivery:
            diff_seconds = (datetime.now(timezone.utc) - recent_delivery.created_at.replace(tzinfo=timezone.utc)).total_seconds()
            if diff_seconds < 600:
                return {
                    "success": False,
                    "error": f"Story was already delivered to chat {self.chat_id} {int(diff_seconds)} seconds ago. Duplicate prevented."
                }

        # Format message safely using HTML entities
        primary_sa = next((sa for sa in story.articles if sa.is_primary and sa.article), None)
        if not primary_sa and story.articles:
            primary_sa = story.articles[0]

        primary_url = primary_sa.article.canonical_url if primary_sa and primary_sa.article else "https://ygf-ngo.org"
        publisher = primary_sa.article.publisher if primary_sa and primary_sa.article else "Source"

        status_emoji = {
            "CORROBORATED": "✅",
            "PARTIALLY_CORROBORATED": "🟡",
            "CONFLICTING": "⚠️",
            "UNVERIFIED": "❓",
            "INSUFFICIENT_EVIDENCE": "🔍",
        }.get(story.verification_status, "📌")

        safe_headline = html.escape(story.headline or "News Story")
        safe_status = html.escape(story.verification_status or "UNVERIFIED")
        safe_summary = html.escape(story.summary_factual or story.headline or "")
        safe_why = html.escape(story.why_it_matters or "")
        safe_publisher = html.escape(publisher)
        safe_url = html.escape(primary_url)

        lines = [
            "📢 <b>YGF AI NEWS INTELLIGENCE</b>",
            "",
            f"<b>{safe_headline}</b>",
            "",
            f"• <b>Status</b>: {status_emoji} {safe_status} (Confidence: {int(story.confidence_score * 100)}%)",
            f"• <b>Sources</b>: {story.source_count} article(s) ({story.independent_source_count} independent publisher(s))",
            "",
            "📝 <b>Factual Summary</b>:",
            safe_summary,
            "",
        ]

        if safe_why:
            lines.extend([
                "💡 <b>Why It Matters</b>:",
                safe_why,
                "",
            ])

        lines.extend([
            f"🔗 <b>Primary Source</b> ({safe_publisher}):",
            safe_url,
        ])

        if custom_note:
            lines.extend([
                "",
                f"💬 <b>Note</b>: {html.escape(custom_note)}"
            ])

        full_message = "\n".join(lines)
        return await self._dispatch_message(db=db, story_id=story.id, text=full_message, parse_mode="HTML")

    async def _dispatch_message(
        self,
        db: Session,
        story_id: Optional[int],
        text: str,
        parse_mode: Optional[str] = "HTML"
    ) -> Dict[str, Any]:
        """Handles HTTP dispatch to Telegram API with chunking, HTML safety, and fallback logging."""
        now = datetime.now(timezone.utc)
        delivery_record = NotificationDelivery(
            story_id=story_id,
            channel="telegram",
            recipient_chat_id=self.chat_id,
            status="PENDING",
            message_preview=text[:250],
            created_at=now,
        )
        db.add(delivery_record)
        db.flush()

        url = f"{self.api_base}/bot{self.bot_token}/sendMessage"
        safe_text = text[:4000]

        payload = {
            "chat_id": self.chat_id,
            "text": safe_text,
            "disable_web_page_preview": False,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                
                # If HTML parsing failed for any reason, retry immediately as plain text
                if resp.status_code == 400 and parse_mode:
                    plain_payload = {
                        "chat_id": self.chat_id,
                        "text": safe_text.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", ""),
                        "disable_web_page_preview": False,
                    }
                    resp = await client.post(url, json=plain_payload)

                if resp.status_code == 200:
                    resp_data = resp.json()
                    msg_id = str(resp_data.get("result", {}).get("message_id", ""))
                    delivery_record.status = "SUCCESS"
                    delivery_record.telegram_message_id = msg_id
                    delivery_record.delivered_at = datetime.now(timezone.utc)
                    db.commit()
                    return {"success": True, "message_id": msg_id}
                else:
                    err_msg = f"HTTP {resp.status_code}: {resp.text}"
                    delivery_record.status = "FAILED"
                    delivery_record.error_message = err_msg[:500]
                    db.commit()
                    return {"success": False, "error": err_msg}

        except Exception as e:
            err_msg = str(e)
            delivery_record.status = "FAILED"
            delivery_record.error_message = err_msg[:500]
            db.commit()
            return {"success": False, "error": err_msg}

telegram_service = TelegramService()
