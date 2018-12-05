FROM allovince/evascrapy:v1.3.2

COPY ./evascrapy/spiders /opt/htdocs/evascrapy/evascrapy/spiders

CMD python start.py
