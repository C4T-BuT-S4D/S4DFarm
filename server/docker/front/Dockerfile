FROM node:16-alpine as build

WORKDIR /app
COPY front/package.json .
COPY front/yarn.lock .
RUN yarn install

COPY front .
RUN yarn build

FROM nginx:1.21.0-alpine

COPY ./docker/front/proxy_params /etc/nginx/proxy_params
COPY ./docker/front/app.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /front
