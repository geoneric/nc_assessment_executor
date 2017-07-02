import ast
import json
import os.path
import sys
import tempfile
import traceback
import zipfile
from flask import Config
import pika
import requests
from .configuration import configuration
from .assessment_executor import *


class AssessmentExecutor(object):

    def __init__(self):
        self.config = Config(__name__)


    def assessment_request_uri(self,
            route):
        route = route.lstrip("/")
        return "http://{}:{}/{}".format(
            self.config["NC_ASSESSMENT_REQUEST_HOST"],
            self.config["NC_ASSESSMENT_REQUEST_PORT"],
            route)


    def plans_uri(self,
            route):
        route = route.lstrip("/")
        return "http://{}:{}/{}".format(
            self.config["NC_PLAN_HOST"],
            self.config["NC_PLAN_PORT"],
            route)


    def on_perform_nca(self,
            channel,
            method_frame,
            header_frame,
            body):

        # Message passed in is the uri to the request to execute

        sys.stdout.write("received message: {}\n".format(body))
        sys.stdout.flush()

        try:

            # Get the request
            request_uri = body
            response = requests.get(request_uri)

            assert response.status_code == 200, response.text

            request = response.json()["assessment_request"]

            skip_request = False

            if request["status"] != "queued":
                sys.stdout.write(
                    "Skipping query because 'status' is not 'queued', "
                    "but '{}'".format(request["status"]))
                sys.stdout.flush()
                skip_request = True

            if not skip_request:

                # Mark the request as 'executing'
                payload = {
                    "status": "executing"
                }
                response = requests.patch(request_uri, json=payload)
                assert response.status_code == 200, response.text


                # Collect all information necessary for the execution of the
                # assessment

                request = response.json()["assessment_request"]
                plan_uri = self.plans_uri(request["plan"])
                response = requests.get(plan_uri)
                assert response.status_code == 200, response.text

                plan = response.json()["plan"]
                assert plan["status"] == "classified"


                # Perform the assessment steps


                # TODO
                # - Do whatever it takes to get the assessment done
                #     - Create a workspace
                #     - Format/clip/... input data
                #     - Perform/request calculations
                #     - Postprocess the results for visualization
                #     - Remove temp stuff

                # ...



                with tempfile.TemporaryDirectory() as temp_directory_pathname:

                    zip_filename = "assessment_result.zip"
                    zip_pathname = os.path.join(temp_directory_pathname,
                        zip_filename)


                    # Create zip-file with raw results
                    with zipfile.ZipFile(zip_pathname, "w") as zip_file:
                        # TODO Add the result files
                        # ...

                        # zip_file.write("/etc/hosts")

                        pass

                        # zip_file.writestr("metainfo.txt", "Blahblahblah")



                    with open(zip_pathname) as zip_file:
                        # Add results resource
                        payload = {
                            "request_id": request["id"],
                            # "data": "data.zip",
                        }
                        files = {
                            "data": (None, json.dumps(payload),
                                "application/json"),
                            "result": (zip_filename, zip_file,
                                "application/zip")
                        }
                        response = requests.post(
                            self.assessment_request_uri("assessment_results"),
                            files=files)
                        assert response.status_code == 201, response.text
                        assessment_result = \
                            response.json()["assessment_result"]


                # Add indicator result resources
                for i in range(4):
                    payload = {
                        "result_id": assessment_result["id"],
                        "difference": "diff{}.map".format(i),
                        "statistics": {
                            "current": {
                                "min": i * 0.5,
                                "mean": i * 5.5,
                                "max": i * 10.5
                            },
                            "new": {
                                "min": i * 0.5,
                                "mean": i * 5.5,
                                "max": i * 10.5
                            },
                        },
                    }
                    response = requests.post(
                        self.assessment_request_uri(
                            "assessment_indicator_results"),
                        json={"assessment_indicator_result": payload})
                    assert response.status_code == 201, response.text



                # Mark the request as 'finished'
                payload = {
                    "status": "succeeded"
                }
                response = requests.patch(request_uri, json=payload)
                assert response.status_code == 200, response.text





                # Notify the user
                # TODO Let RabbitMQ handle this? Just post a message and let
                #      subscribers act on it.




            ### body = body.decode("utf-8")
            ### sys.stdout.write("{}\n".format(body))
            ### sys.stdout.flush()
            ### data = json.loads(body)
            ### plan_uri = data["uri"]
            ### workspace_name = data["workspace"]
            ### response = requests.get(plan_uri)

            ### assert response.status_code == 200, response.text

            ### plan = response.json()["plan"]
            ### pathname = plan["pathname"]
            ### status = plan["status"]
            ### skip_registration = False


            ### if status != "uploaded":
            ###     sys.stderr.write("Skipping plan because 'status' is not "
            ###         "'uploaded', but '{}'".format(status))
            ###     sys.stderr.flush()
            ###     skip_registration = True


            ### if not skip_registration:

            ###     assert status == "uploaded", status

            ###     layer_name = register_raster(
            ###         pathname,
            ###         workspace_name,
            ###         geoserver_uri=self.config["NC_GEOSERVER_URI"],
            ###         geoserver_user=self.config["NC_GEOSERVER_USER"],
            ###         geoserver_password=self.config["NC_GEOSERVER_PASSWORD"])

            ###     # Mark plan as 'registered'.
            ###     payload = {
            ###         "layer_name": layer_name,
            ###         "status": "registered"
            ###     }
            ###     response = requests.patch(plan_uri, json=payload)

            ###     assert response.status_code == 200, response.text


        except Exception as exception:

            sys.stderr.write("{}\n".format(traceback.format_exc()))
            sys.stderr.flush()

            # Mark the request as 'finished'
            payload = {
                "status": "failed"
            }
            response = requests.patch(request_uri, json=payload)
            assert response.status_code == 200, response.text


        channel.basic_ack(delivery_tag=method_frame.delivery_tag)


    def run(self,
            host):

        self.credentials = pika.PlainCredentials(
            self.config["NC_RABBITMQ_DEFAULT_USER"],
            self.config["NC_RABBITMQ_DEFAULT_PASS"]
        )
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host="rabbitmq",
            virtual_host=self.config["NC_RABBITMQ_DEFAULT_VHOST"],
            credentials=self.credentials,
            # Keep trying for 8 minutes.
            connection_attempts=100,
            retry_delay=5  # Seconds
        ))
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)

        self.channel.queue_declare(
            queue="perform_nca",
            durable=True)
        self.channel.basic_consume(
            self.on_perform_nca,
            queue="perform_nca")

        try:
            sys.stdout.write("Start consuming...\n")
            sys.stdout.flush()
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()

        sys.stdout.write("Close connection...\n")
        sys.stdout.flush()
        self.connection.close()


def create_app(
        configuration_name):

    app = AssessmentExecutor()

    configuration_ = configuration[configuration_name]
    app.config.from_object(configuration_)
    configuration_.init_app(app)

    return app
