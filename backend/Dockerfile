FROM python:3.11-slim

WORKDIR /app

# Install CPU-only PyTorch first (avoids pulling ~2 GB CUDA libs)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create model directory (weights can be mounted or built inside)
RUN mkdir -p /app/app/model

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
