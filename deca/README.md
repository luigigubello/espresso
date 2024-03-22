# Deca

**sample here**

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
[sample]
```
