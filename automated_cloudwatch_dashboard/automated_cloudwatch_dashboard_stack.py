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

from aws_cdk import (
    # Duration,
    Stack,
    aws_cloudwatch as cloudwatch
)
from constructs import Construct
from omegaconf import OmegaConf
import os

class AutomatedCloudWatchDashboardStack(Stack):

    def import_class_from_string(self, path):
        from importlib import import_module
        module_path, _, class_name = path.rpartition('.')
        mod = import_module(module_path)
        klass = getattr(mod, class_name)
        return klass

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        __region = kwargs['env'].region
        __conf = OmegaConf.load("config.yaml")
        SUPPORTED_SERVICES = ["EC2", "S3", "ELB", "AutoScaling","Outposts"]
        
        dashboard_name = __conf.dashboard_name
        if(dashboard_name == ''): 
            dashboard_name = "Automated-CloudWatch-Dashboard"
        dashboard = cloudwatch.Dashboard(self, "CWTAG",
            dashboard_name= dashboard_name,
            period_override=cloudwatch.PeriodOverride.AUTO,
            start="-PT24H",
        )
        
        for class_file in SUPPORTED_SERVICES:
            class_file = class_file.replace('.py', '')
            # load the class in services directory
            klass = self.import_class_from_string(f'automated_cloudwatch_dashboard.services.{class_file}.{class_file}')
            # instantiate the class
            obj = klass(__region,__conf.tag_name, list(__conf.tag_values))
            # add the widgets returned by get_widgets() method to the dashboard
            for widget in obj.get_widgets() :
                dashboard.add_widgets(widget)
            
