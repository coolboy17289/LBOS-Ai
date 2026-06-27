# LBOS-AI — System Design Document

## Project Name
LBOS-AI

## Creator
Made by: Lihan Badenhorst

---

# Overview

LBOS-AI is a modular, multi-language artificial intelligence training and inference system designed for experimentation, dataset generation, model training, and evaluation.

The system is built as a pipeline of independent components that communicate through structured data flow.

Pretrained models (if used) are strictly limited to:
- dataset generation
- labeling
- evaluation assistance

They are NOT used as runtime inference engines.

---

# Core Architecture

## System Flow


External Input (User / URL)
↓
Node.js API Gateway
↓
Java Orchestrator
↓
Python Data Processing & Training
↓
Custom ML Model (Lightweight)
↓
Inference Engine
↓
Evaluation Layer (R + MATLAB)
↓
Frontend Dashboard (React TSX)


---

# Language Responsibilities

## C++
- Optional performance optimization layer
- High-speed computation utilities

## TSX (React)
- Full AI control panel UI
- Dataset tools
- Training dashboard
- URL ingestion panel
- Evaluation visualization

## JavaScript (Node.js)
- API gateway
- Request routing
- WebSocket streaming
- URL ingestion handler

## Java
- Workflow orchestration
- Pipeline coordination

## Python
- Dataset preprocessing
- Training pipeline
- Data transformation

## MATLAB
- Numerical analysis layer
- Experimental computation
- Signal/matrix analysis

## R
- Statistical evaluation
- Reporting
- Performance analysis

---

# Key Features

- AI training pipeline control system
- URL ingestion system (YouTube + web content)
- Dataset generation and labeling system
- Custom model training (no runtime LLM dependency)
- Real-time logs across all system layers
- Evaluation dashboard (R + MATLAB)
- React-based full control panel UI

---

# URL INGESTION SYSTEM

Supports:
- YouTube video links
- Web articles

Pipeline:

URL → Extract → Transcribe → Clean → Chunk → Label → Dataset → Training


Outputs structured JSONL datasets for training.

---

# Repository Structure


/cpp
/frontend
/node
/java
/python
/matlab
/r
/design.md
/README.md
/LICENSE


No additional folders allowed unless absolutely required.

---

# LICENSES

## 1. MIT License (Main Software License)

Copyright (c) 2026 Lihan Badenhorst

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND.

---

## 2. Academic / Research Use Clause

This project is intended for:
- educational use
- research experimentation
- AI system design learning

Commercial deployment of trained models derived from this system may require attribution to the original author.

---

## 3. AI Training Data Clause

Any datasets generated using this system:
- remain open for educational use
- must not be used for malicious or harmful model training

---

# BUILD / INSTALLER PROMPT (FOR CLAUDE CODE)

At the end of implementation, generate an **installer-ready GitHub project** with the following requirements:

## TASK:
Create a full GitHub-ready repository for the project:

**Project Name:** lbos-ai  
**Author:** Lihan Badenhorst  

---

## REQUIREMENTS:

1. Generate a complete working project structure based on DESIGN.md
2. Create:
   - full frontend (React TSX dashboard)
   - Node.js API backend
   - Python training engine
   - Java orchestrator
   - optional C++, MATLAB, R modules if required
3. Implement URL ingestion system (YouTube + web scraping + transcription)
4. Ensure dataset flows into training pipeline
5. Ensure system runs locally with a single install command

---

## INSTALLER REQUIREMENT:

Create an installer script that:

- installs dependencies for all languages
- sets up environment automatically
- builds frontend
- starts backend services
- launches full system dashboard

Examples:
- install.sh (Linux/Mac)
- install.bat (Windows)

---

## GITHUB REQUIREMENTS:

- Initialize git repository
- Add proper .gitignore
- Create LICENSE file using MIT license
- Generate README.md automatically

---

## README REQUIREMENT:

Automatically generate a professional README.md that includes:

- project overview
- system architecture diagram
- installation instructions
- usage guide
- feature list
- author credit (Lihan Badenhorst)
- license summary

README must be generated automatically — do NOT require manual writing.

---

## FINAL OUTPUT:

- Fully working repository
- Installer scripts
- GitHub-ready structure
- Auto-generated README.md
- Clean modular architecture

---

## DESIGN PHILOSOPHY:

- minimal but powerful
- no unnecessary complexity
- every component must justify existence
- system must be runnable locally
- AI model must be trained, not hardcoded

---