FROM python:3.9

RUN useradd --create-home appuser
USER appuser
RUN mkdir -p /home/appuser/event
WORKDIR /home/appuser/event
RUN chown appuser:appuser /home/appuser/event


#copy handover app
COPY --chown=appuser:appuser . /home/appuser/event

#Install dependenciesls
RUN python -m venv /home/appuser/event/venv
ENV PATH="/home/appuser/event/venv/bin:$PATH"
RUN pip install wheel
RUN pip install .

EXPOSE 5000
CMD  ["gunicorn", "--config", "/home/appuser/event/gunicorn_config.py", "-b", "0.0.0.0:5000", "ensembl.production.event.app.main:app"]

