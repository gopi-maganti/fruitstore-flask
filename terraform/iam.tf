resource "aws_iam_role" "fruitstore_role" {
  name = "fruitstore-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

resource "aws_iam_policy" "fruitstore_combined_policy" {
  name = "FruitstoreCombinedAccess"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["secretsmanager:GetSecretValue"],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:CreateBucket",
          "s3:DeleteObject",
          "s3:DeleteBucket",
        ],
        Resource = [
          "arn:aws:s3:::fruitstore-image-uploads",
          "arn:aws:s3:::fruitstore-image-uploads/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "fruitstore_combined_attach" {
  role       = aws_iam_role.fruitstore_role.name
  policy_arn = aws_iam_policy.fruitstore_combined_policy.arn
}


resource "aws_iam_instance_profile" "fruitstore_profile" {
  name = "fruitstore-instance-profile"
  role = aws_iam_role.fruitstore_role.name
}