# content_processor_send_local_test_event.ps1
# Sends a test CloudEvent to the local content_processor function 

# Create a test event payload that mimics a Pub/Sub message
$messageData = @{
    brd_workflow_id = "test-workflow-id-$([System.Guid]::NewGuid().ToString().Substring(0, 8))"
    document_id = "test-document-id-$([System.Guid]::NewGuid().ToString().Substring(0, 8))"
}

# Convert the message data to JSON and then Base64 encode it
$jsonData = $messageData | ConvertTo-Json -Compress
$bytes = [System.Text.Encoding]::UTF8.GetBytes($jsonData)
$base64Data = [Convert]::ToBase64String($bytes)

# Create the cloud event structure
$cloudEvent = @{
    specversion = "1.0"
    type = "google.cloud.pubsub.topic.v1.messagePublished"
    source = "pubsub:projects/genai-brd-qi/topics/brd-ready-to-parse"
    id = [System.Guid]::NewGuid().ToString()
    time = (Get-Date).ToUniversalTime().ToString("o")
    datacontenttype = "application/json"
    data = @{
        message = @{
            data = $base64Data
            messageId = "test-message-id"
            publishTime = (Get-Date).ToUniversalTime().ToString("o")
        }
        subscription = "projects/genai-brd-qi/subscriptions/content-processor-sub"
    }
}

# Convert to JSON
$cloudEventJson = $cloudEvent | ConvertTo-Json -Depth 10

# Save to a file for inspection
$cloudEventJson | Out-File -FilePath "content_processor_test_event.json"

Write-Host "Sending test event to content_processor at http://localhost:8083..."
Write-Host "Message data: $jsonData"

# Create sample document in the storage bucket if it doesn't exist
# (This is needed because the function will try to download a file with the document_id)
Write-Host "Creating a sample document in the storage bucket..."
$sampleHtml = @"
<!DOCTYPE html>
<html>
<head>
    <title>Sample BRD Document</title>
</head>
<body>
    <h1>Business Requirements Document</h1>
    <table>
        <tr>
            <th>Requirement ID</th>
            <th>Description</th>
            <th>Priority</th>
        </tr>
        <tr>
            <td>REQ-001</td>
            <td>The system shall process documents</td>
            <td>High</td>
        </tr>
    </table>
</body>
</html>
"@

$sampleHtmlPath = Join-Path $PWD "sample_document.html"
$sampleHtml | Out-File -FilePath $sampleHtmlPath

# Send the request
try {
    $response = Invoke-RestMethod -Method Post -Uri "http://localhost:8083" -ContentType "application/cloudevents+json" -Body $cloudEventJson
    Write-Host "✅ Success! Response: $response"
} catch {
    Write-Host "❌ Error: $_"
} 