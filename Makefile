PYTHON ?= python
export PYTHONPATH := src

.PHONY: setup sample-data validate train pipeline api dashboard eval-sheet capstone-check test docker-up

setup:
	$(PYTHON) -m pip install -r requirements.txt

sample-data:
	$(PYTHON) scripts/make_sample_data.py

validate:
	$(PYTHON) -m rebootroute.data.validation

train:
	$(PYTHON) scripts/train_models.py

pipeline:
	$(PYTHON) scripts/run_pipeline.py

api:
	uvicorn rebootroute.api.main:app --reload --host 0.0.0.0 --port 8000

dashboard:
	streamlit run src/rebootroute/dashboard/app.py

eval-sheet:
	$(PYTHON) scripts/build_human_eval_sheet.py

capstone-check:
	$(PYTHON) scripts/build_capstone_checklist.py

test:
	pytest -q

docker-up:
	docker compose up --build
