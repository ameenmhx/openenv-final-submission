# 1. Start with a standard, lightweight Python computer
FROM python:3.10-slim

# 2. Create a folder inside this mini-computer called /app
WORKDIR /app

# 3. Copy our list of tools into the mini-computer
COPY requirements.txt .

# 4. Tell the mini-computer to install those tools
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy all our python files from your laptop into the mini-computer
COPY . .

# 6. Open port 8000 so the internet can talk to our server
EXPOSE 8000

# 7. The exact terminal command to turn the server on
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]