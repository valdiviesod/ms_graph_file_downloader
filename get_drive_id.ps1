# Variables
$clientID = ''
$secretKey = ''
$tenantID = ''
$targetUserID = '' 

# Authentication URL
$authUrl = "https://login.microsoftonline.com/$tenantID/oauth2/v2.0/token/"

# Request body for authentication
$body = @{
    "scope" = "https://graph.microsoft.com/.default";
    "grant_type" = "client_credentials";
    "client_id" = $clientID
    "client_secret" = $secretKey
}

# Get authentication token
$authToken = Invoke-RestMethod -Uri $authUrl -Method POST -Body $body

# API URL to get the drive ID for the specified user
$url = "https://graph.microsoft.com/v1.0/users/$targetUserID/drive"

# Headers for API request
$headers = @{
    "Authorization" = "Bearer $($authToken.access_token)"
    "Content-type"  = "application/json"
}

# API request
$response = Invoke-RestMethod -Uri $url -Headers $headers -Method Get

# Output the drive ID
Write-Host $response.id
