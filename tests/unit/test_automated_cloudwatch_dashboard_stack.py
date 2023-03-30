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

import aws_cdk as core
import aws_cdk.assertions as assertions

from automated_cloudwatch_dashboard.automated_cloudwatch_dashboard_stack import AutomatedCloudWatchDashboardStack

# example tests. To run these tests, uncomment this file along with the example
# resource in automated_cloudwatch_dashboard/automated_cloudwatch_dashboard_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AutomatedCloudWatchDashboardStack(app, "automated-cloudwatch-dashboard")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
