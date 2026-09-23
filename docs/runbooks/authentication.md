# Authentication Troubleshooting Runbook

## Login Failures

Collect:

- HTTP status codes
- identity-provider availability
- token validation errors
- authentication service logs
- recent configuration changes
- certificate or signing-key changes

HTTP 401 usually indicates authentication failure.

HTTP 403 usually indicates authentication succeeded but authorization
was denied.

## Authentication Latency

For increased login latency:

1. inspect authentication-service latency
2. inspect identity-provider latency
3. inspect database or session-store latency
4. review token-validation latency
5. compare deployments with incident start time

Do not identify an upstream identity provider as the root cause unless
latency or error evidence supports it.
