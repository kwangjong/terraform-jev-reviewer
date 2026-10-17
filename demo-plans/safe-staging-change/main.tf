terraform {
  required_version = ">= 1.4"
}

# This provider-free configuration produces the plan.json shape in this folder.
# Run: terraform init && terraform plan -out=tfplan && terraform show -json tfplan
resource "terraform_data" "release_metadata" {
  input = {
    environment = "staging"
    release     = "2026.10.17"
  }
}
