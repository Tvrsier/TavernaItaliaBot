# TavernaBot 🍺

**TavernaBot** is a Discord bot written in **Python** using **py-cord**, designed to provide
a **server-based virtual economy** with a strong focus on scalability, configurability,
and clean architecture.

The project is being developed for the Italian community  
**“La Taverna di League of Legends”**, but it is designed to be reusable across multiple servers.

---

## ✨ Core Features

- 📈 **XP & Leveling system**
- 💰 **Server-based economy** (guild + user)
- 🛡️ **Restricted command access** (roles / admin / progression-based)
- 🛒 Reward & shop system (roles, perks, custom actions)
- 🧾 Automatic command logging with embeds
- 🧠 Optimized database access with Tortoise ORM
- 📦 Architecture designed for **PEX-based releases**

---

## 🗂️ Project Structure

```text
TavernaBot/
├── app/
│   ├── bot/                # Bot core
│   ├── cogs/               # Commands & listeners
│   ├── checks/             # Custom permission checks
│   ├── lib/
│   │   ├── db/             # Database (Tortoise ORM)
│   │   └── extension_context.py
│   └── logger/             # Centralized logging
│
├── data/                   # SQLite DB / runtime files (ignored)
├── logs/                   # Log files (ignored)
├── info.py                 # Project metadata
├── README.md
└── LICENSE
