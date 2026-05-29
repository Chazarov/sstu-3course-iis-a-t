FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    sbcl \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY exp/requirements.txt ./exp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r exp/requirements.txt

ENV PYTHONUNBUFFERED=1
ENV SBCL_PATH=sbcl

WORKDIR /app/exp/src
EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
