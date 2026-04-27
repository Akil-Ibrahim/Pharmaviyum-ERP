# WebSocket Protocol (v1)

## Overview
This document describes the real-time WebSocket communication protocol used in **PharmaViyum CRM**.  
It enables communication between clients, pharmacists, and pharmacy managers, ensuring real-time updates for chat, notifications, and presence.

**Key points:**
- One WebSocket endpoint `/ws`
- JWT authentication
- Role-based channels (rooms)
- JSON message contract
- Versioned protocol for future-proofing

---

## Connection

**Endpoint:**
