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
import boto3, re
from botocore.config import Config
import aws_cdk.aws_cloudwatch as cloudwatch

class ELB():
    def __init__(self, region: str, tag: str, tag_values: list):
        self.namespace = "AWS/ApplicationELB"
        self.tag_name = tag
        self.tag_values = tag_values
        self.region = region
        self.botoclient = boto3.client('elbv2', config=Config(region_name=region))
        self.alb_arns = self.get_resource_groups()
        self.target_groups = self.get_target_groups()
    

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
            ResourceTypeFilters=["elasticloadbalancing:loadbalancer"],
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
                    ResourceTypeFilters=["elasticloadbalancing:loadbalancer"],
                    ResourcesPerPage=40
                )
                resources.extend(response['ResourceTagMappingList'])
        except KeyError: 
            pass
        return resources

    def get_target_groups(self):
        '''Based on the ALB ARNs collected before retrieve the associated Target Groups'''
        resources = {}
        boto3client = boto3.client('elbv2', config=Config(region_name=self.region))
        for alb_arn in self.alb_arns:
            # filter ARNs that contains /app/
            if(alb_arn['ResourceARN'].find("/app/") > 0):
                response = boto3client.describe_target_groups(
                    LoadBalancerArn=alb_arn['ResourceARN']
                )
                resources[alb_arn['ResourceARN']] = self.extract_target_groups(response)
        return resources

    def extract_target_groups(self, tgs): 
        '''Extract target group name from the ARN'''
        target_group_names = []
        for tg in tgs['TargetGroups']: 
            target_group_names.append(re.search(r':([a-zA-Z0-9_\-/]+)$', tg['TargetGroupArn']).group(1))
            # target_group_names.append(tg['TargetGroupArn'])
        return target_group_names

    def get_widgets(self):
        widgetRows = []

        if(len(self.alb_arns) == 0):
            return []
        
        for alb_arn in self.alb_arns: 
            if (alb_arn['ResourceARN'].find("/app/") < 0):
                continue
            # get alb name from alb ARNs
            alb_name = re.search(r':loadbalancer/([a-zA-Z0-9_\-/]+)$', alb_arn['ResourceARN']).group(1)
            # Header line
            markdown = f'### Application Load Balancer - {alb_name}'
            label = cloudwatch.TextWidget(
                markdown = markdown,
                height = 1,
                width = 24
            )
            widgetRows.append(label)
            # Request widget
            request_widget = self.get_request_widget(alb_name)
            # Connections widget
            connection_widget = self.get_connection_widget(alb_name)
            # Back-ends errors
            backend_response_widget = self.get_backend_response_widget(alb_arn['ResourceARN'], alb_name)
            widgetRows.append(cloudwatch.Row(request_widget, connection_widget, backend_response_widget))
            # Back-ends health
            healthy_widget = self.get_healthy_widget(alb_arn['ResourceARN'], alb_name)
            unhealthy_widget = self.get_unhealthy_widget(alb_arn['ResourceARN'], alb_name)
            widgetRows.append(cloudwatch.Row(healthy_widget, unhealthy_widget))
        return widgetRows


    def get_request_widget(self, alb):
        return cloudwatch.GraphWidget( 
            title=f'HTTP/S Requests',
            left = [
                cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'RequestCount',
                    dimensions_map = dict(
                        LoadBalancer = alb
                    ),
                    statistic = 'Sum',
                    period = cdk.Duration.minutes(1)
                ),
                cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'HTTPCode_ELB_5XX_Count',
                    dimensions_map = dict(
                        LoadBalancer = alb
                    ),
                    statistic = 'Sum',
                    period = cdk.Duration.minutes(1)
                ),
                cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'HTTPCode_ELB_3XX_Count',
                    dimensions_map = dict(
                        LoadBalancer = alb
                    ),
                    statistic = 'Sum',
                    period = cdk.Duration.minutes(1)
                ),                
                cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'HTTPCode_ELB_4XX_Count',
                    dimensions_map = dict(
                        LoadBalancer = alb
                    ),
                    statistic = 'Sum',
                    period = cdk.Duration.minutes(1)
                ),   
            ],
            height = 5,
            width = 8,
            legend_position=cloudwatch.LegendPosition.BOTTOM,
        )

    def get_healthy_widget(self, alb_arn, alb_name):
        metric_array = []
        for tg in self.target_groups[alb_arn]:
            metric_array.append(cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'HealthyHostCount',
                    dimensions_map = dict(
                        TargetGroup = tg,
                        LoadBalancer = alb_name
                    ),
                    statistic = 'Minimum',
                    period = cdk.Duration.minutes(1)
                ))
        return cloudwatch.GraphWidget( 
            title='Healthy Host: Minimum',
            left = metric_array,
            legend_position=cloudwatch.LegendPosition.BOTTOM,
            height = 3,
            width = 12
        )

    def get_unhealthy_widget(self, alb_arn, alb_name):
        metric_array = []
        for tg in self.target_groups[alb_arn]:
            metric_array.append(cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'UnHealthyHostCount',
                    dimensions_map = dict(
                        TargetGroup = tg,
                        LoadBalancer = alb_name
                    ),
                    statistic = 'Maximum',
                    period = cdk.Duration.minutes(1)
                ))
        return cloudwatch.GraphWidget( 
            title='UnHealthy Host: Maximum',
            left = metric_array,
            legend_position=cloudwatch.LegendPosition.BOTTOM,
            height = 3,
            width = 12
        )

    def get_backend_response_widget(self, alb_arn, alb_name):
        metric_array = []
        for tg in self.target_groups[alb_arn]:
            metric_array.append(cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'TargetResponseTime',
                    dimensions_map = dict(
                        TargetGroup = tg,
                        LoadBalancer = alb_name
                    ),
                    statistic = 'Average',
                    period = cdk.Duration.minutes(1)
                ))
        return cloudwatch.GraphWidget( 
            title='Target Response Time: Average',
            left = metric_array,
            legend_position=cloudwatch.LegendPosition.BOTTOM,
            height = 5,
            width = 8
        )

    def get_connection_widget(self, alb):
        return cloudwatch.GraphWidget( 
            title=f'TCP connections',
            left = [
                cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'ActiveConnectionCount',
                    dimensions_map = dict(
                        LoadBalancer = alb
                    ),
                    statistic = 'Sum',
                    period = cdk.Duration.minutes(1)
                ),
                cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'ClientTLSNegotiationErrorCount',
                    dimensions_map = dict(
                        LoadBalancer = alb
                    ),
                    statistic = 'Sum',
                    period = cdk.Duration.minutes(1)
                ),
                cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'NewConnectionCount',
                    dimensions_map = dict(
                        LoadBalancer = alb
                    ),
                    statistic = 'Sum',
                    period = cdk.Duration.minutes(1)
                ),                
                cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'RejectedConnectionCount',
                    dimensions_map = dict(
                        LoadBalancer = alb
                    ),
                    statistic = 'Sum',
                    period = cdk.Duration.minutes(1)
                ),   
            ],
            height = 5,
            width = 8,
            legend_position=cloudwatch.LegendPosition.BOTTOM,
        )
