variable "aws_region" {
  description = "AWS region to deploy resources in"
  type        = string
  default     = "us-east-1"
}

variable "aws_zone" {
  description = "Availability zone"
  type        = string
  default     = "us-east-1a"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_key_path" {
  description = "Path to your local public SSH key"
  type        = string
}

variable "private_key_path" {
  description = "Path to your local private SSH key"
  type        = string
}

variable "ami_id" {
  description = "Ubuntu AMI ID"
  type        = string
}

variable "db_username" {
  description = "Database username"
  type        = string
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Database name"
  type        = string
}

variable "s3_bucket_name" {
  type        = string
  description = "The name of the S3 bucket to upload images"
}

variable "db_secret_name" {
  description = "The name of the AWS Secrets Manager secret for the database credentials"
  type        = string
}
