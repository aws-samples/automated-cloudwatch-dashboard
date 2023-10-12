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

class Outposts():
    def __init__(self, region: str, tag: str, tag_values: list):
        self.namespace = "AWS/Outposts"
        self.tag_name = tag
        self.tag_values = tag_values
        self.botoclient = boto3.client('outposts', config=Config(region_name=region))
        self.outposts = self.get_outposts()
        self.instance_types = self.get_instance_types()
 
    def get_outposts(self):
        resources = []
        response = self.botoclient.list_outposts(
            MaxResults = 40
        )
        resources.extend(response['Outposts'])
        try:       
            while response['NextToken']:
                response = self.botoclient.list_outposts(
                NextToken = response['NextToken'],
                MaxResults = 40
                )
                resources.extend(response['Outposts'])
        except KeyError:
            pass
        return resources
    
    def get_instance_types(self):
        instance_types = {}
        response = {}
        for outpost in self.outposts: 
            outpost_id = outpost['OutpostId']
            response = self.botoclient.get_outpost_instance_types(
                MaxResults=40,
                OutpostId=outpost_id,
            )
            instance_types[outpost_id] = response['InstanceTypes']
        try:       
            while response['NextToken']:
                response = self.botoclient.get_outpost_instance_types(
                    NextToken=response['NextToken'],
                    OutpostId=outpost_id,
                    MaxResults=40
                )
                instance_types[outpost_id] = response['InstanceTypes']
        except KeyError:
            pass
        return instance_types

    def get_widgets(self):
        widgetRows = []

        if(len(self.outposts) == 0):
            return []
        
        for outpost in self.outposts:
            # Skip if the Outpost is not in Active state
            if( outpost['LifeCycleStatus'] != 'ACTIVE' ):
                continue

            outpost_id = outpost['OutpostId']
            outpost_name = outpost['Name']        
            markdown = f'### Outpost {outpost_id} - {outpost_name}'
            # Header line with instance name, id and type
            label = cloudwatch.TextWidget(
                markdown = markdown,
                height = 1,
                width = 24
            )
            widgetRows.append(label)
            # Instance Types Available
            instance_types_widget = self.get_instance_types_available_widget(outpost)
            widgetRows.append(cloudwatch.Row(instance_types_widget))
            # Instance Types Used
            instance_types_widget = self.get_instance_types_used_widget(outpost)
            widgetRows.append(cloudwatch.Row(instance_types_widget))
            # EBS capacity
            ebs_capacity_widget = self.get_ebs_capacity_widget(outpost)
            # S3 Capacity 
            s3_capacity_widget = self.get_s3_capacity_widget(outpost)
            #ConnectedStatus
            conn_status_widget = self.get_conn_status_widget(outpost)
            widgetRows.append(cloudwatch.Row(ebs_capacity_widget, s3_capacity_widget,conn_status_widget))


        return widgetRows

    def get_s3_capacity_widget(self, outpost):
        outpost_id = outpost['OutpostId']
        outpost_name = outpost['Name']
        account = outpost['OwnerId']  
        return cloudwatch.GraphWidget( 
            title=f'S3 Capacity - {outpost_name}',
            left = [
                cloudwatch.Metric(
                    namespace = "AWS/S3Outposts",
                    metric_name = 'OutpostTotalBytes',
                    dimensions_map = dict(
                        OutpostId = outpost_id,
                    ),
                    statistic = 'Average',
                    period = cdk.Duration.minutes(5),
                    account = account,
                ),
                cloudwatch.Metric(
                    namespace = "AWS/S3Outposts",
                    metric_name = 'OutpostFreeBytes',
                    dimensions_map = dict(
                        OutpostId = outpost_id,
                    ),
                    statistic = 'Average',
                    period = cdk.Duration.minutes(5),
                    account = account,
                ) 
            ],
            height = 6,
            width = 12,
            legend_position=cloudwatch.LegendPosition.BOTTOM,
        )

    def get_conn_status_widget(self, outpost):
        outpost_id = outpost['OutpostId']
        outpost_name = outpost['Name']
        account = outpost['OwnerId']  
        return cloudwatch.GraphWidget( 
            title=f'ConnectedStatus - {outpost_name}',
            left = [
                cloudwatch.Metric(
                    namespace = "AWS/Outposts",
                    metric_name = 'ConnectedStatus',
                    dimensions_map = dict(
                        OutpostId = outpost_id,
                    ),
                    statistic = 'Average',
                    period = cdk.Duration.minutes(5),
                    account = account,
                ), 
            ],
            height = 6,
            width = 6,
            legend_position=cloudwatch.LegendPosition.BOTTOM,
        )

    def get_ebs_capacity_widget(self, outpost):
        outpost_id = outpost['OutpostId']
        outpost_name = outpost['Name']
        account = outpost['OwnerId']  
        return cloudwatch.GraphWidget( 
            title=f'EBS Capacity - {outpost_name}',
            left = [
                cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'EBSVolumeTypeCapacityUtilizationGB',
                    dimensions_map = dict(
                        OutpostId = outpost_id,
                        VolumeType= 'gp2'
                    ),
                    statistic = 'Average',
                    period = cdk.Duration.minutes(5),
                    account = account,
                    label = 'GBUsed'
                ),
                cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'EBSVolumeTypeCapacityAvailabilityGB',
                    dimensions_map = dict(
                        OutpostId = outpost_id,
                        VolumeType= 'gp2'
                    ),
                    statistic = 'Average',
                    period = cdk.Duration.minutes(5),
                    account = account,
                    label = 'GBAvail'
                ) 
            ],
            height = 6,
            width = 6,
            legend_position=cloudwatch.LegendPosition.BOTTOM,
            view=cloudwatch.GraphWidgetView.PIE,
        )

    def get_instance_types_available_widget(self, outpost):
        metric_array = []
        outpost_id = outpost['OutpostId']
        outpost_name = outpost['Name']
        account = outpost['OwnerId']

        for instance_type_obj in self.instance_types[outpost_id]:
            instance_type = instance_type_obj['InstanceType']
            metric_array.append(cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'AvailableInstanceType_Count',
                    account = account,
                    dimensions_map = dict(
                        OutpostId = outpost_id,
                        InstanceType = instance_type
                    ),
                    statistic = 'Average',
                    period = cdk.Duration.minutes(5),
                    label = f'{instance_type}'
                ))
        return cloudwatch.GraphWidget( 
            title=f'EC2 Available - {outpost_name}',
            left = metric_array,
            legend_position=cloudwatch.LegendPosition.BOTTOM,
            height = 6,
            width = 12,
        )    

    def get_instance_types_used_widget(self, outpost):
        metric_array = []
        outpost_id = outpost['OutpostId']
        outpost_name = outpost['Name']
        account = outpost['OwnerId']

        for instance_type_obj in self.instance_types[outpost_id]:
            instance_type = instance_type_obj['InstanceType']
            metric_array.append(cloudwatch.Metric(
                    namespace = self.namespace,
                    metric_name = 'UsedInstanceType_Count',
                    account = account,
                    dimensions_map = dict(
                        OutpostId = outpost_id,
                        InstanceType = instance_type
                    ),
                    statistic = 'Average',
                    period = cdk.Duration.minutes(5),
                    label = f'{instance_type}'
                ))
        return cloudwatch.GraphWidget( 
            title=f'EC2 Used - {outpost_name}',
            left = metric_array,
            legend_position=cloudwatch.LegendPosition.BOTTOM,
            height = 6,
            width = 12,
        )          
