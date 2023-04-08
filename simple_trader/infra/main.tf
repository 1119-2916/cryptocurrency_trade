resource "google_pubsub_topic" "simple-trader-trigger" {
  name = "simple-trader-trigger"
}

resource "google_cloud_scheduler_job" "simple-trader-trigger-job" {
  name        = "simple-trader-trigger-job"
  description = "simple trader trigger job"
  schedule    = "*/1 * * * *"
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

data "archive_file" "source_archive_trader" {
  type = "zip"
  source_dir = "${path.cwd}/../functions/trader"
  output_path = "${path.cwd}/../functions/trader.zip"
}

resource "google_storage_bucket" "cloudfunctions-source" {
  name = "11192916-cf-source"
  location = var.region
}

resource "google_storage_bucket_object" "functions_source_trader" {
  name = "trader/${data.archive_file.source_archive_trader.output_md5}.zip}"
  bucket = google_storage_bucket.cloudfunctions-source.name
  source = data.archive_file.source_archive_trader.output_path
}

resource "google_cloudfunctions2_function" "trader" {
  name = "trader"
  location =  var.region

  build_config {
    runtime = "python310"
    entry_point = "subscribe"
    source {
      storage_source {
        bucket = google_storage_bucket.cloudfunctions-source.name
        object = google_storage_bucket_object.functions_source_trader.name
      }
    }
  }
  service_config {
    max_instance_count  = 1
    available_memory    = "256M"
    timeout_seconds     = 60
  }
  event_trigger {
    trigger_region = var.region
    event_type = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic = google_pubsub_topic.simple-trader-trigger.id
  }
}