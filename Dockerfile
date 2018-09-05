FROM allovince/evascrapy:1.1.0

COPY ./evascrapy/spiders /opt/htdocs/evascrapy/spiders

CMD python start.py
