output public_ip {
    value = aws_instance.fruitstore_instance.public_ip
}

output secret_arn {
    value = aws_secretsmanager_secret.db_secret.arn
}

output "public_http"{
    value = "http://${aws_instance.fruitstore_instance.public_ip}:5000"
}