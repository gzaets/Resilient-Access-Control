FROM python:3.11-slim

WORKDIR /app
COPY requirements-main.txt .
RUN pip install --no-cache-dir -r requirements-main.txt

COPY ./src ./src

# Expose Flask (5000) and PySyncObj default (4321); change if you pick other ports
EXPOSE 5000 4321

CMD ["python", "-m", "src.app.main"]
