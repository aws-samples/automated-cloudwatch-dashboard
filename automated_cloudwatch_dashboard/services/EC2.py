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

class EC2():

    def __init__(self, region: str, tag: str, tag_values: list):
        self.namespace = "AWS/EC2"
        self.ebsnamespace = "AWS/EBS"
        self.tag_name = tag
        self.tag_values = tag_values
        self.botoclient = boto3.client('ec2', config=Config(region_name=region))
        self.instances = self.get_instances()
        self.volumes = self.get_volumes()
 
    def get_instances(self):
        '''Get EC2 instances filtered by tag'''
        resources = []
        response = self.botoclient.describe_instances(
            Filters=[
                {
                    'Name': f'tag:{self.tag_name}',
                    'Values': self.tag_values
                }
            ],
            MaxResults=10
        )
        resources.extend(response['Reservations'])
        try:       
            while response['NextToken']:
                response = self.botoclient.describe_instances(
                    NextToken=response['NextToken'],
                    Filters=[
                        {
                            'Name': f'tag:{self.tag_name}',
                            'Values': self.tag_values
                        }
                    ],
                    MaxResults=10
                )
                resources.extend(response['Reservations'])
        except KeyError:
            pass
        return resources

    def get_volumes(self):
        '''Get volumes attached to the instances filtered by tag'''
        resources = {}
        for instance in self.instances:
            instance_id = instance['Instances'][0]['InstanceId']
            response = self.botoclient.describe_volumes(
                Filters=[
                    {
                    'Name': 'attachment.instance-id',
                    'Values': [
                    instance_id
                    ]
                    }
                ]
            )
            resources[instance_id] = response['Volumes']
        return resources

    def get_widgets(self):
        widgetRows = []

        if(len(self.instances) == 0):
            return []
        
        for instance in self.instances:
            instance_id = instance['Instances'][0]['InstanceId']
            instance_type = instance['Instances'][0]['InstanceType']
            instance_name = self.get_instance_name(instance['Instances'][0]['Tags'])

            markdown = f'### Instance {instance_name} - {instance_id} ({instance_type})'
            # Header line with instance name, id and type
            label = cloudwatch.TextWidget(
                markdown = markdown,
                height = 1,
                width = 24
            )
            widgetRows.append(label)
            # CPU Widget
            cpu_widget = self.get_cpu_widget(instance_id)
            # Network Widget
            network_widget = self.get_network_widget(instance_id)
            widgetRows.append(cloudwatch.Row(cpu_widget,network_widget))

            # Disk widget
            if( self.is_nitro(instance_type) ):
                ebs_widget = self.get_ebs_nitro_widget(instance_id)
                widgetRows.append(cloudwatch.Row(ebs_widget))
            else: 
                for volume in self.volumes[instance_id]:
                    ebs_widget = self.get_ebs_widget(instance_id, volume)
                    widgetRows.append(cloudwatch.Row(ebs_widget))

        return widgetRows

    def get_instance_name(self, tags):
        instance_name = ''
        for tag in tags: 
            if(tag['Key'] == 'Name'):
                instance_name = tag['Value']
        return instance_name
    
    def get_cpu_widget(self, instance_id):
        return cloudwatch.GraphWidget( 
            title=f'CPU Utilization - {instance_id}',
            left = [cloudwatch.Metric(
                namespace = self.namespace,
                metric_name = 'CPUUtilization',
                dimensions_map = dict(
                    InstanceId = instance_id
                ),
                statistic = 'Maximum',
            )],
            height = 3,
            width = 12,
            legend_position=cloudwatch.LegendPosition.BOTTOM
        )
    
    def get_network_widget(self, instance_id):
        return cloudwatch.GraphWidget( 
            title=f'Network - {instance_id}',
            left = [
                cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'NetworkPacketsOut',
                    dimensions_map = dict(
                        InstanceId = instance_id
                    ),
                    statistic = 'Maximum',
                    period = cdk.Duration.minutes(1)
                ),
                cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'NetworkPacketsIn',
                    dimensions_map = dict(
                        InstanceId = instance_id
                    ),
                    statistic = 'Maximum',
                    period = cdk.Duration.minutes(1)
                ),
                cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'NetworkIn',
                    dimensions_map = dict(
                        InstanceId = instance_id
                    ),
                    statistic = 'Maximum',
                    period = cdk.Duration.minutes(1)
                ),
                cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'NetworkOut',
                    dimensions_map = dict(
                        InstanceId = instance_id
                    ),
                    statistic = 'Maximum',
                    period = cdk.Duration.minutes(1)
                ),   
            ],
            height = 3,
            width = 12,
            legend_position=cloudwatch.LegendPosition.BOTTOM
        )           

    def get_ebs_nitro_widget(self, instance_id):
        return cloudwatch.GraphWidget( 
            title=f'Disk - {instance_id}',
            left = [
                cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'EBSWriteBytes',
                    dimensions_map = dict(
                        InstanceId = instance_id
                    ),
                    statistic = 'Sum',
                    period = cdk.Duration.minutes(1)
                ),
                cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'EBSReadBytes',
                    dimensions_map = dict(
                        InstanceId = instance_id
                    ),
                    statistic = 'Sum',
                    period = cdk.Duration.minutes(1)
                ),
                cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'EBSIOBalance%',
                    dimensions_map = dict(
                        InstanceId = instance_id
                    ),
                    statistic = 'Sum',
                    period = cdk.Duration.minutes(1)
                ),
                cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'EBSWriteOps',
                    dimensions_map = dict(
                        InstanceId = instance_id
                    ),
                    statistic = 'Sum',
                    period = cdk.Duration.minutes(1)
                ),
                cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'EBSReadOps',
                    dimensions_map = dict(
                        InstanceId = instance_id
                    ),
                    statistic = 'Sum',
                    period = cdk.Duration.minutes(1)
                ),   
            ],
            height = 3,
            width = 24,
            legend_position=cloudwatch.LegendPosition.RIGHT
        ) 

    def is_nitro(self, instance_type):
        """Check if $instance_type runs on Nitro hypervisor"""
        instance_types = []
        resources = []

        response = self.botoclient.describe_instance_types(
	        InstanceTypes=[instance_type],
            Filters=[
	            {
	                'Name': 'hypervisor',
	                'Values': [
	                    'nitro',
	                ]
	            },
	        ],
	    )
        if(len(response['InstanceTypes']) > 0):
            return True
        return False

    def get_ebs_widget(self, instance_id, volume):
        volume_id = volume['VolumeId']
        return cloudwatch.GraphWidget( 
            title=f'Disk - {volume_id}',
            left = [
                cloudwatch.Metric(
                    namespace = self.ebsnamespace,
                    metric_name = 'VolumeReadBytes',
                    dimensions_map = dict(
                        VolumeId = volume_id
                    ),
                    statistic = 'Average',
                    period = cdk.Duration.minutes(1)
                ),
                cloudwatch.Metric(
                    namespace = self.ebsnamespace,
                    metric_name = 'VolumeWriteBytes',
                    dimensions_map = dict(
                        VolumeId = volume_id
                    ),
                    statistic = 'Average',
                    period = cdk.Duration.minutes(1)
                ),
                cloudwatch.Metric(
                    namespace = self.ebsnamespace,
                    metric_name = 'VolumeReadOps',
                    dimensions_map = dict(
                        VolumeId = volume_id
                    ),
                    statistic = 'Average',
                    period = cdk.Duration.minutes(1)
                ),
                cloudwatch.Metric(
                    namespace = self.ebsnamespace,
                    metric_name = 'VolumeWriteOps',
                    dimensions_map = dict(
                        VolumeId = volume_id
                    ),
                    statistic = 'Average',
                    period = cdk.Duration.minutes(1)
                ),
            ],
            height = 3,
            width = 24,
            legend_position=cloudwatch.LegendPosition.RIGHT
        )