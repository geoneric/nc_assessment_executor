import os


class Configuration:

    NC_ASSESSMENT_REQUEST_HOST = "nc_assessment_request"
    NC_PLAN_HOST = "nc_plan"

    NC_RABBITMQ_DEFAULT_USER = os.environ.get("NC_RABBITMQ_DEFAULT_USER")
    NC_RABBITMQ_DEFAULT_PASS = os.environ.get("NC_RABBITMQ_DEFAULT_PASS")
    NC_RABBITMQ_DEFAULT_VHOST = os.environ.get("NC_RABBITMQ_DEFAULT_VHOST")

    # NC_CLIENT_NOTIFIER_URI = os.environ.get("NC_CLIENT_NOTIFIER_URI")


    @staticmethod
    def init_app(
            app):
        pass


class DevelopmentConfiguration(Configuration):

    NC_ASSESSMENT_REQUEST_PORT = 5000
    NC_PLAN_PORT = 5000


class TestConfiguration(Configuration):

    NC_ASSESSMENT_REQUEST_PORT = 5000
    NC_PLAN_PORT = 5000


class ProductionConfiguration(Configuration):

    NC_ASSESSMENT_REQUEST_PORT = 3031
    NC_PLAN_PORT = 3031


configuration = {
    "development": DevelopmentConfiguration,
    "test": TestConfiguration,
    "acceptance": ProductionConfiguration,
    "production": ProductionConfiguration
}
