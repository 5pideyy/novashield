FROM node:21 AS BUILD_IMAGE
WORKDIR /build
COPY . .
ARG PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
RUN npm install
RUN npm install mongoose
RUN npm install geoip-lite
RUN npm run build

FROM node:21-alpine
WORKDIR /usr/src/pow-shield
COPY --from=BUILD_IMAGE /build/dist .
COPY --from=BUILD_IMAGE /build/node_modules ./node_modules
CMD [ "node", "bin/server.js" ]
