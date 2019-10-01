variable "vpc_id" {
  type = string
  default = "vpc-22c28f5"
  description = "ID of a VPC to be used in this project"
}
variable "subnet_id" {
  type = string
  default = "subnet-77c1013a"
  description = "ID of a Subnet to be used in this project on AZ us-east-1a"
}

variable "availability_zone" {
  type = string
  default = "us-east-1a"
  description = "A default AZ"
}