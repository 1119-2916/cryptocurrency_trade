init:
	terraform init -reconfigure

plan:
	terraform plan -var-file=vars/prd.tfvars

apply:
	terraform apply -var-file=vars/prd.tfvars

apply-auto-approve:
	terraform apply -var-file=vars/prd.tfvars -auto-approve

fmt:
	terraform fmt
