# Service Latency Troubleshooting Runbook

## Elevated API Latency

Collect:

- p50, p95 and p99 latency
- request volume
- error rate
- CPU utilization
- memory utilization
- database query duration
- downstream dependency latency
- network errors

Possible hypotheses include:

- overloaded application instances
- slow database queries
- connection-pool saturation
- downstream dependency latency
- network degradation
- resource saturation

## Safe Investigation Order

1. Identify which endpoint is slow.
2. Determine when latency increased.
3. Check request volume and saturation.
4. Check application traces.
5. Check database performance.
6. Check downstream dependencies.
7. Check recent deployments.
