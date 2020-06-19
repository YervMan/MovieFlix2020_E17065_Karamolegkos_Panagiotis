FROM ubuntu:16.04 
MAINTAINER PANAGIOTIS KARAMOLEGKOS <p.karamolegos@yahoo.gr>
RUN apt-get update
RUN apt-get install -y python3 python3-pip 
RUN pip3 install flask pymongo
RUN mkdir /app
COPY service.py /app/service.py  
COPY templates /app/templates
WORKDIR /app
ENTRYPOINT [ "python3","-u", "service.py" ]
