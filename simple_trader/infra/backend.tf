terraform {
  required_version = ">= 1.4.0"
  backend "gcs" {
    bucket = "simple-trader-tfstate"
    prefix = "terraform/state"
  }
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.23"
    }
  }
}