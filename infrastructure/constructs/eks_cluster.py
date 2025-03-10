from aws_cdk import (
    aws_eks as eks,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct


class EksClusterConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)
        
        # Create VPC for EKS cluster
        vpc = ec2.Vpc(
            self,
            "MedConnectVpc",
            max_azs=2,
            nat_gateways=1,
        )
        
        # Create IAM role for EKS cluster
        cluster_role = iam.Role(
            self,
            "ClusterRole",
            assumed_by=iam.ServicePrincipal("eks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSClusterPolicy"),
            ],
        )
        
        # Create IAM role for EKS node group
        node_role = iam.Role(
            self,
            "NodeRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSWorkerNodePolicy"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKS_CNI_Policy"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly"),
            ],
        )
        
        # Create EKS cluster
        cluster = eks.Cluster(
            self,
            "MedConnectCluster",
            cluster_name="med-connect-cluster",
            version=eks.KubernetesVersion.V1_24,
            vpc=vpc,
            default_capacity=0,  # We will create a managed node group instead
            role=cluster_role,
        )
        
        # Add managed node group
        cluster.add_nodegroup_capacity(
            "ManagedNodeGroup",
            instance_types=[ec2.InstanceType("m5.large")],
            min_size=2,
            max_size=4,
            desired_size=2,
            node_role=node_role,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
        )
        
        # Install Kubernetes Metrics Server
        cluster.add_helm_chart(
            "metrics-server",
            chart="metrics-server",
            repository="https://kubernetes-sigs.github.io/metrics-server/",
            namespace="kube-system",
        )
        
        # Install AWS Load Balancer Controller
        cluster.add_helm_chart(
            "aws-load-balancer-controller",
            chart="aws-load-balancer-controller",
            repository="https://aws.github.io/eks-charts",
            namespace="kube-system",
            values={
                "clusterName": cluster.cluster_name,
            },
        )
        
        # Export cluster name
        self.cluster_name = cluster.cluster_name 