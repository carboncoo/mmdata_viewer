# Data Viewer

A Streamlit-based visualization tool for inspecting and comparing model predictions on multimodal QA datasets.

## 💡 Supported Features


1. 📊 **Data Exploration**: Browse the dataset by Task, Subtask, or Category, with support for viewing original images.

2. 🔍 **Result Comparison**: Import model prediction outputs and filter records (e.g., “Model A correct, Model B incorrect”) for efficient error analysis.

3. ⚙️ **Easy Extensibility**: Quickly integrate new datasets and prediction results via the configuration file, provided they adhere to the required JSON format.

## 🚀 Getting Started

To run the app:

```bash
bash run.sh
```

## 🛠 Dependencies

- `streamlit`
- `pandas`
- `PIL`
- `json`

## 📁 Expected Directory Structure

Each dataset profile should follow this structure:

```
example_data/
├── <dataset_name>/
│   ├── annotations.json           # Ground truth annotations
│   ├── <image_dir>/               # Image files referenced in the annotations
│   └── <pred_dir>/ (optional)     # JSON files containing model predictions
```

## 🧾 JSON File Format

### Annotations (Ground Truth)

Each entry in `annotations.json` should follow this format:

```json
[
  {
    "Question_id": "perception/diagram_and_table/diagram/0001",
    "Image": "apartment10JV.jpg",
    "Text": "What's the percentage of Operating Expenses in FY 2025 in this table?",
    "Question Type": "Multiple Choice",
    "Answer choices": [
      "(A) 24%",
      "(B) 13%",
      "(C) 12%",
      "(D) 11%",
      "(E) This image doesn't feature the data."
    ],
    "Ground truth": "B",
    "Category": "diagram", // optional
    "Subtask": "Diagram and Table", // optional
    "Task": "Perception" // optional
  }
]
```

### Model Predictions

Each prediction file should be a `.json` file named after the model (e.g., `modelA.json`) with this format:

```json
[
  {
    "Question_id": "perception/diagram_and_table/diagram/0001",
    "response": "(B)",
    "correct": true
  }
]
```

Each `Question_id` must match one from the annotation file. The `response` field contains the model's answer, and `correct` indicates whether the prediction matches the ground truth.

## ⚙️ Configuration Profiles

All dataset configurations are stored in `config_profiles.json` at the project root. Each profile maps a profile name to:

- `json_path`: Path to the annotation file (required).
- `pred_dir`: Path to the directory containing model prediction JSON files (optional; can be empty).
- `image_root`: Path to the directory containing images (required).

Example `config_profiles.json`:

```json
{
  "HRScene": {
    "json_path": "example_data/hrscene/annotations.json",
    "pred_dir": "",
    "image_root": "example_data/hrscene/images"
  },
  "MME-Realworld": {
    "json_path": "example_data/mme_realworld/MME_realworld.json",
    "pred_dir": "example_data/mme_realworld/mme_realwolrd_test_results",
    "image_root": "example_data/mme_realworld/mme_images"
  }
}
```

Feel free to modify or extend the UI via `app.py` to suit your own datasets and evaluation needs.