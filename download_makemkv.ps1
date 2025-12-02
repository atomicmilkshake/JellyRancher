Invoke-WebRequest -Uri "https://www.makemkv.com/download/Setup_MakeMKV_v1.18.2.exe" -OutFile "$env:TEMP\Setup_MakeMKV_v1.18.2.exe"
Start-Process -FilePath "$env:TEMP\Setup_MakeMKV_v1.18.2.exe" -Wait