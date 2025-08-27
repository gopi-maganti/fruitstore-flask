import json
import os

from troposphere import Join, Output, Parameter, Ref, Tags, Template
import troposphere.ec2 as ec2
from troposphere.iam import Role, InstanceProfile, Policy

# ===== Config paths =====
param_dir = "../cloudformation/params"
tags_file = "../cloudformation/tags/common_tags.json"
parameters = {}

# ===== Initialize Template =====
template = Template()
template.set_version("2010-09-09")
template.set_description("EC2 infrastructure with SSM, KeyPair, IAM")

# ===== Add Required Parameters =====
instance_type_param = template.add_parameter(Parameter(
    "InstanceType",
    Type="String",
    Default="t2.micro",
    Description="EC2 instance type (e.g., t2.micro, t3.small)"
))
parameters["InstanceType"] = instance_type_param

# ===== Load Optional Params =====
if os.path.exists(param_dir):
    for file in os.listdir(param_dir):
        file_path = os.path.join(param_dir, file)
        if os.path.isfile(file_path) and file.endswith(".json"):
            with open(file_path) as f:
                param_data = json.load(f)
                for name, cfg in param_data.items():
                    if name in parameters:
                        continue  # avoid duplicate
                    parameters[name] = template.add_parameter(
                        Parameter(
                            name,
                            Type=cfg["Type"],
                            Default=cfg.get("Default"),
                            Description=cfg.get("Description", ""),
                        )
                    )

# ===== Load Tags if available =====
common_tags = []
if os.path.exists(tags_file):
    with open(tags_file) as f:
        common_tags = json.load(f)

# ===== VPC =====
vpc = template.add_resource(
    ec2.VPC(
        "FruitsVPC",
        CidrBlock="10.0.0.0/16",
        EnableDnsSupport=True,
        EnableDnsHostnames=True,
        Tags=Tags(*common_tags),
    )
)

# ===== Internet Gateway & Route Table =====
igw = template.add_resource(ec2.InternetGateway("FruitsIGW", Tags=Tags(*common_tags)))

template.add_resource(ec2.VPCGatewayAttachment(
    "AttachGateway",
    VpcId=Ref(vpc),
    InternetGatewayId=Ref(igw)
))

route_table = template.add_resource(ec2.RouteTable(
    "PublicRouteTable",
    VpcId=Ref(vpc),
    Tags=Tags(*common_tags)
))

template.add_resource(ec2.Route(
    "DefaultRoute",
    DestinationCidrBlock="0.0.0.0/0",
    GatewayId=Ref(igw),
    RouteTableId=Ref(route_table),
))

# ===== Subnets =====
subnet1 = template.add_resource(ec2.Subnet(
    "PublicSubnet1",
    VpcId=Ref(vpc),
    CidrBlock="10.0.1.0/24",
    AvailabilityZone=Join("", ["us-east-1", "a"]),
    MapPublicIpOnLaunch=True,
    Tags=Tags(*common_tags),
))

template.add_resource(ec2.SubnetRouteTableAssociation(
    "Subnet1RouteAssoc",
    SubnetId=Ref(subnet1),
    RouteTableId=Ref(route_table)
))

# ===== Security Group =====
security_group = template.add_resource(ec2.SecurityGroup(
    "FruitsSG",
    GroupDescription="Allow SSH and HTTP",
    VpcId=Ref(vpc),
    SecurityGroupIngress=[
        ec2.SecurityGroupRule(IpProtocol="tcp", FromPort=22, ToPort=22, CidrIp="0.0.0.0/0"),
        ec2.SecurityGroupRule(IpProtocol="tcp", FromPort=80, ToPort=80, CidrIp="0.0.0.0/0"),
    ],
    Tags=Tags(*common_tags),
))

# ===== EC2 Key Pair (optional - no private key exposed) =====
key_pair = template.add_resource(ec2.KeyPair(
    "FruitsKeyPair",
    KeyName="Fruits-key-pair",
    Tags=Tags(*common_tags),
))

# ===== IAM Role & Instance Profile for SSM =====
ssm_role = template.add_resource(Role(
    "SSMRole",
    AssumeRolePolicyDocument={
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": ["ec2.amazonaws.com"]},
            "Action": ["sts:AssumeRole"]
        }]
    },
    Policies=[Policy(
        PolicyName="AllowSSM",
        PolicyDocument={
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "ssm:*",
                    "ec2messages:*",
                    "cloudwatch:PutMetricData",
                    "ec2:Describe*",
                    "logs:*"
                ],
                "Resource": "*"
            }]
        }
    )],
    Tags=Tags(*common_tags),
))

instance_profile = template.add_resource(InstanceProfile(
    "SSMInstanceProfile",
    Roles=[Ref(ssm_role)],
    Path="/"
))

# ===== EC2 Instance =====
ec2_instance = template.add_resource(ec2.Instance(
    "FruitsInstance",
    ImageId="ami-0e1989e836322f58b",
    InstanceType=Ref(instance_type_param),
    KeyName=Ref(key_pair),
    IamInstanceProfile=Ref(instance_profile),
    NetworkInterfaces=[
        ec2.NetworkInterfaceProperty(
            SubnetId=Ref(subnet1),
            DeviceIndex="0",
            AssociatePublicIpAddress=True,
            GroupSet=[Ref(security_group)],
        )
    ],
    Tags=Tags(*common_tags),
))

# ===== Output Public IP =====
template.add_output(Output(
    "PublicIP",
    Description="Public IP of EC2",
    Value=Ref(ec2_instance)
))

# ===== Write Template =====
out_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
os.makedirs(out_dir, exist_ok=True)

out_path = os.path.join(out_dir, "template.json")
with open(out_path, "w") as f:
    f.write(template.to_json())

print(f"✅ template.json generated at {out_path}")
