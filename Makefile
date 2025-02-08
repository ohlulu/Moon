#!make
.DEFAULT_GOAL := run

# ====== 基礎設定 ====== #
PYTHON = python3
SRC_DIR = src

# Colors for pretty output
NC    	= \033[0m
GREEN 	= \033[0;32m
BLUE 	= \033[0;34m
RED 	= \033[0;31m
YELLOW	= \033[1;33m

# ====== 執行項目 ====== #
.PHONY: run
run:
	@echo "$(BLUE)開始執行主程式...$(NC)"
	$(PYTHON) -m $(SRC_DIR).main

.PHONY: collect
collect:
	@echo "$(BLUE)開始執行資料收集...$(NC)"
	$(PYTHON) -m $(SRC_DIR).services.market_data_collector

.PHONY: analyze-spot
analyze-spot:
	@echo "$(BLUE)開始分析現貨市場...$(NC)"
	$(PYTHON) -m $(SRC_DIR).analyze_spot

.PHONY: analyze-swap
analyze-swap:
	@echo "$(BLUE)開始分析合約市場...$(NC)"
	$(PYTHON) -m $(SRC_DIR).analyze_swap\

.PHONY: analyze-swap-v2
analyze-swap-v2:
	@echo "$(BLUE)開始分析合約市場...$(NC)"
	$(PYTHON) -m $(SRC_DIR).analyze_swap_v2

.PHONY: analyze-grid
analyze-grid:
	@echo "$(BLUE)開始分析網格市場...$(NC)"
	$(PYTHON) -m $(SRC_DIR).analyze_grid

# ====== 安裝依賴 ====== #
.PHONY: install
install:
	@echo "$(BLUE)開始安裝依賴套件...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)依賴套件安裝完成！$(NC)"

# # ====== 幫助信息 ====== #
# .PHONY: help
# help:
# 	@echo "$(BLUE)=============================="
# 	@echo "     可用的 make 指令列表"
# 	@echo "==============================$(NC)"
# 	@echo "$(GREEN)基本操作:$(NC)"
# 	@echo "  $(YELLOW)make run$(NC)           - 執行主程式"
# 	@echo "  $(YELLOW)make install$(NC)       - 安裝依賴套件"
# 	@echo ""
# 	@echo "$(GREEN)清理任務:$(NC)"
# 	@echo "  $(YELLOW)make clean$(NC)         - 清理暫存檔案"
# 	@echo "  $(YELLOW)make clean-reports$(NC)  - 清理分析報告"
# 	@echo ""
# 	@echo "$(GREEN)其他:$(NC)"
# 	@echo "  $(YELLOW)make help$(NC)          - 顯示此幫助信息"
# 	@echo "$(BLUE)==============================$(NC)"