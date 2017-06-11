FROM posbank.geoneric.eu:5000/nca/nc_base:latest

MAINTAINER Kor de Jong <k.dejong@geoneric.eu>

COPY cmd.sh server.py /
COPY nc_assessment_executor /nc_assessment_executor
COPY test /test

CMD ["/cmd.sh"]
