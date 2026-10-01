# ChainShield AI

### AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic

**From Raw Blockchain Transactions to Actionable Threat Intelligence**

ChainShield AI is a blockchain investigation platform built to help analyze Bitcoin transaction data and find patterns that may need further investigation.

The main idea is simple: instead of looking at transactions one by one, ChainShield AI combines **transaction analysis, graph relationships, machine learning, behavioral features, rule-based checks, and explainable results** in one place.

The system is built as an **investigation-support tool**. It helps an investigator find unusual activity and understand the reasons behind a result. It does not make a final decision about whether a wallet or transaction is involved in a crime.

---

## Table of Contents

* [Problem]
* [What We Built]
* [Key Features]
* [How the System Works
* [System Flow]
* [System Architecture]
* [Graph-Based Analysis]
* [Machine Learning]
* [Risk Scoring]
* [Explainability]
* [Data Sources]
* [Investigation Workflow]
* [Technology Stack]
* [Project Structure]
* [Running the Project]
* [Dataset Note]
* [Example]
* [Limitations]
* [Future Scope]
* [SIH 2026]
* [Team]

---

# Problem

Bitcoin transactions are publicly available, but analyzing a large amount of transaction data manually is difficult.

A transaction is not always useful when looked at by itself. It can be connected to many wallets, transactions and other entities. When these connections become large, finding a useful pattern manually takes a lot of time.

Some of the main problems are:

### 1. Large amount of transaction data

Investigators may have to work with thousands or millions of records. Going through them manually is slow.

### 2. Hidden relationships

A suspicious pattern may involve several transactions or wallets rather than one transaction.

For example:

```text
Wallet A
   |
Transaction 1
   |
Wallet B
   |
Transaction 2
   |
Wallet C
```

Looking at each transaction separately may not show the complete relationship.

### 3. Difficult to identify unusual behavior

Patterns such as unusual transaction amounts, repeated interactions, high transaction frequency or unusual connectivity can be difficult to identify manually.

### 4. ML results can be difficult to understand

If a model simply returns:

```text
Anomaly Score: High
```

the investigator still needs to know why the transaction was flagged.

### 5. Different analysis methods are usually separated

Transaction analysis, graph analysis, anomaly detection and investigation reports may require different tools.

ChainShield AI tries to bring these parts together in one workflow.

---

# What We Built

ChainShield AI takes transaction data and processes it through multiple analysis stages.

```text
Transaction Data
       ↓
Data Validation
       ↓
Feature Extraction
       ↓
Behavioral Analysis
       ↓
Graph Analysis
       ↓
ML / Anomaly Detection
       ↓
Rule-Based Checks
       ↓
Risk Fusion
       ↓
Explainable Result
       ↓
Investigation Dashboard
```

The investigator can then explore the transaction, connected entities, graph relationships and reasons behind the detected risk indicators.

---

# Key Features

## Transaction Investigation

The platform provides a place to search and inspect transaction information.

Depending on the available dataset, the system can work with information such as:

* Transaction ID
* Wallet/entity information
* Transaction value
* Timestamp
* Transaction relationships
* Network-related information
* Risk indicators

---

## Behavioral Analysis

The system extracts useful features from transaction data to understand how an entity behaves.

Examples include:

* Transaction frequency
* Transaction amount patterns
* Incoming and outgoing activity
* Number of connections
* Repeated interactions
* Network-related features

These features are used by the analysis and ML components.

---

## Entity Relationship Graph

One of the main parts of ChainShield AI is graph-based analysis.

Transactions and entities can be represented as a network:

```text
             Wallet A
                |
          Transaction 1
                |
             Wallet B
             /       \
            /         \
   Transaction 2   Transaction 3
         |               |
      Wallet C         Wallet D
```

The graph helps the investigator see relationships that are difficult to understand from a normal table.

---

## Hidden Connection Analysis

The system can explore relationships between connected entities and transactions.

This can help identify:

* Direct connections
* Indirect connections
* Transaction paths
* Highly connected entities
* Related transaction clusters

---

## Machine Learning

ChainShield AI uses machine learning as one part of the overall analysis rather than relying on ML alone.

The project includes:

* Random Forest
* Isolation Forest

Random Forest is useful when labeled transaction data is available.

Isolation Forest is used for anomaly detection where unusual records need to be identified.

---

## Hybrid Risk Analysis

The project combines different signals instead of depending on a single model.

```text
Machine Learning
       +
Behavioral Features
       +
Graph Signals
       +
Rule-Based Checks
       ↓
Risk Fusion
       ↓
Risk Indicator
```

This gives the investigator more context around a transaction or entity.

---

## Explainable Results

A major focus of the project is understanding **why** something was flagged.

Instead of showing only a score, ChainShield AI can provide supporting indicators such as:

```text
High network connectivity
Unusual transaction behavior
Abnormal transaction pattern
Suspicious relationship detected
```

The exact indicators depend on the data and analysis being performed.

---

# How the System Works

The complete processing flow is:

```text
                 ┌──────────────────────┐
                 │   Bitcoin Transaction│
                 │        Data          │
                 └──────────┬───────────┘
                            ↓
                 ┌──────────────────────┐
                 │ Validation &         │
                 │ Normalization        │
                 └──────────┬───────────┘
                            ↓
                 ┌──────────────────────┐
                 │ Feature Extraction   │
                 └──────────┬───────────┘
                            ↓
             ┌──────────────┼──────────────┐
             ↓              ↓              ↓
       Behavioral       Graph          ML / Anomaly
        Analysis       Analysis          Detection
             │              │              │
             └──────────────┼──────────────┘
                            ↓
                 ┌──────────────────────┐
                 │ Rule-Based Analysis  │
                 └──────────┬───────────┘
                            ↓
                 ┌──────────────────────┐
                 │ Risk Fusion          │
                 └──────────┬───────────┘
                            ↓
                 ┌──────────────────────┐
                 │ Explainability       │
                 └──────────┬───────────┘
                            ↓
                 ┌──────────────────────┐
                 │ Investigation UI     │
                 └──────────────────────┘
```

---

# System Architecture

ChainShield AI is divided into a frontend, backend and analysis layer.

```text
┌─────────────────────────────────────────────┐
│                  FRONTEND                   │
│                                             │
│ React + Tailwind CSS + Vite                 │
│                                             │
│ Dashboard | Search | Graph | Alerts |       │
│ Investigations | Reports                    │
└──────────────────────┬──────────────────────┘
                       │
                       │ REST API
                       ↓
┌─────────────────────────────────────────────┐
│                  BACKEND                    │
│                                             │
│ Python + FastAPI + Pydantic                 │
│                                             │
│ API | Authentication | Data Processing      │
└──────────────────────┬──────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────┐
│             ANALYSIS LAYER                  │
│                                             │
│ Feature Extraction                          │
│ Behavioral Analysis                         │
│ Graph Analysis                              │
│ Machine Learning                            │
│ Rule-Based Detection                        │
│ Risk Fusion                                 │
│ Explainability                              │
└──────────────────────┬──────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────┐
│             INVESTIGATION RESULT            │
│                                             │
│ Risk Indicators | Graph | Explanation       │
│ Transaction Details | Investigation Data     │
└─────────────────────────────────────────────┘
```

---

# Graph-Based Analysis

Graph analysis is used to represent relationships between transactions and entities.

### Nodes

Depending on the dataset, nodes can represent:

* Wallet addresses
* Transactions
* Network entities

### Edges

Edges represent relationships such as:

* Transaction connections
* Wallet interactions
* Network relationships

A simplified example:

```text
Wallet A
   |
   | Transaction
   ↓
Wallet B
   |
   | Transaction
   ↓
Wallet C
```

With more data, the graph can become:

```text
          Wallet A
          /      \
         /        \
    Wallet B     Wallet C
       |           |
       |           |
    Wallet D ---- Wallet E
```

This allows the investigator to explore relationships and identify entities that may require closer examination.

The backend contains graph analysis components for:

* Graph construction
* Traversal
* Relationship analysis
* Centrality analysis
* Entity tracing

---

# Machine Learning

ChainShield AI currently uses two main ML approaches.

## Random Forest

Random Forest is used for classification when labeled data is available.

Basic flow:

```text
Labeled Dataset
      ↓
Feature Extraction
      ↓
Model Training
      ↓
Random Forest
      ↓
Prediction
```

---

## Isolation Forest

Isolation Forest is used for anomaly detection.

It is useful when the goal is to find records that behave differently from the majority of the dataset.

```text
Transaction Features
        ↓
Isolation Forest
        ↓
Anomaly Detection
        ↓
Anomaly Signal
```

The anomaly result is treated as one signal in the overall investigation process.

---

# Risk Scoring

ChainShield AI uses a risk-fusion approach.

Different analysis components provide different signals:

```text
ML Signal
     +
Behavioral Signal
     +
Graph Signal
     +
Rule-Based Signal
     ↓
Risk Fusion Engine
     ↓
Combined Risk Indicator
```

The result can be used to prioritize transactions or entities for further investigation.

A high risk indicator does **not** mean that the entity is automatically involved in criminal activity.

It simply means that the available data contains patterns that may require further investigation.

---

# Explainability

For an investigation system, simply showing a machine learning result is not enough.

ChainShield AI therefore focuses on showing supporting information along with the result.

The general process is:

```text
Model / Analysis Result
          ↓
Relevant Features
          ↓
Detected Patterns
          ↓
Graph Context
          ↓
Human-Readable Explanation
```

For example:

```text
Risk Indicator: High

Possible supporting factors:
- Unusual transaction behavior
- High number of connections
- Abnormal transaction pattern
- Related suspicious entities
```

The investigator can then use these indicators together with the graph and transaction information.

---

# Data Sources

The current project is designed to work with local transaction datasets.

The project uses structured data containing information such as:

* Transaction identifiers
* Wallet/entity identifiers
* Transaction values
* Timestamps
* Transaction relationships
* Labels/classes where available
* Network information where available

The system also contains smaller synthetic and test datasets for development and demonstration.

---

# Investigation Workflow

A typical investigation can look like this:

### 1. Select or import data

The investigator provides transaction data or selects an available dataset.

### 2. Validate the input

The backend checks and processes the input structure.

### 3. Extract features

Relevant transaction and behavioral features are generated.

### 4. Build relationships

The system creates graph relationships between entities and transactions.

### 5. Run analysis

Multiple analysis methods are applied:

* Behavioral analysis
* Graph analysis
* Machine learning
* Rule-based checks

### 6. Combine the results

The risk-fusion layer combines the available signals.

### 7. Explain the result

The system displays supporting indicators and relevant graph context.

### 8. Investigate

The investigator can explore:

* Connected wallets
* Related transactions
* Transaction paths
* Risk indicators
* Graph relationships

### 9. Review the result

The final interpretation is left to the investigator and should be supported by additional evidence.

---

# Technology Stack

## Frontend

| Technology   | Use                   |
| ------------ | --------------------- |
| React        | User interface        |
| JavaScript   | Frontend logic        |
| Tailwind CSS | Styling               |
| Vite         | Development and build |

## Backend

| Technology | Use                  |
| ---------- | -------------------- |
| Python     | Backend and analysis |
| FastAPI    | REST API             |
| Pydantic   | Data validation      |

## Machine Learning

| Technology                       | Use                  |
| -------------------------------- | -------------------- |
| Scikit-learn                     | ML models            |
| Random Forest                    | Classification       |
| Isolation Forest                 | Anomaly detection    |
| SHAP / explainability components | Model interpretation |

## Graph Analysis

| Technology          | Use                         |
| ------------------- | --------------------------- |
| NetworkX            | Graph processing            |
| Graph algorithms    | Relationship analysis       |
| Centrality analysis | Network importance analysis |

## Data

| Data                         | Use                                              |
| ---------------------------- | ------------------------------------------------ |
| Bitcoin transaction datasets | Analysis                                         |
| Elliptic-related datasets    | Transaction classification/relationship analysis |
| Synthetic datasets           | Testing                                          |
| Custom test CSVs             | Application testing                              |

---

# Project Structure

```text
chainshield-ai/
│
├── backend/
│   │
│   ├── app/
│   │   ├── api/
│   │   ├── correlation_engine/
│   │   ├── data_sources/
│   │   ├── dataset_analysis/
│   │   ├── entity_graph/
│   │   ├── explainability/
│   │   ├── feature_engine/
│   │   ├── graph_engine/
│   │   ├── ml/
│   │   ├── models/
│   │   └── risk_engine/
│   │
│   ├── data/
│   ├── scripts/
│   ├── analysis-result.json
│   └── requirements.txt
│
└── frontend/
    │
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   ├── layout/
    │   ├── App.jsx
    │   ├── api.js
    │   └── main.jsx
    │
    ├── package.json
    ├── package-lock.json
    ├── vite.config.js
    └── tailwind.config.js
```

---

# Running the Project

## Requirements

Install the following first:

* Python 3.x
* Node.js
* npm
* Git

---

## Clone the Repository

```bash
git clone https://github.com/CodeWithFaisu07/chainshield-ai-1-.git

cd chainshield-ai-1-
```

---

## Backend

```bash
cd chainshield-ai/backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the FastAPI application:

```bash
uvicorn app.main:app --reload
```

---

## Frontend

Open another terminal:

```bash
cd chainshield-ai/frontend
```

Install dependencies:

```bash
npm install
```

Run the frontend:

```bash
npm run dev
```

Vite will display the local URL in the terminal.

---

# Dataset Note

The full `elliptic_txs_features.csv` dataset is **not included in this repository** because the file is very large.

The repository contains the smaller datasets required for testing and demonstration.

Current data structure:

```text
backend/data/
├── bitcoin_synthetic_dataset.csv
├── elliptic_txs_classes.csv
├── elliptic_txs_edgelist.csv
│
└── imports/
    ├── bitcoin_synthetic_dataset.csv
    ├── btc_transactions_dataset2_suspicious.csv
    ├── chainshield_test_1_mixed.csv
    └── chainshield_test_2_suspicious.csv
```

If the complete Elliptic feature dataset is required for the offline analysis module, it needs to be provided locally and placed at the expected path:

```text
backend/data/elliptic_txs_features.csv
```

The file is ignored by Git because of its size.

---

# Example

Suppose an investigator wants to inspect a transaction.

The process can be:

```text
Transaction ID
      ↓
Transaction Details
      ↓
Connected Entities
      ↓
Graph Expansion
      ↓
Feature Extraction
      ↓
Behavioral Analysis
      ↓
ML Analysis
      ↓
Risk Fusion
      ↓
Explanation
```

The investigator can then see the transaction's surrounding relationships and the indicators that caused the system to flag it for further review.

For example:

```text
Transaction
     |
     ├── Wallet A
     ├── Wallet B
     ├── Related Transaction 1
     └── Related Transaction 2
              |
              └── Connected Entity
```

This gives more context than looking at the original transaction record alone.

---

# Why We Use a Hybrid Approach

Different methods solve different parts of the problem.

### Machine Learning

Useful for detecting patterns in transaction features, but a model output alone may not explain the complete relationship.

### Graph Analysis

Useful for understanding relationships, paths and connected entities, but a connection by itself does not mean suspicious activity.

### Rule-Based Detection

Useful for known patterns and conditions, but fixed rules may not detect every type of unusual behavior.

### Behavioral Analysis

Provides additional context about how transactions or entities behave over time or across relationships.

For this reason, ChainShield AI combines these methods instead of depending on only one.

```text
              Transaction Data
                     |
        ┌────────────┼────────────┐
        ↓            ↓            ↓
   ML Analysis   Graph Analysis  Rules
        ↓            ↓            ↓
        └────────────┼────────────┘
                     ↓
              Risk Fusion
                     ↓
              Explanation
                     ↓
             Human Investigator
```

---

# Limitations

ChainShield AI is currently a prototype/research-oriented system, so there are some limitations.

### Bitcoin-focused

The current implementation mainly targets Bitcoin transaction analysis.

### Dataset dependency

Results depend on the quality and completeness of the available datasets.

### No automatic criminal attribution

A high risk indicator or anomaly does not prove criminal activity.

### Offline dataset limitations

When working with local datasets, the system can only analyze the information available in those datasets.

### ML limitations

Machine learning models can produce false positives and false negatives.

For this reason, results should always be reviewed by a human investigator.

---

# Future Scope

The current system can be extended in several directions.

## Real-Time Blockchain Monitoring

Connect the analysis pipeline with live blockchain data sources for continuous monitoring.

## Multi-Blockchain Support

Extend the platform to other blockchain networks.

## Advanced Graph Intelligence

Add more advanced graph algorithms and graph-based machine learning.

## Natural Language Investigation

Allow investigators to ask questions such as:

```text
"Show connected entities within three hops of this wallet."
```

and convert the query into an investigation workflow.

## Real-Time Alerts

Monitor incoming transaction data and generate alerts when selected patterns are detected.

## Better Entity Clustering

Automatically group related wallets and entities based on their transaction behavior and network relationships.

## Investigation Report Generation

Generate structured reports containing:

* Transaction information
* Graph relationships
* Risk indicators
* Supporting features
* Analysis results
* Investigation timeline

---

# SIH 2026

**Project:** ChainShield AI

**Theme:** Blockchain & Cybersecurity

**Project Focus:** AI-powered monitoring and analysis of Bitcoin transaction traffic.

The project focuses on reducing the manual effort required to analyze transaction data and helping investigators find relationships and unusual patterns.

### Core Pipeline

```text
Raw Transaction Data
        ↓
Data Processing
        ↓
Feature Extraction
        ↓
Graph + Behavioral Analysis
        ↓
Machine Learning
        ↓
Risk Fusion
        ↓
Explainable Findings
        ↓
Investigation
```

### Project Tagline

> **From Raw Blockchain Transactions to Actionable Threat Intelligence**

---

# Team Trace X

ChainShield AI was developed as part of **Smart India Hackathon 2026** by Team Trace X.

The project brings together work across:

* Blockchain analysis
* Cybersecurity
* Machine learning
* Graph/network analysis
* Backend development
* Frontend development
* Data processing

---

# Disclaimer

ChainShield AI is an investigation-support and research-oriented system.

A model prediction, anomaly, graph relationship, or risk indicator should not be treated as proof of criminal activity.

The system is intended to help investigators identify patterns and relationships that may require further examination. Final conclusions should be based on additional evidence and human investigation.

---

# Conclusion

ChainShield AI combines several analysis techniques into a single Bitcoin investigation workflow:

```text
Bitcoin Transaction Analysis
             +
Behavioral Analysis
             +
Graph Analysis
             +
Machine Learning
             +
Rule-Based Detection
             +
Explainability
             ↓
   Investigation Support
```

The goal is not to replace the investigator.

The goal is to make it easier to move from a large amount of raw transaction data to **useful relationships, unusual patterns, and understandable investigation signals**.

---

## Repository

GitHub:
https://github.com/CodeWithFaisu07/chainshield-ai-1-
