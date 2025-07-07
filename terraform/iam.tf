resource "aws_iam_role" "fruitstore_role" {
  name = "fruitstore-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

resource "aws_iam_policy" "secrets_policy" {
  name   = "FruitstoreSecretsAccess"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["secretsmanager:GetSecretValue", "logs:PutLogEvents"],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "secrets_attach" {
  role       = aws_iam_role.fruitstore_role.name
  policy_arn = aws_iam_policy.secrets_policy.arn
}

resource "aws_iam_instance_profile" "fruitstore_profile" {
  name = "fruitstore-instance-profile"
  role = aws_iam_role.fruitstore_role.name
}