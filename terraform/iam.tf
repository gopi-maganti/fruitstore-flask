#-----------------------------
# EC2 Assume Role Policy
#-----------------------------
data "aws_iam_policy_document" "ec2_assume" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

#-----------------------------
# IAM Role for EC2 Instance
#-----------------------------
resource "aws_iam_role" "fruitstore_role" {
  name               = "fruitstore-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

#-----------------------------
# Secrets Manager Policy
#-----------------------------
resource "aws_iam_policy" "secrets_policy" {
  name = "FruitstoreSecretsAccess"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["secretsmanager:GetSecretValue"],
        Resource = "*"
      }
    ]
  })
}

#-----------------------------
# S3 Access Policy
#-----------------------------
resource "aws_iam_policy" "s3_policy" {
  name = "FruitstoreS3Access"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:CreateBucket",
          "s3:DeleteObject",
          "s3:DeleteBucket"
        ],
        Resource = [
          "arn:aws:s3:::fruitstore-image-uploads",
          "arn:aws:s3:::fruitstore-image-uploads/*"
        ]
      }
    ]
  })
}

#-----------------------------
# CloudWatch Logs Policy
#-----------------------------
resource "aws_iam_policy" "logs_policy" {
  name = "FruitstoreLogsAccess"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "*"
      }
    ]
  })
}

#-----------------------------
# Attach All Policies to Role
#-----------------------------
resource "aws_iam_role_policy_attachment" "attach_secrets" {
  role       = aws_iam_role.fruitstore_role.name
  policy_arn = aws_iam_policy.secrets_policy.arn
}

resource "aws_iam_role_policy_attachment" "attach_s3" {
  role       = aws_iam_role.fruitstore_role.name
  policy_arn = aws_iam_policy.s3_policy.arn
}

resource "aws_iam_role_policy_attachment" "attach_logs" {
  role       = aws_iam_role.fruitstore_role.name
  policy_arn = aws_iam_policy.logs_policy.arn
}

#-----------------------------
# IAM Instance Profile for EC2
#-----------------------------
resource "aws_iam_instance_profile" "fruitstore_profile" {
  name = "fruitstore-instance-profile"
  role = aws_iam_role.fruitstore_role.name
}
