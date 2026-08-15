terraform {
  backend "s3" {
    bucket = "fraud-api-tf-state-2004"
    key = "global/s3/terraform.tfstate"
    region = "eu-west-2"
    dynamodb_table = "fraud-api-tf-locks-2004"
    encrypt = true
  }
}
