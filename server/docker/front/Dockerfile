FROM node:20-slim AS front-base
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable && corepack prepare pnpm@8.9.0 --activate

COPY front /app
WORKDIR /app

FROM front-base AS front-build
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install
RUN pnpm run build

FROM nginx:1.21.0-alpine

COPY ./docker/front/proxy_params /etc/nginx/proxy_params
COPY ./docker/front/app.conf /etc/nginx/conf.d/default.conf
COPY --from=front-build /app/dist /front
