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
import re

class S3():

    def __init__(self, region: str, tag: str, tag_values: list):
        self.namespace = "AWS/S3"
        self.tag_name = tag
        self.tag_values = tag_values
        self.region = region
        self.buckets = self.get_bucket_names()

    def get_bucket_names(self):
        '''Get S3 buckets filtered by tag'''
        resource_groups = self.get_resource_groups()
        bucket_names = []
        for resource in resource_groups:
            # extract bucket name from the ARN included in resource 
            bucket_names.append(re.search(r':([0-9a-z\-]+)$', resource['ResourceARN']).group(1))
        return bucket_names 
     
    def get_resource_groups(self):
        boto3client = boto3.client('resourcegroupstaggingapi', config=Config(region_name=self.region))
        resources = []

        response = boto3client.get_resources(
            TagFilters=[
                {
                'Key': self.tag_name,
                'Values': self.tag_values
                },
            ],
            ResourceTypeFilters=["s3:bucket"],
            ResourcesPerPage=40
        )
        resources.extend(response['ResourceTagMappingList'])
        try:
            while response['PaginationToken'] != '':
                response = boto3client.get_resources(
                    PaginationToken=response['PaginationToken'],
                    TagFilters=[
                        {
                            'Key': self.tag_name,
                            'Values': self.tag_values
                        },
                    ],
                    ResourceTypeFilters=["s3:bucket"],
                    ResourcesPerPage=40
                )
                resources.extend(response['ResourceTagMappingList'])
        except KeyError: 
            pass
        return resources

    def get_widgets(self):
        widgetRows = []

        if(len(self.buckets) == 0):
            return []
        
        # Header line
        markdown = f'### S3 Buckets'
        label = cloudwatch.TextWidget(
            markdown = markdown,
            height = 1,
            width = 24
        )
        widgetRows.append(label)
        # BucketSizeBytes: Average
        bucket_size_widget = self.get_bucket_size_widget()
        # NumberOfObjects: Average
        obj_num = self.get_obj_num()
        widgetRows.append(cloudwatch.Row(bucket_size_widget,obj_num))
        return widgetRows

    def get_bucket_size_widget(self):
        metric_array = []
        for bucket in self.buckets:
            metric_array.append(cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'BucketSizeBytes',
                    dimensions_map = dict(
                        BucketName = bucket,
                        StorageType = 'StandardStorage'
                    ),
                    statistic = 'Average',
                    period = cdk.Duration.hours(24)
                ))
        return cloudwatch.GraphWidget( 
            title='BucketSizeBytes: Average',
            left = metric_array,
            legend_position=cloudwatch.LegendPosition.RIGHT,
            height = 6,
            width = 12
        )

    def get_obj_num(self):
        metric_array = []
        for bucket in self.buckets:
            metric_array.append(cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'NumberOfObjects',
                    dimensions_map = dict(
                        BucketName = bucket,
                        StorageType = 'AllStorageTypes'
                    ),
                    statistic = 'Average',
                    period = cdk.Duration.hours(24)
                ))
        return cloudwatch.GraphWidget( 
            title='NumberOfObjects: Average',
            left = metric_array,
            legend_position=cloudwatch.LegendPosition.RIGHT,
            height = 6,
            width = 12
        )