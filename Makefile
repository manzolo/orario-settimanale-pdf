.DEFAULT_GOAL := help

IMAGE_NAME := pdf-generator
CSV        ?= orario.csv
OUTPUT_PDF := $(CSV:.csv=.pdf)

.PHONY: help build run generate clean rebuild

help: ## Mostra questo messaggio di aiuto
	@awk 'BEGIN {FS = ":.*##"; printf "\nUso: make \033[36m<target>\033[0m [CSV=file.csv]\n\nTarget disponibili:\n\n"} \
	      /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "  Parametro opzionale:"
	@echo "    CSV=file.csv   CSV da elaborare (default: orario.csv)"
	@echo "                   Il PDF generato prende lo stesso nome del CSV."
	@echo ""
	@echo "  Esempi:"
	@echo "    make                      genera orario.pdf da orario.csv"
	@echo "    make CSV=famiglia.csv     genera famiglia.pdf da famiglia.csv"
	@echo "    make run CSV=scuola.csv   solo generazione, senza rebuild"
	@echo ""

build: ## Costruisce l'immagine Docker
	docker compose build

run: ## Genera il PDF (richiede build). Usa CSV=file.csv per file diversi
	docker compose run --rm --user $$(id -u):$$(id -g) pdf-generator ./generate-pdf.sh $(CSV)
	@echo ""
	@if [ -f $(OUTPUT_PDF) ]; then \
	    echo "  PDF generato: $(OUTPUT_PDF) ($$(du -h $(OUTPUT_PDF) | cut -f1))"; \
	else \
	    echo "  ATTENZIONE: $(OUTPUT_PDF) non trovato"; \
	fi

generate: build run ## Esegue build + generazione PDF in un solo comando

rebuild: ## Ricostruisce l'immagine e rigenera il PDF
	docker compose build
	@$(MAKE) run CSV=$(CSV)

clean: ## Rimuove i file generati e l'immagine Docker
	@rm -f *.html *.pdf && echo "  Rimossi file generati" || true
	@docker rmi $(IMAGE_NAME) 2>/dev/null && echo "  Rimossa immagine $(IMAGE_NAME)" || echo "  Immagine $(IMAGE_NAME) non presente"
