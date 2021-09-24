FROM continuumio/miniconda3
COPY conda_env.yaml /conda_env/conda_env.yaml
RUN conda env create -f=/conda_env/conda_env.yaml && conda clean --all -f --yes

COPY src /src/
WORKDIR /src/
EXPOSE 5050

CMD ["conda", "run", "--no-capture-output", "-n", "app",  "gunicorn", "-c", "gunicorn_config.py", "wsgi"]
