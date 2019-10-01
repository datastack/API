resource "aws_instance" "api" {
  availability_zone = var.availability_zone
  ami = "ami-0b69ea66ff7391e80"
  instance_type = "t2.micro"
  associate_public_ip_address = true
  subnet_id = var.subnet_id
  security_groups = [aws_security_group.ec2_api.id]
  key_name = "fernandes"
}