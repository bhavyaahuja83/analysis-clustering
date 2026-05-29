# Telecalling Analytics & Lead Intelligence Platform

A Python-based analytics platform designed to process large-scale telecalling datasets, generate behavioral lead clusters, identify optimal outreach windows, and produce business-facing intelligence reports.

This project was originally developed to analyze large telecalling datasets and surface actionable lead engagement insights through clustering, time-slot analysis, and AI-assisted interpretation.

---

## Features

### Data Processing

* Handles large datasets using chunked loading workflows.
* Supports preprocessing and normalization of telecalling records.
* Generates demographic and behavioral lead segments.

### Lead Clustering

* Multi-dimensional clustering using:

  * Age Groups
  * Gender
  * Income Bands
  * Profession Categories
  * Geographic Regions
  * Product / Brand Segments

* Automatically groups similar lead profiles into high-volume clusters.

### Outreach Intelligence

* Calculates:

  * Pickup Rates
  * Average Call Duration
  * High-Engagement Time Windows

* Identifies best outreach periods by:

  * Day of Week
  * Time of Day

### Reporting

* Excel export generation.
* Structured cluster summaries.
* Business-friendly output formats.

### AI-Assisted Analysis

* Local LLM integration through Ollama.
* Cluster refinement workflows.
* Automated insight generation.

### Visualization

Includes both:

* Desktop Cluster Viewer (Tkinter)
* Web-Based Cluster Dashboard (Flask + Bootstrap)

---

## Technology Stack

### Core

* Python
* Pandas
* OpenPyXL
* IJSON

### Analytics

* Custom clustering engine
* Statistical aggregation
* Behavioral segmentation

### AI

* Ollama
* Phi-3

### UI

* Tkinter
* Flask
* Bootstrap

---

## Project Structure

```text
.
├── main.py
├── data_loader.py
├── cluster_creator.py
├── time_analysis.py
├── export_excel.py
├── ai_loader.py
├── cluster_gui.py
├── cluster_web_app.py
├── requirements.txt
└── data/
```

---

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd telecalling-analytics-platform
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate:

Windows

```bash
.venv\Scripts\activate
```

Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Running the Analytics Pipeline

```bash
python main.py
```

The pipeline will:

1. Load data
2. Preprocess records
3. Generate lead clusters
4. Analyze engagement windows
5. Export results

Output:

```text
output_clusters.xlsx
```

---

## Running the Desktop Viewer

```bash
python cluster_gui.py
```

Provides a desktop interface for browsing cluster outputs and engagement patterns.

---

## Dataset

The original production dataset is not included in this repository.

A synthetic demonstration dataset can be used for testing and showcasing functionality.

This repository contains implementation code only and does not include confidential business data.

---

## Use Cases

* Lead Segmentation
* Telecalling Optimization
* Campaign Planning
* Contact Center Analytics
* Customer Engagement Analysis
* Outreach Timing Optimization

---

## Future Improvements

* Real-time dashboarding
* Predictive lead scoring
* Automated campaign recommendations
* CRM integrations
* Cloud deployment
* Advanced ML-based clustering

---

## Disclaimer

This repository is intended for demonstration and portfolio purposes. Any production datasets, customer information, and business-sensitive records have been removed for confidentiality and privacy compliance.
