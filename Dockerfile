FROM python:3.11-slim

# Install ImageMagick and other necessary libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    imagemagick \
    libmagickwand-dev \
    ghostscript \
    poppler-utils \
 && rm -rf /var/lib/apt/lists/*


# Set ImageMagick policy to allow PDF handling
RUN sed -i 's/rights="none" pattern="PDF"/rights="read | write" pattern="PDF"/' /etc/ImageMagick-6/policy.xml

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000

ENV FLASK_APP=app.py
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
