import asyncio
import base64
import datetime
import random
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright

from config_store import ConfigStore, DATA_DIR
from rule_engine import evaluate_message

PROFILE_DIR = DATA_DIR / "chrome_profile"


class ZaloBotManager:
    def __init__(self, config_store: ConfigStore):
        self.config_store = config_store
        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.browser_running: bool = False
        self.logged_in: bool = False
        self.detected_profile_name: Optional[str] = None
        self.current_chat_name: Optional[str] = None
        self.last_error: Optional[str] = None
        self.monitor_task: Optional[asyncio.Task] = None

        # Dedup & cooldown tracking
        self.processed_messages: Set[str] = set()
        self.baseline_capturedChats: Set[str] = set()
        self.last_reply_ts_by_chat: Dict[str, float] = {}

        # Activity logs (kept in memory, up to 300 entries)
        self.logs: List[Dict[str, Any]] = []
        self.stats = {
            "messages_scanned": 0,
            "replies_sent": 0,
            "rules_matched": 0,
            "started_at": None
        }

    def add_log(self, level: str, title: str, detail: str = "", meta: Optional[Dict[str, Any]] = None):
        entry = {
            "id": f"log-{int(time.time() * 1000)}-{random.randint(100, 999)}",
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "level": level,  # "info", "success", "warning", "error"
            "title": title,
            "detail": detail,
            "meta": meta or {}
        }
        self.logs.insert(0, entry)
        if len(self.logs) > 300:
            self.logs = self.logs[:300]

    def get_status(self) -> Dict[str, Any]:
        cfg = self.config_store.load()
        return {
            "browser_running": self.browser_running,
            "logged_in": self.logged_in,
            "bot_enabled": cfg.get("settings", {}).get("bot_enabled", False),
            "detected_profile_name": self.detected_profile_name,
            "current_chat_name": self.current_chat_name,
            "last_error": self.last_error,
            "stats": self.stats
        }

    async def launch_browser(self) -> Dict[str, Any]:
        if self.browser_running and self.context and self.page and not self.page.is_closed():
            try:
                await self.page.bring_to_front()
            except Exception:
                pass
            self.add_log("info", "Đã đưa cửa sổ Zalo Web lên phía trước.")
            return self.get_status()

        self.last_error = None
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            if not self.playwright:
                self.playwright = await async_playwright().start()

            # Launch persistent Chrome or Edge context so Zalo login session is saved
            launch_kwargs = dict(
                user_data_dir=str(PROFILE_DIR),
                headless=False,
                viewport={"width": 1280, "height": 840},
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-default-browser-check",
                    "--disable-infobars"
                ]
            )
            try:
                self.context = await self.playwright.chromium.launch_persistent_context(
                    channel="chrome", **launch_kwargs
                )
            except Exception:
                self.context = await self.playwright.chromium.launch_persistent_context(
                    channel="msedge", **launch_kwargs
                )

            pages = self.context.pages
            self.page = pages[0] if pages else await self.context.new_page()

            self.page.on("close", self._on_page_closed)
            await self.page.goto("https://chat.zalo.me", wait_until="domcontentloaded", timeout=45000)
            try:
                await self.page.bring_to_front()
            except Exception:
                pass

            self.browser_running = True
            if not self.stats["started_at"]:
                self.stats["started_at"] = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")

            self.add_log(
                "info",
                "Đã mở trình duyệt Zalo Web (chat.zalo.me)",
                "Bạn có thể quét mã QR ngay trên khung hiển thị của Dashboard hoặc trên cửa sổ Chrome."
            )

            if not self.monitor_task or self.monitor_task.done():
                self.monitor_task = asyncio.create_task(self._monitor_loop())

            return self.get_status()
        except Exception as e:
            self.last_error = str(e)
            self.browser_running = False
            self.add_log("error", "Không thể mở trình duyệt Zalo Web", str(e))
            return self.get_status()

    async def get_screenshot_base64(self) -> Optional[str]:
        if not self.browser_running or not self.page or self.page.is_closed():
            return None
        try:
            png_bytes = await self.page.screenshot(type="jpeg", quality=75)
            return "data:image/jpeg;base64," + base64.b64encode(png_bytes).decode("ascii")
        except Exception:
            return None

    def _on_page_closed(self, _page):
        self.browser_running = False
        self.logged_in = False
        self.add_log("warning", "Cửa sổ trình duyệt Zalo Web đã bị đóng.")

    async def close_browser(self) -> Dict[str, Any]:
        if self.monitor_task and not self.monitor_task.done():
            self.monitor_task.cancel()
        try:
            if self.context:
                await self.context.close()
        except Exception:
            pass
        try:
            if self.playwright:
                await self.playwright.stop()
        except Exception:
            pass
        self.context = None
        self.page = None
        self.playwright = None
        self.browser_running = False
        self.logged_in = False
        self.current_chat_name = None
        self.add_log("info", "Đã đóng trình duyệt Zalo Web.")
        return self.get_status()

    async def _monitor_loop(self):
        """Background loop that checks login state, scans unread chats, and processes incoming messages."""
        while self.browser_running and self.page and not self.page.is_closed():
            try:
                state = await self._inspect_zalo_dom()
                was_logged_in = self.logged_in
                self.logged_in = state.get("logged_in", False)

                if self.logged_in and not was_logged_in:
                    self.add_log(
                        "success",
                        "Đã kết nối thành công với tài khoản Zalo Web!",
                        f"Tài khoản phát hiện: {state.get('profile_name') or 'Đã đăng nhập'}"
                    )

                if state.get("profile_name"):
                    self.detected_profile_name = state["profile_name"]

                self.current_chat_name = state.get("chat_name")

                cfg = self.config_store.load()
                settings = cfg.get("settings", {})
                bot_enabled = settings.get("bot_enabled", False)

                if self.logged_in and bot_enabled:
                    # 1. Process current open chat if it has a new incoming message
                    await self._process_active_chat(state, cfg)

                    # 2. If auto_open_unread is enabled, click on an unread conversation item
                    if settings.get("auto_open_unread", True):
                        clicked_chat = await self._click_next_unread_chat()
                        if clicked_chat:
                            await asyncio.sleep(1.2)
                            new_state = await self._inspect_zalo_dom()
                            self.current_chat_name = new_state.get("chat_name")
                            await self._process_active_chat(new_state, cfg)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.last_error = str(e)

            await asyncio.sleep(1.8)

    async def _inspect_zalo_dom(self) -> Dict[str, Any]:
        """Runs JS inside Zalo Web to detect login state, active chat info, and latest incoming message."""
        if not self.page or self.page.is_closed():
            return {"logged_in": False}

        js_code = """
        () => {
            const url = window.location.href || '';
            const bodyText = document.body ? (document.body.innerText || '') : '';
            // 1. Check if logged in (on chat.zalo.me and sidebar or chat list exists)
            const hasSidebar = !!(
                document.querySelector('#conversationListId') ||
                document.querySelector('.msg-item') ||
                document.querySelector('.conv-item') ||
                document.querySelector('#main-tab') ||
                document.querySelector('#contact-search-input') ||
                document.querySelector('#richInput') ||
                document.querySelector('[data-id^="div_Main_Tab"]')
            );
            const hasQr = !!(
                url.includes('id.zalo.me') ||
                document.querySelector('.qrcode') ||
                document.querySelector('.za-qr') ||
                document.querySelector('img[src*=" data:image/png;base64"]') && bodyText.includes('QR') ||
                bodyText.includes('Quét mã QR') ||
                bodyText.includes('Đăng nhập qua mã QR')
            );
            const loggedIn = hasSidebar && !hasQr;
            if (!loggedIn) {
                return { logged_in: false };
            }

            // 2. Try to detect user's own profile name from avatar title/alt
            let profileName = null;
            const avatarEl = document.querySelector('#main-tab .zavatar img, nav .zavatar img, [title][class*="avatar"]');
            if (avatarEl) {
                profileName = avatarEl.getAttribute('title') || avatarEl.getAttribute('alt') || null;
            }

            // 3. Detect active open conversation name & whether it is a Group or Private 1-1 chat
            let chatName = null;
            const headerTitleSelectors = [
                'header .header-title',
                '.thread-chat-title',
                '#header .title',
                '.chat-box-header .truncate',
                'header .truncate'
            ];
            for (const sel of headerTitleSelectors) {
                const el = document.querySelector(sel);
                if (el && el.innerText && el.innerText.trim()) {
                    chatName = el.innerText.trim();
                    break;
                }
            }

            let isGroup = false;
            const headerEl = document.querySelector('header, #header, .chat-box-header');
            if (headerEl) {
                const headerText = (headerEl.innerText || '').toLowerCase();
                if (
                    headerText.includes('thành viên') ||
                    headerText.includes('members') ||
                    headerEl.querySelector('.fa-group, [class*="member"], [class*="group"]')
                ) {
                    isGroup = true;
                }
            }

            // 4. Inspect message cards in active conversation
            const msgNodes = Array.from(
                document.querySelectorAll('#messageViewContainer .card, .message-view .card, [data-id^="div_ReceivedMsg"], [data-id^="div_SentMsg"], .chat-message')
            );

            let lastIncoming = null;
            for (let i = msgNodes.length - 1; i >= 0; i--) {
                const node = msgNodes[i];
                const cls = (node.className || '') + ' ' + (node.parentElement ? node.parentElement.className : '');
                const dataId = node.getAttribute('data-id') || '';

                // Skip outgoing messages from 'me'
                const isMe = cls.split(/\\s+/).includes('me') || dataId.includes('SentMsg') || !!node.closest('.me');
                if (isMe) {
                    continue;
                }

                // Extract message text
                const textEl = node.querySelector('.text, .card--text, [data-component="text-container"], .msg-content');
                const rawText = textEl ? textEl.innerText.trim() : (node.innerText || '').trim();
                if (!rawText) {
                    continue;
                }

                // Extract sender name in group chat
                let senderName = chatName || 'Người gửi';
                const senderEl = node.querySelector('.card-sender-name, .sender-name, [class*="sender-name"]');
                if (senderEl && senderEl.innerText.trim()) {
                    senderName = senderEl.innerText.trim();
                    isGroup = true;
                } else {
                    // Check avatar title near message
                    const msgAvatar = node.parentElement ? node.parentElement.querySelector('.zavatar [title], .zavatar img[alt]') : null;
                    if (msgAvatar) {
                        const avName = msgAvatar.getAttribute('title') || msgAvatar.getAttribute('alt');
                        if (avName && avName.trim()) {
                            senderName = avName.trim();
                        }
                    }
                }

                // Check if message contains a DOM @mention highlight
                const mentionEl = node.querySelector('.text-is-mention, a.mention, [class*="mention"], span[data-mention]');
                const domMentioned = !!mentionEl || rawText.includes('@');

                const msgId = dataId || `${chatName || ''}|${senderName}|${rawText.slice(0, 120)}`;
                lastIncoming = {
                    msg_id: msgId,
                    sender_name: senderName,
                    text: rawText,
                    dom_mentioned: domMentioned
                };
                break;
            }

            return {
                logged_in: true,
                profile_name: profileName,
                chat_name: chatName,
                chat_type: isGroup ? 'group' : 'private',
                last_incoming: lastIncoming
            };
        }
        """
        return await self.page.evaluate(js_code)

    async def _click_next_unread_chat(self) -> Optional[str]:
        """Finds a conversation in the sidebar with an unread badge or @mention indicator and clicks it."""
        if not self.page or self.page.is_closed():
            return None

        js_click_unread = """
        () => {
            const items = Array.from(document.querySelectorAll('.msg-item, .conv-item, [id^="friend-item-"]'));
            for (const item of items) {
                const unreadBadge = item.querySelector(
                    '.conv-action__unread, .conv-Unread, [class*="unread"], .fa-num, .z-noti-badge, [class*="mention"]'
                );
                if (unreadBadge) {
                    const nameEl = item.querySelector('.conv-item-title__name, .truncate, .title');
                    const name = nameEl ? nameEl.innerText.trim() : 'Cuộc trò chuyện mới';
                    item.click();
                    return name;
                }
            }
            return null;
        }
        """
        try:
            return await self.page.evaluate(js_click_unread)
        except Exception:
            return None

    async def _process_active_chat(self, state: Dict[str, Any], cfg: Dict[str, Any]):
        chat_name = state.get("chat_name")
        last_incoming = state.get("last_incoming")
        if not chat_name or not last_incoming:
            return

        msg_id = last_incoming.get("msg_id")
        signature = f"{chat_name}::{msg_id}"

        # When first opening a conversation that hasn't been seen yet, if the message was already sitting there
        # before the bot started, only process if it hasn't been processed yet.
        if signature in self.processed_messages:
            return

        self.processed_messages.add(signature)
        self.stats["messages_scanned"] += 1

        sender_name = last_incoming.get("sender_name") or chat_name
        message_text = last_incoming.get("text") or ""
        dom_mentioned = bool(last_incoming.get("dom_mentioned", False))
        chat_type = state.get("chat_type", "private")

        # Also include detected profile name in tag names dynamically if available
        settings = cfg.get("settings", {})
        if self.detected_profile_name:
            tag_list = list(settings.get("my_tag_names", []))
            if f"@{self.detected_profile_name}" not in tag_list:
                tag_list.append(f"@{self.detected_profile_name}")
            cfg_copy = dict(cfg)
            cfg_copy["settings"] = dict(settings, my_tag_names=tag_list)
        else:
            cfg_copy = cfg

        eval_result = evaluate_message(
            config=cfg_copy,
            chat_name=chat_name,
            sender_name=sender_name,
            chat_type=chat_type,
            message_text=message_text,
            dom_mentioned=dom_mentioned
        )

        if not eval_result["matched"]:
            self.add_log(
                "info",
                f"Bỏ qua tin nhắn từ [{chat_name}] ({sender_name})",
                f"Nội dung: \"{message_text[:80]}\" — Lý do: {eval_result['reason']}",
                meta={"chat_name": chat_name, "sender": sender_name, "chat_type": eval_result["effective_chat_type"]}
            )
            return

        # Check cooldown per conversation
        cooldown_sec = float(settings.get("cooldown_sec", 15))
        now_ts = time.time()
        last_ts = self.last_reply_ts_by_chat.get(chat_name, 0.0)
        if now_ts - last_ts < cooldown_sec:
            remaining = int(cooldown_sec - (now_ts - last_ts))
            self.add_log(
                "warning",
                f"Đang trong thời gian chờ chống spam cho [{chat_name}] (còn {remaining}s)",
                f"Tin nhắn từ {sender_name}: \"{message_text[:80]}\""
            )
            return

        self.stats["rules_matched"] += 1
        reply_text = eval_result["reply_text"]
        matched_rule = eval_result["matched_rule"]

        # Random human delay
        delay_min = float(settings.get("delay_min_sec", 2.0))
        delay_max = float(settings.get("delay_max_sec", 5.0))
        if delay_max < delay_min:
            delay_max = delay_min
        wait_sec = round(random.uniform(delay_min, delay_max), 1)

        self.add_log(
            "info",
            f"Khớp kịch bản: {matched_rule.get('name')} — Đang chờ {wait_sec}s như người thật...",
            f"[{chat_name}] {sender_name}: \"{message_text[:90]}\""
        )

        await asyncio.sleep(wait_sec)

        # Send reply into Zalo Web input box
        sent_ok = await self._send_zalo_reply(
            reply_text=reply_text,
            typing_simulation=bool(settings.get("typing_simulation", True))
        )
        if sent_ok:
            self.last_reply_ts_by_chat[chat_name] = time.time()
            self.stats["replies_sent"] += 1
            self.add_log(
                "success",
                f"Đã tự động trả lời [{chat_name}] ({sender_name})",
                f"Nội dung gửi: \"{reply_text}\"",
                meta={
                    "rule_name": matched_rule.get("name"),
                    "chat_name": chat_name,
                    "sender": sender_name,
                    "delay_sec": wait_sec
                }
            )
        else:
            self.add_log(
                "error",
                f"Không tìm thấy ô nhập tin nhắn cho [{chat_name}]",
                "Hãy đảm bảo cửa sổ trò chuyện đang mở trên Zalo Web."
            )

    async def _send_zalo_reply(self, reply_text: str, typing_simulation: bool = True) -> bool:
        if not self.page or self.page.is_closed():
            return False

        input_selectors = [
            "#richInput",
            "#input_line_0",
            '[contenteditable="true"].rich-input',
            '#chat-input-container [contenteditable="true"]',
            '[contenteditable="true"]'
        ]

        for selector in input_selectors:
            try:
                locator = self.page.locator(selector).first
                if await locator.count() > 0 and await locator.is_visible():
                    await locator.click()
                    if typing_simulation:
                        # Type with slight human cadence (15-35ms per char, capped for long messages)
                        char_delay = 18 if len(reply_text) < 120 else 8
                        await locator.press_sequentially(reply_text, delay=char_delay)
                    else:
                        await locator.fill(reply_text)
                    await asyncio.sleep(0.25)
                    await self.page.keyboard.press("Enter")
                    return True
            except Exception:
                continue
        return False
