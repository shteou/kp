FROM python:3.8-slim

RUN apt update && apt install -y curl procps && apt clean

RUN groupadd -g 999 metaworkflow && \
    useradd -mr -u 999 -g metaworkflow metaworkflow
USER metaworkflow
WORKDIR /home/metaworkflow

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .

ENV PYTHONUNBUFFERED=0

CMD [ "python", "main.py" ]
