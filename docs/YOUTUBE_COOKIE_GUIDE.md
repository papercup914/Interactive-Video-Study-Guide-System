# 🍪 YouTube 봇 감지(Bot Detection) 우회를 위한 쿠키(cookies.txt) 설정 가이드

본 문서는 AWS EC2와 같은 클라우드 환경에서 유튜브 영상을 분석할 때 발생하는 **봇 감지(Sign in to confirm you are not a bot)** 현상을 100% 우회하기 위해 cookies.txt를 발급받고 서버에 등록하는 방법을 안내합니다.

---

## 📌 1. 봇 차단 원인 및 쿠키의 역할

- **원인**: 유튜브는 AWS, GCP 등의 데이터센터 IP 대역에서 대량의 요청이나 오디오 추출 요청이 발생하면 기계적인 접근(Bot)으로 간주하여 차단합니다.
- **해결책**: 일반 브라우저에서 로그인된 세션 쿠키(cookies.txt)를 백엔드에 제공하면, 유튜브 서버가 실제 인증된 사용자 요청으로 인식하여 봇 차단을 우회합니다.

> [!CAUTION]
> **보안 주의사항 (중요):**
> 1. 개인 금융, 이메일 등이 연동된 **본계정의 쿠키는 절대로 사용하지 마십시오.**
> 2. 가이드 생성 전용으로 사용할 **새로운 구글 서브 계정(부계정)**을 생성한 후 해당 계정의 쿠키를 추출하는 것을 강력히 권장합니다.
> 3. cookies.txt 파일은 .gitignore에 등록되어 GitHub에 커밋되지 않도록 안전하게 보호되고 있습니다.

---

## 🛠️ 2. 쿠키(cookies.txt) 추출 방법 (1분 소요)

### Step 1: 크롬/엣지 확장 프로그램 설치
1. 크롬 웹스토어에서 [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) 확장 프로그램을 설치합니다.
   *(오픈소스 기반으로 로컬에서만 쿠키를 텍스트로 추출해 주는 안전한 확장 프로그램입니다.)*

### Step 2: 유튜브 접속 및 부계정 로그인
1. 브라우저의 새 프로필 또는 시크릿 창에서 **유튜브(https://www.youtube.com)**에 접속합니다.
2. 새로 만든 **일회용 부계정**으로 로그인합니다.

### Step 3: 쿠키 내보내기 (Export)
1. 유튜브 홈 화면에서 브라우저 우측 상단의 Get cookies.txt LOCALLY 확장 프로그램 아이콘을 클릭합니다.
2. **Export** (또는 Copy) 버튼을 클릭하여 cookies.txt 파일을 다운로드하거나 내용을 복사합니다.

---

## 🚀 3. 서버(AWS EC2)에 쿠키 등록하기

쿠키를 등록하는 방법은 **두 가지**가 있습니다. 가장 편한 방법을 선택하세요.

### 방법 A. 파일로 등록 (가장 추천 ⭐️ - 실시간 적용)

`backend/data/` 디렉토리는 Docker 컨테이너에 실시간 볼륨 마운트되어 있으므로, 파일을 넣자마자 컨테이너 재시작 없이 즉시 적용됩니다.

1. **로컬 PC에서 EC2로 파일 전송 (SCP 사용 시):**
   ```bash
   scp -i "내키페어.pem" cookies.txt ubuntu@<EC2-IP>:~/Interactive-Video-Study-Guide-System/backend/data/cookies.txt
   ```
2. **또는 EC2 터미널에서 직접 생성:**
   ```bash
   cd ~/Interactive-Video-Study-Guide-System
   nano backend/data/cookies.txt
   ```
   *(복사한 쿠키 내용을 붙여넣은 뒤 `Ctrl + O` ➡️ `Enter` ➡️ `Ctrl + X`로 저장)*

---

### 방법 B. 환경변수(`backend/.env`)로 등록

1. EC2 터미널에서 `backend/.env`를 엽니다:
   ```bash
   nano backend/.env
   ```
2. 맨 아래에 복사한 쿠키 문자열을 한 줄로 입력합니다:
   ```env
   YOUTUBE_COOKIES_TEXT=.youtube.com TRUE / TRUE 1798765432 GPS 1 ...
   ```
3. 도커 컨테이너를 재기동합니다:
   ```bash
   docker compose restart fastapi celery_worker
   ```

---

## ✅ 4. 쿠키 정상 적용 여부 진단 (1초 검증)

서버 터미널에서 아래 명령어를 실행하여 쿠키가 정상 인식되는지 즉시 확인합니다:

```bash
python3 scripts/verify_cookies.py
```

**정상 출력 예시:**
```
============================================================
[YouTube cookies.txt 유효성 및 로더 진단 스크립트]
============================================================

1. 탐색 대상 쿠키 경로 목록:
   - backend/data/cookies.txt            : 🟢 [존재함] (4250 bytes)
   - /app/backend/data/cookies.txt       : ⚪ [없음]
   - backend/cookies.txt                 : ⚪ [없음]
   - ...

2. 최종 감지된 쿠키 파일:
   👉 🟢 감지 성공: backend/data/cookies.txt
   👉 로드된 세션 쿠키 개수: 12개
   ✅ 쿠키 파일 형식이 올바르며 정상적으로 로드되었습니다.
============================================================
```

👉 이제 자막이 없는 영상이나 고화질 롱폼 영상도 AWS IP 차단 없이 완벽하게 오디오 추출 및 AI 학습서 생성이 진행됩니다!
