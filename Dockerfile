ARG PY_VERSION=3.12

FROM python:$PY_VERSION as base
# create non-root user (primarily for devcontainer)
RUN groupadd --gid 1000 vscode \
    && useradd --uid 1000 --gid 1000 -m vscode

WORKDIR /app
COPY . /app/
RUN chown -R vscode /app

FROM base AS hatch
RUN pip3 install hatch
RUN hatch run build
ENV HATCH_ENV=default
ENTRYPOINT ["hatch", "run"]

FROM base AS prod
COPY --from=hatch /app/dist/*.whl /tmp
RUN pip3 install /tmp/*.whl
RUN pip3 install gunicorn
ENTRYPOINT ["gunicorn", ""]
USER vscode

FROM base AS dev
USER vscode
RUN pip3 install hatch 
RUN pip3 install $(find /app -name 'requirement*.txt' -exec echo -n '-r {} ' \;)

