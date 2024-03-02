FROM node:20.11-bullseye

WORKDIR /app

COPY . .

RUN /app/puppeteer-deb-deps.sh

RUN npm install

EXPOSE 8080

# Create a no-root users to run Chrome
RUN adduser --disabled-login noprivileges
USER noprivileges

RUN npx puppeteer browsers install chrome

CMD ["node", "index.js"]