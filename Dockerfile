FROM allovince/evascrapy:v2.2.0
# Keep the crawler image rebuild aligned with the pinned EvaScrapy runtime.

# Fail the image build if the pinned runtime is missing the crawler's timezone dependency.
RUN python -c "import pytz; print(pytz.__version__)"

COPY ./evascrapy/spiders /opt/htdocs/evascrapy/evascrapy/spiders

CMD python start.py
