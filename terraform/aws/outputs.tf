output "elb_dnd" {
  value = aws_elb.default-elb.dns_name
}