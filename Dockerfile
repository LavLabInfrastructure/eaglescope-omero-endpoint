ARG PY_VERSION=3.12

FROM python:$PY_VERSION as base
# create non-root user (primarily for devcontainer)
RUN groupadd --gid 1000 vscode \
    && useradd --uid 1000 --gid 1000 -m vscode

WORKDIR /app
COPY . /app/
RUN chown -R vscode /app

FROM base AS hatch
RUN pip3 install hatch https://github.com/glencoesoftware/zeroc-ice-py-linux-x86_64/releases/download/20240202/zeroc_ice-3.6.5-cp312-cp312-manylinux_2_28_x86_64.whl 
RUN hatch build
ENV HATCH_ENV=default
ENTRYPOINT ["hatch", "run"]

FROM base AS prod
COPY --from=hatch /app/dist/*.whl /tmp
RUN pip3 install https://github.com/glencoesoftware/zeroc-ice-py-linux-x86_64/releases/download/20240202/zeroc_ice-3.6.5-cp312-cp312-manylinux_2_28_x86_64.whl && \
    pip3 install /tmp/*.whl
RUN pip3 install gunicorn
ENTRYPOINT ["gunicorn", "omero_scoper.__main__:main()"]
USER vscode

FROM base AS dev
USER vscode
RUN pip3 install hatch 
RUN pip3 install $(find /app -name 'requirement*.txt' -exec echo -n '-r {} ' \;)

