
print("Start Import")
try:
    from mcp_backend_z3_current import prove_logic
    print("Import Successful")
except Exception as e:
    print(f"Import Failed: {e}")

print("End")
