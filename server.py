#!/usr/bin/env python

from typing import Optional
from fastapi import FastAPI, HTTPException, responses
from pydantic import BaseModel
import os
import uvicorn
from seleniumbase import SB
import requests
import urllib3
import whois
import datetime
import easyocr
import platform
from sewar.full_ref import uqi, psnr
from PIL import Image
import numpy as np
from operator import itemgetter



def cloudflare_captcha_check(source_code):
    return "https://challenges.cloudflare.com" in source_code


def cloudflare_bypass_check(source_code):
    return "/cdn-cgi/challenge-platform/" not in source_code


def seleniumbase_browser(url, hostname, result, cf_bypass):
    with SB(uc_cdp=True, guest_mode=True) as sb:
        sb.set_window_size(1366, 768)
        sb.open(url)
        pre_captcha = sb.get_page_source()
        sb.sleep(8)
        result["cloudflare"] = cloudflare_captcha_check(pre_captcha)
        if result["cloudflare"] and cf_bypass:
            # bypass cloudflare captcha - 22.09.2023
            # credits to Michael Mintz
            # https://stackoverflow.com/a/76575463
            if sb.is_element_visible('input[value*="Verify"]'):
                sb.click('input[value*="Verify"]')
            elif sb.is_element_visible('iframe[title*="challenge"]'):
                sb.switch_to_frame('iframe[title*="challenge"]')
                sb.click("span.mark")
            sb.sleep(6)
            captcha_bypassed = sb.get_page_source()
            result["cloudflare_bypass"] = cloudflare_bypass_check(captcha_bypassed)
        current_dt = str(datetime.datetime.now()).replace(' ', '_')
        try:
            os.makedirs('./screenshots')
        except OSError:
            pass
        sb.save_screenshot('screenshots/screenshot_' + hostname + '_' + current_dt + '.png')
        result["screenshot"] = 'http://127.0.0.1:8080/screenshot_' + hostname + '_' + current_dt + '.png'


def ocr_url(image):
    try:
        image_reader = easyocr.Reader(['en'], model_storage_directory='models', download_enabled=False)
        ocr_text = image_reader.readtext(image)
        high_confidence_text = []
        for item in ocr_text:
            if item[-1] > 0.85:
                high_confidence_text.append([item[-2], item[-1]])
        return high_confidence_text[:15]
    except Exception:
        return []


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


def image_similarity(img_path):
    try:
        os.makedirs('./similarity')
    except OSError:
        pass
    samples = list(os.walk('similarity'))[0][2]
    evaluation = []
    for sample in samples:
        sample_img = np.array(Image.open("similarity/" + sample))
        screenshot = np.array(Image.open(img_path))
        uqi_value = uqi(sample_img, screenshot)
        psnr_value = psnr(sample_img, screenshot)
        if uqi_value > 0.95 and psnr_value > 20:
            evaluation.append(["http://127.0.0.1:8080/" + sample, uqi_value, psnr_value])
    sorted_evaluation = sorted(evaluation, key=itemgetter(2), reverse=True)
    if sorted_evaluation:
        return sorted_evaluation[0][0]
    else:
        return ""

app = FastAPI()

# Endpoint to scan a URL and return a JSON response
# curl -X POST http://127.0.0.1:8080/scanUrl -d 'https://example.org'

class SubmittedUrl(BaseModel):
    url: str
    cf_bypass: Optional[bool] = False
    ocr: Optional[bool] = False
    similarity: Optional[bool] = False

@app.post("/scanUrl", response_model=dict)
async def scan_url(submitted_url: SubmittedUrl):
    submitted_url = submitted_url.model_dump()
    try:
        response_data = {"url": submitted_url["url"], "url_redirect": site_exist_check(submitted_url["url"]), "hostname": "",
                         "creation_date": "", "registrar": "", "cloudflare": False, "cloudflare_bypass": False,
                         "screenshot": "", "ocr": [], "similarity": ""}
        
        if response_data["url_redirect"]:
            response_data["hostname"] = url_hostname(submitted_url["url"])
            response_data["creation_date"] = whois_creation_date(response_data["hostname"])
            response_data["registrar"] = whois_registrar(response_data["hostname"])
            seleniumbase_browser(submitted_url["url"], response_data["hostname"], response_data, submitted_url["cf_bypass"])
            screenshot_path = "screenshots/" + response_data["screenshot"].removeprefix('http://127.0.0.1:8080/')
            if submitted_url["ocr"]:
                response_data["ocr"] = ocr_url(screenshot_path)
            if submitted_url["similarity"]:
                response_data["similarity"] = image_similarity(screenshot_path)

        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# http://127.0.0.1:8080/{image}.png
@app.get("/{image_name}")
async def get_image(image_name: str):
    if image_name.startswith("screenshot_"):
        image_path = os.path.join("screenshots", image_name)
    else:
        image_path = os.path.join("similarity", image_name)

    if os.path.isfile(image_path):
        return responses.FileResponse(image_path, media_type="image/png")

    # Return a 404 Not Found response if the image file does not exist
    return {"error": "Image not found"}, 404


if platform.system() == "Darwin" and platform.processor() == "arm":
    uvicorn.run(app, host="127.0.0.1", port=8080)