# Project Okavango — Environmental Analysis Tool
### Advanced Programming 2026 | Group F | NOVA SBE

An AI-powered environmental monitoring tool that combines satellite imagery analysis with global deforestation data to detect at-risk areas worldwide. Built as part of a two-day hackathon focused on environmental protection using the most recent data available.

---

## What it does

- Visualizes global environmental indicators (deforestation, land protection, biodiversity) on interactive world maps
- Allows users to select any coordinates on Earth, download a live satellite image, and run AI analysis on it
- Uses local AI models via [Ollama](https://ollama.com) to describe the image and assess whether the area is at environmental risk
- Caches all results to avoid redundant computation

---

## Environmental Indicators

Data sourced from [Our World in Data](https://ourworldindata.org):

- Annual change in forest area
- Annual deforestation
- Terrestrial protected areas
- Forest area as share of land area
- Red List Index (biodiversity)

Geospatial data from [Natural Earth](https://www.naturalearthdata.com/downloads/110m-cultural-vectors/).

---

## Members

| Name | Student Number | Email |
|------|---------------|-------|
| Petra Ignjatovic | 72179 | 72179@novasbe.pt |
| Nino Makharadze | 75057 | 75057@novasbe.pt |
| Javiera Prenafeta | 75087 | 75087@novasbe.pt |
| Maddalena Manfredi | 71946 | 71946@novasbe.pt |

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com) installed and running on your machine

### 1. Clone the repository
```bash
git clone https://github.com/AdPro26/Group_F.git
cd Group_F
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
streamlit run app/ourStreamlitApp.py
```

> The app will automatically pull the required AI models (`llava:7b`, `llama3:8b`) via Ollama on first use if they are not already installed.

### 4. Run tests
```bash
pytest
```

---

## Repository Structure

```text
Group_F/
├── Project/               # Assignment documentation
│   ├── Part1.md           # Description of Part 1 assignment
│   └── Part2.md           # Description of Part 2 assignment
├── app/                   # Streamlit application
│   └── ourStreamlitApp.py
├── database/              # Cached AI analysis results
│   └── images.csv
├── downloads/             # Downloaded environmental datasets
├── images/                # Downloaded satellite images
├── notebooks/             # Prototyping scripts
│   ├── DataProcessor.py   # Data processing class
│   ├── Locations.py       # Satellite image download & AI analysis
│   └── LoadingDatasets.py
├── tests/                 # Unit tests (pytest)
│   ├── test_download_data.py
│   └── test_merge_data2.py
├── .gitignore
├── LICENSE
├── models.yaml            # AI model configuration
├── README.md              # Project documentation (this file)
└── main.py                # Main execution script
```

---

## AI Configuration

The AI pipeline is fully configurable via [`models.yaml`](models.yaml):

```yaml
image_analysis:
  model: "llava:7b"          # Vision model for image description
  prompt: "Describe in detail what you see in this satellite image."
  max_tokens: 500

text_analysis:
  model: "llama3:8b"         # Text model for risk assessment
  prompt: "Based on the following satellite image description, is there any environmental danger present? Answer Y or N followed by a brief explanation."
  max_tokens: 200
```

To use different models, simply update `models.yaml` — no code changes needed.

---

## Environmental Danger Examples

Below are three examples of the app successfully identifying environmental risks.

### Example 1 — <!-- Location name -->
**Coordinates:** <!-- lat, lon, zoom -->

<!-- Add screenshot of the app here: ![Example 1](images/example1.png) -->

> **Image description:** <!-- paste the model's description -->

> ⚠️ **ENVIRONMENTAL RISK DETECTED** — <!-- paste the risk assessment summary -->

---

### Example 2 — <!-- Location name -->
**Coordinates:** <!-- lat, lon, zoom -->

<!-- Add screenshot of the app here: ![Example 2](images/example2.png) -->

> **Image description:** <!-- paste the model's description -->

> ⚠️ **ENVIRONMENTAL RISK DETECTED** — <!-- paste the risk assessment summary -->

---

### Example 3 — <!-- Location name -->
**Coordinates:** <!-- lat, lon, zoom -->

<!-- Add screenshot of the app here: ![Example 3](images/example3.png) -->

> **Image description:** <!-- paste the model's description -->

> ⚠️ **ENVIRONMENTAL RISK DETECTED** — <!-- paste the risk assessment summary -->

---

## Contribution to UN Sustainable Development Goals

This project directly supports three of the UN's [Sustainable Development Goals](https://sdgs.un.org/goals):

**SDG 13 — Climate Action**: Deforestation is one of the largest contributors to greenhouse gas emissions. By making it easy to visualize annual deforestation trends and detect at-risk areas from satellite imagery, this tool supports early intervention and evidence-based climate policy.

**SDG 15 — Life on Land**: The tool aggregates data on forest area change, land degradation, and terrestrial protected areas, enabling users to monitor the health of land ecosystems across any country. The AI image analysis layer allows on-demand inspection of any area on Earth for signs of environmental damage such as clear-cutting, mining, or urban encroachment.

**SDG 14 — Life Below Water**: Coastal deforestation and land degradation directly impact marine ecosystems through runoff and sedimentation. By flagging at-risk coastal areas, the tool can help identify threats to nearby water bodies before they escalate.

---

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
