# Espresso

Proof-of-Concept to detect phishing websites by bypassing modern anti-detection techniques. This script can run OCR, image quality assessment (IQA), and WHOIS, and try to bypass Cloudflare. Browser emulation using Seleniumbase.

## How To Use

Build the Docker image.

```
docker build -t espresso .
```

Launch the server.

```
docker run -p 8080:8080 -it espresso
```

And submit the suspicious URL sending a POST request.

```
curl -X POST http://127.0.0.1:8080/scanUrl -H "Content-Type: application/json" -d '{"url": "https://example.org", "ocr": true, "similarity": true}'
```

The JSON payload structure is the following:

```
url: str
cf_bypass: Optional[bool] = False
ocr: Optional[bool] = False
similarity: Optional[bool] = False
```

The server should return the following JSON:

```
{"url":"https://example.org","url_redirect":"https://example.org/","hostname":"example.org","creation_date":"1995-08-31 04:00:00","registrar":"ICANN","cloudflare":false,"cloudflare_bypass":false,"screenshot":"http://127.0.0.1:8080/screenshot_example.org_2023-10-04_18:47:23.816416.png","ocr":[["Example Domain",0.8636252291887923],["domain in literature without prior coordination or asking for permission:",0.9289502852506653]],"similarity":""}% 
```

- **url:** it is the submitted URL.
- **url_redirect:** ff there is no redirect, `url` and `url_redirect` match.
- **hostname:** hostname of `url`.
- **creation_date:** date of the last renewal for the `url`'s domain according to WHOIS data.
- **registrar:** domain registrar of the `url`'s domain according to WHOIS data.
- **cloudflare:** `true` if there is a Cloudflare challenge.
- **cloudflare_bypass:** `true` if the client has been able to pass the Cloudflare challenge.
- **screenshot:** URL of the screenshot of the page.
- **ocr:** it returns an array of tuples, containing the extracted strings with high confidence (>0.85)
- **similarity:** URL of the most similar sample, if it exists.

## FAQs

**Q:** I cannot run the Docker container on Apple Mx.

**A:** Yes. This image can run on `amd64` platform, and not on `arm64`, because otherwise Chrome crashes. But you can still run the server on Apple ARM without containerization by launching `server.py`.

**Q:** The first `Espresso` Docker build is slow.

**A:** Yes, installing [EasyOCR](https://github.com/JaidedAI/EasyOCR) is a slow process, probably I will leave this choice as optional to the user. In addition, I recommend at least 32GB of virtual disk for EasyOCR and its models, and a GPU to optimize EasyOCR.

**Q:** `Espresso` cannot bypass Cloudflare captcha.

**A:** Yes, this can happen, it's a mouse-n-cat game. Cloudflare captcha uses heuristic metrics to detect non-human actions or automation. They probably evaluate the client configuration (window resoluzion, plugins, etc), the IP (hosting vs. ISP, number of requests, etc), and other unknown metrics. So, if you iterate requests from the same IP, probably Cloudflare will block you.