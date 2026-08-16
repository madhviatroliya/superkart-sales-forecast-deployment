FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Run the API with gunicorn instead of Flask development server
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:7860", "app:superkart_api"]
