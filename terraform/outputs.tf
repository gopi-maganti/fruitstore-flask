output public_ip {
    value = aws_instance.fruitstore_instance.public_ip
}

output "public_http"{
    value = "http://${aws_instance.fruitstore_instance.public_ip}:5000"
}