FROM allovince/evascrapy:v2.1.10
# Keep the crawler image rebuild aligned with the pinned EvaScrapy runtime.

COPY ./evascrapy/spiders /opt/htdocs/evascrapy/evascrapy/spiders

CMD python start.py
