# send_test_event.ps1
# Sends a test CloudEvent to the local asset_indexer function using event.json

$event = Get-Content -Raw event.json
Invoke-RestMethod -Method Post -Uri http://localhost:8081 -ContentType "application/cloudevents+json" -Body $event 