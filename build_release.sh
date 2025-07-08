#!/bin/bash

# RELEASE build script for PyYAML-Rust

echo "🔥 STARTING RELEASE COMPILATION (EXTREME OPTIMIZATIONS)"
echo "="*60

# Configure environment
export PATH="$HOME/.cargo/bin:$PATH"
source "$HOME/.cargo/env" 2>/dev/null || true
source venv/bin/activate

# Verify everything is available
if ! command -v rustc &> /dev/null; then
    echo "❌ rustc not found"
    exit 1
fi

if ! command -v maturin &> /dev/null; then
    echo "❌ maturin not found"
    exit 1
fi

echo "✅ Rust detected: $(rustc --version)"
echo "✅ Maturin detected: $(maturin --version)"

# Compile in RELEASE mode with maximum optimizations
echo ""
echo "🚀 Building in RELEASE mode..."
echo "   - Maximum speed optimizations"
echo "   - Aggressive inlining"
echo "   - No debug symbols"

# Configure variables for extreme optimization
export RUSTFLAGS="-C target-cpu=native -C opt-level=3"

maturin develop --release --strip

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 RELEASE COMPILATION SUCCESSFUL!"
    echo "   📊 Optimized module installed"
    echo "   🚀 Ready for extreme benchmarks"
else
    echo "❌ Error in RELEASE compilation"
    exit 1
fi 