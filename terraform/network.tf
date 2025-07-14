resource "aws_vpc" "fruitstore_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "FruitStoreVPC"
  }
}

resource "aws_vpc_dhcp_options" "fruitstore_dhcp" {
  domain_name         = "ec2.internal"
  domain_name_servers = ["AmazonProvidedDNS"]
}

resource "aws_vpc_dhcp_options_association" "fruitstore_dhcp_assoc" {
  vpc_id          = aws_vpc.fruitstore_vpc.id
  dhcp_options_id = aws_vpc_dhcp_options.fruitstore_dhcp.id
}

resource "aws_subnet" "fruitstore_subnet_1a" {
  vpc_id                  = aws_vpc.fruitstore_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true
}

resource "aws_subnet" "fruitstore_subnet_1b" {
  vpc_id                  = aws_vpc.fruitstore_vpc.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true
}

resource "aws_internet_gateway" "fruitstore_IGW" {
  vpc_id = aws_vpc.fruitstore_vpc.id
}

resource "aws_route_table" "fruitstore_RT" {
  vpc_id = aws_vpc.fruitstore_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.fruitstore_IGW.id
  }
}

resource "aws_route_table_association" "fruitstore_RTA_1a" {
  subnet_id      = aws_subnet.fruitstore_subnet_1a.id
  route_table_id = aws_route_table.fruitstore_RT.id
}

resource "aws_route_table_association" "fruitstore_RTA_1b" {
  subnet_id      = aws_subnet.fruitstore_subnet_1b.id
  route_table_id = aws_route_table.fruitstore_RT.id
}

resource "aws_db_subnet_group" "fruitstore_subnet_group" {
  name       = "fruitstore-db-subnet-group"
  subnet_ids = [
    aws_subnet.fruitstore_subnet_1a.id,
    aws_subnet.fruitstore_subnet_1b.id
  ]

  tags = {
    Name = "FruitStoreDBSubnetGroup"
  }
}