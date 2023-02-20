FROM ghcr.io/binkhq/python:3.11-poetry as build

WORKDIR /src
ADD . .
RUN poetry export -f requirements.txt --output requirements.txt

FROM ghcr.io/binkhq/python:3.11
WORKDIR /app
COPY --from=build /src/requirements.txt /src/settings.py /src/main.py ./
RUN pip install -r requirements.txt

ENTRYPOINT [ "linkerd-await", "--" ]
CMD [ "python", "main.py" ]
