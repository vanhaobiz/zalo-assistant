import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CONFIG_PATH = DATA_DIR / "config.json"


DEFAULT_CONFIG: Dict[str, Any] = {
    "settings": {
        "bot_enabled": False,
        "my_tag_names": ["@TênCủaBạn", "@Minh"],
        "group_require_tag": True,
        "private_require_tag": False,
        "delay_min_sec": 2.0,
        "delay_max_sec": 5.5,
        "cooldown_sec": 15,
        "auto_open_unread": True,
        "typing_simulation": True
    },
    "target_controls": [
        {
            "id": "tc-1",
            "name": "Nhóm Dự Án Công Ty",
            "chat_type": "group",
            "enabled": True,
            "note": "Nhóm công việc chính - chỉ trả lời khi được tag @"
        },
        {
            "id": "tc-2",
            "name": "Sếp Tuấn",
            "chat_type": "private",
            "enabled": True,
            "note": "Tin nhắn riêng của sếp"
        },
        {
            "id": "tc-3",
            "name": "Nhóm Gia Đình",
            "chat_type": "group",
            "enabled": False,
            "note": "Tắt trả lời tự động cho nhóm gia đình"
        }
    ],
    "rules": [
        {
            "id": "rule-1",
            "name": "Kịch bản riêng cho Sếp Tuấn (Khi nhắn công việc/báo cáo)",
            "enabled": True,
            "priority": 100,
            "scope_type": "specific",
            "target_names": ["Sếp Tuấn"],
            "require_tag_override": "default",
            "match_type": "contains",
            "keywords": ["báo cáo", "tiến độ", "xong chưa", "họp", "gấp"],
            "reply_templates": [
                "Dạ em đã nhận được tin nhắn của {sender} lúc {time}. Em đang tổng hợp lại số liệu và sẽ gửi báo cáo chi tiết trong ít phút nữa ạ!",
                "Dạ vâng ạ, em đang xử lý phần việc này rồi ạ, lát nữa xong em báo {sender} ngay nhé!"
            ]
        },
        {
            "id": "rule-2",
            "name": "Nhóm Dự Án - Khi được tag hỏi tiến độ / hỗ trợ",
            "enabled": True,
            "priority": 90,
            "scope_type": "specific",
            "target_names": ["Nhóm Dự Án Công Ty"],
            "require_tag_override": "always",
            "match_type": "contains",
            "keywords": ["hỗ trợ", "check", "kiểm tra", "tiến độ", "lỗi", "bug", "review"],
            "reply_templates": [
                "Chào {sender}, mình đã thấy thông báo tag trong {chat_name}. Mình đang kiểm tra vấn đề này và sẽ phản hồi lại ngay nhé!",
                "Ok {sender} nhé, để mình check lại nội dung này trên hệ thống rồi báo lại vào nhóm {chat_name} nha."
            ]
        },
        {
            "id": "rule-3",
            "name": "Báo giá & Tư vấn dịch vụ (Cho mọi tin nhắn riêng hoặc nhóm khi tag)",
            "enabled": True,
            "priority": 80,
            "scope_type": "all",
            "target_names": [],
            "require_tag_override": "default",
            "match_type": "contains",
            "keywords": ["báo giá", "bảng giá", "chi phí", "giá sao", "tư vấn"],
            "reply_templates": [
                "Chào {sender}! Cảm ơn bạn đã quan tâm. Hiện bên mình đang có bảng giá cập nhật mới nhất ngày {date}. Bạn vui lòng cho mình xin thêm nhu cầu cụ thể để mình gửi báo giá chi tiết nhé!",
                "Dạ chào {sender}, mình đã nhận được yêu cầu báo giá của bạn. Đợi mình một chút mình gửi file chi phí qua cho bạn xem nhé!"
            ]
        },
        {
            "id": "rule-4",
            "name": "Lịch họp / Lịch hẹn",
            "enabled": True,
            "priority": 70,
            "scope_type": "all",
            "target_names": [],
            "require_tag_override": "default",
            "match_type": "contains",
            "keywords": ["lịch họp", "mấy giờ họp", "link họp", "google meet", "zoom"],
            "reply_templates": [
                "Chào {sender}, mình đã ghi nhận thông tin về lịch họp lúc {time}. Mình sẽ tham gia đúng giờ nhé!"
            ]
        },
        {
            "id": "rule-5",
            "name": "Trả lời tự động TẤT CẢ Tin nhắn cá nhân (1-1) (Mọi nội dung)",
            "enabled": True,
            "priority": 20,
            "scope_type": "private",
            "target_names": [],
            "require_tag_override": "never",
            "match_type": "all",
            "keywords": [],
            "reply_templates": [
                "Chào {sender}, mình đã nhận được tin nhắn của bạn lúc {time}. Hiện mình đang bận chút việc, mình sẽ xem và phản hồi bạn ngay khi có thể nhé!",
                "Dạ chào {sender}, cảm ơn bạn đã nhắn tin. Mình sẽ kiểm tra nội dung và trả lời bạn sớm nhất nhé!"
            ]
        },
        {
            "id": "rule-6",
            "name": "Phản hồi mặc định khi được Tag @ trong bất kỳ Nhóm nào",
            "enabled": True,
            "priority": 10,
            "scope_type": "group",
            "target_names": [],
            "require_tag_override": "always",
            "match_type": "all",
            "keywords": [],
            "reply_templates": [
                "Chào {sender}, mình vừa nhận được lượt nhắc tên (@) của bạn trong nhóm {chat_name}. Hiện mình đang bận chút việc, mình sẽ xem và phản hồi bạn sớm nhất nhé!"
            ]
        }
    ]
}


class ConfigStore:
    def __init__(self, path: Path = CONFIG_PATH):
        self.path = path
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save(DEFAULT_CONFIG)

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            self.save(DEFAULT_CONFIG)
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Ensure top-level keys exist
            for k, v in DEFAULT_CONFIG.items():
                if k not in data:
                    data[k] = v
            return data
        except Exception:
            return json.loads(json.dumps(DEFAULT_CONFIG))

    def save(self, data: Dict[str, Any]) -> Dict[str, Any]:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return data

    def update_settings(self, new_settings: Dict[str, Any]) -> Dict[str, Any]:
        data = self.load()
        data["settings"].update(new_settings)
        self.save(data)
        return data["settings"]

    def upsert_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        data = self.load()
        rules: List[Dict[str, Any]] = data.get("rules", [])
        if not rule.get("id"):
            rule["id"] = f"rule-{uuid.uuid4().hex[:8]}"
        for idx, existing in enumerate(rules):
            if existing.get("id") == rule["id"]:
                rules[idx] = rule
                self.save(data)
                return rule
        rules.append(rule)
        data["rules"] = rules
        self.save(data)
        return rule

    def delete_rule(self, rule_id: str) -> bool:
        data = self.load()
        before = len(data.get("rules", []))
        data["rules"] = [r for r in data.get("rules", []) if r.get("id") != rule_id]
        self.save(data)
        return len(data["rules"]) < before

    def upsert_target_control(self, tc: Dict[str, Any]) -> Dict[str, Any]:
        data = self.load()
        controls: List[Dict[str, Any]] = data.get("target_controls", [])
        if not tc.get("id"):
            tc["id"] = f"tc-{uuid.uuid4().hex[:8]}"
        for idx, existing in enumerate(controls):
            if existing.get("id") == tc["id"] or (
                existing.get("name", "").strip().lower() == tc.get("name", "").strip().lower()
                and tc.get("name")
            ):
                tc["id"] = existing["id"]
                controls[idx] = tc
                self.save(data)
                return tc
        controls.append(tc)
        data["target_controls"] = controls
        self.save(data)
        return tc

    def delete_target_control(self, tc_id: str) -> bool:
        data = self.load()
        before = len(data.get("target_controls", []))
        data["target_controls"] = [
            c for c in data.get("target_controls", []) if c.get("id") != tc_id
        ]
        self.save(data)
        return len(data["target_controls"]) < before
