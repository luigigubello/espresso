#!/usr/bin/env python

from fastapi import FastAPI, HTTPException, responses, Body
import os
import uvicorn
from seleniumbase import SB
import requests
import urllib3
import whois
import datetime


def cloudflare_captcha_check(source_code):
    return "https://challenges.cloudflare.com" in source_code


def cloudflare_bypass_check(source_code):
    return "/cdn-cgi/challenge-platform/" not in source_code


def seleniumbase_browser(url, hostname, result):
    with SB(uc_cdp=True, guest_mode=True) as sb:
        sb.set_window_size(1366, 768)
        sb.open(url)
        pre_captcha = sb.get_page_source()
        result["cloudflare"] = cloudflare_captcha_check(pre_captcha)
        # bypass cloudflare captcha - 22.09.2023
        # credits to Michael Mintz
        # https://stackoverflow.com/a/76575463
        if sb.is_element_visible('input[value*="Verify"]'):
            sb.click('input[value*="Verify"]')
        elif sb.is_element_visible('iframe[title*="challenge"]'):
            sb.switch_to_frame('iframe[title*="challenge"]')
            sb.click("span.mark")
        sb.sleep(6)
        if result["cloudflare"]:
            captcha_bypassed = sb.get_page_source()
            result["cloudflare_bypass"] = cloudflare_bypass_check(captcha_bypassed)
        current_dt = str(datetime.datetime.now()).replace(' ', '_')
        try:
            os.makedirs('./screenshots')
        except OSError:
            pass
        sb.save_screenshot('screenshots/' + hostname + '_' + current_dt + '.png')
        result["screenshot"] = hostname + '_' + current_dt + '.png'


def site_exist_check(url):
    try:
        response = requests.get(url, allow_redirects=True)
        return response.url
    except Exception:
        return ""


def url_hostname(url):
    return ".".join(urllib3.util.parse_url(url).host.split(".")[-2:])


def whois_creation_date(url):
    try:
        w = whois.whois(url)
        return w["creation_date"].strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def whois_registrar(url):
    try:
        w = whois.whois(url)
        return w["registrar"]
    except Exception:
        return ""


app = FastAPI()

# Endpoint to scan a URL and return a JSON response
# curl -X POST http://127.0.0.1:8080/scanUrl -d 'https://example.org'
@app.post("/scanUrl", response_model=dict)
async def scan_url(submitted_url: str = Body()):
    try:
        response_data = {"url": submitted_url, "url_redirect": site_exist_check(submitted_url), "hostname": "",
                         "creation_date": "", "registrar": "", "cloudflare": False, "cloudflare_bypass": False,
                         "screenshot": ""}

        if response_data["url_redirect"]:
            response_data["hostname"] = url_hostname(submitted_url)
            response_data["creation_date"] = whois_creation_date(response_data["hostname"])
            response_data["registrar"] = whois_registrar(response_data["hostname"])
            seleniumbase_browser(submitted_url, response_data["hostname"], response_data)

        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# http://127.0.0.1:8080/{image}.png
@app.get("/{image_name}")
async def get_image(image_name: str):
    image_path = os.path.join("screenshots", image_name)

    if os.path.isfile(image_path):
        return responses.FileResponse(image_path, media_type="image/png")

    # Return a 404 Not Found response if the image file does not exist
    return {"error": "Image not found"}, 404
