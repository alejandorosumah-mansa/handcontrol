#!/usr/bin/env make -f

# HandControl macOS Build Makefile

.PHONY: help build build-py311 clean install-deps test dmg

help:
	@echo "HandControl macOS Build"
	@echo "======================"
	@echo ""
	@echo "Commands:"
	@echo "  build-py311    Build .app with Python 3.11 (fixes cv2 corruption)"
	@echo "  build          Build .app with current Python (may fail on 3.9)"
	@echo "  clean          Clean build artifacts"
	@echo "  install-deps   Install Python 3.11 via Homebrew"
	@echo "  test           Test the built app"
	@echo "  dmg            Create DMG from built app"

# Build with Python 3.11 (recommended - fixes cv2 corruption)
build-py311:
	@echo "Building with Python 3.11..."
	./build_app_py311.py

# Build with current Python (legacy, may fail with cv2 corruption on Python 3.9)
build:
	@echo "Building with current Python..."
	python build_app.py

# Install Python 3.11 if not available
install-deps:
	@if ! command -v python3.11 >/dev/null 2>&1; then \
		echo "Installing Python 3.11..."; \
		brew install python@3.11; \
	else \
		echo "Python 3.11 already installed"; \
	fi

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ venv_py311/ "*.spec"
	rm -rf build_resources/MinorityReport.iconset/

# Test the built app
test:
	@if [ -f "dist/Minority Report.app/Contents/MacOS/Minority Report" ]; then \
		echo "Testing built app..."; \
		"./dist/Minority Report.app/Contents/MacOS/Minority Report" --help; \
	else \
		echo "❌ App not found. Run 'make build-py311' first."; \
		exit 1; \
	fi

# Create DMG
dmg: test
	@echo "Creating DMG..."
	hdiutil create -volname "Minority Report" -srcfolder "dist/Minority Report.app" -ov -format UDZO "dist/MinorityReport.dmg"
	@echo "✅ DMG created: dist/MinorityReport.dmg"