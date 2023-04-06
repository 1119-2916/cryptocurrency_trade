resource "google_storage_bucket" "cloudfunctions-source" {
  name     = "cloudfunctions-source-${var.project_id}"
  location = var.region
}

resource "google_pubsub_topic" "simple-trader-trigger" {
  name = "simple-trader-trigger"
}

resource "google_cloud_scheduler_job" "simple-trader-trigger-job" {
  name        = "simple-trader-trigger-job"
  description = "simple trader trigger job"
  schedule    = "0 10 * * *"
  time_zone   = "Asia/Tokyo"

  pubsub_target {
    topic_name = "projects/${var.project_id}/topics/${google_pubsub_topic.simple-trader-trigger.name}"
    data       = base64encode("invoke simple trader!")
  }
}

resource "google_bigquery_dataset" "simple_trader_info" {
  dataset_id                  = "simple_trader11192916"
  friendly_name               = "simple_trader"
  description                 = "simple trader info set"
  location                    = var.region
}

resource "google_bigquery_table" "trader_log" {
  dataset_id          = google_bigquery_dataset.simple_trader_info.dataset_id
  table_id            = "trader_log"
  deletion_protection = false

  schema = <<EOF
[
  {
    "name": "time",
    "type": "DATETIME",
    "mode": "REQUIRED",
    "description": "running datetime"
  },
  {
    "name": "price",
    "type": "INTEGER",
    "mode": "REQUIRED",
    "description": "price"
  },
  {
    "name": "buy",
    "type": "BOOLEAN",
    "mode": "REQUIRED",
    "description": "buy request chech result"
  }
]
EOF

}