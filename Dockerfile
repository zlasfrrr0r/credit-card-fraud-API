# FROM base image of python 3.11
FROM python:3.11-slim

# create working directory
WORKDIR /app

# copy everything here into the working directory
COPY . /app

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# expose port
EXPOSE 8000

# run app
CMD [ "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" ]