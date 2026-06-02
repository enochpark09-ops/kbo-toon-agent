# ⚾ KBO 4컷 만화 에이전트

KBO 구단 마스코트 누끼 이미지를 활용해 **4컷 웹툰을 자동 생성·배포**하는 Vercel 앱입니다.

---

## 📁 프로젝트 구조

```
KBO-TOON-AGENT/
├── public/
│   ├── asset/              ← 마스코트 누끼 PNG (Team Kia/1.png 형식)
│   └── output/             ← 생성된 만화 저장 위치
├── api/
│   └── generate.py         ← Vercel Serverless API (Python)
├── index.html              ← 사용자 인터페이스
├── requirements.txt        ← Python 의존성
├── vercel.json             ← Vercel 라우팅 설정
└── .gitignore
```

---

## 🚀 배포 방법

### 1. 누끼 이미지 준비
`public/asset/` 아래에 팀 폴더를 만들고 `1.png ~ 21.png` 파일을 넣으세요.
```
public/asset/
├── Team Kia/       1.png ~ 21.png
├── Team Hanwha/    1.png ~ 21.png
...
└── Team LG/        1.png ~ 21.png
```

### 2. GitHub 리포지토리 생성 후 푸시
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/KBO-TOON-AGENT.git
git push -u origin main
```

### 3. Vercel 연결
1. [vercel.com](https://vercel.com) → **Import Project** → GitHub 리포 선택
2. Framework Preset: **Other**
3. **Environment Variables** 설정:

| 키 | 값 |
|---|---|
| `GITHUB_TOKEN` | GitHub Personal Access Token (repo 권한) |
| `REPO_OWNER`   | GitHub 유저명 |
| `REPO_NAME`    | `KBO-TOON-AGENT` |

4. **Deploy** 클릭

---

## 🎨 사용 방법

1. 배포된 URL 접속
2. 4컷 각각에 대해 **홈팀 / 원정팀 구단 선택** + **표정 번호** + **대사** 입력
3. **🔥 오늘자 만화 배포하기** 클릭
4. 생성된 800×3200 JPEG 만화가 GitHub에 자동 푸시되어 Vercel에 반영

---

## 📌 표정 번호 가이드

| 번호 | 동작 | 번호 | 동작 |
|------|------|------|------|
| 1 | 승리 | 11 | 질주 |
| 2 | 패배 | 12 | 홈런 |
| 3 | 기쁨 | 13 | 다이빙 |
| 4 | 슬픔 | 14 | 응원 |
| 5 | 화남 | 15 | 작전 |
| 6 | 아픔 | 16 | 하이파이브 |
| 7 | 타자 | 17 | 집중 |
| 8 | 투수 | 18 | 당황 |
| 9 | 포수 | 19 | 파이팅 |
| 10 | 깃발 | 20 | 탈진 |
| 21 | 메인 | | |
