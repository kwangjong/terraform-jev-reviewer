terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "demo-only"
  secret_key                  = "demo-only"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    s3 = "http://localhost:4566"
  }
}

variable "create_bucket" {
  type    = bool
  default = true
}

# LocalStack-only: the workflow creates this bucket then produces a genuine
# Terraform deletion plan by setting create_bucket=false.
resource "aws_s3_bucket" "production_primary" {
  count         = var.create_bucket ? 1 : 0
  bucket        = "jev-reviewer-production-primary-demo"
  force_destroy = true
}
