import datetime
import random
import re
from typing import Any, Dict, List, Optional


def check_is_tagged(
    message_text: str,
    dom_mentioned: bool,
    my_tag_names: List[str]
) -> bool:
    """
    Checks if the message tags the user either via Zalo Web DOM mention highlight
    or by matching one of configured @tag names in message text.
    """
    if dom_mentioned:
        return True
    msg_lower = (message_text or "").lower()
    for tag in my_tag_names:
        clean_tag = tag.strip().lower()
        if not clean_tag:
            continue
        if not clean_tag.startswith("@"):
            clean_tag_with_at = "@" + clean_tag
        else:
            clean_tag_with_at = clean_tag
        if clean_tag_with_at in msg_lower or clean_tag in msg_lower:
            return True
    return False


def format_reply_template(
    template: str,
    sender: str,
    chat_name: str,
    message_text: str
) -> str:
    now = datetime.datetime.now()
    replacements = {
        "{sender}": sender or "bạn",
        "{chat_name}": chat_name or "cuộc trò chuyện",
        "{time}": now.strftime("%H:%M"),
        "{date}": now.strftime("%d/%m/%Y"),
        "{message}": message_text or ""
    }
    result = template
    for key, val in replacements.items():
        result = result.replace(key, val)
    return result


def evaluate_message(
    config: Dict[str, Any],
    chat_name: str,
    sender_name: str,
    chat_type: str,  # "group" or "private"
    message_text: str,
    dom_mentioned: bool = False
) -> Dict[str, Any]:
    """
    Evaluates an incoming Zalo message against target_controls, tag rules, and scenarios.
    Returns a dictionary with:
      - matched: bool
      - reply_text: Optional[str]
      - matched_rule: Optional[Dict]
      - reason: str
      - is_tagged: bool
      - effective_chat_type: str
    """
    settings = config.get("settings", {})
    target_controls = config.get("target_controls", [])
    rules = config.get("rules", [])

    chat_name_norm = (chat_name or "").strip().lower()
    sender_name_norm = (sender_name or "").strip().lower()
    effective_chat_type = chat_type if chat_type in ("group", "private") else "private"

    # 1. Check Target Controls (per-person / per-group enable/disable & explicit type override)
    for tc in target_controls:
        tc_name = (tc.get("name") or "").strip().lower()
        if not tc_name:
            continue
        if tc_name == chat_name_norm or tc_name in chat_name_norm or (
            effective_chat_type == "private" and tc_name == sender_name_norm
        ):
            if tc.get("chat_type") in ("group", "private"):
                effective_chat_type = tc["chat_type"]
            if not tc.get("enabled", True):
                return {
                    "matched": False,
                    "reply_text": None,
                    "matched_rule": None,
                    "reason": f"Đã tắt tự động trả lời cho '{tc.get('name')}' trong danh sách Người/Nhóm.",
                    "is_tagged": False,
                    "effective_chat_type": effective_chat_type
                }

    # 2. Check if user is tagged @
    my_tag_names = settings.get("my_tag_names", [])
    is_tagged = check_is_tagged(message_text, dom_mentioned, my_tag_names)

    # 3. Sort rules by priority descending
    active_rules = [r for r in rules if r.get("enabled", True)]
    active_rules.sort(key=lambda r: int(r.get("priority", 0)), reverse=True)

    msg_norm = (message_text or "").strip().lower()
    # Also prepare text with @tags stripped for cleaner exact/keyword matching if needed
    msg_without_tags = msg_norm
    for tag in my_tag_names:
        t_low = tag.strip().lower()
        if t_low:
            msg_without_tags = msg_without_tags.replace(t_low, "").strip()

    for rule in active_rules:
        scope_type = rule.get("scope_type", "all")
        target_names = [
            t.strip().lower() for t in rule.get("target_names", []) if t.strip()
        ]

        # Check scope_type
        has_wildcard = "*" in target_names
        if scope_type == "group" and effective_chat_type != "group":
            continue
        if scope_type == "private" and effective_chat_type != "private":
            continue
        if scope_type == "specific":
            if not target_names:
                continue
            target_matched = has_wildcard or any(
                t == chat_name_norm
                or t in chat_name_norm
                or t == sender_name_norm
                or t in sender_name_norm
                for t in target_names
            )
            if not target_matched:
                continue
        elif target_names and not has_wildcard:
            # Optional target filter even when scope_type is group/private/all
            target_matched = any(
                t == chat_name_norm
                or t in chat_name_norm
                or t == sender_name_norm
                or t in sender_name_norm
                for t in target_names
            )
            if not target_matched:
                continue

        # Check @tag requirement for this rule
        tag_override = rule.get("require_tag_override", "default")
        if tag_override == "always":
            require_tag = True
        elif tag_override == "never":
            require_tag = False
        else:
            if effective_chat_type == "group":
                require_tag = settings.get("group_require_tag", True)
            else:
                require_tag = settings.get("private_require_tag", False)

        if require_tag and not is_tagged:
            continue

        # Check keyword / content matching
        match_type = rule.get("match_type", "contains")
        keywords = [k.strip() for k in rule.get("keywords", []) if k.strip()]

        keyword_matched = False
        matched_keyword = None

        if match_type == "all" or not keywords or "*" in keywords:
            keyword_matched = True
            matched_keyword = "<Tất cả nội dung>"
        elif match_type == "contains":
            for kw in keywords:
                if kw.lower() in msg_norm:
                    keyword_matched = True
                    matched_keyword = kw
                    break
        elif match_type == "exact":
            for kw in keywords:
                kw_low = kw.lower()
                if msg_norm == kw_low or msg_without_tags == kw_low:
                    keyword_matched = True
                    matched_keyword = kw
                    break
        elif match_type == "regex":
            for kw in keywords:
                try:
                    if re.search(kw, message_text or "", re.IGNORECASE):
                        keyword_matched = True
                        matched_keyword = kw
                        break
                except re.error:
                    continue

        if not keyword_matched:
            continue

        # We have a matching rule!
        templates = [
            t.strip() for t in rule.get("reply_templates", []) if t.strip()
        ]
        if not templates:
            continue

        chosen_template = random.choice(templates)
        display_sender = sender_name or chat_name or "bạn"
        reply_text = format_reply_template(
            chosen_template,
            sender=display_sender,
            chat_name=chat_name or display_sender,
            message_text=message_text
        )

        return {
            "matched": True,
            "reply_text": reply_text,
            "matched_rule": rule,
            "matched_keyword": matched_keyword,
            "reason": f"Khớp kịch bản '{rule.get('name')}' (Từ khóa: {matched_keyword})",
            "is_tagged": is_tagged,
            "effective_chat_type": effective_chat_type
        }

    # Explain why no rule matched
    if effective_chat_type == "group" and settings.get("group_require_tag", True) and not is_tagged:
        reason = "Tin nhắn trong Nhóm nhưng không tag @Tên_của_bạn nên bỏ qua."
    else:
        reason = "Không có kịch bản nào khớp với nội dung / đối tượng của tin nhắn này."

    return {
        "matched": False,
        "reply_text": None,
        "matched_rule": None,
        "matched_keyword": None,
        "reason": reason,
        "is_tagged": is_tagged,
        "effective_chat_type": effective_chat_type
    }
