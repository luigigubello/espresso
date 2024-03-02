const cv = require('./opencv.js');
const { createCanvas, loadImage, Image } = require('canvas');
const puppeteer = require('puppeteer');
const validator = require('validator');
const express = require('express');
const bodyParser = require('body-parser');
const path = require('path');
const fs = require('fs/promises');

const app = express();
const port = 8080;

app.use(bodyParser.json());

// Define the path for the screenshots folder in /tmp
const screenshotsFolder = '/tmp/screenshots';

// Check if the screenshots folder exists, if not, create it
fs.mkdir(screenshotsFolder, { recursive: true })
    .then(() => console.log('Screenshots folder created in /tmp'))
    .catch(err => console.error('Error creating screenshots folder:', err));

app.use('/screenshots', express.static(screenshotsFolder));

async function isValidURL(url) {
  return validator.isURL(url);
}

async function imageSimilarity(imgPath) {
    // Load the screenshot image with canvas
    const canvasScreenshot = await loadImage(imgPath);

    try {
        await fs.mkdir('similarity');
    } catch (e) {
        // Directory already exists
    }

    const samples = await fs.readdir('similarity');
    const evaluation = [];

    for (const sample of samples) {
        const samplePath = `similarity/${sample}`;
        const canvasSample = await loadImage(samplePath);

        // Convert canvas images to cv::Mat
        const src = canvasToMat(canvasScreenshot);
        const dst = canvasToMat(canvasSample);

        // Check if src and dst have the same dimensions
        if (src.rows !== dst.rows || src.cols !== dst.cols) {
            console.error('Error: src and dst have different dimensions');
            continue;
        }
        
        // More human-readable
        const similarityScore = calculateSimilarity(src, dst);
        const scaledSimilarityScore = parseInt(similarityScore);

        if (similarityScore < 100) {
            evaluation.push([`http://127.0.0.1:8080/${sample}`, scaledSimilarityScore]);
        }

        // Release Mats
        src.delete();
        dst.delete();
    }

    // Sort by similarity score in increasing order
    evaluation.sort((a, b) => a[1] - b[1]);

    if (evaluation.length > 0) {
        return evaluation[0];
    } else {
        return '';
    }
}

function canvasToMat(canvas) {
    // Create a virtual canvas using the canvas library
    const virtualCanvas = createCanvas(canvas.width, canvas.height);
    const virtualCtx = virtualCanvas.getContext('2d');

    // Draw the image onto the virtual canvas
    virtualCtx.drawImage(canvas, 0, 0, canvas.width, canvas.height);

    // Create a new ImageData object from the virtual canvas
    const imageData = virtualCtx.getImageData(0, 0, canvas.width, canvas.height);

    // Use the ImageData object to create a cv.Mat
    const src = cv.matFromImageData(imageData);
    return src;
}



function calculateSimilarity(src, dst) {
    // Convert Mats to LAB color space
    const srcLab = new cv.Mat();
    const dstLab = new cv.Mat();
    cv.cvtColor(src, srcLab, cv.COLOR_BGR2Lab);
    cv.cvtColor(dst, dstLab, cv.COLOR_BGR2Lab);

    // Create MatVector to store Mats
    const srcVector = new cv.MatVector();
    const dstVector = new cv.MatVector();
    srcVector.push_back(srcLab);
    dstVector.push_back(dstLab);

    // Calculate histograms for each channel in LAB color space
    const channels = [0, 1, 2];
    const histSize = [8, 8, 8];
    const ranges = [0, 256, 0, 256, 0, 256];
    const hist1 = new cv.Mat();
    const hist2 = new cv.Mat();
    cv.calcHist(srcVector, channels, new cv.Mat(), hist1, histSize, ranges);
    cv.calcHist(dstVector, channels, new cv.Mat(), hist2, histSize, ranges);

    // Normalize histograms
    cv.normalize(hist1, hist1, 0, 1, cv.NORM_MINMAX, -1);
    cv.normalize(hist2, hist2, 0, 1, cv.NORM_MINMAX, -1);

    // Calculate Mean Squared Error (MSE)
    const srcData = new Float32Array(hist1.data32F);
    const dstData = new Float32Array(hist2.data32F);

    let mse = 0;
    for (let i = 0; i < srcData.length; ++i) {
        mse += (srcData[i] - dstData[i]) ** 2;
    }
    mse /= srcData.length;

    // console.log('Calculated MSE:', mse);

    // The lower the MSE, the more similar the images
    const similarityScore = mse / (srcLab.rows * srcLab.cols);
    const scaledSimilarityScore = similarityScore * 100000000000;

    // console.log('Scaled Similarity Score:', scaledSimilarityScore);

    // Release Mats and MatVector
    srcLab.delete();
    dstLab.delete();
    srcVector.delete();
    dstVector.delete();
    hist1.delete();
    hist2.delete();

    return scaledSimilarityScore;
}




async function captureScreenshot(url) {
    const browser = await puppeteer.launch({ headless: 'new' });
    const page = await browser.newPage();

    try {
        await page.setViewport({ width: 1920, height: 1080 });
        await page.goto(url, { waitUntil: 'networkidle0' });

        // Capture screenshot
        try {
            await fs.mkdir('screenshots');
        } catch (e) {
            // Directory already exists
        }
        const parsedURL = new URL(url);
        const screenshotPath = `/tmp/screenshots/screenshot_${parsedURL.hostname}.png`;
        await page.screenshot({ path: screenshotPath });

        // Return both screenshot and page.url
        return {
            screenshotPath,
            url: page.url(),
        };
    } finally {
        await browser.close();
    }
}

app.post('/scanUrl', async (req, res) => {
    try {
        const { url } = req.body;

        if (!(await isValidURL(url))) {
            return res.status(400).json({ error: `${url} is not a valid URL.` });
        }

        const response_data = {
            url,
            url_redirect: '',
            screenshot: '',
            similarity: '',
        };

        const { screenshotPath, url: pageUrl } = await captureScreenshot(url);
        response_data.url_redirect = pageUrl;

        // Adjust the construction of the screenshot URL
        response_data.screenshot = `http://127.0.0.1:${port}/${path.basename(screenshotPath)}`;

        const similarityCheck = await imageSimilarity(screenshotPath);
        response_data.similarity = similarityCheck[0] ? similarityCheck[0] : '';
        response_data.score = similarityCheck[1]

        res.json(response_data);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/:image_name', async (req, res) => {
    const { image_name } = req.params;
    const similarityFolder = path.join(__dirname, 'similarity');
    const imagePath = path.join(screenshotsFolder, image_name);

    try {
        await fs.access(imagePath);
        res.sendFile(imagePath);
    } catch (error) {
        // If the image is not found in the screenshots folder, try finding it in the similarity folder
        const similarityImagePath = path.join(similarityFolder, image_name);

        try {
            await fs.access(similarityImagePath);
            res.sendFile(similarityImagePath);
        } catch (error) {
            res.status(404).json({ error: 'Image not found' });
        }
    }
});

app.listen(port, () => {
    console.log(`Server is running on http://127.0.0.1:${port}`);
});
