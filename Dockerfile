FROM allovince/evascrapy:v2.1.6

COPY ./evascrapy/spiders /opt/htdocs/evascrapy/evascrapy/spiders

CMD python start.py