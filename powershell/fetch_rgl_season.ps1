param (
    [Int]$IdFrom,
    [Int]$IdTo
)

# Define the range of seasons you want to loop through
for ($season = $IdFrom; $season -le $IdTo; $season++) {
    Write-Host "Fetching data for season $season..."
    
    # Write the season ID to the file first
    "Season ID: $season" | Out-File -FilePath "season_output.json" -Append -NoNewline
    
    try {
        # Run the Invoke-RestMethod command with the current season number
        $response = Invoke-RestMethod -Uri "https://api.rgl.gg/v0/seasons/$season" -Method GET -Headers @{accept = "*/*"} -ErrorAction Stop
        
        # Append the response to the output file
        $response | Out-File -FilePath "season_output.json" -Append
    }
    catch {
        # Handle 404 or other errors
        if ($_.Exception.Response.StatusCode.value__ -eq 404) {
            "Error: Season $season not found (404)" | Out-File -FilePath "season_output.json" -Append
        }
        else {
            "Error: $($_.Exception.Message)" | Out-File -FilePath "season_output.json" -Append
        }
    }
    
    # Add just a single separator line between seasons
    "----------------------------------------" | Out-File -FilePath "season_output.json" -Append
    
    # Optional: add a small delay between requests to be nice to the API
    Start-Sleep -Seconds 1
}
Write-Host "All seasons downloaded!"