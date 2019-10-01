resource "aws_elb" "default-elb" {
  name = "default-elb"
  listener {
    instance_port = 8000
    instance_protocol = "http"
    lb_port = 80
    lb_protocol = "http"
  }
  health_check {
    healthy_threshold = 10
    interval = 30
    target = "HTTP:8000/healthcheck.html"
    timeout = 5
    unhealthy_threshold = 2
  }
  instances = [aws_instance.api.id]
  security_groups = [aws_security_group.elb_api.id, aws_security_group.ec2_api.id]
  subnets = [var.subnet_id]
}