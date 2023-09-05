FROM python:3.11.2-slim

ADD . .
SHELL ["/bin/bash", "-c"]
RUN pip install -r req.txt
CMD python main.py