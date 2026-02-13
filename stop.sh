#!/bin/bash
# ============================================================
#  OBD SuperStar Agent — Stop All Services
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo ""
echo -e "${RED}Stopping OBD SuperStar Agent...${NC}"

lsof -ti:8000 | xargs kill -9 2>/dev/null && echo -e "${GREEN}  ✓ Backend stopped${NC}" || echo "  - Backend was not running"
lsof -ti:3000 | xargs kill -9 2>/dev/null && echo -e "${GREEN}  ✓ Frontend stopped${NC}" || echo "  - Frontend was not running"

echo -e "${GREEN}✓ Done.${NC}"
echo ""
