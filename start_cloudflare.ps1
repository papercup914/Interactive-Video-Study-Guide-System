[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "🚀 스터디 가이드 생성기 - 외부 공개 터널링 (Cloudflare)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[필수 조건]" -ForegroundColor Yellow
Write-Host "1. 백엔드가 실행 중이어야 합니다. (포트 8000)"
Write-Host "2. 프론트엔드가 실행 중이어야 합니다. (포트 3000)"
Write-Host ""

$exePath = ".\cloudflared.exe"
if (-Not (Test-Path -Path $exePath)) {
    Write-Host "초기 설정: Cloudflared 터널링 프로그램을 다운로드합니다. (약 30MB, 최초 1회만)" -ForegroundColor Yellow
    Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile $exePath
    Write-Host "다운로드 완료!" -ForegroundColor Green
    Write-Host ""
}

Write-Host "※ 실행 후 로그 중에서 'https://~~~~~~.trycloudflare.com' 처럼 생긴 주소를 찾아 지인에게 공유하세요!" -ForegroundColor Green
Write-Host "※ 경고 화면(IP 확인창) 없이 곧바로 접속됩니다." -ForegroundColor Green
Write-Host ""
Write-Host "터널링을 시작합니다... (종료하려면 Ctrl+C)" -ForegroundColor Cyan
Write-Host "※ .env 파일에 TELEGRAM_BOT_TOKEN 및 TELEGRAM_CHAT_ID를 설정하면 모바일로 자동 공유됩니다." -ForegroundColor Yellow
Write-Host ""

# .env 파일 로드 (루트 폴더)
if (Test-Path ".env") {
    foreach ($line in Get-Content ".env") {
        if ($line -match "^([^#\s]+?)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim())
        }
    }
}

$botToken = [Environment]::GetEnvironmentVariable("TELEGRAM_BOT_TOKEN")
$chatId = [Environment]::GetEnvironmentVariable("TELEGRAM_CHAT_ID")
$urlSent = $false

# cloudflared의 오류 출력(stderr)을 표준 출력(stdout)으로 합쳐서 한 줄씩 가로채기
& .\cloudflared.exe tunnel --url http://localhost:3000 --http-host-header "localhost" 2>&1 | ForEach-Object {
    $line = $_.ToString()
    Write-Host $line
    
    if (-not $urlSent -and $line -match "(https://[a-zA-Z0-9-]+\.trycloudflare\.com)") {
        $url = $matches[1]
        $urlSent = $true
        Write-Host "`n[성공] URL 획득 완료: $url" -ForegroundColor Green
        
        if ($botToken -and $chatId) {
            Write-Host "텔레그램으로 링크를 전송하는 중..." -ForegroundColor Cyan
            $message = "🚀 스터디 가이드 서버가 열렸습니다!`n`n🔗 접속 주소: $url"
            $telegramApiUrl = "https://api.telegram.org/bot$botToken/sendMessage"
            $body = @{
                chat_id = $chatId
                text = $message
            }
            try {
                Invoke-RestMethod -Uri $telegramApiUrl -Method Post -Body $body | Out-Null
                Write-Host "✅ 텔레그램 전송 완료! 휴대폰을 확인하세요." -ForegroundColor Green
            } catch {
                Write-Host "❌ 텔레그램 전송 실패: $_" -ForegroundColor Red
            }
        }
    }
}
