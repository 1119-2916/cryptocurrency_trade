provider "google" {
  credentials = file("./gmo-tatsuya-ikeda-fc4ce5693a5e.json")
  project     = var.project_id
  region      = var.region
}