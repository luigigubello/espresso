# Deca

Proof-of-Concept to detect phishing websites under certain specific conditions and threat models. In particular, this script checks if the web server returns some header commonly returned by phishing sites and the TLS certificate date. 

## How To Use

Build the Docker image.

```
docker build -t deca .
```

Launch the server.

```
docker run -p 8080:8080 -it deca
```

And submit the suspicious URL sending a POST request.

```
curl -X POST http://127.0.0.1:8080/scanUrl -H "Content-Type: application/json" -d '{"url": "https://example.org"}'
```

The server should return the following JSON:

```
{"url":"https://example.org","url_redirect":"https://example.org/","cloudflare_headers":{"cf-mitigated":"","server":"ECS (nyd/D10A)","report-to":false,"nel":false,"cf-ray":false},"certificate_dates":{"creation_date":"2024-01-30T00:00:00","expiration_date":"2025-03-01T23:59:59","current_date":"2024-03-22T17:26:10.951501","difference_in_days":52}}
```
