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
Write-Host ""

.\cloudflared.exe tunnel --url http://localhost:3000 --http-host-header "localhost"
