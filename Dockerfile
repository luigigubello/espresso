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
RUN models.sh

# Install Chromedriver for Selenium
RUN seleniumbase install chromedriver

CMD ["python", "server.py"]
