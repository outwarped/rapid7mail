FROM python:3.12.1 as builder

WORKDIR /src
COPY . /src

RUN pip install poetry

RUN poetry install

RUN poetry run coverage run -m pytest && poetry run coverage report -m

RUN poetry build

FROM python:3.12.1-slim as app

WORKDIR /app

COPY --from=builder /src/dist/*.whl /app

RUN pip install *.whl

EXPOSE 8025
EXPOSE 8026

ENTRYPOINT [ "python", "-m", "rapid7mail" ]
