#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JARVIS Security Filter
- Input Validation (XSS, Command Injection 방지)
- Rate Limiting
- Authentication
- Logging
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Tuple
import hashlib

class SecurityFilter:
    """보안 필터링 클래스"""

    def __init__(self, max_requests_per_minute: int = 30):
        self.max_requests = max_requests_per_minute
        self.user_requests: Dict[int, list] = {}
        self.blocked_users = set()
        self.allowed_commands = {
            "pages", "status", "dashboard", "analytics", "teams", "operations",
            "uptime", "errors", "users", "report", "deploy", "mission", "help"
        }

    def validate_command(self, command: str) -> Tuple[bool, str]:
        """명령어 검증"""
        # 명령어 제거
        cmd = command.lstrip('/').strip()

        # 명령어 길이 체크
        if len(cmd) > 100:
            return False, "명령어가 너무 깁니다."

        # 허용된 명령어 확인
        base_cmd = cmd.split()[0].lower()
        if base_cmd not in self.allowed_commands:
            return False, f"알 수 없는 명령어: {base_cmd}"

        return True, "OK"

    def validate_input(self, text: str, max_length: int = 500) -> Tuple[bool, str]:
        """입력값 검증"""
        if not text:
            return False, "입력이 비어있습니다."

        if len(text) > max_length:
            return False, f"입력이 너무 깁니다. (최대 {max_length} 글자)"

        # XSS 필터링
        dangerous_chars = ["<", ">", "\"", "'", ";", "&", "|", "`", "$"]
        for char in dangerous_chars:
            if char in text:
                return False, f"허용되지 않는 문자가 포함되어 있습니다: {char}"

        # SQL Injection 패턴 필터링
        sql_patterns = [
            r"(?i)(union|select|insert|update|delete|drop|create|alter|exec|execute)",
            r"(?i)(--|#|/\*|\*/)",
        ]
        for pattern in sql_patterns:
            if re.search(pattern, text):
                return False, "의심스러운 입력 패턴이 감지되었습니다."

        return True, "OK"

    def validate_deploy_args(self, env: str, version: str) -> Tuple[bool, str]:
        """배포 명령어 인자 검증"""
        # Environment 검증
        valid_envs = ["prod", "production", "staging", "dev", "development"]
        if env.lower() not in valid_envs:
            return False, f"유효한 환경: {', '.join(valid_envs)}"

        # Version 검증 (semantic versioning)
        if not re.match(r"^v?\d+\.\d+\.\d+$", version):
            return False, "버전 형식: v1.2.3"

        return True, "OK"

    def validate_mission_name(self, name: str) -> Tuple[bool, str]:
        """미션 이름 검증"""
        # 길이 체크
        if len(name) < 3 or len(name) > 100:
            return False, "미션 이름은 3-100 글자여야 합니다."

        # 특수문자 제거
        if not re.match(r"^[\w\s\-_가-힣]+$", name):
            return False, "미션 이름에는 영문, 숫자, 한글, 하이픈만 가능합니다."

        return True, "OK"

    def check_rate_limit(self, user_id: int) -> Tuple[bool, str]:
        """Rate Limiting 체크"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)

        # 사용자의 요청 히스토리 정리
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []

        # 1분 이내의 요청만 유지
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if req_time > minute_ago
        ]

        # Rate limit 체크
        if len(self.user_requests[user_id]) >= self.max_requests:
            return False, f"요청이 너무 많습니다. (최대 {self.max_requests}/분)"

        # 요청 기록
        self.user_requests[user_id].append(now)
        return True, "OK"

    def is_user_blocked(self, user_id: int) -> bool:
        """사용자 차단 여부 체크"""
        return user_id in self.blocked_users

    def block_user(self, user_id: int):
        """사용자 차단"""
        self.blocked_users.add(user_id)

    def sanitize_output(self, text: str) -> str:
        """출력 샘니타이징"""
        # 이미 마크다운은 안전하지만, 극단적인 포맷만 제거
        return text[:1000]  # 최대 1000글자 제한

    def log_security_event(self, event_type: str, user_id: int, details: str):
        """보안 이벤트 로깅"""
        timestamp = datetime.now().isoformat()
        log_msg = f"[{timestamp}] {event_type} | User: {user_id} | Details: {details}"
        print(f"[SECURITY] {log_msg}")


class RequestLogger:
    """요청 로깅"""

    def __init__(self):
        self.logs = []

    def log_request(self, user_id: int, command: str, status: str):
        """요청 로깅"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "command": command,
            "status": status
        }
        self.logs.append(log_entry)

    def get_recent_logs(self, count: int = 10) -> list:
        """최근 로그 조회"""
        return self.logs[-count:]


# 전역 인스턴스
security_filter = SecurityFilter(max_requests_per_minute=30)
request_logger = RequestLogger()
