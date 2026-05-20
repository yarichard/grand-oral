---
title: Grand Oral
emoji: 🐨
colorFrom: red
colorTo: yellow
sdk: gradio
sdk_version: 6.14.0
python_version: '3.13'
app_file: app.py
pinned: false
short_description: Agentic for Baccalaureat
---

## Grand oral topic selection
The aim of this project is to evaluate if one topic is relevant for the french baccalaureat grand oral
It is based on the following technologies:
- Langgraph for agentic AI
- Gradio for UI

The agent graph is composed with the following agents:
- Agents in charge of evaluating if a topic is relevant (pros, cons, and a judge)
- Agent in charge of building the plan (student)
- Agent in charge of generating images to illustrate the grand oral

![Langgraph](./graph.png)
