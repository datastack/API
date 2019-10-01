data "aws_vpc" "this" {
  id = "vpc-22c28f58"
}

resource "aws_security_group" "elb_api" {
  name = "ELB security group"
  description = "Input role to access HTTP 80 on ELB"
  ingress {
    from_port = 80
    protocol = "tcp"
    to_port = 80
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ec2_api" {
  name = "API security group"
  description = "Input role to access API service from ELB only"
  ingress {
    from_port = 8000
    protocol = "tcp"
    to_port = 8000
    security_groups = [aws_security_group.elb_api.id]
  }
  ingress {
    from_port = 22
    protocol = "tcp"
    to_port = 22
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port = 0
    protocol = "-1"
    to_port = 0
    cidr_blocks = ["0.0.0.0/0"]
  }
}