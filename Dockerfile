FROM paddlepaddle/paddle:2.1.3-gpu-cuda11.2-cudnn8

# Configure Proxy
ENV http_proxy "http://USER:PASSWORD@proxy-sa.mahidol:8080/"
ENV https_proxy "http://USER:PASSWORD@proxy-sa.mahidol:8080/"

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Clone PaddleDetection
WORKDIR /PaddleDetection
COPY /PaddleDetection /PaddleDetection

# Install Mandatory Packages
RUN pip install Cython
RUN pip install -r requirements.txt

# Source Compile PaddletDetection
RUN python setup.py install


