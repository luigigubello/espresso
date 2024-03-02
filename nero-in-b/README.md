# Nero In B

Proof-of-Concept to measure the distance between two screenshots using OpenCV. More reliable than `sewar`'s algorithms. Browser emulation using Playwright.

## How To Use

Build the Docker image.

```
docker build -t nero-in-b .
```

Launch the server.

```
docker run -p 8080:8080 -it nero-in-b
```

And submit the suspicious URL sending a POST request.

```
curl -X POST http://127.0.0.1:8080/scanUrl -H "Content-Type: application/json" -d '{"url": "https://example.org"}'
```

The server should return the following JSON:

```
{"url":"https://example.org","url_redirect":"https://example.org/","screenshot":"http://127.0.0.1:8080/screenshot_example.org.png","similarity":""}
```
