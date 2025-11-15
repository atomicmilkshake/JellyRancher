$body = @{
    text = 'recent work on Jellyfin Organizer'
    user_id = 'jellyfin_agent'
    limit = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri 'http://localhost:8080/memory/query' -Method Post -Body $body -ContentType 'application/json'
