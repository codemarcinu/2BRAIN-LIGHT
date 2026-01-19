import sys
import os

print("🔍 Checking imports...")
try:
    import finanse
    print("✅ Finanse: OK")
except ImportError as e:
    print(f"❌ Finanse Error: {e}")

try:
    import wiedza
    print("✅ Wiedza: OK")
except ImportError as e:
    print(f"❌ Wiedza Error: {e}")

try:
    import watcher
    print("✅ Watcher: OK")
except ImportError as e:
    print(f"❌ Watcher Error: {e}")
    
try:
    import bot
    print("✅ Bot: OK")
except ImportError as e:
    print(f"❌ Bot Error: {e}")

print("Done.")
