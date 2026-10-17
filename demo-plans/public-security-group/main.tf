terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region                      = "us-east-1"
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  access_key                  = "demo-only"
  secret_key                  = "demo-only"
}

# Intentionally unsafe: this is a review example, not a configuration to apply.
resource "aws_security_group" "public_web" {
  name        = "demo-public-web"
  description = "DEMO ONLY: public HTTPS exposure"

  ingress {
    protocol    = "tcp"
    from_port   = 443
    to_port     = 443
    cidr_blocks = ["0.0.0.0/0"]
  }
}
