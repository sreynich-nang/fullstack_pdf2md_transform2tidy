FROM continuumio/miniconda3:latest

WORKDIR /app

COPY environment.yml .
RUN conda env create -f environment.yml

SHELL ["conda", "run", "-n", "TorchMarker", "/bin/bash", "-c"]

COPY . .

EXPOSE 8000

CMD ["conda", "run", "-n", "TorchMarker", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
