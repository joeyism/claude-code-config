#!/usr/bin/env python3
"""Test that the masking feature keybinding works correctly."""

from claude_code_config.tui import ClaudeConfigApp
from claude_code_config.models import McpServer

print("=" * 70)
print("Testing Masking Feature - Keybinding Fix")
print("=" * 70)

# Test 1: Verify binding is uppercase V
print("\n✓ Test 1: Keybinding is uppercase V")
app = ClaudeConfigApp()
found = False
for binding in app.BINDINGS:
    if "toggle_mask" in str(binding):
        key, action, label = binding
        print(f"  Binding: key='{key}', action='{action}', label='{label}'")
        assert key == "V", f"Expected 'V', got '{key}'"
        assert action == "toggle_mask", f"Expected 'toggle_mask', got '{action}'"
        found = True
        break

assert found, "toggle_mask binding not found!"
print("  ✓ Uppercase V binding is correct")

# Test 2: Verify action method exists
print("\n✓ Test 2: action_toggle_mask method exists")
assert hasattr(app, 'action_toggle_mask'), "action_toggle_mask method not found!"
print("  ✓ Method exists")

# Test 3: Verify mask_value method exists
print("\n✓ Test 3: mask_value method exists")
assert hasattr(app, 'mask_value'), "mask_value method not found!"
print("  ✓ Method exists")

# Test 4: Test masking logic
print("\n✓ Test 4: Masking logic works")
test_secret = "sk-1234567890abcdef"

# Test masked (default)
assert app.mask_sensitive_values == True, "Should default to masked"
masked = app.mask_value(test_secret)
assert masked == "****", f"Expected '****', got '{masked}'"
print(f"  Masked: '{test_secret}' → '{masked}' ✓")

# Test unmasked
app.mask_sensitive_values = False
unmasked = app.mask_value(test_secret)
assert unmasked == test_secret, f"Expected '{test_secret}', got '{unmasked}'"
print(f"  Unmasked: '{test_secret}' → '{unmasked}' ✓")

# Test 5: Verify lowercase v is still for view_pasted
print("\n✓ Test 5: Lowercase 'v' still works for view_pasted")
found = False
for binding in app.BINDINGS:
    if binding[0] == "v":
        key, action, label = binding
        print(f"  Binding: key='{key}', action='{action}', label='{label}'")
        assert action == "view_pasted", f"Expected 'view_pasted', got '{action}'"
        found = True
        break

assert found, "lowercase v binding not found!"
print("  ✓ Lowercase 'v' is still view_pasted (no conflict)")

print("\n" + "=" * 70)
print("All Tests Passed! ✓")
print("=" * 70)
print("\nSummary:")
print("  • Uppercase V toggles masking")
print("  • Lowercase v views pasted content")
print("  • No keybinding conflicts")
print("  • Masking logic works correctly")
print("\nTo use in the app: Press capital V to toggle masking")
