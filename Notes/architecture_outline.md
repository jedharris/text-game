# Architecture Outline

# 1. Overview

To be written when the rest is done 

# 2. Core Concepts and Domain Model

## 2.1 Fundamental Entities
- Behaviors: 
    - vocabulary, 
    - commands and 
    - handlers  
- Rooms and Exits
- Actors
- Unified model
    - Items  
    - Containers
    - Doors and Locks 
-IDs and Names

## 2.2 Narration
- LLM interface (JSON)
- Narration prompts 
- Narration traits

# 3. Runtime Flow

## 3.1 Game Loop
- Input acquisition  
- Parsing  
- Intent resolution  
- Action execution  
- Output generation  

## 3.2 Error Handling and Robustness
- Handling unrecognized commands  
- Fallback mechanisms  

# 4. Parsing and Command Handling

## 4.1 Parser Architecture
- Tokenization  
- Grammar handling  
- Disambiguation rules  

## 4.2 Intent Resolution
- Matching parsed input to verbs  
- Object resolution  
- Interaction patterns  

## 4.3 Extending the Parser
- How new verbs or syntax are added  

# 5. World Model, Data Structures and Persistence

## 5.1 Internal model
- How rooms and exits are stored (Python classes, dicts, etc.)  
- How objects exist within rooms  
- How entities are represented  
- How actor state is represented 
- How the game state is updated 

# 5.2 Persistence and Save/Load
- State validation
- Save / Load game state files  
- What is saved and what is reconstructed  

# 6. Appendix

- Data model diagrams  
- Class hierarchies  
- Example flow charts  
- Coding conventions  
- Sample room or scenario definitions
