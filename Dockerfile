FROM allovince/evascrapy:1.1.2

COPY ./evascrapy/spiders /opt/htdocs/evascrapy/evascrapy/spiders

CMD python start.py
