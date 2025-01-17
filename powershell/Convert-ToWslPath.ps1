param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$WindowsPath
)

# Convert backslashes to forward slashes
$WslPath = $WindowsPath -replace "\\", "/"

# Extract drive letter, convert to lowercase, and reconstruct path
if ($WslPath -match "^([A-Za-z]):") {
    $driveLetter = $matches[1].ToLower()
    $WslPath = "/" + $driveLetter + ($WslPath -replace "^[A-Za-z]:")
}

# Add quotes if the path contains spaces
if ($WslPath -match "\s") {
    $WslPath = "`"$WslPath`""
}

# Output the converted path
Write-Output $WslPath