SHELL := /bin/bash

.PHONY: backup
backup:
	@bash scripts/backup_repo.sh

