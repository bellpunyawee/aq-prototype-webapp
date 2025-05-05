FROM python:3.12-slim

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

COPY entrypoint-prod.sh /usr/src/app/entrypoint.sh

RUN chmod +x /usr/src/app/entrypoint.sh

EXPOSE 80
ENV HOSTNAME "0.0.0.0"
ENV FLASK_RUN_HOST "0.0.0.0"
ENV FLASK_RUN_PORT "80"
ENV FLASK_ENV "production"
ENV FLASK_APP "server_frontend.py"

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]