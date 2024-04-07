#!/bin/bash

# Send a request without authentication
response_unauthorized=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3040)

# Check if response status code is 401 Unauthorized
if [[ "$response_unauthorized" == "401" ]]; then
  echo "Test passed: Response is 401 Unauthorized"
else
  echo "Test failed: Response is not 401 Unauthorized"
  exit 1
fi

# Send a request with basic authentication
response_authorized=$(curl -s -o /dev/null -w "%{http_code}" -u user:test-password http://localhost:3040)

# Check if response status code is 200 OK
if [[ "$response_authorized" == "200" ]]; then
  echo "Test passed: Response is 200 OK when passing basic authentication"
  exit 0
else
  echo "Test failed: Response is not 200 OK when passing basic authentication"
  exit 1
fi
