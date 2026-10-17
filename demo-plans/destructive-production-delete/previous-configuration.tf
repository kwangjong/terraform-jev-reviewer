# The database resource that existed in state before a removal from configuration.
# This file has a .tf suffix only to document the source of the destroy plan; do
# not run it or apply it. A real destroy plan is produced when this resource is
# removed from a state-backed configuration.
resource "aws_db_instance" "primary" {
  identifier             = "production-primary"
  engine                 = "postgres"
  instance_class         = "db.t4g.micro"
  allocated_storage      = 20
  username               = "app_admin"
  password               = "not-a-real-password"
  skip_final_snapshot    = false
  publicly_accessible    = false
}
