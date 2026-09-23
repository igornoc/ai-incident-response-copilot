# Payment API Troubleshooting Runbook

## HTTP 500 Error Spike

When a payment or checkout API starts returning HTTP 500 responses,
first determine whether failures affect all requests or only a subset.

Collect:

- affected endpoints
- request IDs
- timestamps
- deployment history
- application error logs
- database latency
- database connection-pool usage
- upstream payment-provider health
- CPU and memory utilization

HTTP 500 alone does not identify a root cause.

## Database Connection Pool Exhaustion

Database connection-pool exhaustion can cause server-side failures,
timeouts, and elevated HTTP 500 rates.

Supporting evidence may include:

- connection acquisition timeout errors
- connections near the configured pool limit
- increasing database wait time
- failures beginning during a traffic spike
- application threads waiting for connections

Recommended checks:

1. Inspect database connection-pool metrics.
2. Look for connection timeout errors.
3. Inspect slow or long-running queries.
4. Compare connection usage with the last healthy period.
5. Review recent database-related deployment changes.

Do not conclude that connection pool exhaustion is the cause based
only on HTTP 500 responses.

## Upstream Payment Provider

An upstream payment provider may also cause checkout failures.

Check:

- upstream HTTP status codes
- upstream latency
- timeout rates
- provider status information
- correlation between provider errors and application errors

Do not retry payments blindly because duplicate transactions may occur.

## Recent Deployment

If errors began shortly after a deployment:

1. compare incident and deployment timestamps
2. review configuration changes
3. inspect changed queries
4. inspect changed dependencies
5. use rollback only when evidence supports the deployment hypothesis
