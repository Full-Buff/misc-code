param (
    [string]$FileName,
    [string]$Content
)

New-Item -ItemType File -Name $FileName
Set-Content -Path $FileName -Value $Content