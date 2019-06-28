FROM allovince/evascrapy:v2.0.0

COPY ./evascrapy/spiders /opt/htdocs/evascrapy/evascrapy/spiders

CMD python start.py
