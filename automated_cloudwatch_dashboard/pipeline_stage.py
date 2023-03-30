# ----------------------------------------------------------------------------
# LEGAL DISCALIMER
# ----------------------------------------------------------------------------
# The sample code; software libraries; command line tools; proofs of concept;
# templates; or other related technology (including any of the foregoing that
# are provided by our personnel) is provided to you as AWS Content under the
# AWS Customer Agreement, or the relevant written agreement between you and
# AWS (whichever applies).You should not use this AWS Content in your 
# production accounts, or on production or other critical data. You are 
# responsible for testing, securing, and optimizing the AWS Content, such as
# sample code, as appropriate for production grade use based on your specific
# quality control practices and standards. Deploying AWS Content may incur AWS
# charges for creating or using AWS chargeable resources, such as running 
# Amazon EC2 instances or using Amazon S3 storage.
# ----------------------------------------------------------------------------

from constructs import Construct
from aws_cdk import (
    Stage
)
from .automated_cloudwatch_dashboard_stack import AutomatedCloudWatchDashboardStack
import aws_cdk as cdk
import os

class AutomatedCloudWatchDashboardDeployStage(Stage):

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        service = AutomatedCloudWatchDashboardStack(self, 'AutomatedCloudWatchDashboard', 
        env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION'))
        )
