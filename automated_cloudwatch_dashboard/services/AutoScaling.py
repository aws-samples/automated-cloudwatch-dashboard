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

import aws_cdk as cdk
import boto3
from botocore.config import Config
import aws_cdk.aws_cloudwatch as cloudwatch

class AutoScaling():

    def __init__(self, region: str, tag: str, tag_values: list):
        self.namespace = "AWS/AutoScaling"
        self.tag_name = tag
        self.tag_values = tag_values
        self.botoclient = boto3.client('autoscaling', config=Config(region_name=region))
        self.as_groups = self.get_as_groups()

    def get_as_groups(self):
        '''Get AutoScaling groups filtered by tag'''
        resources = []
        response = self.botoclient.describe_auto_scaling_groups(
            Filters=[
                {
                    'Name': f'tag:{self.tag_name}',
                    'Values': self.tag_values
                }
            ],
            MaxRecords=10
        )
        resources.extend(response['AutoScalingGroups'])
        try:       
            while response['NextToken']:
                response = self.botoclient.describe_auto_scaling_groups(
                    NextToken=response['NextToken'],
                    Filters=[
                        {
                            'Name': f'tag:{self.tag_name}',
                            'Values': self.tag_values
                        }
                    ],
                    MaxRecords=10
                )
                resources.extend(response['AutoScalingGroups'])
        except KeyError:
            pass
        return resources

    def get_widgets(self):
        widgetRows = []

        if(len(self.as_groups) == 0):
            return []
        
        markdown = f'### AutoScaling Group'
        # Header line with instance name, id and type
        label = cloudwatch.TextWidget(
            markdown = markdown,
            height = 1,
            width = 24
        )
        widgetRows.append(label)
        # GroupInServiceInstances widget
        in_service = self.get_in_service()
        # GroupDesiredCapacity Widget
        desired_capacity = self.get_desired_capacity()
        widgetRows.append(cloudwatch.Row(in_service,desired_capacity))

        return widgetRows

    def get_in_service(self):
        metric_array = []
        for as_group in self.as_groups:
            as_group_name = as_group['AutoScalingGroupName']
            
            metric_array.append(cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'GroupInServiceInstances',
                    dimensions_map = dict(
                        AutoScalingGroupName = as_group_name,
                    ),
                    statistic = 'Average',
                    period = cdk.Duration.minutes(5)
                ))
        return cloudwatch.GraphWidget( 
            title='GroupInServiceInstances: Average',
            left = metric_array,
            legend_position=cloudwatch.LegendPosition.RIGHT,
            height = 6,
            width = 12
        )

    def get_desired_capacity(self):
        metric_array = []
        for as_group in self.as_groups:
            as_group_name = as_group['AutoScalingGroupName']
            
            metric_array.append(cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'GroupDesiredCapacity',
                    dimensions_map = dict(
                        AutoScalingGroupName = as_group_name,
                    ),
                    statistic = 'Average',
                    period = cdk.Duration.minutes(5)
                ))
        return cloudwatch.GraphWidget( 
            title='GroupDesiredCapacity: Average',
            left = metric_array,
            legend_position=cloudwatch.LegendPosition.RIGHT,
            height = 6,
            width = 12
        )

