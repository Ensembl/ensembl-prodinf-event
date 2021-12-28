
FROM python:3.7.10

RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

RUN mkdir /home/appuser/.ssh 
RUN echo 'Host * \n\
    StrictHostKeyChecking no \n\
    UserKnownHostsFile=/dev/null' >  /home/appuser/.ssh/config 

WORKDIR /home/appuser

#copy handover app
COPY . /home/appuser

#Install dependenciesls
RUN python -m venv /home/appuser/venv
ENV PATH="/home/appuser/venv/bin:$PATH"
RUN pip install -r requirements.txt
RUN pip install .

EXPOSE 5000
CMD  ["/home/appuser/venv/bin/gunicorn", "--config", "/home/appuser/gunicorn_config.py", "-b", "0.0.0.0:5000", "ensembl.production.event.app.main:app"]

