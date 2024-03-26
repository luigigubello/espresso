from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import requests
import datetime
import platform
import ssl
import urllib3
from cryptography import x509


def get_tls_dates(url):
    try:
        response = requests.get(url, allow_redirects=True)
        domain = urllib3.util.parse_url(response.url).host
        cert = ssl.get_server_certificate((domain, 443))

        cert_obj = x509.load_pem_x509_certificate(cert.encode())
        creation_date = cert_obj.not_valid_before
        expiration_date = cert_obj.not_valid_after
        current_date = datetime.datetime.now()
        # high suspicious if < 7
        difference = (current_date - creation_date).days

        return {"creation_date": creation_date, "expiration_date": expiration_date, "current_date": current_date,
                "difference_in_days": difference}
    except Exception as e:
        print("Error retrieving TLS creation or expiration date:", e)
        return {"creation_date": "", "expiration_date": "", "current_date": "", "difference_in_days": ""}


def cf_response_headers(url):
    try:
        response = requests.get(url, allow_redirects=True)
        headers_dict = dict(response.headers.items())
        print(headers_dict)
        cloudflare_headers_url = {"cf-mitigated": "", "server": "", "report-to": False, "nel": False, "cf-ray": False}
        for key in headers_dict.keys():
            if key.casefold() == "cf-mitigated":
                # suspicious if {"cf-mitigated": "challenge"}
                cloudflare_headers_url['cf-mitigated'] = headers_dict[key]
            elif key.casefold() == "server":
                # suspicious if {"server": "cloudflare"}
                cloudflare_headers_url['server'] = headers_dict[key]
            elif key.casefold() == "report-to":
                # suspicious if {"report-to": True}
                if 'nel.cloudflare.com' in headers_dict[key]:
                    cloudflare_headers_url['report-to'] = True
            elif key.casefold() == "nel":
                cloudflare_headers_url['nel'] = True
            elif key.casefold() == "cf-ray":
                cloudflare_headers_url['cf-ray'] = True
            else:
                continue
        return cloudflare_headers_url
    except Exception as e:
        print("Error printing response headers:", e)
        return {"cf-mitigated": "", "server": "", "report-to": False, "nel": False, "cf-ray": False}


def url_redirection(url):
    try:
        response = requests.get(url, allow_redirects=True)
        final_url = response.url
        return final_url
    except Exception as e:
        print("Error retrieving final redirected headers:", e)
        return ""


app = FastAPI()


class SubmittedUrl(BaseModel):
    url: str


@app.post("/scanUrl", response_model=dict)
async def scan_url(submitted_url: SubmittedUrl):
    submitted_url = submitted_url.model_dump()
    redirection = url_redirection(submitted_url["url"])
    try:
        response_data = {"url": submitted_url["url"], "url_redirect": redirection,
                         "cloudflare_headers": cf_response_headers(redirection),
                         "certificate_dates": get_tls_dates(redirection)}
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if platform.system() == "Darwin" and platform.processor() == "arm":
    uvicorn.run(app, host="127.0.0.1", port=8080)
