FROM allovince/evascrapy:v1.2.1

COPY ./evascrapy/spiders /opt/htdocs/evascrapy/evascrapy/spiders

CMD python start.py
