#!/bin/bash

response_unauthorized=$(curl -Iv http://localhost:5000 2>&1)

# Check if response contains HTTP/1.1 401 Unauthorized
if [[ "$response_unauthorized" == *"HTTP/1.1 401 Unauthorized"* ]]; then
  echo "Test passed: Response is 401 Unauthorized"
else
  echo "Test failed: Response is not 401 Unauthorized"
  exit 1
fi

response_authorized=$(curl -Iv -u test-user:test-password http://localhost:5000 2>&1)

# Check if response contains HTTP/1.1 200 OK
if [[ "$response_authorized" == *"HTTP/1.1 200 OK"* ]]; then
  echo "Test passed: Response is 200 OK when passing basic authentication"
  exit 0
else
  echo "Test failed: Response is not 200 OK when passing basic authentication"
  exit 1
fi
