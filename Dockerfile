FROM python:3.12-slim

# Dipendenze di sistema per WeasyPrint (Pango, Cairo, font)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libcairo2 \
    libffi8 \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu-core \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir weasyprint

# Copia gli script di avvio nell'immagine
# (orario.csv e genera_html.py arrivano dal volume mount a runtime)
COPY *.sh /app/

WORKDIR /app

CMD ["./generate-pdf.sh"]
