# KBO 마스코트 4컷 만화 에이전트

마스코트 이미지를 등록하고 매일 스토리를 입력하면 Flux API로 4컷 만화를 자동 생성합니다.

## 파일 구조

```
kbo-comic-agent/
├── public/
│   └── index.html        ← 메인 PWA
├── api/
│   └── flux.js           ← Flux API 프록시 (Vercel serverless)
├── vercel.json
└── package.json
```

## Vercel 배포

```bash
# 1. Vercel CLI 설치
npm i -g vercel

# 2. 이 폴더에서 배포
cd kbo-comic-agent
vercel --prod

# Framework Preset: Other (중요!)
# Output Directory: public
```

## API 키 준비

### Flux API (필수 - 이미지 생성)
1. https://api.bfl.ml 가입
2. Dashboard → API Keys → 발급
3. 앱 설정 탭에 입력

### Claude API (선택 - 향후 자동화)
1. https://console.anthropic.com
2. API Keys 발급
3. 앱 설정 탭에 입력

## 사용 방법

### ① 마스코트 등록
- 10개 구단 카드 클릭
- 캐릭터 이름, 성격, 말버릇, 스타일 입력
- **이미지 업로드** (내가 만든 마스코트 이미지)
- 저장

### ② 스토리 입력
- 출연 마스코트 선택 (1~3명)
- 오늘의 스토리 자유 입력
- 분위기 + 배경 선택
- "4컷 만화 구성 생성" 클릭

### ③ 만화 결과
- 4컷 구성 자동 생성 (텍스트 + 마스코트 이미지 미리보기)
- "Flux로 4컷 이미지 생성" 클릭 → API가 각 컷 실제 이미지 생성
- 완성된 이미지가 패널에 자동 삽입

## Flux 프롬프트 구조

```
[스타일] Korean webtoon style, clean line art, vibrant colors
[캐릭터] {캐릭터명} ({비주얼 설명})
[장면] {컷 액션 설명}
[배경] {배경}
[기타] manga panel composition, no text, consistent character design
```

이미지를 업로드한 마스코트는 프롬프트에 "reference image provided" 가 포함됩니다.
(향후 Flux Redux/IP-Adapter로 업그레이드 시 실제 이미지 참조 가능)

## 향후 업그레이드

- [ ] Flux Redux로 캐릭터 일관성 강화
- [ ] Claude Vision으로 업로드 이미지 자동 분석
- [ ] 완성된 4컷 이미지 합성 (캔버스 API)
- [ ] X/인스타 자동 포스팅 연동
- [ ] 히스토리 클라우드 저장
