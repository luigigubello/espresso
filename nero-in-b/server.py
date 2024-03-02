#!/usr/bin/env python

from fastapi import FastAPI, HTTPException, responses
from pydantic import BaseModel
import os
import uvicorn
import urllib3
import platform
from playwright.async_api import async_playwright
import cv2
import numpy as np
from operator import itemgetter


def url_hostname(url):
    return ".".join(urllib3.util.parse_url(url).host.split(".")[-2:])


async def browser_screenshot(url):
    async with async_playwright() as p:
        browser_type = p.chromium
        browser = await browser_type.launch()
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        await page.goto(url)
        # networkidle is discouraged https://playwright.dev/docs/api/class-page
        await page.wait_for_load_state("networkidle")
        try:
            os.makedirs('./screenshots')
        except OSError:
            pass
        await page.screenshot(path='screenshots/screenshot_' + url_hostname(url) + '.png')
        redirect_url = page.url
        await browser.close()
        return {"screenshot": "http://127.0.0.1:8080/" + "screenshot_" + url_hostname(url) + ".png",
                "redirect_url": redirect_url}


def image_similarity(img_path):
    # Load images
    screenshot = cv2.imread(img_path)
    try:
        os.makedirs('./similarity')
    except OSError:
        pass
    samples = list(os.walk('similarity'))[0][2]
    evaluation = []
    for sample in samples:
        sample_img = cv2.imread("similarity/" + sample)

        # sample_img = cv2.resize(sample_img, (1366, 768))
        # screenshot = cv2.resize(screenshot, (1366, 768))

        # Convert images to LAB color space
        sample_img_color = cv2.cvtColor(sample_img, cv2.COLOR_BGR2LAB)
        screenshot_color = cv2.cvtColor(screenshot, cv2.COLOR_BGR2LAB)

        # Calculate histograms for each channel in LAB color space
        hist1 = cv2.calcHist([sample_img_color], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        hist2 = cv2.calcHist([screenshot_color], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])

        # Normalize histograms
        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()

        # Calculate Mean Squared Error (MSE)
        mse = np.sum((hist1 - hist2) ** 2)

        # The lower the MSE, the more similar the images
        similarity_score = mse / float(sample_img_color.shape[0] * sample_img_color.shape[1])
        similarity_score *= 1000000000

        if similarity_score < 100:
            evaluation.append(["http://127.0.0.1:8080/" + sample, similarity_score])
    sorted_evaluation = sorted(evaluation, key=itemgetter(1), reverse=True)
    if sorted_evaluation:
        return sorted_evaluation[0]
    else:
        return ""


app = FastAPI()


class SubmittedUrl(BaseModel):
    url: str


@app.post("/scanUrl", response_model=dict)
async def scan_url(submitted_url: SubmittedUrl):
    submitted_url = submitted_url.model_dump()
    try:
        response_data = {"url": submitted_url["url"], "url_redirect": "",
                         "screenshot": "", "similarity": ""}
        browser_emulation = await browser_screenshot(submitted_url["url"])
        response_data["url_redirect"] = browser_emulation["redirect_url"]
        response_data["screenshot"] = browser_emulation["screenshot"]
        screenshot_path = "screenshots/" + response_data["screenshot"].removeprefix('http://127.0.0.1:8080/')
        similarity_score = image_similarity(screenshot_path)
        if similarity_score:
            response_data["similarity"] = similarity_score[0]
            response_data["score"] = similarity_score[1]
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
    return {"error": "Image not found"}, 404


if platform.system() == "Darwin" and platform.processor() == "arm":
    uvicorn.run(app, host="127.0.0.1", port=8080)
