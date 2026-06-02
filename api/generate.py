from http.server import BaseHTTPRequestHandler
import json
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import base64
import os
import textwrap

# ──────────────────────────────────────────
# 환경변수 (Vercel 대시보드에서 설정)
# ──────────────────────────────────────────
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO_OWNER   = os.environ.get("REPO_OWNER", "")
REPO_NAME    = os.environ.get("REPO_NAME", "KBO-TOON-AGENT")

# ──────────────────────────────────────────
# 상수
# ──────────────────────────────────────────
CUT_W, CUT_H     = 800, 800          # 1컷 캔버스 크기
CHAR_AREA_H      = 560               # 캐릭터 배치 영역 높이
BUBBLE_AREA_H    = 160               # 말풍선 영역 높이
SUMMARY_AREA_H   =  80               # 하단 요약 텍스트 높이
BG_COLOR         = (255, 255, 255)
SUMMARY_BG       = (30,  30,  30)
SUMMARY_FG       = (255, 255, 255)
BORDER_COLOR     = (220, 220, 220)
BUBBLE_COLOR     = (255, 255, 255)
BUBBLE_BORDER    = (50,  50,  50)
LEFT_TINT        = (230, 240, 255)   # 왼쪽 캐릭터 배경 틴트
RIGHT_TINT       = (255, 235, 230)   # 오른쪽 캐릭터 배경 틴트

# 구단 한글명 매핑
TEAM_KR = {
    "Team Kia":    "KIA 타이거즈",
    "Team Hanwha": "한화 이글스",
    "Team Lotte":  "롯데 자이언츠",
    "Team Samsung":"삼성 라이온즈",
    "Team Kiwoom": "키움 히어로즈",
    "Team NC":     "NC 다이노스",
    "Team SSG":    "SSG 랜더스",
    "Team KT":     "KT 위즈",
    "Team Doosan": "두산 베어스",
    "Team LG":     "LG 트윈스",
}

# ──────────────────────────────────────────
# 폰트 로딩 (Vercel 환경 대응)
# ──────────────────────────────────────────
def get_font(size):
    candidates = [
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

# ──────────────────────────────────────────
# 캐릭터 이미지 로딩
# ──────────────────────────────────────────
def load_character(team: str, num: int) -> Image.Image | None:
    """
    public/asset/{team}/{num}.png 를 RGBA로 읽어 반환.
    Vercel 환경에서는 /var/task/public/asset/ 경로 사용.
    """
    base_dirs = [
        os.path.join(os.path.dirname(__file__), "..", "public", "asset"),
        "/var/task/public/asset",
    ]
    for base in base_dirs:
        path = os.path.join(base, team, f"{num}.png")
        if os.path.exists(path):
            return Image.open(path).convert("RGBA")
    return None

# ──────────────────────────────────────────
# 말풍선 그리기
# ──────────────────────────────────────────
def draw_speech_bubble(draw: ImageDraw.ImageDraw,
                        text: str,
                        box: tuple,          # (x1,y1,x2,y2)
                        tail_x: int,
                        tail_dir: str = "left",  # "left" | "right"
                        font=None):
    x1, y1, x2, y2 = box
    r = 18
    # 둥근 사각형
    draw.rounded_rectangle([x1, y1, x2, y2], radius=r,
                            fill=BUBBLE_COLOR, outline=BUBBLE_BORDER, width=2)
    # 꼬리 삼각형
    tail_y = y2 - 4
    if tail_dir == "left":
        tail_pts = [(tail_x, tail_y+20), (tail_x+12, tail_y), (tail_x+28, tail_y)]
    else:
        tail_pts = [(tail_x, tail_y+20), (tail_x-12, tail_y), (tail_x-28, tail_y)]
    draw.polygon(tail_pts, fill=BUBBLE_COLOR, outline=BUBBLE_BORDER)

    # 텍스트 줄바꿈
    max_chars = 16
    lines = textwrap.wrap(text, width=max_chars)[:3]
    line_h = (font.size if hasattr(font, 'size') else 16) + 4
    total_text_h = len(lines) * line_h
    start_y = y1 + ((y2 - y1) - total_text_h) // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        tx = x1 + ((x2 - x1) - tw) // 2
        ty = start_y + i * line_h
        draw.text((tx, ty), line, fill=(20, 20, 20), font=font)

# ──────────────────────────────────────────
# 단일 컷 생성 (핵심 함수)
# ──────────────────────────────────────────
def draw_premium_cut(story: dict) -> Image.Image:
    """
    story = {
        "left_team":  "Team Hanwha",
        "left_num":   2,
        "left_text":  "오늘은 우리가 이긴다!",
        "right_team": "Team Kia",
        "right_num":  1,
        "right_text": "어림없지!",
        "summary":    "▶ 1컷: 기선제압"
    }
    """
    canvas = Image.new("RGBA", (CUT_W, CUT_H), BG_COLOR + (255,))
    draw   = ImageDraw.Draw(canvas)

    font_bubble  = get_font(22)
    font_summary = get_font(20)
    font_label   = get_font(16)

    # ── 배경 틴트 (좌/우 구분) ──
    left_bg  = Image.new("RGBA", (CUT_W // 2, CHAR_AREA_H), LEFT_TINT  + (180,))
    right_bg = Image.new("RGBA", (CUT_W // 2, CHAR_AREA_H), RIGHT_TINT + (180,))
    canvas.paste(left_bg,  (0,       0), left_bg)
    canvas.paste(right_bg, (CUT_W//2, 0), right_bg)

    # ── 구단 라벨 ──
    left_label  = TEAM_KR.get(story.get("left_team",  ""), story.get("left_team",  ""))
    right_label = TEAM_KR.get(story.get("right_team", ""), story.get("right_team", ""))

    lb_bbox = draw.textbbox((0,0), left_label, font=font_label)
    rb_bbox = draw.textbbox((0,0), right_label, font=font_label)
    draw.text((10, 6), left_label,  fill=(60, 60, 160), font=font_label)
    draw.text((CUT_W - rb_bbox[2] - rb_bbox[0] - 10, 6),
              right_label, fill=(160, 60, 60), font=font_label)

    # ── 구분선 ──
    draw.line([(CUT_W//2, 0), (CUT_W//2, CHAR_AREA_H)],
              fill=(180, 180, 180), width=2)

    # ── 캐릭터 배치 ──
    char_y_base = CHAR_AREA_H    # 발바닥 기준 y
    max_char_h  = CHAR_AREA_H - 30

    for side in ("left", "right"):
        team = story.get(f"{side}_team", "")
        num  = story.get(f"{side}_num",  1)
        char = load_character(team, num)

        if char is None:
            # 캐릭터 없을 때 플레이스홀더
            ph_x = 80 if side == "left" else CUT_W//2 + 80
            draw.rectangle([ph_x, 80, ph_x+180, 300], outline=(200,200,200), width=2)
            draw.text((ph_x+20, 170), f"{team}\n#{num}", fill=(150,150,150), font=font_label)
            continue

        # 비율 유지 리사이즈
        cw, ch = char.size
        scale  = min((CUT_W//2 - 40) / cw, max_char_h / ch)
        new_w  = int(cw * scale)
        new_h  = int(ch * scale)
        char   = char.resize((new_w, new_h), Image.LANCZOS)

        # 좌우 반전 (오른쪽 팀은 왼쪽 보도록)
        if side == "right":
            char = char.transpose(Image.FLIP_LEFT_RIGHT)

        # 중앙 하단 정렬
        if side == "left":
            cx = (CUT_W//2 - new_w) // 2
        else:
            cx = CUT_W//2 + (CUT_W//2 - new_w) // 2
        cy = char_y_base - new_h - 10

        canvas.paste(char, (cx, cy), char)

    # ── 말풍선 영역 ──
    bubble_top = CHAR_AREA_H
    bubble_bot = bubble_top + BUBBLE_AREA_H

    # 배경
    draw.rectangle([0, bubble_top, CUT_W, bubble_bot], fill=(245, 245, 245))
    draw.line([(0, bubble_top), (CUT_W, bubble_top)], fill=BORDER_COLOR, width=1)

    pad = 12
    # 왼쪽 말풍선
    draw_speech_bubble(
        draw,
        story.get("left_text", ""),
        (pad, bubble_top + pad, CUT_W//2 - pad, bubble_bot - pad - 20),
        tail_x = CUT_W//4,
        tail_dir = "left",
        font = font_bubble
    )
    # 오른쪽 말풍선
    draw_speech_bubble(
        draw,
        story.get("right_text", ""),
        (CUT_W//2 + pad, bubble_top + pad, CUT_W - pad, bubble_bot - pad - 20),
        tail_x = CUT_W*3//4,
        tail_dir = "right",
        font = font_bubble
    )

    # ── 하단 요약 텍스트 ──
    summary_top = bubble_bot
    draw.rectangle([0, summary_top, CUT_W, CUT_H], fill=SUMMARY_BG)
    summary = story.get("summary", "")
    sb = draw.textbbox((0,0), summary, font=font_summary)
    sw = sb[2] - sb[0]
    draw.text(((CUT_W - sw)//2, summary_top + (SUMMARY_AREA_H - (sb[3]-sb[1]))//2),
              summary, fill=SUMMARY_FG, font=font_summary)

    # ── 외곽 테두리 ──
    draw.rectangle([0, 0, CUT_W-1, CUT_H-1], outline=BORDER_COLOR, width=2)

    return canvas.convert("RGB")

# ──────────────────────────────────────────
# GitHub에 이미지 푸시
# ──────────────────────────────────────────
def push_to_github(img_bytes: bytes, filename: str = "kbo_today_webtoon.jpg") -> str:
    path    = f"public/output/{filename}"
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type":  "application/json",
    }

    # 기존 파일 sha 확인
    res = requests.get(api_url, headers=headers, timeout=10)
    sha = res.json().get("sha") if res.status_code == 200 else None

    payload = {
        "message": "🤖 에이전트: 오늘자 KBO 4컷 만화 자동 업데이트",
        "content": base64.b64encode(img_bytes).decode("utf-8"),
        "branch":  "main",
    }
    if sha:
        payload["sha"] = sha

    put_res = requests.put(api_url, data=json.dumps(payload), headers=headers, timeout=30)
    return put_res.status_code

# ──────────────────────────────────────────
# Vercel Serverless Handler
# ──────────────────────────────────────────
class handler(BaseHTTPRequestHandler):

    def _send_json(self, code: int, body: dict):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type",                  "application/json; charset=utf-8")
        self.send_header("Content-Length",                str(len(data)))
        self.send_header("Access-Control-Allow-Origin",   "*")
        self.send_header("Access-Control-Allow-Methods",  "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers",  "Content-Type")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self._send_json(200, {})

    def do_POST(self):
        try:
            length     = int(self.headers.get("Content-Length", 0))
            raw        = self.rfile.read(length)
            input_data = json.loads(raw.decode("utf-8"))   # list of 4 story dicts

            if not isinstance(input_data, list) or len(input_data) != 4:
                self._send_json(400, {"status": "error", "message": "4컷 데이터 배열이 필요합니다."})
                return

            # ── 4컷 생성 ──
            cuts = [draw_premium_cut(story) for story in input_data]

            # ── 세로 병합 (800 × 3200) ──
            webtoon = Image.new("RGB", (CUT_W, CUT_H * 4), BG_COLOR)
            for i, cut in enumerate(cuts):
                webtoon.paste(cut, (0, i * CUT_H))

            # ── JPEG 직렬화 ──
            buf = io.BytesIO()
            webtoon.save(buf, format="JPEG", quality=92)
            img_bytes = buf.getvalue()

            # ── GitHub 업로드 ──
            status_code = push_to_github(img_bytes)

            if status_code in (200, 201):
                pub_url = f"https://kbo-toon-agent.vercel.app/output/kbo_today_webtoon.jpg"
                self._send_json(200, {"status": "success", "url": pub_url})
            else:
                self._send_json(500, {"status": "error",
                                      "message": f"GitHub 푸시 실패 (HTTP {status_code})"})

        except Exception as e:
            self._send_json(500, {"status": "error", "message": str(e)})
