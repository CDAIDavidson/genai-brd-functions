# content_processor_send_local_test_event.ps1
# Sends a test request to the local content_processor function 

# Create a test payload with direct parameters
$requestData = @{
    brd_workflow_id = "test-workflow-id-$([System.Guid]::NewGuid().ToString().Substring(0, 8))"
    document_id = "test-document-id-$([System.Guid]::NewGuid().ToString().Substring(0, 8))"
    data = @{
        title = "Test Document Title"
        source_file = "sample_document.html"
    }
}

# Convert to JSON
$requestJson = $requestData | ConvertTo-Json -Depth 10

# Save to a file for inspection
$requestJson | Out-File -FilePath "content_processor_test_event.json"

Write-Host "Sending test request to content_processor at http://localhost:8083..."
Write-Host "Request data: $($requestJson)"

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
    $response = Invoke-RestMethod -Method Post -Uri "http://localhost:8083" -ContentType "application/json" -Body $requestJson
    Write-Host "✅ Success! Response: $response"
} catch {
    Write-Host "❌ Error: $_"
} 