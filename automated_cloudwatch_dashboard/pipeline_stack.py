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
    Stack,
    aws_codecommit as codecommit,
    pipelines as pipelines,
    aws_iam as iam,
    aws_s3_assets as s3_assets,
    Duration,
)
from omegaconf import OmegaConf
import aws_cdk.aws_events_targets as targets
import aws_cdk.aws_events as events
from .pipeline_stage import AutomatedCloudWatchDashboardDeployStage
from cdk_nag import NagSuppressions

class AutomatedCloudWatchDashboardPipeline(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # prepare the asset which contains the repo code
        code_asset = s3_assets.Asset(self, "ChartAsset",
                        path="./",
                        exclude=["cdk.out",".venv",".git"]
                    )

        # create the repo on CodeCommit
        repo = codecommit.Repository(
                self, 'AutomatedCloudWatchDashboardRepo',
                repository_name = "AutomatedCloudWatchDashboardRepo",
                code = codecommit.Code.from_asset(code_asset, "master")
        )

        # create the pipeline in CodePipeline
        pipeline = pipelines.CodePipeline(
            self,
            "CWTAGPipeline",
            synth=pipelines.ShellStep(
                "Synth",
                input=pipelines.CodePipelineSource.code_commit(repo, "master"),
                commands=[
                    "npm install -g aws-cdk",  # Installs the cdk cli on Codebuild
                    "pip install -r requirements.txt",  # Instructs Codebuild to install required packages
                    "cdk synth",
                ],            
            ),
            use_change_sets=False,
            # Defaults for all CodeBuild projects
            code_build_defaults=pipelines.CodeBuildOptions(
            # Additional policy statements for the execution role
                role_policy=[
                    iam.PolicyStatement(
                        actions=["ec2:DescribeAvailabilityZones",
                                "ec2:DescribeInstanceAttribute",
                                "ec2:DescribeInstanceTypes",
                                "ec2:DescribeInstances",
                                "ec2:DescribeNetworkInterfaces",
                                "ec2:DescribeNetworkInterfaceAttribute",
                                "ec2:DescribeVolumes",
                                "elasticloadbalancing:DescribeLoadBalancers",
                                "autoscaling:DescribeAutoScalingGroups",
                                "s3:GetBucketTagging",
                                "s3:ListBucket",
                                "s3-outposts:GetObjectTagging",
                                "s3-outposts:ListBucket",
                                "rds:DescribeDBInstances",
                                "rds:ListTagsForResource",
                                "tag:GetResources",
                                "tag:GetTagKeys",
                                "tag:GetTagValues",
                                "outposts:ListOutposts",
                                "outposts:GetOutpost",
                                "outposts:GetOutpostInstanceTypes"
                        ],
                        resources=["*"],
                        effect=iam.Effect.ALLOW
                    )
                ]
            ),
        )

        # Add stage to the pipeline to deploy the CW Dashboard
        deploy = AutomatedCloudWatchDashboardDeployStage(self, "Deploy")
        deploy_stage = pipeline.add_stage(deploy)
        
        # Build pipeline. we neet this step before using the pipeline
        # as target of the event rule
        pipeline.build_pipeline()

        NagSuppressions.add_resource_suppressions(pipeline.pipeline.artifact_bucket, [
            dict(
                id = 'AwsSolutions-S1', 
                reason = 'Artifact bucket is created by codepipelines Construct and we have no control on it to enable logging' 
            )
            ],
        );

        NagSuppressions.add_resource_suppressions(pipeline, [
            dict(
                id = 'AwsSolutions-IAM5', 
                reason = 'Suppressing errors due to CodePipeline default IAM policy' 
            )
            ],
            apply_to_children=True
        );

        NagSuppressions.add_resource_suppressions(pipeline, [
            dict(
                id = 'AwsSolutions-CB4', 
                reason = 'Suppressing errors due to CodeBuild defaults defined by CodePipeline' 
            )
            ],
            apply_to_children=True
        );

        # Create an EventBridge rule to run the pipeline at each   
        '''
        Event rule JSON: 
        {
            "source": ["aws.tag"],
            "detail-type": ["Tag Change on Resource"],
            "detail": {
                "changed-tag-keys": ["<tag name>"],
            }
        }
        '''
        conf = OmegaConf.load("config.yaml")

        rule = events.Rule(self, "EventRule",
            event_pattern=events.EventPattern(
                source = ["aws.tag"],
                detail_type = ["Tag Change on Resource"],
                detail = {
                "changed-tag-keys": [conf.tag_name],
                }
            )
        )
        # add_target accepts as input only CodePipeline objects from 
        # CodePipeline core lib. note that here we use pipelines lib
        rule.add_target(targets.CodePipeline(pipeline.pipeline))

