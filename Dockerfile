FROM python:3.11-bullseye

# Install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt -y update
RUN apt install -y google-chrome-stable

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

# Install EasyOCR models
RUN apt install unzip
RUN mkdir models
RUN wget -q https://github.com/JaidedAI/EasyOCR/releases/download/v1.3/english_g2.zip -O /tmp/english_g2.zip
RUN wget -q https://github.com/JaidedAI/EasyOCR/releases/download/pre-v1.1.6/craft_mlt_25k.zip -O /tmp/craft_mlt_25k.zip
RUN unzip /tmp/english_g2.zip -d /app/models
RUN unzip /tmp/craft_mlt_25k.zip -d /app/models

# Install Chromedriver for Selenium
RUN seleniumbase install chromedriver

CMD ["uvicorn", "server:app", "--host=0.0.0.0", "--port=8080"]
