import asyncio
import re
import socket
import subprocess
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config_store import ConfigStore
from rule_engine import evaluate_message
from zalo_bot import ZaloBotManager

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
BIN_DIR = BASE_DIR / "bin"
CLOUDFLARED_PATH = BIN_DIR / "cloudflared.exe"
STATIC_DIR.mkdir(parents=True, exist_ok=True)


def get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class TunnelManager:
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.public_url: Optional[str] = None
        self.status: str = "stopped"
        self._lock = threading.Lock()

    def start(self, port: int = 8000):
        with self._lock:
            if self.process and self.process.poll() is None and self.public_url:
                return
            self.stop()
            if not CLOUDFLARED_PATH.exists():
                self.status = "missing_binary"
                return

            self.status = "starting"
            self.public_url = None
            try:
                self.process = subprocess.Popen(
                    [
                        str(CLOUDFLARED_PATH),
                        "tunnel",
                        "--url",
                        f"http://127.0.0.1:{port}",
                        "--no-autoupdate"
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
                )
                t = threading.Thread(target=self._read_output, daemon=True)
                t.start()
            except Exception as e:
                self.status = f"error: {e}"

    def _read_output(self):
        if not self.process or not self.process.stdout:
            return
        url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
        for line in self.process.stdout:
            match = url_pattern.search(line)
            if match:
                self.public_url = match.group(0)
                self.status = "running"

    def stop(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
            except Exception:
                pass
        self.process = None
        self.public_url = None
        self.status = "stopped"

    def get_info(self, port: int = 8000) -> Dict[str, Any]:
        lan_ip = get_lan_ip()
        running = bool(self.process and self.process.poll() is None)
        if not running and self.status == "running":
            self.status = "stopped"
        return {
            "lan_ip": lan_ip,
            "lan_url": f"http://{lan_ip}:{port}",
            "public_url": self.public_url,
            "tunnel_status": self.status,
            "tunnel_running": running
        }


config_store = ConfigStore()
bot_manager = ZaloBotManager(config_store)
tunnel_manager = TunnelManager()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    tunnel_manager.start(8000)
    yield
    tunnel_manager.stop()


app = FastAPI(title="Zalo Auto-Reply Dashboard", lifespan=lifespan)


class SettingsPayload(BaseModel):
    bot_enabled: Optional[bool] = None
    my_tag_names: Optional[List[str]] = None
    group_require_tag: Optional[bool] = None
    private_require_tag: Optional[bool] = None
    delay_min_sec: Optional[float] = None
    delay_max_sec: Optional[float] = None
    cooldown_sec: Optional[int] = None
    auto_open_unread: Optional[bool] = None
    typing_simulation: Optional[bool] = None


class RulePayload(BaseModel):
    id: Optional[str] = None
    name: str
    enabled: bool = True
    priority: int = 50
    scope_type: str = "all"  # "all" | "group" | "private" | "specific"
    target_names: List[str] = []
    require_tag_override: str = "default"  # "default" | "always" | "never"
    match_type: str = "contains"  # "contains" | "exact" | "regex" | "all"
    keywords: List[str] = []
    reply_templates: List[str] = []


class TargetControlPayload(BaseModel):
    id: Optional[str] = None
    name: str
    chat_type: str = "group"  # "group" | "private"
    enabled: bool = True
    note: str = ""


class SimulatePayload(BaseModel):
    chat_name: str
    sender_name: str
    chat_type: str = "group"  # "group" | "private"
    message_text: str
    dom_mentioned: bool = False


@app.get("/")
async def index():
    return FileResponse(
        STATIC_DIR / "index.html",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"}
    )


@app.get("/api/state")
async def get_state():
    cfg = config_store.load()
    return {
        "status": bot_manager.get_status(),
        "config": cfg,
        "logs": bot_manager.logs[:100],
        "share": tunnel_manager.get_info(8000)
    }


@app.get("/api/share")
async def get_share_info():
    return tunnel_manager.get_info(8000)


@app.post("/api/share/restart")
async def restart_share_tunnel():
    tunnel_manager.stop()
    tunnel_manager.start(8000)
    await asyncio.sleep(2.5)
    return tunnel_manager.get_info(8000)


@app.post("/api/browser/launch")
async def launch_browser():
    status = await bot_manager.launch_browser()
    return {"status": status}


@app.post("/api/browser/close")
async def close_browser():
    status = await bot_manager.close_browser()
    return {"status": status}


@app.get("/api/browser/screenshot")
async def browser_screenshot():
    img = await bot_manager.get_screenshot_base64()
    return {
        "image": img,
        "status": bot_manager.get_status()
    }


@app.post("/api/browser/reload")
async def browser_reload():
    if bot_manager.page and not bot_manager.page.is_closed():
        try:
            await bot_manager.page.reload(wait_until="domcontentloaded", timeout=30000)
            bot_manager.add_log("info", "Đã tải lại trang Zalo Web để lấy mã QR mới.")
        except Exception as e:
            bot_manager.add_log("error", "Lỗi khi tải lại Zalo Web", str(e))
    return {"status": bot_manager.get_status()}


@app.post("/api/settings")
async def update_settings(payload: SettingsPayload):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updated = config_store.update_settings(updates)
    if "bot_enabled" in updates:
        state_str = "BẬT" if updates["bot_enabled"] else "TẮT"
        bot_manager.add_log("info", f"Đã {state_str} chế độ Tự động trả lời Zalo.")
    return {"settings": updated, "status": bot_manager.get_status()}


@app.post("/api/rules")
async def save_rule(payload: RulePayload):
    rule = config_store.upsert_rule(payload.model_dump())
    bot_manager.add_log("info", f"Đã lưu kịch bản: {rule.get('name')}")
    return {"rule": rule, "rules": config_store.load().get("rules", [])}


@app.delete("/api/rules/{rule_id}")
async def delete_rule(rule_id: str):
    ok = config_store.delete_rule(rule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Không tìm thấy kịch bản")
    bot_manager.add_log("warning", f"Đã xóa kịch bản ID: {rule_id}")
    return {"rules": config_store.load().get("rules", [])}


@app.post("/api/targets")
async def save_target(payload: TargetControlPayload):
    tc = config_store.upsert_target_control(payload.model_dump())
    bot_manager.add_log("info", f"Đã cập nhật cấu hình Người/Nhóm: {tc.get('name')}")
    return {"target": tc, "target_controls": config_store.load().get("target_controls", [])}


@app.delete("/api/targets/{tc_id}")
async def delete_target(tc_id: str):
    ok = config_store.delete_target_control(tc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Không tìm thấy mục")
    return {"target_controls": config_store.load().get("target_controls", [])}


@app.post("/api/simulate")
async def simulate_message(payload: SimulatePayload):
    cfg = config_store.load()
    result = evaluate_message(
        config=cfg,
        chat_name=payload.chat_name,
        sender_name=payload.sender_name,
        chat_type=payload.chat_type,
        message_text=payload.message_text,
        dom_mentioned=payload.dom_mentioned
    )
    settings = cfg.get("settings", {})
    return {
        "result": result,
        "delay_range": f"{settings.get('delay_min_sec', 2.0)}s - {settings.get('delay_max_sec', 5.0)}s"
    }


@app.post("/api/logs/clear")
async def clear_logs():
    bot_manager.logs.clear()
    return {"logs": []}


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
